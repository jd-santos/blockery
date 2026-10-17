"""Prepare one gated, audited release bundle. Does not publish or run Minecraft."""

import argparse
import hashlib
import json
import re
import subprocess
import tomllib

from scripts import build_pack, check_exports, validate_pack


def release_plan(root, slug, version):
    if slug not in check_exports.PROFILES:
        raise build_pack.BuildError("Choose one of the four supported distributions")
    if (
        not build_pack.VERSION.fullmatch(version)
        or version.lower() == "unreleased"
        or version.lower().endswith("-draft")
    ):
        raise build_pack.BuildError("Choose a filename-safe non-draft release version")
    profile = build_pack.plan(root, slug)
    if profile["pending"]:
        raise build_pack.BuildError("Release blocked: " + "; ".join(profile["pending"]))
    tag = f"{slug.removeprefix('blockery-')}-{version}"
    notes = f"docs/releases/{tag}.md"
    if not build_pack.source_path(root, notes).read_text().strip():
        raise build_pack.BuildError("Release notes must not be empty")
    return {
        "profile": slug,
        "tag": tag,
        "notes": notes,
        "archive": f"local/dist/{slug}-{version}.mrpack",
    }


def prepare(root, slug, version, revision):
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision):
        raise build_pack.BuildError("Expected a full source commit ID")
    plan = release_plan(root, slug, version)
    bundle = root / "local" / "release"
    if bundle.exists() or bundle.is_symlink():
        raise build_pack.BuildError("Release bundle already exists; do not overwrite it")
    validate_pack.validate(root)
    archive = build_pack.build(root, slug, version)  # Normal build, never --draft.
    record = check_exports.audit_archive(root, slug, version, archive)
    notes = build_pack.source_path(root, plan["notes"]).read_bytes()
    report = {
        "formatVersion": 1,
        "tag": plan["tag"],
        "sourceRevision": revision,
        "sourceRepository": "https://github.com/jd-santos/blockery",
        "packwizRevision": "ef87d964f8cb",
        "releaseNotes": {
            "path": plan["notes"],
            "sha256": hashlib.sha256(notes).hexdigest(),
        },
        "validationScope": (
            "Source/index checks and archive metadata/override audit. "
            "No downloaded-JAR closure or Minecraft runtime testing. "
            "Test these exact bytes before publishing the draft release."
        ),
        "artifacts": [record],
    }
    # The builder already rejects a symlinked local directory. Reserve this bundle
    # exclusively so a retry cannot replace another candidate's evidence.
    bundle.mkdir()
    (bundle / "release-set.json").write_text(json.dumps(report, indent=2) + "\n")
    (bundle / "SHA256SUMS").write_text(f"{record['sha256']}  {archive.name}\n")
    (bundle / "release-notes.md").write_bytes(notes)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "build"))
    parser.add_argument("profile", choices=check_exports.PROFILES)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    try:
        if args.command == "plan":
            result = release_plan(build_pack.ROOT, args.profile, args.version)
        else:
            revision = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=build_pack.ROOT,
                check=True, capture_output=True, text=True,
            ).stdout.strip()
            result = prepare(build_pack.ROOT, args.profile, args.version, revision)
        print(json.dumps(result, indent=2))
    except (
        build_pack.BuildError, check_exports.ExportCheckError, OSError,
        tomllib.TOMLDecodeError, subprocess.CalledProcessError,
    ) as error:
        parser.exit(1, f"Release preparation failed: {error}\n")


if __name__ == "__main__":
    main()
