"""Offline maintenance fixtures. No real updates, network access, or world writes."""

import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import scripts.build_pack as builder
import scripts.upgrade_pack as upgrade
import scripts.validate_pack as validator


class Terminal(io.StringIO):
    def isatty(self):
        return True


class MaintenanceFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for directory in ("build", "mods", "config"):
            (self.root / directory).mkdir()
        (self.root / "LICENSE").write_text("Fixture license\n")
        (self.root / "build/NOTICE.txt").write_text("Fixture notice\n")
        (self.root / "build/profiles.toml").write_text(
            '[profiles.base]\nname = "Base"\nside = "client"\n'
            'mods = ["mods/shared.pw.toml"]\n'
            '[profiles.extras]\nname = "Extras"\nextends = "base"\n'
            'mods = ["mods/client.pw.toml"]\n'
            '[profiles.server]\nname = "Server"\nside = "server"\n'
            'mods = ["mods/shared.pw.toml", "mods/server.pw.toml"]\n'
        )
        for name, side in (("shared", "both"), ("client", "client"), ("server", "server")):
            (self.root / f"mods/{name}.pw.toml").write_text(
                f'name = "{name}"\nfilename = "{name}.jar"\nside = "{side}"\n'
                '[download]\nurl = "https://cdn.modrinth.com/data/example.jar"\n'
                f'hash-format = "sha512"\nhash = "{"a" * 128}"\n'
                f'[update.modrinth]\nmod-id = "{name}"\nversion = "old-{name}"\n'
            )
        self.refresh()

    def refresh(self):
        index = 'hash-format = "sha256"\n'
        for path in sorted((self.root / "mods").glob("*.pw.toml")):
            index += (
                f'[[files]]\nfile = "mods/{path.name}"\n'
                f'hash = "{hashlib.sha256(path.read_bytes()).hexdigest()}"\nmetafile = true\n'
            )
        (self.root / "index.toml").write_text(index)
        (self.root / "pack.toml").write_text(
            'name = "Fixture"\npack-format = "packwiz:1.1.0"\n'
            '[index]\nfile = "index.toml"\nhash-format = "sha256"\n'
            f'hash = "{hashlib.sha256(index.encode()).hexdigest()}"\n'
            '[versions]\nminecraft = "1.0"\nfabric = "0.1"\n'
        )

    def snapshot(self):
        return {str(path.relative_to(self.root)): path.read_bytes()
                for path in self.root.rglob("*") if path.is_file()}

    def disable(self, value="mods/shared.pw.toml", confirm=None):
        upgrade.change_disabled(
            self.root, value, "Waiting for target support", stdin=Terminal(), stdout=Terminal(),
            confirm=confirm if confirm is not None else lambda prompt: "yes",
        )

    @staticmethod
    def versions(url) -> list[dict[str, Any]]:
        if "meta.fabricmc.net" in url:
            return [{"loader": {"version": "0.2"}}]
        project = url.split("/project/")[1].split("/")[0]
        return [{"id": f"new-{project}", "project_id": project, "version_number": "2.0",
                 "date_published": "2026-10-16T00:00:00Z", "version_type": "release",
                 "game_versions": ["2.0"], "loaders": ["fabric"], "dependencies": []}]


class ValidationTests(MaintenanceFixture):
    def test_valid_source_and_report_are_read_only(self):
        before = self.snapshot()
        result = validator.validate(self.root)
        self.assertEqual(len(result["profiles"]), 3)
        fetch = Mock(side_effect=AssertionError("Offline must not fetch"))
        report = upgrade.assess(self.root, "2.0", "0.2", fetch=fetch)
        self.assertEqual(report["loader"]["status"], "unknown")
        self.assertTrue(all(entry["status"] == "unknown" for entry in report["entries"]))
        self.assertEqual(before, self.snapshot())
        fetch.assert_not_called()

    def test_stale_index_and_indexed_file_fail(self):
        (self.root / "index.toml").write_text("changed")
        with self.assertRaisesRegex(builder.BuildError, "index hash"):
            validator.validate(self.root)
        self.refresh()
        (self.root / "mods/shared.pw.toml").write_text("changed")
        with self.assertRaisesRegex(builder.BuildError, "file hash"):
            validator.validate(self.root)

    def test_selected_metadata_must_be_indexed(self):
        index = (self.root / "index.toml").read_text()
        # Keep a valid index hash while removing a selected entry.
        path = self.root / "mods/shared.pw.toml"
        contents = path.read_text()
        path.unlink()
        self.refresh()
        path.write_text(contents)
        with self.assertRaisesRegex(builder.BuildError, "not indexed"):
            validator.validate(self.root)
        self.assertIn("shared", index)

    def test_policy_unknown_paths_empty_reasons_and_symlinks_fail(self):
        for value in ("../outside.pw.toml", "config/file.pw.toml", "mods/missing.pw.toml"):
            with self.subTest(value=value):
                (self.root / upgrade.POLICY).write_text('[disabled]\n' + json.dumps(value) + ' = "why"\n')
                with self.assertRaises(builder.BuildError):
                    builder.plan(self.root, "base")
        (self.root / upgrade.POLICY).write_text('[disabled]\n"mods/shared.pw.toml" = ""\n')
        with self.assertRaisesRegex(builder.BuildError, "reason"):
            builder.plan(self.root, "base")
        (self.root / upgrade.POLICY).unlink()
        (self.root / upgrade.POLICY).symlink_to(self.root / "mods/shared.pw.toml")
        with self.assertRaisesRegex(builder.BuildError, "symlink"):
            builder.plan(self.root, "base")


