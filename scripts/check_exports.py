"""Audit generated mrpacks for expected metadata and reviewed overrides.

This checks archive structure and declared manifest content. It does not verify
transitive dependency closure, downloaded payloads, or Minecraft runtime behavior.
"""

import argparse
import hashlib
import json
import stat
import tomllib
import zipfile
from pathlib import PurePosixPath
from urllib.parse import unquote

from scripts import build_pack

PROFILES = (
    "blockery-client",
    "blockery-extras-client",
    "blockery-server-survival",
    "blockery-server-creative",
)


class ExportCheckError(ValueError):
    """A generated archive does not match its selected distribution recipe."""


def _require(condition, message):
    if not condition:
        raise ExportCheckError(message)


def _archive_files(archive):
    files = set()
    seen = set()
    for entry in archive.infolist():
        name = entry.filename
        is_directory = entry.is_dir()
        normalized = name[:-1] if is_directory else name
        path = PurePosixPath(normalized)
        _require(
            normalized
            and "\\" not in name
            and "\x00" not in name
            and not path.is_absolute()
            and path.as_posix() == normalized
            and not any(part in {"", ".", ".."} for part in normalized.split("/"))
            and not path.parts[0].endswith(":"),
            f"Unsafe archive path: {name!r}",
        )
        folded = normalized.casefold()
        _require(folded not in seen, f"Duplicate archive path: {name}")
        seen.add(folded)
        _require(not entry.flag_bits & 1, f"Encrypted archive entry: {name}")
        file_type = stat.S_IFMT(entry.external_attr >> 16)
        _require(
            file_type in {0, stat.S_IFREG, stat.S_IFDIR}
            and not (is_directory and file_type == stat.S_IFREG)
            and not (not is_directory and file_type == stat.S_IFDIR),
            f"Unsupported archive entry type: {name}",
        )
        if not is_directory:
            files.add(normalized)
    for name in files:
        parents = PurePosixPath(name).parents
        _require(
            not any(parent.as_posix() in files for parent in parents),
            f"Archive file is also a parent directory: {name}",
        )
    bad_entry = archive.testzip()
    _require(bad_entry is None, f"Archive CRC check failed: {bad_entry}")
    return files


def _expected_mods(root, profile):
    expected = {}
    for metadata_path in profile["mods"]:
        metadata = tomllib.loads((root / metadata_path).read_text())
        destination = PurePosixPath(metadata_path).parent / metadata["filename"]
        side = metadata.get("side", "both")
        expected[str(destination)] = {
            "env": {
                "client": "unsupported" if side == "server" else "required",
                "server": "unsupported" if side == "client" else "required",
            },
            "hashes": {metadata["download"]["hash-format"]: metadata["download"]["hash"]},
            "downloads": [unquote(metadata["download"]["url"])],
        }
    return expected


