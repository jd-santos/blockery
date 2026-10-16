"""Fixture tests for the CI-only mrpack archive audit."""

import json
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

from scripts import check_exports


class ExportAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ("build", "mods", "config"):
            (self.root / directory).mkdir()
        (self.root / "LICENSE").write_bytes(b"Fixture license\n")
        (self.root / "build/NOTICE.txt").write_bytes(b"Fixture notice\n")
        (self.root / "pack.toml").write_text(
            '[versions]\nfabric = "0.19.5"\nminecraft = "1.21.10"\n'
        )
        download = ('[download]\nurl = "https://cdn.modrinth.com/fixture.jar"\n'
                    f'hash-format = "sha512"\nhash = "{"a" * 128}"\n')
        (self.root / "mods/client.pw.toml").write_text(
            'name = "Client fixture"\nfilename = "client.jar"\nside = "client"\n' + download
        )
        (self.root / "mods/server.pw.toml").write_text(
            'name = "Server fixture"\nfilename = "server.jar"\nside = "server"\n' + download
        )
        (self.root / "config/server.json").write_text('{"fixture": true}\n')
        (self.root / "build/profiles.toml").write_text(
            '[profiles.fixture-client]\n'
            'name = "Fixture Client"\nside = "client"\n'
            'mods = ["mods/client.pw.toml"]\nfiles = []\n'
            '[profiles.fixture-server]\n'
            'name = "Fixture Server"\nside = "server"\n'
            'mods = ["mods/server.pw.toml"]\n'
            'files = ["config/server.json"]\n'
        )
        self.archive_path = self.root / "fixture.mrpack"

    def manifest(self, slug):
        if slug == "fixture-client":
            name = "Fixture Client"
            mod_path = "mods/client.jar"
            env = {"client": "required", "server": "unsupported"}
        else:
            name = "Fixture Server"
            mod_path = "mods/server.jar"
            env = {"client": "unsupported", "server": "required"}
        return {
            "formatVersion": 1,
            "game": "minecraft",
            "versionId": "fixture-draft",
            "name": name,
            "files": [{"path": mod_path, "env": env, "hashes": {"sha512": "a" * 128},
                       "downloads": ["https://cdn.modrinth.com/fixture.jar"]}],
            "dependencies": {"fabric-loader": "0.19.5", "minecraft": "1.21.10"},
        }

    def write_archive(
        self,
        slug="fixture-client",
        manifest=None,
        extra_entries=(),
        notice=b"Fixture notice\n",
        include_notice=True,
        include_server_config=True,
    ):
        if manifest is None:
            manifest = self.manifest(slug)
        with zipfile.ZipFile(
            self.archive_path, "w", compression=zipfile.ZIP_STORED
        ) as archive:
            archive.writestr("modrinth.index.json", json.dumps(manifest))
            if include_notice:
                archive.writestr(
                    "overrides/blockery-notices/LICENSE.txt",
                    b"Fixture license\n",
                )
                archive.writestr(
                    "overrides/blockery-notices/NOTICE.txt",
                    notice,
                )
            if slug == "fixture-server" and include_server_config:
                archive.writestr(
                    "overrides/config/server.json",
                    b'{"fixture": true}\n',
                )
            for name, contents in extra_entries:
                archive.writestr(name, contents)

    def test_valid_client_archive_checks_identity_sides_and_notices(self):
        self.write_archive()
        result = check_exports.audit_archive(
            self.root, "fixture-client", "fixture-draft", self.archive_path
        )
        self.assertEqual(result["name"], "Fixture Client")
        self.assertEqual(result["side"], "client")
        self.assertEqual(result["manifestFileCount"], 1)
        self.assertNotIn("overrides/config/server.json", result["overrides"])

    def test_valid_server_archive_checks_reviewed_config_override(self):
        self.write_archive(slug="fixture-server")
        result = check_exports.audit_archive(
            self.root, "fixture-server", "fixture-draft", self.archive_path
        )
        self.assertIn("overrides/config/server.json", result["overrides"])

    def test_manifest_identity_dependencies_version_and_side_are_checked(self):
        mutations = (
            ("name", "Wrong name"),
            ("versionId", "wrong-version"),
            ("dependencies", {}),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                manifest = self.manifest("fixture-client")
                manifest[field] = value
                self.write_archive(manifest=manifest)
                with self.assertRaises(check_exports.ExportCheckError):
                    check_exports.audit_archive(
                        self.root, "fixture-client", "fixture-draft", self.archive_path
                    )

        manifest = self.manifest("fixture-client")
        manifest["files"][0]["env"] = {
            "client": "unsupported",
            "server": "required",
        }
        self.write_archive(manifest=manifest)
        with self.assertRaisesRegex(check_exports.ExportCheckError, "side declarations"):
            check_exports.audit_archive(
                self.root, "fixture-client", "fixture-draft", self.archive_path
            )

    def test_manifest_download_hash_and_url_declarations_match_source(self):
        for field, value in (("hashes", {"sha512": "b" * 128}),
                             ("downloads", ["https://example.com/wrong.jar"])):
            with self.subTest(field=field):
                manifest = self.manifest("fixture-client")
                manifest["files"][0][field] = value
                self.write_archive(manifest=manifest)
                with self.assertRaises(check_exports.ExportCheckError):
                    check_exports.audit_archive(self.root, "fixture-client", "fixture-draft", self.archive_path)

    def test_client_config_and_other_unexpected_files_are_rejected(self):
        self.write_archive(
            extra_entries=[("overrides/config/personal.json", b'{"private": true}\n')]
        )
        with self.assertRaisesRegex(check_exports.ExportCheckError, "Archive files differ"):
            check_exports.audit_archive(
                self.root, "fixture-client", "fixture-draft", self.archive_path
            )

    def test_unexpected_path_and_duplicate_zip_entry_are_rejected(self):
        self.write_archive(extra_entries=[("overrides/../outside.txt", b"unexpected")])
        with self.assertRaisesRegex(check_exports.ExportCheckError, "Unsafe archive path"):
            check_exports.audit_archive(
                self.root, "fixture-client", "fixture-draft", self.archive_path
            )

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            self.write_archive(
                extra_entries=[("modrinth.index.json", b'{"duplicate": true}')]
            )
        with self.assertRaisesRegex(check_exports.ExportCheckError, "Duplicate archive path"):
            check_exports.audit_archive(
                self.root, "fixture-client", "fixture-draft", self.archive_path
            )

    def test_crc_and_notice_bytes_are_checked(self):
        self.write_archive(notice=b"Altered notice\n")
        with self.assertRaisesRegex(check_exports.ExportCheckError, "Override bytes"):
            check_exports.audit_archive(
                self.root, "fixture-client", "fixture-draft", self.archive_path
            )

        self.write_archive()
        archive_bytes = bytearray(self.archive_path.read_bytes())
        marker = b"Fixture notice\n"
        offset = archive_bytes.find(marker)
        self.assertGreaterEqual(offset, 0)
        archive_bytes[offset] ^= 1
        self.archive_path.write_bytes(archive_bytes)
        with self.assertRaisesRegex(check_exports.ExportCheckError, "CRC"):
            check_exports.audit_archive(
                self.root, "fixture-client", "fixture-draft", self.archive_path
            )


if __name__ == "__main__":
    unittest.main()
