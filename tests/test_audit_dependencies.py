"""Offline pinned-JAR fixtures. Never open a Minecraft instance or use the network."""

import contextlib
import hashlib
import io
import json
import struct
import tempfile
import tomllib
import unittest
import warnings
import zipfile
from pathlib import Path
from unittest.mock import patch

from scripts import audit_dependencies as audit
from scripts import build_pack as builder
from scripts import fabric_versions


def mod(identifier="shared", version="1.2.3", **fields):
    return {"schemaVersion": 1, "id": identifier, "version": version, **fields}


def jar(data=None, members=None):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        if data is not None:
            archive.writestr("fabric.mod.json", json.dumps(data))
        for name, contents in (members or {}).items():
            archive.writestr(name, contents)
    return output.getvalue()


class VersionTests(unittest.TestCase):
    def test_fabric_numeric_predicates(self):
        cases = [
            ("1.2", "1.2.0.0", True), ("01.002", "1.2", True),
            ("1.2.3+mc1.21", "=1.2.3+other", True),
            ("1.2.3", ">=1.0 <2", True), ("2", ">=1 <2", False),
            ("1.2.3", ">1.2.3", False), ("1.2.3", "<=1.2.3", True),
            ("1.2.4", "~1.2.3", True), ("1.3", "~1.2.3", False),
            ("1.0.5", "~1", True), ("1.1", "~1", False),
            ("0.9", "^0.2", True), ("1.0", "^0.2", False),
            ("1.9.0-beta", "^1.2.3", True), ("2.0-alpha", "^1.2.3", False),
            ("1.2.0-alpha", "1.2.x", True), ("1.3-alpha", "1.2.x", False),
            ("1.2.3.4", "1.2.X.*", True), ("2", "1.*", False),
            ("1.2.3-alpha.2", ">1.2.3-alpha.1 <1.2.3", True),
            ("1.2.3-alpha.10", ">1.2.3-alpha.2", True),
            ("1.2.3-01", ">1.2.3-1", True),  # Loader treats 01 as text.
            ("1.2.3-alpha", ">1.2.3-0", True),
            ("1.2.3-", "<1.2.3-0", True), ("1.2.3-", "<1.2.3-alpha", True),
            ("1.2.3", ">1.2.3-", True), ("release", "=release", True),
            ("release", "other", False), ("release", "*", True),
            ("2", ["1.x", ">=2 <3"], True), ("4", ["1.x", "2.x"], False),
            ("1", "", True), ("1", "  *  >=1 ", True),
        ]
        for version, predicate, expected in cases:
            with self.subTest(version=version, predicate=predicate):
                self.assertIs(fabric_versions.matches(version, predicate), expected)

    def test_unsupported_and_malformed_predicates_remain_unknown(self):
        for version, predicate in [
            ("1", ">= 1"), ("1", "1 || 2"), ("1", ">=1\t<2"),
            ("1", "1.2.3.x"), ("1", ">=1.x"), ("1", "1.x.2"),
            ("1", "1.x-alpha"), ("release", ">release"), ("release", "~release"),
            ("1", ["*", ">= 2"]), ("1", []), ("1", [None]), ("1", True),
            (None, "*"), ("", "*"), ("26w14a", ">=1.21"),
            ("1." + ".".join(["0"] * 17), "1"), ("1", ">=2147483648"),
        ]:
            with self.subTest(version=version, predicate=predicate):
                self.assertIsNone(fabric_versions.matches(version, predicate))


class AuditTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.jars = self.root / "local/jars"
        for directory in ("build", "mods", "local/jars"):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
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
        for name in ("shared", "client", "server"):
            self.pin(name, jar(mod(name)))

    def refresh(self):
        index = 'hash-format = "sha256"\n'
        for path in sorted((self.root / "mods").glob("*.pw.toml")):
            index += (f'[[files]]\nfile = "mods/{path.name}"\nmetafile = true\n'
                      f'hash = "{hashlib.sha256(path.read_bytes()).hexdigest()}"\n')
        (self.root / "index.toml").write_text(index)
        (self.root / "pack.toml").write_text(
            'name = "Fixture"\npack-format = "packwiz:1.1.0"\n'
            '[index]\nfile = "index.toml"\nhash-format = "sha256"\n'
            f'hash = "{hashlib.sha256(index.encode()).hexdigest()}"\n'
            '[versions]\nminecraft = "1.21.10"\nfabric = "0.19.5"\n'
        )

    def pin(self, name, raw, algorithm="sha512"):
        (self.jars / f"{name}.jar").write_bytes(raw)
        side = "both" if name == "shared" else name
        (self.root / f"mods/{name}.pw.toml").write_text(
            f'name = "{name}"\nfilename = "{name}.jar"\nside = "{side}"\n'
            '[download]\nurl = "https://cdn.modrinth.com/fixture.jar"\n'
            f'hash-format = "{algorithm}"\nhash = "{hashlib.new(algorithm, raw).hexdigest()}"\n'
        )
        self.refresh()

    def report(self, profile="base", **targets):
        before = self.snapshot()
        result = audit.audit(self.root, profile, self.jars, **targets)
        self.assertEqual(before, self.snapshot())
        return result

    def snapshot(self):
        return {str(path.relative_to(self.root)): path.read_bytes()
                for path in self.root.rglob("*") if path.is_file() and not path.is_symlink()}

    def dependency(self, report, identifier, kind="depends", consumer="shared"):
        return next(f for f in report["findings"] if f.get("dependency") == identifier
                    and f.get("kind") == kind and f.get("mod") == consumer)

    def test_pinned_artifacts_and_target_builtins_are_read_only(self):
        self.pin("shared", jar(mod(depends={"minecraft": "~1.21.10", "fabricloader": ">=0.19", "java": ">=21"})), "sha256")
        result = self.report(java="21")
        self.assertEqual(result["status"], "checked")
        self.assertEqual(result["artifacts"][0]["status"], "verified")
        self.assertEqual({f["status"] for f in result["findings"]}, {"satisfied"})
        self.assertEqual(self.report(minecraft="1.20", java="21")["status"], "violated")
        self.assertEqual(self.dependency(self.report(), "java")["status"], "unknown")
        self.assertEqual(self.dependency(self.report(minecraft="26w14a"), "minecraft")["status"], "unknown")

    def test_required_dependencies_and_aliases(self):
        self.pin("shared", jar(mod(depends={"library_api": ">=2"})))
        self.pin("client", jar(mod("library", "2.1", provides=["library_api"])))
        self.assertEqual(self.report()["status"], "violated")
        result = self.report("extras")
        self.assertEqual(self.dependency(result, "library_api")["status"], "satisfied")
        self.assertEqual(self.dependency(result, "library_api")["providers"][0]["id"], "library")
        self.pin("client", jar(mod("library", "1", provides=["library_api"])))
        self.assertEqual(self.report("extras")["status"], "violated")

    def test_breaks_conflicts_recommendations_and_suggestions(self):
        self.pin("shared", jar(mod(breaks={"client": "<2"}, conflicts={"client": "*"},
                                   recommends={"missing": "*"}, suggests={"optional": "*"})))
        result = self.report("extras")
        self.assertEqual(self.dependency(result, "client", "breaks")["status"], "violated")
        self.assertEqual(self.dependency(result, "client", "conflicts")["status"], "warning")
        self.assertEqual(self.dependency(result, "missing", "recommends")["status"], "warning")
        self.assertEqual(self.dependency(result, "optional", "suggests")["status"], "informational")
        base = self.report()
        self.assertEqual(self.dependency(base, "client", "breaks")["status"], "satisfied")
        self.assertEqual(base["status"], "checked")

    def test_nested_candidates_have_provenance_and_conditional_constraints(self):
        nested = jar(mod("library", "2", depends={"absent": "*"}))
        self.pin("shared", jar(mod(depends={"library": ">=2"}, jars=[{"file": "META-INF/jars/lib.jar"}]),
                               {"META-INF/jars/lib.jar": nested}))
        result = self.report()
        self.assertEqual(result["status"], "unknown")
        finding = self.dependency(result, "library")
        self.assertEqual(finding["status"], "unknown")
        self.assertIs(finding["providers"][0]["matches"], True)
        self.assertEqual(finding["providers"][0]["source"], "mods/shared.jar!/META-INF/jars/lib.jar")
        conditional = self.dependency(result, "absent", consumer="library")
        self.assertEqual(conditional["scope"], "nested-candidate")
        self.assertEqual(conditional["status"], "unknown")

    def test_recursive_nested_jars_and_unreferenced_candidates_are_not_forced(self):
        deep = jar(mod("deep_library", "3"))
        inner = jar(mod("library", jars=[{"file": "deep.jar"}]), {"deep.jar": deep})
        self.pin("shared", jar(mod(jars=[{"file": "inner.jar"}]), {"inner.jar": inner, "undeclared.jar": b"ignored"}))
        result = self.report()
        self.assertEqual(len(result["candidates"]), 3)
        self.assertEqual(result["candidates"][2]["source"], "mods/shared.jar!/inner.jar!/deep.jar")
        self.assertEqual(result["status"], "unknown")

    def test_competing_providers_and_builtin_collisions_are_unknown(self):
        self.pin("shared", jar(mod(depends={"library": "*"}, provides=["library"])))
        self.pin("client", jar(mod("library")))
        result = self.report("extras")
        self.assertEqual(self.dependency(result, "library")["status"], "unknown")
        self.assertTrue(any(f["kind"] == "provider-selection" for f in result["findings"]))
        self.pin("client", jar(mod("library", provides=["minecraft"])))
        self.pin("shared", jar(mod(depends={"minecraft": "*"})))
        self.assertEqual(self.dependency(self.report("extras"), "minecraft")["status"], "unknown")

    def test_environment_filtering_includes_nested_parent_reachability(self):
        self.pin("shared", jar(mod(depends={"library": "*"})))
        self.pin("client", jar(mod("client", environment="server", jars=[{"file": "bad.jar"}]),
                               {"bad.jar": b"not a zip"}))
        result = self.report("extras")
        self.assertEqual(result["ignored"][0]["id"], "client")
        self.assertEqual(result["status"], "violated")
        nested = jar(mod("library", environment="server"))
        self.pin("shared", jar(mod(depends={"library": "*"}, jars=[{"file": "lib.jar"}]), {"lib.jar": nested}))
        self.assertEqual(self.report()["status"], "violated")

    def test_global_disabled_entries_are_not_read_or_counted_as_providers(self):
        self.pin("shared", jar(mod(depends={"client": "*"})))
        (self.root / "build/disabled-mods.toml").write_text('[disabled]\n"mods/client.pw.toml" = "Waiting"\n')
        (self.jars / "client.jar").unlink()
        result = self.report("extras")
        self.assertEqual(result["status"], "violated")
        self.assertEqual(len(result["artifacts"]), 1)
        self.assertEqual(result["disabled"], {"mods/client.pw.toml": "Waiting"})

    def test_missing_or_hash_mismatched_artifacts_do_not_prove_dependency_absence(self):
        self.pin("shared", jar(mod(depends={"library": "*"})))
        path = self.jars / "client.jar"
        path.write_bytes(b"wrong pin")
        for action in (lambda: None, path.unlink):
            action()
            result = self.report("extras")
            self.assertEqual(result["status"], "unknown")
            self.assertEqual(self.dependency(result, "library")["status"], "unknown")
            self.assertEqual(result["artifacts"][1]["status"], "unknown")

    def test_corrupt_archives_or_nested_metadata_discard_the_entire_subtree(self):
        for raw in (b"not a zip", jar(), jar(mod(jars=[{"file": "missing.jar"}])),
                    jar(mod(jars=[{"file": "bad.jar"}]), {"bad.jar": b"broken"}),
                    jar(None, {"fabric.mod.json": b"{invalid"})):
            with self.subTest(raw=raw[:20]):
                self.pin("shared", raw)
                result = self.report()
                self.assertEqual(result["status"], "unknown")
                self.assertEqual(result["candidates"], [])

    def test_invalid_metadata_shapes_remain_unknown(self):
        for fields in ({"schemaVersion": 0}, {"schemaVersion": True}, {"id": "Bad id"},
                       {"version": None}, {"version": "1\x1b[0m"}, {"environment": ["client"]},
                       {"provides": "library"}, {"provides": [1]}, {"provides": ["shared"]},
                       {"provides": ["library", "library"]}, {"depends": []},
                       {"breaks": {"client": False}}, {"depends": {"library": []}},
                       {"jars": {}}, {"jars": [None]}, {"jars": [{"file": "../outside.jar"}]}):
            with self.subTest(fields=fields):
                self.pin("shared", jar({**mod(), **fields}))
                self.assertEqual(self.report()["status"], "unknown")
        for raw in (b'{"schemaVersion":1,"id":"shared","id":"other","version":"1"}',
                    b'{"schemaVersion":1,"id":"shared","version":"1","custom":NaN}'):
            self.pin("shared", jar(None, {"fabric.mod.json": raw}))
            self.assertEqual(self.report()["status"], "unknown")

    def test_unsupported_predicates_are_unknown_even_for_absent_dependencies(self):
        for kind in ("depends", "breaks", "conflicts", "recommends", "suggests"):
            self.pin("shared", jar({**mod(), kind: {"missing": ">= 2"}}))
            self.assertEqual(self.report()["status"], "unknown")

    def test_zip_paths_duplicates_and_links_are_rejected_without_extraction(self):
        for name in ("../outside.jar", "/outside", "C:/outside", "foo\\bar", "foo//bar", "foo/./bar", "control\x1b"):
            with self.subTest(name=name):
                self.pin("shared", jar(mod(), {name: b"data"}))
                self.assertEqual(self.report()["status"], "unknown")
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive, warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            archive.writestr("fabric.mod.json", json.dumps(mod()))
            archive.writestr("fabric.mod.json", json.dumps(mod()))
        self.pin("shared", output.getvalue())
        self.assertEqual(self.report()["status"], "unknown")
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            archive.writestr("fabric.mod.json", json.dumps(mod()))
            link = zipfile.ZipInfo("lib.jar")
            link.create_system = 3
            link.external_attr = 0o120777 << 16
            archive.writestr(link, "outside.jar")
        self.pin("shared", output.getvalue())
        self.assertEqual(self.report()["status"], "unknown")

    def test_host_symlinks_are_refused(self):
        path = self.jars / "shared.jar"
        raw = path.read_bytes()
        path.unlink()
        (self.jars / "copy.jar").write_bytes(raw)
        path.symlink_to(self.jars / "copy.jar")
        self.assertEqual(self.report()["status"], "unknown")
        directory = self.root / "jars-link"
        directory.symlink_to(self.jars, target_is_directory=True)
        self.assertEqual(audit.audit(self.root, "base", directory)["status"], "unknown")

    def test_size_depth_entry_and_candidate_limits(self):
        raw = jar(mod(jars=[{"file": "inner.jar"}]), {"inner.jar": jar(mod("library"))})
        for setting, limit in (("MAX_JAR_BYTES", 10), ("MAX_JSON_BYTES", 10),
                               ("MAX_ENTRIES", 1), ("MAX_DEPTH", 0), ("MAX_CANDIDATES", 1)):
            with self.subTest(setting=setting), patch.object(audit, setting, limit):
                self.pin("shared", raw)
                self.assertEqual(self.report()["status"], "unknown")
        with self.assertRaisesRegex(audit.EvidenceError, "Total inspected-byte"):
            audit.inspect_jar(raw, "fixture.jar", "client", audit.Budget(remaining=1))

    def test_central_directory_limit_precedes_zipfile_allocation(self):
        raw = jar(mod(), {f"member-{i}": b"" for i in range(64)})
        for declared_count in (65, 1):
            changed = bytearray(raw)
            end = changed.rfind(b"PK\x05\x06")
            struct.pack_into("<2H", changed, end + 8, declared_count, declared_count)
            self.pin("shared", bytes(changed))
            with patch.object(audit, "MAX_ENTRIES", 32), patch.object(audit.zipfile, "ZipFile") as allocate:
                result = self.report()
                self.assertEqual(result["status"], "unknown")
                self.assertIn("entry-count limit", result["findings"][0]["reason"])
                allocate.assert_not_called()

    def test_malformed_or_unsupported_directories_are_rejected_before_allocation(self):
        original = jar(mod())
        end = original.rfind(b"PK\x05\x06")
        central = original.find(b"PK\x01\x02")
        variations = [original[:-1], original + b"trailing", b"prefix" + original]
        for position, contents in ((end + 4, b"\x01\x00"),  # Multi-disk.
                                   (end + 8, b"\xff\xff\xff\xff"),  # ZIP64 count.
                                   (end + 8, b"\x00\x00\x00\x00"),  # False count.
                                   (central + 34, b"\x01\x00"),  # Entry starts on another disk.
                                   (central + 34, b"\xff\xff"),  # ZIP64 disk-start sentinel.
                                   (central, b"broken"),
                                   (central + 28, b"\xff\xff")):  # Oversized record.
            changed = bytearray(original)
            changed[position:position + len(contents)] = contents
            variations.append(bytes(changed))
        for raw in variations:
            with self.subTest(raw=raw[-24:]):
                self.pin("shared", raw)
                with patch.object(audit.zipfile, "ZipFile") as allocate:
                    self.assertEqual(self.report()["status"], "unknown")
                    allocate.assert_not_called()
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            archive.writestr("fabric.mod.json", json.dumps(mod()))
            archive.comment = b"ordinary comment"
        self.pin("shared", output.getvalue())
        self.assertEqual(self.report()["status"], "checked")

    def test_fabric_arbitrary_build_text_is_not_invalid_prerelease(self):
        # Loader 0.19.5 explicitly permits arbitrary build contents and ignores
        # them in compareTo; imposing SemVer build syntax would be incorrect.
        self.pin("shared", jar(mod(depends={"library": ">=2"})))
        for version in ("10+!", "10+", "10+foo..bar", "10+mc1.21/extra"):
            with self.subTest(version=version):
                self.pin("client", jar(mod("library", version)))
                result = self.report("extras")
                self.assertEqual(result["status"], "checked")
                self.assertEqual(self.dependency(result, "library")["status"], "satisfied")
        for version in ("10-!", "10+build text"):
            with self.subTest(version=version):
                self.pin("client", jar(mod("library", version)))
                self.assertEqual(self.report("extras")["status"], "unknown")

    def test_constraint_and_alias_limits_and_provider_report_cap(self):
        self.pin("shared", jar(mod(depends={"minecraft": "*"})))
        with patch.object(audit, "MAX_CONSTRAINTS", 0):
            self.assertEqual(self.report()["status"], "unknown")
        self.pin("shared", jar(mod(provides=["library"])))
        with patch.object(audit, "MAX_ALIASES", 0):
            self.assertEqual(self.report()["status"], "unknown")
        consumer = {"source": "fixture.jar", "id": "shared", "nested": False}
        choices = [{"id": "library", "version": "1", "source": str(i), "nested": False}
                   for i in range(audit.MAX_REPORTED_PROVIDERS + 5)]
        finding = audit.check_dependency(consumer, "depends", "library", "*", {"library": choices}, False)
        self.assertEqual(finding["status"], "unknown")
        self.assertEqual(finding["provider_count"], len(choices))
        self.assertEqual(len(finding["providers"]), audit.MAX_REPORTED_PROVIDERS)

    def test_corrupted_deflate_and_unsupported_compression_are_unknown(self):
        raw = bytearray(jar(mod()))
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            info = archive.getinfo("fabric.mod.json")
        start = info.header_offset + 30 + len(info.filename.encode()) + len(info.extra)
        raw[start] = 255
        self.pin("shared", bytes(raw))
        self.assertEqual(self.report()["status"], "unknown")
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_BZIP2) as archive:
            archive.writestr("fabric.mod.json", json.dumps(mod()))
        self.pin("shared", output.getvalue())
        self.assertEqual(self.report()["status"], "unknown")

    def test_resource_packs_are_not_treated_as_mod_jars(self):
        directory = self.root / "resourcepacks"
        directory.mkdir()
        metadata = directory / "visual.pw.toml"
        metadata.write_text('name = "Visual"\nfilename = "visual.zip"\nside = "client"\n'
                            '[download]\nurl = "https://cdn.modrinth.com/visual.zip"\n'
                            f'hash-format = "sha256"\nhash = "{"0" * 64}"\n')
        recipes = self.root / "build/profiles.toml"
        # Add to the inherited base selection without creating any resource-pack download.
        recipes.write_text(recipes.read_text().replace(
            'mods = ["mods/shared.pw.toml"]',
            'mods = ["mods/shared.pw.toml", "resourcepacks/visual.pw.toml"]'))
        self.refresh()
        index = self.root / "index.toml"
        index.write_text(index.read_text() + '\n[[files]]\nfile = "resourcepacks/visual.pw.toml"\n'
                         f'metafile = true\nhash = "{hashlib.sha256(metadata.read_bytes()).hexdigest()}"\n')
        pack = self.root / "pack.toml"
        old = tomllib.loads(pack.read_text())["index"]["hash"]
        pack.write_text(pack.read_text().replace(old, hashlib.sha256(index.read_bytes()).hexdigest()))
        result = self.report()
        self.assertEqual(result["status"], "checked")
        self.assertEqual(len(result["artifacts"]), 1)

    def test_text_reports_disabled_and_environment_filtered_entries(self):
        self.pin("shared", jar(mod(environment="server")))
        (self.root / "build/disabled-mods.toml").write_text('[disabled]\n"mods/client.pw.toml" = "Waiting"\n')
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            audit.print_report(self.report("extras"))
        self.assertIn('ignored:', output.getvalue())
        self.assertIn('"reason": "wrong-environment"', output.getvalue())
        self.assertIn('disabled:', output.getvalue())
        self.assertIn('Waiting', output.getvalue())

    def test_cli_json_and_text_do_not_imply_runtime_compatibility(self):
        for as_json in (False, True):
            output = io.StringIO()
            arguments = ["audit_dependencies.py", "base", "--jars", str(self.jars)]
            if as_json:
                arguments.append("--json")
            with patch.object(builder, "ROOT", self.root), patch("sys.argv", arguments), contextlib.redirect_stdout(output):
                audit.main()
            if as_json:
                self.assertEqual(json.loads(output.getvalue())["status"], "checked")
            self.assertIn("not Fabric's resolver or a runtime test", output.getvalue())
        with self.assertRaisesRegex(builder.BuildError, "Unknown build profile"):
            audit.audit(self.root, "missing", self.jars)
        with self.assertRaisesRegex(builder.BuildError, "Platform versions"):
            self.report(java="../21")

    def test_stale_source_is_rejected_before_reading_any_jars(self):
        path = self.root / "mods/shared.pw.toml"
        data = tomllib.loads(path.read_text())
        path.write_text(path.read_text() + "\n# Unindexed change\n")
        with patch.object(audit, "read_pinned") as read:
            with self.assertRaisesRegex(builder.BuildError, "hash mismatch"):
                audit.audit(self.root, "base", self.jars)
            read.assert_not_called()
        self.assertEqual(data["filename"], "shared.jar")


if __name__ == "__main__":
    unittest.main()
