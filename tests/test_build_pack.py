"""Fixture-based tests. No network requests or real Minecraft processes."""

import hashlib
import json
import tempfile
import tomllib
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from scripts import build_pack as builder


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "build").mkdir()
        (self.root / "mods").mkdir()
        (self.root / "config").mkdir()
        (self.root / "pack.toml").write_text(
            'name = "Source Pack"\nversion = "unreleased"\npack-format = "packwiz:1.1.0"\n'
            '[index]\nfile = "index.toml"\nhash-format = "sha256"\nhash = "original"\n'
            '[versions]\nminecraft = "1.21.10"\nfabric = "0.19.5"\n'
        )
        (self.root / "index.toml").write_text("original index\n")
        for name, side in (("shared", "both"), ("client", "client"), ("server", "server")):
            (self.root / f"mods/{name}.pw.toml").write_text(
                f'name = "{name}"\nfilename = "{name}.jar"\nside = "{side}"\n'
                '[download]\nurl = "https://cdn.modrinth.com/example.jar"\n'
                'hash-format = "sha512"\nhash = "example"\n'
            )
        (self.root / "config/shared.json").write_text('{"enabled": true}\n')
        (self.root / "config/unselected.json").write_text('{}\n')
        self.recipes(
            '[profiles.base]\nname = "Base"\nside = "client"\n'
            'mods = ["mods/shared.pw.toml"]\nfiles = ["config/shared.json"]\n'
            'pending = ["Decide base"]\n'
            '[profiles.pro]\nname = "Pro"\nextends = "base"\n'
            'mods = ["mods/client.pw.toml", "mods/shared.pw.toml"]\n'
            'pending = ["Review extras"]\n'
        )

    def recipes(self, content):
        (self.root / "build/profiles.toml").write_text(content)

    def snapshot(self):
        return {
            str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in self.root.rglob("*")
            if p.is_file() and "local" not in p.relative_to(self.root).parts
        }

    def test_inheritance_deduplicates_and_retains_pending(self):
        profile = builder.plan(self.root, "pro")
        self.assertEqual(profile["mods"], ["mods/shared.pw.toml", "mods/client.pw.toml"])
        self.assertEqual(profile["files"], ["config/shared.json"])
        self.assertEqual(profile["pending"], ["Decide base", "Review extras"])

    def test_cycle_and_unknown_parent(self):
        for content in (
            '[profiles.a]\nextends = "b"\n[profiles.b]\nextends = "a"\n',
            '[profiles.a]\nextends = "missing"\n',
        ):
            with self.subTest(content=content):
                self.recipes(content)
                with self.assertRaises(builder.BuildError):
                    builder.plan(self.root, "a")

    def test_cross_side_inheritance_and_incompatible_mod_rejected(self):
        self.recipes(
            '[profiles.base]\nside = "client"\n'
            '[profiles.server]\nextends = "base"\nside = "server"\n'
        )
        with self.assertRaisesRegex(builder.BuildError, "inherit across"):
            builder.plan(self.root, "server")
        self.recipes('[profiles.server]\nside = "server"\nmods = ["mods/client.pw.toml"]\n')
        with self.assertRaisesRegex(builder.BuildError, "incompatible"):
            builder.plan(self.root, "server")

    def test_paths_rejected_before_reading(self):
        for value in (
            "../private.json", "/absolute", "config//x.json", "config/./x.json",
            "config\\x.json", "config/.env.schema", "config/secrets.json",
            "config/access-token.json", "config/key.pem", "config/password.key",
            "config/NoChatReports/NCR-Encryption.json", "config/axiom/axiom.json",
            "config/ops.json", "config/world/x.json", "config/audioplayer_uploads/x.json",
        ):
            with self.subTest(path=value), self.assertRaises(builder.BuildError):
                builder.safe_path(value)

    def test_missing_sources_and_source_symlinks(self):
        with self.assertRaisesRegex(builder.BuildError, "Missing source"):
            builder.source_path(self.root, "config/missing.json")
        (self.root / "config/link.json").symlink_to(self.root / "config/shared.json")
        with self.assertRaisesRegex(builder.BuildError, "symlinks"):
            builder.source_path(self.root, "config/link.json")

    def test_metadata_destination_traversal_and_collisions(self):
        client = self.root / "mods/client.pw.toml"
        text = client.read_text()
        for filename in ("../outside.jar", "shared.jar"):
            with self.subTest(filename=filename):
                client.write_text(text.replace("client.jar", filename))
                with self.assertRaises(builder.BuildError):
                    builder.plan(self.root, "pro")

    def test_unknown_fields_invalid_arrays_and_unapproved_bundled_files(self):
        for field in (
            'modz = []', 'mods = "mods/shared.pw.toml"', 'pending = [1]',
            'files = ["README.md"]', 'files = ["config/mod.jar"]',
            'files = ["config/mod.JAR"]', 'files = ["config/pack.ZIP"]',
            'files = ["config/entry.PW.TOML"]',
        ):
            with self.subTest(field=field):
                self.recipes('[profiles.base]\nside = "client"\n' + field + '\n')
                with self.assertRaises(builder.BuildError):
                    builder.plan(self.root, "base")

    def test_release_and_empty_draft_gates(self):
        with patch.object(builder.subprocess, "run") as run:
            with self.assertRaisesRegex(builder.BuildError, "Release blocked"):
                builder.build(self.root, "base", "1.0.0")
            run.assert_not_called()
        self.recipes('[profiles.base]\nside = "client"\nmods = []\n')
        with self.assertRaisesRegex(builder.BuildError, "No mods"):
            builder.build(self.root, "base", "preview", draft=True)

    def test_version_traversal_and_unreleased_release_blocked(self):
        self.recipes('[profiles.base]\nside = "client"\nmods = ["mods/shared.pw.toml"]\n')
        for version in ("../outside", "", "a/b", "unreleased"):
            with self.subTest(version=version), self.assertRaises(builder.BuildError):
                builder.build(self.root, "base", version)

    def fake_packwiz(self, command, cwd, check):
        self.assertTrue(check)
        if command[1] == "refresh":
            self.assertFalse((cwd / "config/unselected.json").exists())
            self.assertFalse((cwd / "build").exists())
            self.assertFalse((cwd / "mods/server.pw.toml").exists())
            staged = tomllib.loads((cwd / "pack.toml").read_text())
            self.assertEqual(staged["name"], "Pro")
            self.assertEqual(staged["version"], "preview-draft")
            self.assertEqual(staged["versions"], {"minecraft": "1.21.10", "fabric": "0.19.5"})
            self.assertEqual((cwd / "mods/shared.pw.toml").read_bytes(),
                             (self.root / "mods/shared.pw.toml").read_bytes())
        else:
            self.assertEqual(command[1:4], ["modrinth", "export", "-o"])
            with zipfile.ZipFile(command[4], "w") as archive:
                archive.writestr("modrinth.index.json", json.dumps({"versionId": "preview-draft"}))

    def test_isolated_draft_build_and_no_overwrite(self):
        before = self.snapshot()
        with patch.object(builder.shutil, "which", return_value="/fixture/packwiz"), patch.object(
            builder.subprocess, "run", side_effect=self.fake_packwiz
        ) as run:
            result = builder.build(self.root, "pro", "preview", draft=True)
            self.assertEqual(result.name, "pro-preview-draft.mrpack")
            self.assertTrue(result.is_file())
            self.assertEqual(run.call_count, 2)
            with self.assertRaisesRegex(builder.BuildError, "already exists"):
                builder.build(self.root, "pro", "preview", draft=True)
            self.assertEqual(run.call_count, 2)
        self.assertEqual(before, self.snapshot())

    def test_copy_failure_or_interrupt_removes_partial_export_and_allows_retry(self):
        artifact = self.root / "local/dist/pro-preview-draft.mrpack"

        def fail_copy(incoming, outgoing):
            outgoing.write(b"partial archive")
            raise failure

        with (
            patch.object(builder.shutil, "which", return_value="/fixture/packwiz"),
            patch.object(builder.subprocess, "run", side_effect=self.fake_packwiz),
        ):
            for failure in (OSError("copy failed"), KeyboardInterrupt()):
                with (
                    self.subTest(failure=type(failure).__name__),
                    patch.object(builder.shutil, "copyfileobj", side_effect=fail_copy),
                    self.assertRaises(type(failure)),
                ):
                    builder.build(self.root, "pro", "preview", draft=True)
                self.assertFalse(artifact.exists())
            self.assertEqual(builder.build(self.root, "pro", "preview", draft=True), artifact)
            with zipfile.ZipFile(artifact) as archive:
                self.assertIn("modrinth.index.json", archive.namelist())

    def test_missing_packwiz_and_output_symlink(self):
        with (
            patch.object(builder.shutil, "which", return_value=None),
            self.assertRaisesRegex(builder.BuildError, "packwiz is required"),
        ):
            builder.build(self.root, "pro", "preview", draft=True)
        (self.root / "local").symlink_to(self.root / "config", target_is_directory=True)
        with (
            patch.object(builder.shutil, "which", return_value="/fixture/packwiz"),
            self.assertRaisesRegex(builder.BuildError, "Output directory"),
        ):
            builder.build(self.root, "pro", "preview", draft=True)


if __name__ == "__main__":
    unittest.main()
