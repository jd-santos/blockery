"""Offline release preparation tests. No GitHub writes or real exports."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import build_pack, check_exports, prepare_release


class ReleaseTests(unittest.TestCase):
    slug = "blockery-server-survival"
    version = "2026.10.17"
    revision = "a" * 40

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "build").mkdir()
        (self.root / "LICENSE").write_text("Fixture license\n")
        (self.root / "build/NOTICE.txt").write_text("Fixture notice\n")
        self.recipes()
        self.notes = self.root / "docs/releases/server-survival-2026.10.17.md"
        self.notes.parent.mkdir(parents=True)
        self.notes.write_text("Fixture release notes. Not a real release.\n")

    def recipes(self, pending="[]"):
        (self.root / "build/profiles.toml").write_text(
            '[profiles.blockery-server-survival]\nname = "Survival"\n'
            'side = "server"\nmods = []\nfiles = []\n'
            f'pending = {pending}\n'
            '[profiles.blockery-server-creative]\nextends = "blockery-server-survival"\n'
        )

    def test_plan_preserves_tag_convention_and_exact_notes_path(self):
        result = prepare_release.release_plan(self.root, self.slug, self.version)
        self.assertEqual(result["tag"], "server-survival-2026.10.17")
        self.assertEqual(result["notes"], str(self.notes.relative_to(self.root)))
        self.assertEqual(result["archive"],
                         "local/dist/blockery-server-survival-2026.10.17.mrpack")

    def test_invalid_profile_or_version_is_rejected_before_reading_notes(self):
        for slug, version in (
            ("unknown", self.version), (self.slug, "../bad"),
            (self.slug, "2026.10.17-draft"), (self.slug, "unreleased"),
            (self.slug, "x\nrun=bad"), (self.slug, ""),
        ):
            with self.subTest(slug=slug, version=version), self.assertRaises(
                build_pack.BuildError
            ):
                prepare_release.release_plan(self.root, slug, version)

    def test_inherited_pending_checks_block_before_export(self):
        self.recipes('["Test this candidate"]')
        for slug in (self.slug, "blockery-server-creative"):
            with self.subTest(slug=slug), patch(
                "scripts.prepare_release.build_pack.build"
            ) as build, self.assertRaisesRegex(build_pack.BuildError, "Release blocked"):
                prepare_release.prepare(self.root, slug, self.version, self.revision)
            build.assert_not_called()

    def test_missing_empty_and_symlinked_notes_are_rejected(self):
        self.notes.unlink()
        with self.assertRaisesRegex(build_pack.BuildError, "Missing source"):
            prepare_release.release_plan(self.root, self.slug, self.version)
        self.notes.write_text(" \n")
        with self.assertRaisesRegex(build_pack.BuildError, "empty"):
            prepare_release.release_plan(self.root, self.slug, self.version)
        self.notes.unlink()
        self.notes.symlink_to(self.root / "LICENSE")
        with self.assertRaisesRegex(build_pack.BuildError, "symlinks"):
            prepare_release.release_plan(self.root, self.slug, self.version)

    def test_bundle_contains_audited_bytes_notes_checksums_and_source(self):
        archive = self.root / "local/dist" / f"{self.slug}-{self.version}.mrpack"
        archive.parent.mkdir(parents=True)
        archive.write_bytes(b"Fixture archive bytes")
        record = {"archive": archive.name,
                  "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                  "dependencies": {"minecraft": "1.21.10", "fabric-loader": "0.19.5"}}
        with patch("scripts.prepare_release.validate_pack.validate") as validate, patch(
            "scripts.prepare_release.build_pack.build", return_value=archive
        ) as build, patch(
            "scripts.prepare_release.check_exports.audit_archive", return_value=record
        ) as audit:
            result = prepare_release.prepare(self.root, self.slug, self.version, self.revision)
        validate.assert_called_once_with(self.root)
        build.assert_called_once_with(self.root, self.slug, self.version)
        audit.assert_called_once_with(self.root, self.slug, self.version, archive)
        bundle = self.root / "local/release"
        self.assertEqual(json.loads((bundle / "release-set.json").read_text()), result)
        self.assertEqual(result["sourceRevision"], self.revision)
        self.assertEqual(result["artifacts"], [record])
        self.assertEqual((bundle / "release-notes.md").read_bytes(), self.notes.read_bytes())
        self.assertEqual((bundle / "SHA256SUMS").read_text(),
                         f"{record['sha256']}  {archive.name}\n")
        self.assertEqual(result["releaseNotes"]["sha256"],
                         hashlib.sha256(self.notes.read_bytes()).hexdigest())
        with patch("scripts.prepare_release.build_pack.build") as build, self.assertRaisesRegex(
            build_pack.BuildError, "already exists"
        ):
            prepare_release.prepare(self.root, self.slug, self.version, self.revision)
        build.assert_not_called()

    def test_failed_validation_or_archive_audit_cannot_produce_release_bundle(self):
        for stage, error in (
            ("validate_pack.validate", build_pack.BuildError("bad source")),
            ("check_exports.audit_archive", check_exports.ExportCheckError("bad archive")),
        ):
            with self.subTest(stage=stage), patch(
                "scripts.prepare_release.validate_pack.validate"
            ), patch("scripts.prepare_release.build_pack.build"), patch(
                "scripts.prepare_release." + stage, side_effect=error
            ), self.assertRaises((build_pack.BuildError, check_exports.ExportCheckError)):
                prepare_release.prepare(self.root, self.slug, self.version, self.revision)
            self.assertFalse((self.root / "local/release").exists())

    def test_invalid_revision_rejected_before_build(self):
        with patch("scripts.prepare_release.build_pack.build") as build, self.assertRaisesRegex(
            build_pack.BuildError, "commit ID"
        ):
            prepare_release.prepare(self.root, self.slug, self.version, "main")
        build.assert_not_called()


if __name__ == "__main__":
    unittest.main()