class AssessmentTests(MaintenanceFixture):
    def test_online_candidates_and_loader_are_not_applied(self):
        before = self.snapshot()
        report = upgrade.assess(self.root, "2.0", "0.2", online=True, fetch=self.versions)
        self.assertEqual(report["loader"]["status"], "available")
        self.assertEqual({entry["status"] for entry in report["entries"]}, {"candidate"})
        self.assertEqual(before, self.snapshot())
        self.assertIn("not implemented", report["confirmation"])

    def test_metadata_mismatch_prerelease_and_network_failure_are_not_success(self):
        def prereleases(url):
            result = self.versions(url)
            if "api.modrinth.com" in url:
                result[0]["version_type"] = "beta"
            return result

        report = upgrade.assess(self.root, "2.0", "0.2", True, fetch=prereleases)
        self.assertEqual({entry["status"] for entry in report["entries"]}, {"unavailable"})
        report = upgrade.assess(self.root, "2.0", "0.2", True, True, fetch=prereleases)
        self.assertEqual({entry["status"] for entry in report["entries"]}, {"candidate"})
        report = upgrade.assess(self.root, "2.0", "0.2", True, fetch=Mock(side_effect=OSError("offline")))
        self.assertEqual({entry["status"] for entry in report["entries"]}, {"unknown"})
        self.assertEqual(report["loader"]["status"], "unknown")

    def test_disabled_entries_are_not_queried_or_reenabled_and_dependency_is_reported(self):
        self.disable()
        before = self.snapshot()
        def dependencies(url):
            result = self.versions(url)
            if "api.modrinth.com" in url:
                result[0]["dependencies"] = [{"dependency_type": "required", "project_id": "shared"}]
            return result
        fetch = Mock(side_effect=dependencies)
        report = upgrade.assess(self.root, "2.0", "0.2", True, fetch=fetch)
        self.assertFalse(any("/project/shared/" in call.args[0] for call in fetch.call_args_list))
        self.assertTrue(any(finding["status"] == "disabled-required-dependency" for finding in report["dependency_findings"]))
        self.assertEqual(before, self.snapshot())

    def test_malformed_modrinth_evidence_is_unknown_and_read_only(self):
        cases = (
            lambda versions: [None],
            lambda versions: ["not an object"],
            lambda versions: [{**versions[0], "game_versions": None}],
            lambda versions: [{**versions[0], "loaders": [None]}],
            lambda versions: [{**versions[0], "date_published": None}],
            lambda versions: [{**versions[0], "date_published": "zzz"}],
            lambda versions: [{**versions[0], "date_published": "2026-10-16"}],
            lambda versions: [{**versions[0], "date_published": "2026-10-16T00:00:00"}],
            lambda versions: [{**versions[0], "dependencies": [{"dependency_type": "unexpected"}]}],
            lambda versions: [{**versions[0], "dependencies": None}],
            lambda versions: [{**versions[0], "dependencies": [None]}],
            lambda versions: [{**versions[0], "dependencies": [{"dependency_type": "required", "project_id": []}]}],
        )
        before = self.snapshot()
        for malformed in cases:
            def fetch(url, malformed=malformed):
                versions = self.versions(url)
                return malformed(versions) if "api.modrinth.com" in url else versions
            with self.subTest(malformed=malformed):
                report = upgrade.assess(self.root, "2.0", "0.2", True, fetch=fetch)
                self.assertEqual({entry["status"] for entry in report["entries"]}, {"unknown"})
                self.assertTrue(all(entry["candidate"] is None and entry["issues"] for entry in report["entries"]))
                self.assertEqual(report["dependency_findings"], [])
                self.assertEqual(before, self.snapshot())

    def test_publication_times_compare_instants_and_normalize_to_utc(self):
        def fetch(url):
            versions = self.versions(url)
            if "api.modrinth.com" not in url:
                return versions
            newest = {**versions[0], "id": "newest", "date_published": "2026-10-16T00:30:00+00:00"}
            older = {**versions[0], "id": "older", "date_published": "2026-10-16T01:00:00+02:00"}
            return [older, newest]
        before = self.snapshot()
        report = upgrade.assess(self.root, "2.0", "0.2", True, fetch=fetch)
        for entry in report["entries"]:
            self.assertEqual(entry["candidate"]["version_id"], "newest")
            self.assertEqual(entry["candidate"]["published"], "2026-10-16T00:30:00+00:00")
        self.assertEqual(before, self.snapshot())

    def test_supported_dependency_types_remain_valid_evidence(self):
        for kind in ("required", "optional", "incompatible", "embedded"):
            def fetch(url, kind=kind):
                versions = self.versions(url)
                if "api.modrinth.com" in url:
                    versions[0]["dependencies"] = [{"dependency_type": kind, "project_id": "missing"}]
                return versions
            with self.subTest(kind=kind):
                report = upgrade.assess(self.root, "2.0", "0.2", True, fetch=fetch)
                self.assertEqual({entry["status"] for entry in report["entries"]}, {"candidate"})
                self.assertEqual(bool(report["dependency_findings"]), kind == "required")

    def test_malformed_loader_evidence_is_unknown_with_error(self):
        for malformed in ([None], [{"loader": None}], [{"loader": {"version": []}}]):
            def fetch(url, malformed=malformed):
                return malformed if "meta.fabricmc.net" in url else self.versions(url)
            with self.subTest(malformed=malformed):
                report = upgrade.assess(self.root, "2.0", "0.2", True, fetch=fetch)
                self.assertEqual(report["loader"]["status"], "unknown")
                self.assertIn("error", report["loader"])

    def test_api_fetch_rejects_local_or_untrusted_urls(self):
        for url in ("file:///etc/hosts", "http://api.modrinth.com/v2", "https://example.com/",
                    "https://api.modrinth.com@evil.invalid/v2", "https://api.modrinth.com:444/v2"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                upgrade.fetch_json(url)


class DisableTests(MaintenanceFixture):
    def test_noninteractive_and_declined_confirmation_never_write(self):
        before = self.snapshot()
        with self.assertRaisesRegex(builder.BuildError, "Interactive"):
            upgrade.change_disabled(self.root, "mods/shared.pw.toml", "why", stdin=io.StringIO(), stdout=io.StringIO())
        with self.assertRaisesRegex(builder.BuildError, "Not confirmed"):
            self.disable(confirm=lambda prompt: "no")
        self.assertEqual(before, self.snapshot())

    def test_confirmed_global_disable_and_enable_preserve_pins_and_inheritance(self):
        before = self.snapshot()
        self.disable()
        after = self.snapshot()
        self.assertEqual({path: value for path, value in after.items() if path != upgrade.POLICY}, before)
        for slug in ("base", "extras", "server"):
            profile = builder.plan(self.root, slug)
            self.assertNotIn("mods/shared.pw.toml", profile["mods"])
            self.assertIn("mods/shared.pw.toml", profile["disabled"])
        upgrade.change_disabled(self.root, "mods/shared.pw.toml", enable=True,
                                stdin=Terminal(), stdout=Terminal(), confirm=lambda prompt: "yes")
        self.assertIn("mods/shared.pw.toml", builder.plan(self.root, "base")["mods"])

    def test_source_changes_during_confirmation_are_rejected(self):
        def mutate(prompt):
            (self.root / "mods/shared.pw.toml").write_text("concurrent edit")
            return "yes"
        with self.assertRaisesRegex(builder.BuildError, "Source changed"):
            self.disable(confirm=mutate)
        self.assertFalse((self.root / upgrade.POLICY).exists())

    def test_source_changes_while_printing_preview_are_rejected(self):
        root = self.root
        class ChangingTerminal(Terminal):
            def write(self, value):
                recipes = root / "build/profiles.toml"
                recipes.write_text(recipes.read_text().replace('"mods/shared.pw.toml"', '"mods/client.pw.toml"'))
                return super().write(value)
        confirm = Mock(return_value="yes")
        with self.assertRaisesRegex(builder.BuildError, "Source changed"):
            upgrade.change_disabled(self.root, "mods/shared.pw.toml", "why",
                                    stdin=Terminal(), stdout=ChangingTerminal(), confirm=confirm)
        confirm.assert_not_called()
        self.assertFalse((self.root / upgrade.POLICY).exists())

    def test_source_changes_during_proposal_validation_are_rejected(self):
        validate = validator.validate
        calls = 0
        def concurrent_validate(root):
            nonlocal calls
            result = validate(root)
            calls += 1
            if calls == 2:
                recipes = root / "build/profiles.toml"
                recipes.write_text(recipes.read_text() + '\n# concurrent edit\n')
            return result
        with patch.object(validator, "validate", side_effect=concurrent_validate), self.assertRaisesRegex(builder.BuildError, "Source changed"):
            self.disable()
        self.assertFalse((self.root / upgrade.POLICY).exists())

    def test_policy_changes_during_confirmation_are_rejected(self):
        def mutate(prompt):
            (self.root / upgrade.POLICY).write_text('[disabled]\n"mods/client.pw.toml" = "other change"\n')
            return "yes"
        with self.assertRaisesRegex(builder.BuildError, "Policy changed"):
            self.disable(confirm=mutate)

    def test_stage_omits_disabled_metadata_without_deleting_source(self):
        self.disable()
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            builder.stage_pack(self.root, stage, builder.plan(self.root, "extras"), "fixture-draft")
            self.assertFalse((stage / "mods/shared.pw.toml").exists())
            self.assertTrue((stage / "mods/client.pw.toml").exists())
            self.assertTrue((self.root / "mods/shared.pw.toml").exists())


if __name__ == "__main__":
    unittest.main()