def audit_archive(root, slug, version, archive_path):
    profile = build_pack.plan(root, slug)
    _require(not archive_path.is_symlink(), f"Archive must not be a symlink: {archive_path}")
    _require(archive_path.is_file(), f"Missing archive: {archive_path}")
    try:
        with zipfile.ZipFile(archive_path) as archive:
            files = _archive_files(archive)
            _require("modrinth.index.json" in files, "Missing modrinth.index.json")
            try:
                manifest = json.loads(archive.read("modrinth.index.json"))
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise ExportCheckError(f"Invalid Modrinth manifest: {error}") from error
            _require(isinstance(manifest, dict), "Manifest must be a JSON object")
            _require(manifest.get("formatVersion") == 1, "Unexpected manifest formatVersion")
            _require(manifest.get("game") == "minecraft", "Unexpected manifest game")
            _require(
                manifest.get("name") == profile["name"],
                "Manifest name does not match profile",
            )
            _require(manifest.get("versionId") == version, "Manifest version does not match draft")

            pack = tomllib.loads((root / "pack.toml").read_text())
            expected_dependencies = {
                "fabric-loader" if key == "fabric" else key: value
                for key, value in pack["versions"].items()
            }
            _require(
                manifest.get("dependencies") == expected_dependencies,
                "Manifest dependencies do not match pack.toml versions",
            )

            expected_mods = _expected_mods(root, profile)
            manifest_mods = manifest.get("files")
            _require(isinstance(manifest_mods, list), "Manifest files must be an array")
            actual_mods = {}
            for item in manifest_mods:
                _require(isinstance(item, dict), "Manifest file entries must be objects")
                path = item.get("path")
                _require(isinstance(path, str), "Manifest file is missing its path")
                _require(path not in actual_mods, f"Duplicate manifest file path: {path}")
                actual_mods[path] = item
            _require(
                set(actual_mods) == set(expected_mods),
                "Manifest mod paths differ from recipe; "
                f"missing={sorted(set(expected_mods) - set(actual_mods))}, "
                f"unexpected={sorted(set(actual_mods) - set(expected_mods))}",
            )
            for path, expected in expected_mods.items():
                actual = actual_mods[path]
                _require(actual.get("env") == expected["env"],
                         f"Manifest side declarations do not match metadata: {path}")
                hashes = actual.get("hashes", {})
                _require(isinstance(hashes, dict) and all(hashes.get(key) == value for key, value in expected["hashes"].items()),
                         f"Manifest declared hashes do not match metadata: {path}")
                downloads = actual.get("downloads")
                _require(isinstance(downloads, list) and all(isinstance(url, str) for url in downloads),
                         f"Invalid manifest download URLs: {path}")
                _require([unquote(url) for url in downloads] == expected["downloads"],
                         f"Manifest download URLs do not match metadata: {path}")

            expected_overrides = {
                f"overrides/{source}": (root / source).read_bytes()
                for source in profile["files"]
            }
            for source, destination in build_pack.NOTICE_SOURCES.items():
                expected_overrides[f"overrides/{destination}"] = (root / source).read_bytes()
            expected_archive_files = {"modrinth.index.json", *expected_overrides}
            _require(
                files == expected_archive_files,
                "Archive files differ from expected manifest and overrides; "
                f"missing={sorted(expected_archive_files - files)}, "
                f"unexpected={sorted(files - expected_archive_files)}",
            )
            if profile["side"] == "client":
                _require(
                    not any(path.startswith("overrides/config/") for path in files),
                    "Client archive unexpectedly contains config overrides",
                )
            for destination, expected_bytes in expected_overrides.items():
                _require(
                    archive.read(destination) == expected_bytes,
                    f"Override bytes differ from reviewed source: {destination}",
                )
    except (OSError, zipfile.BadZipFile, RuntimeError) as error:
        raise ExportCheckError(f"Cannot inspect {archive_path}: {error}") from error

    return {
        "profile": slug,
        "archive": archive_path.name,
        "name": profile["name"],
        "side": profile["side"],
        "versionId": version,
        "dependencies": expected_dependencies,
        "disabled": profile.get("disabled", {}),
        "sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        "manifestFileCount": len(expected_mods),
        "overrides": sorted(expected_overrides),
    }


def audit_exports(root, version):
    _require(
        isinstance(version, str) and build_pack.VERSION.fullmatch(version),
        "Version must be a filename-safe identifier",
    )
    output = root / "local" / "dist"
    _require(
        not (root / "local").is_symlink() and not output.is_symlink(),
        "Export directory must not be a symlink",
    )
    records = []
    for slug in PROFILES:
        archive = output / f"{slug}-{version}-draft.mrpack"
        records.append(audit_archive(root, slug, f"{version}-draft", archive))

    checksums = "".join(
        f"{hashlib.sha256((output / item['archive']).read_bytes()).hexdigest()}  "
        f"{item['archive']}\n"
        for item in records
    )
    report = {
        "formatVersion": 1,
        "version": version,
        "packwizRevision": "ef87d964f8cb",
        "validationScope": (
            "Archive paths, duplicates, CRC, manifest identity and side declarations, "
            "and expected override bytes. No dependency closure, downloaded payload, "
            "or runtime verification."
        ),
        "artifacts": records,
    }
    for filename, content in (("SHA256SUMS", checksums), ("ci-report.json", json.dumps(report, indent=2) + "\n")):
        destination = output / filename
        _require(not destination.is_symlink(), f"Report destination must not be a symlink: {filename}")
        destination.write_text(content)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version",
        required=True,
        help="Filename-safe draft version without -draft",
    )
    args = parser.parse_args()
    try:
        print(json.dumps(audit_exports(build_pack.ROOT, args.version), indent=2))
    except (ExportCheckError, build_pack.BuildError, OSError, tomllib.TOMLDecodeError) as error:
        parser.exit(1, f"Export check failed: {error}\n")


if __name__ == "__main__":
    main()
