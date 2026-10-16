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
        (self.root / "LICENSE").write_text("Fixture license text\n")
        (self.root / "build/NOTICE.txt").write_text("Fixture scoped notice\n")
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
            '[profiles.expanded]\nname = "Extras Client"\nextends = "base"\n'
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
        profile = builder.plan(self.root, "expanded")
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

    def test_notice_sources_are_required_and_reject_symlinks(self):
        for value in builder.NOTICE_SOURCES:
            with self.subTest(source=value):
                source = self.root / value
                text = source.read_text()
                source.unlink()
                with self.assertRaisesRegex(builder.BuildError, "Missing source"):
                    builder.plan(self.root, "expanded")
                source.symlink_to(self.root / "config/shared.json")
                with self.assertRaisesRegex(builder.BuildError, "symlinks"):
                    builder.plan(self.root, "expanded")
                source.unlink()
                source.write_text(text)

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
                    builder.plan(self.root, "expanded")

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
            for source, destination in builder.NOTICE_SOURCES.items():
                self.assertEqual((cwd / destination).read_bytes(),
                                 (self.root / source).read_bytes())
            self.assertFalse((cwd / "config/unselected.json").exists())
            self.assertFalse((cwd / "build").exists())
            self.assertFalse((cwd / "mods/server.pw.toml").exists())
            staged = tomllib.loads((cwd / "pack.toml").read_text())
            self.assertEqual(staged["name"], "Extras Client")
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
            result = builder.build(self.root, "expanded", "preview", draft=True)
            self.assertEqual(result.name, "expanded-preview-draft.mrpack")
            self.assertTrue(result.is_file())
            self.assertEqual(run.call_count, 2)
            with self.assertRaisesRegex(builder.BuildError, "already exists"):
                builder.build(self.root, "expanded", "preview", draft=True)
            self.assertEqual(run.call_count, 2)
        self.assertEqual(before, self.snapshot())

    def test_normal_release_preserves_version_and_sources(self):
        self.recipes(
            '[profiles.base]\nname = "Base"\nside = "client"\n'
            'mods = ["mods/shared.pw.toml"]\nfiles = ["config/shared.json"]\n'
            'pending = []\n'
        )
        before = self.snapshot()

        def export(command, cwd, check):
            self.assertTrue(check)
            staged = tomllib.loads((cwd / "pack.toml").read_text())
            self.assertEqual(staged["version"], "2026.10.12")
            if command[1] == "modrinth":
                with zipfile.ZipFile(command[4], "w") as archive:
                    archive.writestr(
                        "modrinth.index.json", json.dumps({"versionId": staged["version"]})
                    )

        with (
            patch.object(builder.shutil, "which", return_value="/fixture/packwiz"),
            patch.object(builder.subprocess, "run", side_effect=export) as run,
        ):
            result = builder.build(self.root, "base", "2026.10.12")
            self.assertEqual(result.name, "base-2026.10.12.mrpack")
            self.assertEqual(run.call_count, 2)
            with zipfile.ZipFile(result) as archive:
                self.assertEqual(
                    json.loads(archive.read("modrinth.index.json"))["versionId"],
                    "2026.10.12",
                )
        self.assertEqual(before, self.snapshot())

    def test_copy_failure_or_interrupt_removes_partial_export_and_allows_retry(self):
        artifact = self.root / "local/dist/expanded-preview-draft.mrpack"

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
                    builder.build(self.root, "expanded", "preview", draft=True)
                self.assertFalse(artifact.exists())
            self.assertEqual(builder.build(self.root, "expanded", "preview", draft=True), artifact)
            with zipfile.ZipFile(artifact) as archive:
                self.assertIn("modrinth.index.json", archive.namelist())

    def test_missing_packwiz_and_output_symlink(self):
        with (
            patch.object(builder.shutil, "which", return_value=None),
            self.assertRaisesRegex(builder.BuildError, "packwiz is required"),
        ):
            builder.build(self.root, "expanded", "preview", draft=True)
        (self.root / "local").symlink_to(self.root / "config", target_is_directory=True)
        with (
            patch.object(builder.shutil, "which", return_value="/fixture/packwiz"),
            self.assertRaisesRegex(builder.BuildError, "Output directory"),
        ):
            builder.build(self.root, "expanded", "preview", draft=True)


