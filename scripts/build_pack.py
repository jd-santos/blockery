# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Build isolated Packwiz distributions from explicit repository recipes."""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import tomllib
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
VERSION = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*\Z")
NOTICE_SOURCES = {
    "LICENSE": "blockery-notices/LICENSE.txt",
    "build/NOTICE.txt": "blockery-notices/NOTICE.txt",
}
PRIVATE_NAMES = {
    "server.properties",
    "ops.json",
    "whitelist.json",
    "banned-players.json",
    "banned-ips.json",
    "usercache.json",
    "eula.txt",
    "ncr-encryption.json",
    "axiom.json",
}
PRIVATE_PARTS = {
    ".git",
    "world",
    "world_nether",
    "world_the_end",
    "logs",
    "crash-reports",
    "backups",
    "server-runtime",
    "audioplayer_uploads",
}


class BuildError(ValueError):
    """A recipe or build request is unsafe or incomplete."""


def safe_path(value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise BuildError(f"Invalid relative path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in {"", ".", ".."} for p in value.split("/")):
        raise BuildError(f"Path must be normalized and relative: {value!r}")
    for part in path.parts:
        lower = part.lower()
        if (
            lower.startswith(".env")
            or any(word in lower for word in ("credential", "secret", "token"))
            or lower.endswith((".key", ".pem"))
            or lower in PRIVATE_NAMES | PRIVATE_PARTS
        ):
            raise BuildError(f"Private/runtime path is forbidden: {value}")
    return path


def source_path(root, value):
    relative = safe_path(value)
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise BuildError(f"Source symlinks are forbidden: {value}")
    if not current.is_file():
        raise BuildError(f"Missing source file: {value}")
    return current


def string_list(value, field):
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        raise BuildError(f"{field} must be an array of strings")
    return value


def read_recipes(root):
    path = source_path(root, "build/profiles.toml")
    data = tomllib.loads(path.read_text())
    if set(data) != {"profiles"} or not isinstance(data["profiles"], dict):
        raise BuildError("Expected a [profiles] recipe table")
    return data["profiles"]


def resolve_profile(recipes, slug, ancestors=()):
    if not isinstance(slug, str) or not SLUG.fullmatch(slug):
        raise BuildError(f"Invalid profile name: {slug!r}")
    if slug in ancestors:
        raise BuildError("Recipe inheritance cycle: " + " -> ".join((*ancestors, slug)))
    if slug not in recipes:
        raise BuildError(f"Unknown profile: {slug}")
    item = recipes[slug]
    allowed = {"name", "side", "extends", "mods", "files", "pending"}
    if not isinstance(item, dict) or set(item) - allowed:
        raise BuildError(f"Unknown fields or invalid table for {slug}")
    parent = {"mods": [], "files": [], "pending": []}
    if "extends" in item:
        parent = resolve_profile(recipes, item["extends"], (*ancestors, slug))
    side = item.get("side", parent.get("side"))
    if side not in {"client", "server"}:
        raise BuildError(f"{slug}: side must be client or server")
    if parent.get("side", side) != side:
        raise BuildError(f"{slug}: cannot inherit across client/server sides")
    name = item.get("name", slug)
    if not isinstance(name, str) or not name.strip():
        raise BuildError(f"{slug}: name must be nonempty")
    result = {"slug": slug, "name": name, "side": side}
    for field in ("mods", "files", "pending"):
        own = string_list(item.get(field, []), f"{slug}.{field}")
        result[field] = list(dict.fromkeys(parent[field] + own))
    return result


def disabled_mods(root):
    """Read reversible global exclusions without removing their pinned metadata."""
    policy = root / "build/disabled-mods.toml"
    if not policy.exists() and not policy.is_symlink():
        return {}
    data = tomllib.loads(source_path(root, "build/disabled-mods.toml").read_text())
    if set(data) != {"disabled"} or not isinstance(data["disabled"], dict):
        raise BuildError("Expected only a [disabled] table in build/disabled-mods.toml")
    selected = set()
    recipes = read_recipes(root)
    for slug in recipes:
        selected.update(resolve_profile(recipes, slug)["mods"])
    for value, reason in data["disabled"].items():
        relative = safe_path(value)
        if relative.parts[0] not in {"mods", "resourcepacks"} or not value.endswith(".pw.toml"):
            raise BuildError(f"Disabled entry must be mod/resource-pack metadata: {value}")
        source_path(root, value)
        if value not in selected:
            raise BuildError(f"Disabled entry is not selected by any recipe: {value}")
        if not isinstance(reason, str) or not reason.strip():
            raise BuildError(f"Disabled entry needs a nonempty reason: {value}")
    return data["disabled"]


def plan(root, slug):
    profile = resolve_profile(read_recipes(root), slug)
    disabled = disabled_mods(root)
    profile["disabled"] = {value: disabled[value] for value in profile["mods"] if value in disabled}
    destinations = set()
    selected = []
    for value in profile["mods"]:
        relative = safe_path(value)
        if relative.parts[0] not in {"mods", "resourcepacks"} or not value.endswith(
            ".pw.toml"
        ):
            raise BuildError(f"Metadata must be under mods/ or resourcepacks/: {value}")
        source = source_path(root, value)
        data = tomllib.loads(source.read_text())
        side = data.get("side", "both")
        if side not in {"client", "server", "both"}:
            raise BuildError(f"Invalid mod side: {value}")
        if side not in {"both", profile["side"]}:
            raise BuildError(f"{slug}: incompatible {side} metadata: {value}")
        filename = safe_path(data.get("filename"))
        if value in disabled:
            continue
        destination = relative.parent / filename
        if str(destination) in destinations:
            raise BuildError(f"Duplicate installed path: {destination}")
        destinations.add(str(destination))
        selected.append(value)
    for value in profile["files"]:
        relative = safe_path(value)
        if relative.parts[0] != "config" or value.lower().endswith((".pw.toml", ".jar", ".zip")):
            raise BuildError(f"Only explicit config files may be bundled: {value}")
        source_path(root, value)
        if value in destinations:
            raise BuildError(f"Duplicate installed path: {value}")
        destinations.add(value)
    for value in NOTICE_SOURCES:
        source_path(root, value)
    profile["mods"] = selected
    profile["notices"] = list(NOTICE_SOURCES.values())
    return profile


def stage_pack(root, stage, profile, version):
    original = tomllib.loads(source_path(root, "pack.toml").read_text())
    supported = {"name", "version", "author", "description", "pack-format", "index", "versions"}
    if set(original) - supported:
        raise BuildError("Unsupported root pack fields; review staging before building")
    empty_index = 'hash-format = "sha256"\nfiles = []\n'
    (stage / "index.toml").write_text(empty_index)
    values = {
        "name": profile["name"],
        "version": version,
        "pack-format": original["pack-format"],
    }
    for field in ("author", "description"):
        if field in original:
            values[field] = original[field]
    def quote(value):
        return json.dumps(value, ensure_ascii=False)

    text = "\n".join(f"{k} = {quote(v)}" for k, v in values.items())
    text += '\n\n[index]\nfile = "index.toml"\nhash-format = "sha256"\n'
    text += f'hash = "{hashlib.sha256(empty_index.encode()).hexdigest()}"\n\n[versions]\n'
    text += "\n".join(f"{k} = {quote(v)}" for k, v in original["versions"].items())
    (stage / "pack.toml").write_text(text + "\n")
    sources = [(value, value) for value in profile["mods"] + profile["files"]]
    sources.extend(NOTICE_SOURCES.items())
    for source, value in sources:
        destination = stage / value
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path(root, source), destination)


def build(root, slug, version, draft=False):
    profile = plan(root, slug)
    if not VERSION.fullmatch(version):
        raise BuildError("Version must be a filename-safe nonempty identifier")
    if not draft and (profile["pending"] or version.lower() == "unreleased"):
        raise BuildError("Release blocked: resolve pending decisions and choose a release version")
    if not profile["mods"]:
        raise BuildError("No mods selected; this recipe is not ready even for a draft export")
    packwiz = shutil.which("packwiz")
    if packwiz is None:
        raise BuildError("packwiz is required; see docs/tooling.md")
    output_version = version + ("-draft" if draft else "")
    # Never follow an output directory symlink into an unrelated checkout or runtime.
    output = root
    for part in ("local", "dist"):
        output /= part
        if output.is_symlink():
            raise BuildError(f"Output directory must not be a symlink: {output}")
        output.mkdir(exist_ok=True)
    artifact = output / f"{slug}-{output_version}.mrpack"
    if artifact.exists() or artifact.is_symlink():
        raise BuildError(f"Output already exists; choose another version: {artifact}")
    with tempfile.TemporaryDirectory(prefix="blockery-build-") as directory:
        stage = Path(directory)
        stage_pack(root, stage, profile, output_version)
        subprocess.run([packwiz, "refresh"], cwd=stage, check=True)
        candidate = stage / "candidate.mrpack"
        subprocess.run(
            [packwiz, "modrinth", "export", "-o", str(candidate)], cwd=stage, check=True
        )
        # Exclusive creation preserves an existing artifact, including a concurrent build.
        with candidate.open("rb") as incoming:
            outgoing = artifact.open("xb")
            try:
                with outgoing:
                    shutil.copyfileobj(incoming, outgoing)
            except BaseException:
                # Only clean up after our exclusive creation succeeded, never on collision.
                artifact.unlink()
                raise
    return artifact


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="List recipes and unresolved release decisions")
    show = commands.add_parser("plan", help="Validate selection without copying configs")
    show.add_argument("profile")
    export = commands.add_parser("build", help="Export an isolated Packwiz pack")
    export.add_argument("profile")
    export.add_argument("--version", required=True)
    export.add_argument("--draft", action="store_true", help="Allow pending recipes; not for publication")
    args = parser.parse_args()
    try:
        if args.command == "list":
            recipes = read_recipes(ROOT)
            for slug in recipes:
                profile = plan(ROOT, slug)
                print(f"{slug}: {profile['side']}, {len(profile['mods'])} metadata files")
                for value, reason in profile["disabled"].items():
                    print(f"  disabled: {value}: {reason}")
                for reason in profile["pending"]:
                    print(f"  pending: {reason}")
        elif args.command == "plan":
            print(json.dumps(plan(ROOT, args.profile), indent=2))
        else:
            print(build(ROOT, args.profile, args.version, args.draft))
    except (BuildError, OSError, tomllib.TOMLDecodeError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Build failed: {error}\n")


if __name__ == "__main__":
    main()
