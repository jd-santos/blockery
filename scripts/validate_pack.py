# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Read-only source/index/profile checks. Not a downloaded-mod or gameplay audit."""

import argparse
import hashlib
import json
import re
import tomllib
from pathlib import Path
from urllib.parse import urlsplit

if __package__:
    from . import build_pack as builder
else:
    import build_pack as builder


def digest(path, algorithm):
    if algorithm not in {"sha256", "sha512"}:
        raise builder.BuildError(f"Unsupported hash algorithm: {algorithm}")
    return hashlib.new(algorithm, path.read_bytes()).hexdigest()


def validate(root):
    """Validate canonical indexed inputs without refreshing or changing them."""
    pack = tomllib.loads(builder.source_path(root, "pack.toml").read_text())
    versions = pack.get("versions", {})
    if not all(isinstance(versions.get(k), str) and versions[k] for k in ("minecraft", "fabric")):
        raise builder.BuildError("Expected explicit Minecraft and Fabric Loader versions")
    reference = pack["index"]
    index_path = builder.source_path(root, reference["file"])
    if digest(index_path, reference["hash-format"]) != reference["hash"]:
        raise builder.BuildError("Canonical index hash does not match pack.toml; run packwiz refresh")
    index = tomllib.loads(index_path.read_text())
    entries = index.get("files", [])
    if not isinstance(entries, list):
        raise builder.BuildError("Index files must be an array")
    indexed = {}
    for entry in entries:
        value = entry["file"]
        if value in indexed:
            raise builder.BuildError(f"Duplicate indexed path: {value}")
        path = builder.source_path(root, value)
        if digest(path, entry.get("hash-format", index["hash-format"])) != entry["hash"]:
            raise builder.BuildError(f"Indexed file hash mismatch: {value}; run packwiz refresh")
        indexed[value] = entry
    profiles = {}
    for slug in builder.read_recipes(root):
        profile = builder.plan(root, slug)
        for value in profile["mods"] + list(profile["disabled"]) + profile["files"]:
            if value not in indexed:
                raise builder.BuildError(f"Selected file is not indexed: {value}")
        profiles[slug] = profile
    metadata = {}
    for value, entry in indexed.items():
        if not entry.get("metafile"):
            continue
        if not value.endswith(".pw.toml") or Path(value).parts[0] not in {"mods", "resourcepacks"}:
            raise builder.BuildError(f"Unsupported metadata path: {value}")
        data = tomllib.loads(builder.source_path(root, value).read_text())
        builder.safe_path(data["filename"])
        if data.get("side", "both") not in {"client", "server", "both"}:
            raise builder.BuildError(f"Invalid metadata side: {value}")
        download = data["download"]
        parsed = urlsplit(download["url"])
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise builder.BuildError(f"Expected a public HTTPS download URL: {value}")
        algorithm = download["hash-format"]
        size = {"sha256": 64, "sha512": 128}.get(algorithm)
        if not size or not re.fullmatch(r"[a-fA-F0-9]{" + str(size) + r"}", download["hash"]):
            raise builder.BuildError(f"Invalid download hash declaration: {value}")
        metadata[value] = data
    for profile in profiles.values():
        for value in profile["mods"] + list(profile["disabled"]):
            if value not in metadata:
                raise builder.BuildError(f"Selected metadata lacks an indexed metafile declaration: {value}")
    return {
        "versions": versions,
        "indexed_files": len(indexed),
        "profiles": profiles,
        "disabled": builder.disabled_mods(root),
        "metadata": metadata,
        "coverage": "Source/index hashes, recipe safety, metadata declarations, and disable policy only; no downloaded-JAR dependency or runtime checks.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print the validation summary as JSON")
    args = parser.parse_args()
    try:
        result = validate(builder.ROOT)
        summary = {key: value for key, value in result.items() if key != "metadata"}
        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print(f"Validated {result['indexed_files']} indexed files and {len(result['profiles'])} profiles.")
            print(result["coverage"])
            for slug, profile in result["profiles"].items():
                print(f"{slug}: {len(profile['mods'])} active downloads, {len(profile['disabled'])} disabled")
    except (builder.BuildError, OSError, KeyError, TypeError, ValueError) as error:
        parser.exit(1, f"Validation failed: {error}\n")


if __name__ == "__main__":
    main()