class RepositoryProfileTests(unittest.TestCase):
    """Check the real recipes without exports, network calls, or server execution."""

    root = Path(__file__).resolve().parents[1]
    base_downloads = {
        "mods/appleskin.pw.toml",
        "mods/fabric-api.pw.toml",
        "mods/ferrite-core.pw.toml",
        "mods/immediatelyfast.pw.toml",
        "mods/lithium.pw.toml",
        "mods/malilib.pw.toml",
        "mods/minihud.pw.toml",
        "mods/shulkerboxtooltip.pw.toml",
        "mods/simple-voice-chat.pw.toml",
        "mods/statuseffecttimer.pw.toml",
        "mods/view-distance-fix.pw.toml",
        "mods/xaeros-minimap.pw.toml",
        "mods/xaeros-world-map.pw.toml",
        "resourcepacks/redstone-tweaks.pw.toml",
    }
    shared_server_configs = {
        "config/armorposer.toml",
        "config/axesareweapons.json5",
        "config/bookshelfinspector-config.yml",
        "config/collective.json5",
        "config/fallingtree.json",
        "config/justmobheads.json5",
        "config/justmobheads/headchances.txt",
        "config/justplayerheads.json5",
        "config/NoChatReports/NCR-Common.json",
        "config/shulkerdropstwo.json5",
        "config/silencemobs.json5",
    }

    def test_server_configs_inherit_and_stage_exact_reviewed_sources(self):
        for slug in ("blockery-server-survival", "blockery-server-creative"):
            with self.subTest(profile=slug), tempfile.TemporaryDirectory() as temp:
                profile = builder.plan(self.root, slug)
                self.assertEqual(profile["side"], "server")
                self.assertEqual(set(profile["files"]), self.shared_server_configs)
                stage = Path(temp)
                builder.stage_pack(self.root, stage, profile, "config-preview-draft")
                actual = {
                    str(p.relative_to(stage))
                    for p in (stage / "config").rglob("*") if p.is_file()
                }
                self.assertEqual(actual, self.shared_server_configs)
                for value in actual:
                    self.assertEqual((stage / value).read_bytes(),
                                     (self.root / value).read_bytes())
                armor = tomllib.loads((stage / "config/armorposer.toml").read_text())
                self.assertTrue(armor["general"]["restrictResizeToOP"])
        self.assertEqual(builder.plan(self.root, "blockery-extras-client")["files"], [])

    def test_all_nonempty_profiles_stage_exact_license_notices(self):
        for slug in ("blockery-client", "blockery-extras-client", "blockery-server-survival", "blockery-server-creative"):
            with self.subTest(profile=slug), tempfile.TemporaryDirectory() as temp:
                profile = builder.plan(self.root, slug)
                self.assertEqual(profile["notices"], list(builder.NOTICE_SOURCES.values()))
                stage = Path(temp)
                builder.stage_pack(self.root, stage, profile, "notice-preview-draft")
                actual = {str(p.relative_to(stage))
                          for p in (stage / "blockery-notices").rglob("*") if p.is_file()}
                self.assertEqual(actual, set(builder.NOTICE_SOURCES.values()))
                for source, destination in builder.NOTICE_SOURCES.items():
                    self.assertEqual((stage / destination).read_bytes(),
                                     (self.root / source).read_bytes())
                self.assertFalse((stage / "LICENSE").exists())
                self.assertFalse((stage / "build").exists())

    def test_client_recipe_names_and_rejection_of_retired_slugs(self):
        expected = {
            "blockery-client": "Blockery Client",
            "blockery-extras-client": "Blockery Extras Client",
            "blockery-server-survival": "Blockery Server Survival",
            "blockery-server-creative": "Blockery Server Creative",
        }
        self.assertEqual(set(builder.read_recipes(self.root)), set(expected))
        for slug, name in expected.items():
            with self.subTest(profile=slug):
                profile = builder.plan(self.root, slug)
                self.assertEqual(profile["slug"], slug)
                self.assertEqual(profile["name"], name)
                with tempfile.TemporaryDirectory() as temp:
                    stage = Path(temp)
                    builder.stage_pack(self.root, stage, profile, "naming-preview-draft")
                    staged = tomllib.loads((stage / "pack.toml").read_text())
                    self.assertEqual(staged["name"], name)
        for retired in ("blockery", "blockery-pro"):
            with self.subTest(retired=retired), self.assertRaisesRegex(builder.BuildError, "Unknown profile"):
                builder.plan(self.root, retired)

    def test_base_client_matches_approved_everyday_client_selection(self):
        profile = builder.plan(self.root, "blockery-client")
        self.assertEqual(profile["side"], "client")
        self.assertEqual(set(profile["mods"]), self.base_downloads)
        self.assertEqual(len(profile["mods"]), len(self.base_downloads))

    def test_extras_client_is_an_additive_superset_without_duplicate_base_entries(self):
        recipes = builder.read_recipes(self.root)
        base = builder.plan(self.root, "blockery-client")
        expanded = builder.plan(self.root, "blockery-extras-client")
        self.assertEqual(recipes["blockery-extras-client"]["extends"], "blockery-client")
        self.assertTrue(set(base["mods"]) < set(expanded["mods"]))
        self.assertTrue(set(base["mods"]).isdisjoint(recipes["blockery-extras-client"]["mods"]))
        self.assertEqual(expanded["mods"][:len(base["mods"])], base["mods"])
        self.assertEqual(len(expanded["mods"]), len(set(expanded["mods"])))
        # Include carry-over entries as well as newly approved Extras Client features: none
        # of the previous full client loadout should disappear during this split.
        extras = {
            "mods/amecs.pw.toml",
            "mods/architectury-api.pw.toml",
            "mods/armor-poser.pw.toml",
            "mods/audioplayer.pw.toml",
            "mods/axes-are-weapons.pw.toml",
            "mods/axiom.pw.toml",
            "mods/bookshelf-inspector.pw.toml",
            "mods/cloth-config.pw.toml",
            "mods/collective.pw.toml",
            "mods/coord-finder.pw.toml",
            "mods/entity-model-features.pw.toml",
            "mods/entitytexturefeatures.pw.toml",
            "mods/fabric-language-kotlin.pw.toml",
            "mods/fallingtree.pw.toml",
            "mods/horse-statistics.pw.toml",
            "mods/inventory-profiles-next.pw.toml",
            "mods/jei.pw.toml",
            "mods/just-mob-heads.pw.toml",
            "mods/just-player-heads.pw.toml",
            "mods/libipn.pw.toml",
            "mods/litematica.pw.toml",
            "mods/modmenu.pw.toml",
            "mods/no-chat-reports.pw.toml",
            "mods/placeholder-api.pw.toml",
            "mods/screencopy.pw.toml",
            "mods/shulker-drops-two.pw.toml",
            "mods/silence-mobs.pw.toml",
            "mods/stendhal.pw.toml",
            "mods/styled-chat.pw.toml",
            "mods/tweakeroo.pw.toml",
            "mods/worldedit.pw.toml",
            "resourcepacks/fresh-animations.pw.toml",
        }
        self.assertEqual(set(expanded["mods"]), self.base_downloads | extras)
        self.assertTrue(extras.isdisjoint(base["mods"]))
        self.assertEqual(expanded["pending"], base["pending"] + recipes["blockery-extras-client"]["pending"])

    def test_client_stages_do_not_copy_legacy_configs_or_instance_settings(self):
        for slug in ("blockery-client", "blockery-extras-client"):
            with self.subTest(profile=slug), tempfile.TemporaryDirectory() as temp:
                profile = builder.plan(self.root, slug)
                self.assertEqual(profile["files"], [])
                stage = Path(temp)
                builder.stage_pack(self.root, stage, profile, "client-preview-draft")
                self.assertFalse((stage / "config").exists())
                self.assertFalse((stage / "options.txt").exists())
                self.assertFalse((stage / "servers.dat").exists())
                staged = {str(p.relative_to(stage)) for p in stage.rglob("*.pw.toml")}
                self.assertEqual(staged, set(profile["mods"]))
                for value in staged:
                    self.assertEqual((stage / value).read_bytes(), (self.root / value).read_bytes())

    def test_new_extras_client_mod_pins_are_client_only_and_excluded_from_servers(self):
        pins = {
            "mods/entity-model-features.pw.toml": ("4I1XuqiY", "9Gv6SVe7"),
            "mods/inventory-profiles-next.pw.toml": ("O7RBXm3n", "OUS6sPr1"),
        }
        for path, (project, version) in pins.items():
            with self.subTest(path=path):
                metadata = tomllib.loads((self.root / path).read_text())
                self.assertEqual(metadata["side"], "client")
                self.assertEqual(metadata["update"]["modrinth"], {"mod-id": project, "version": version})
                self.assertIn(path, builder.plan(self.root, "blockery-extras-client")["mods"])
                for slug in ("blockery-client", "blockery-server-survival", "blockery-server-creative"):
                    self.assertNotIn(path, builder.plan(self.root, slug)["mods"])

    def test_permissions_dependency_is_selected_only_by_server_profiles(self):
        path = "mods/fabric-permissions-api.pw.toml"
        metadata = tomllib.loads((self.root / path).read_text())
        self.assertEqual(metadata["side"], "server")
        for slug in ("blockery-server-survival", "blockery-server-creative"):
            with self.subTest(profile=slug):
                self.assertIn(path, builder.plan(self.root, slug)["mods"])
        for slug in ("blockery-client", "blockery-extras-client"):
            with self.subTest(profile=slug):
                self.assertNotIn(path, builder.plan(self.root, slug)["mods"])

    def test_survival_ready_and_unresolved_profiles_remain_blocked(self):
        self.assertEqual(builder.plan(self.root, "blockery-server-survival")["pending"], [])
        self.assertEqual(
            builder.plan(self.root, "blockery-server-creative")["pending"],
            ["Review creative target differences before release."],
        )
        for slug in ("blockery-client", "blockery-extras-client", "blockery-server-creative"):
            with self.subTest(profile=slug), patch.object(builder.subprocess, "run") as run:
                self.assertTrue(builder.plan(self.root, slug)["pending"])
                with self.assertRaisesRegex(builder.BuildError, "Release blocked"):
                    builder.build(self.root, slug, "2026.10.12")
                run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
