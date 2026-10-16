# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Assess coordinated upgrades without changing pins; confirm reversible exclusions."""

import argparse
import difflib
import hashlib
import json
import os
import sys
import tempfile
import tomllib
from datetime import UTC, datetime
from urllib.parse import quote, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

if __package__:
    from . import build_pack as builder
    from . import validate_pack as validator
else:
    import build_pack as builder
    import validate_pack as validator

POLICY = "build/disabled-mods.toml"
COVERAGE = (
    "Assessment only: candidate metadata is not a resolved dependency graph or a gameplay test. "
    "Version application is not implemented. No source pins or release gates are changed."
)


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("API redirects are not permitted")


def fetch_json(url):
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.hostname not in {"api.modrinth.com", "meta.fabricmc.net"}
            or parsed.username or parsed.password or parsed.port not in {None, 443}):
        raise ValueError("Only the public HTTPS Modrinth and Fabric APIs are permitted")
    request = Request(url, headers={"User-Agent": "Blockery-maintenance/1 (github.com/jd-santos/blockery)"})
    with build_opener(NoRedirects()).open(request, timeout=20) as response:
        try:
            return json.load(response)
        except (ValueError, UnicodeError) as error:
            raise ValueError("API returned invalid JSON") from error


def publication_time(value):
    """Compare timezone-aware API timestamps as instants, not strings."""
    published = datetime.fromisoformat(value)
    if "T" not in value or published.tzinfo is None:
        raise ValueError("Expected a timezone-aware publication timestamp")
    return published.astimezone(UTC)


def validate_versions(versions):
    """Reject malformed API evidence before selecting any candidate."""
    if not isinstance(versions, list):
        raise TypeError("Expected a version list")
    for version in versions:
        if not isinstance(version, dict):
            raise TypeError("Expected version objects")
        for field in ("id", "project_id", "version_number", "date_published", "version_type"):
            if not isinstance(version.get(field), str) or not version[field]:
                raise ValueError(f"Invalid version field: {field}")
        publication_time(version["date_published"])
        if version["version_type"] not in {"release", "beta", "alpha"}:
            raise ValueError("Invalid version type")
        for field in ("game_versions", "loaders"):
            values = version.get(field)
            if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
                raise ValueError(f"Invalid version field: {field}")
        dependencies = version.get("dependencies")
        if not isinstance(dependencies, list):
            raise TypeError("Expected a dependency list")
        for dependency in dependencies:
            if not isinstance(dependency, dict) or not isinstance(dependency.get("dependency_type"), str):
                raise TypeError("Invalid dependency object")
            if dependency["dependency_type"] not in {"required", "optional", "incompatible", "embedded"}:
                raise ValueError("Unsupported dependency type")
            for field in ("project_id", "version_id"):
                value = dependency.get(field)
                if value is not None and (not isinstance(value, str) or not value):
                    raise ValueError(f"Invalid dependency field: {field}")


def assess(root, minecraft, fabric, online=False, include_prerelease=False, fetch=fetch_json):
    if not all(isinstance(version, str) and builder.VERSION.fullmatch(version) for version in (minecraft, fabric)):
        raise builder.BuildError("Choose explicit nonempty Minecraft and Fabric target versions")
    source = validator.validate(root)
    entries = []
    for value, data in source["metadata"].items():
        profiles = [slug for slug, profile in source["profiles"].items() if value in profile["mods"]]
        selected_by = [slug for slug, profile in source["profiles"].items() if value in profile["mods"] or value in profile["disabled"]]
        if not selected_by:
            continue
        pin = data.get("update", {}).get("modrinth", {})
        entry = {
            "path": value, "name": data.get("name", value), "project_id": pin.get("mod-id"),
            "current_version_id": pin.get("version"), "current_filename": data["filename"],
            "profiles": profiles, "selected_by": selected_by,
            "status": "unknown", "candidate": None, "issues": [],
        }
        if value in source["disabled"]:
            entry.update(status="disabled", reason=source["disabled"][value])
        elif not online:
            entry["issues"].append("Offline assessment: target compatibility has not been queried.")
        elif not pin.get("mod-id") or not pin.get("version"):
            entry["issues"].append("No supported Modrinth update pin; review manually.")
        else:
            query = {"game_versions": json.dumps([minecraft])}
            if value.startswith("mods/"):
                query["loaders"] = json.dumps(["fabric"])
            url = "https://api.modrinth.com/v2/project/" + quote(pin["mod-id"], safe="") + "/version?" + urlencode(query)
            try:
                versions = fetch(url)
                validate_versions(versions)
                suitable = [
                    version for version in versions
                    if version.get("project_id") == pin["mod-id"]
                    and minecraft in version.get("game_versions", [])
                    and (not value.startswith("mods/") or "fabric" in version.get("loaders", []))
                    and (include_prerelease or version.get("version_type") == "release")
                ]
                if not suitable:
                    entry["status"] = "unavailable"
                    entry["issues"].append("No matching Modrinth release under the selected prerelease policy.")
                else:
                    candidate = max(suitable, key=lambda version: publication_time(version["date_published"]))
                    entry["candidate"] = {
                        "version_id": candidate["id"], "version_number": candidate["version_number"],
                        "published": publication_time(candidate["date_published"]).isoformat(), "dependencies": candidate.get("dependencies", []),
                    }
                    entry["status"] = "unchanged" if candidate["id"] == pin["version"] else "candidate"
            except (OSError, ValueError, KeyError, TypeError) as error:
                entry["issues"].append(f"Modrinth lookup failed: {error}")
        entries.append(entry)
    blockers = []
    for entry in entries:
        if not entry["candidate"]:
            continue
        for dependency in entry["candidate"]["dependencies"]:
            if dependency.get("dependency_type") != "required":
                continue
            project = dependency.get("project_id")
            matches = [other for other in entries if project and other["project_id"] == project]
            for slug in entry["profiles"]:
                active = [other for other in matches if slug in other["profiles"]]
                disabled = [other for other in matches if slug in other["selected_by"] and other["status"] == "disabled"]
                version = dependency.get("version_id")
                if not active:
                    blockers.append({"profile": slug, "path": entry["path"], "dependency_project": project,
                                     "dependency_version": version,
                                     "status": "disabled-required-dependency" if disabled else "unresolved-required-dependency",
                                     "note": "No active selected project; nested providers require a downloaded-JAR audit."})
                elif version and not any(other["candidate"] and other["candidate"]["version_id"] == version for other in active):
                    blockers.append({"profile": slug, "path": entry["path"], "dependency_project": project,
                                     "dependency_version": version, "status": "required-version-needs-review"})
    loader = {"status": "unknown", "version": fabric}
    if online:
        try:
            loaders = fetch("https://meta.fabricmc.net/v2/versions/loader/" + quote(minecraft, safe=""))
            if not isinstance(loaders, list):
                raise TypeError("Expected a loader list")
            for item in loaders:
                if (not isinstance(item, dict) or not isinstance(item.get("loader"), dict)
                        or not isinstance(item["loader"].get("version"), str)
                        or not item["loader"]["version"]):
                    raise ValueError("Invalid loader object")
            loader["status"] = "available" if any(item["loader"]["version"] == fabric for item in loaders) else "unavailable"
        except (OSError, ValueError, KeyError, TypeError) as error:
            loader["error"] = str(error)
    return {
        "current": source["versions"], "target": {"minecraft": minecraft, "fabric": fabric},
        "online": online, "include_prerelease": include_prerelease, "loader": loader,
        "entries": entries, "dependency_findings": blockers, "coverage": COVERAGE,
        "confirmation": "No changes applied. Review this report; version application is not implemented.",
    }


def policy_text(disabled):
    lines = ["# Reversible global exclusions. Original metadata and pins are retained.", "[disabled]"]
    lines.extend(f"{json.dumps(path)} = {json.dumps(reason)}" for path, reason in sorted(disabled.items()))
    return "\n".join(lines) + "\n"


def change_disabled(root, value, reason=None, enable=False, stdin=None, stdout=None, confirm=None):
    """Only mutate the fixed policy file, after preview and interactive approval."""
    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    confirm = input if confirm is None else confirm
    # Discover only validated inputs, then establish a baseline before deriving
    # the proposal. Revalidation must use the same bytes as that baseline.
    discovered = validator.validate(root)
    paths = {"pack.toml", "index.toml", "build/profiles.toml", *discovered["metadata"],
             *builder.NOTICE_SOURCES}
    paths.update(value for profile in discovered["profiles"].values() for value in profile["files"])
    before = {path: hashlib.sha256(builder.source_path(root, path).read_bytes()).hexdigest() for path in paths}
    policy = root / POLICY
    old = builder.source_path(root, POLICY).read_text() if policy.exists() or policy.is_symlink() else ""

    def require_unchanged():
        if any(hashlib.sha256(builder.source_path(root, path).read_bytes()).hexdigest() != expected for path, expected in before.items()):
            raise builder.BuildError("Source changed during confirmation; reassess before applying")
        current = builder.source_path(root, POLICY).read_text() if policy.exists() or policy.is_symlink() else ""
        if policy.is_symlink() or policy.parent.is_symlink() or current != old:
            raise builder.BuildError("Policy changed during confirmation; reassess before applying")

    source = validator.validate(root)
    require_unchanged()
    selected = set().union(*(set(p["mods"]) | set(p["disabled"]) for p in source["profiles"].values()))
    builder.safe_path(value)
    if value not in selected or value not in source["metadata"]:
        raise builder.BuildError("Choose an existing selected metadata path")
    disabled = dict(source["disabled"])
    if enable:
        if value not in disabled:
            raise builder.BuildError("Entry is not disabled")
        del disabled[value]
    else:
        if not isinstance(reason, str) or not reason.strip():
            raise builder.BuildError("Disabling requires a nonempty reason")
        disabled[value] = reason.strip()
    new = policy_text(disabled)
    if old == new:
        raise builder.BuildError("No policy change")
    print("".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), fromfile=POLICY, tofile=POLICY)), file=stdout)
    affected = [slug for slug, profile in source["profiles"].items() if value in profile["mods"] or value in profile["disabled"]]
    print("Affected distributions: " + ", ".join(affected), file=stdout)
    print("Warning: dependencies are not automatically resolved or disabled. Removing content mods can affect worlds. Revalidate before release.", file=stdout)
    if not stdin.isatty() or not stdout.isatty():
        raise builder.BuildError("Interactive confirmation required; no files changed")
    require_unchanged()
    try:
        answer = confirm("Apply only this disable-policy change? Type 'yes': ")
    except (EOFError, KeyboardInterrupt):
        raise builder.BuildError("Confirmation cancelled; no files changed") from None
    if answer != "yes":
        raise builder.BuildError("Not confirmed; no files changed")
    require_unchanged()
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=policy.parent, prefix=".disabled-", suffix=".tmp", delete=False) as temporary:
            name = temporary.name
            temporary.write(new)
        os.replace(name, policy)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)
    print("Policy changed; pins retained. Revalidate dependencies and test before release.", file=stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    report = commands.add_parser("report", help="Read-only target assessment; never applies versions")
    report.add_argument("--minecraft", required=True)
    report.add_argument("--fabric", required=True)
    report.add_argument("--online", action="store_true", help="Query public Modrinth and Fabric metadata")
    report.add_argument("--include-prerelease", action="store_true", help="Include beta/alpha candidates")
    report.add_argument("--json", action="store_true")
    disable = commands.add_parser("disable", help="Preview and confirm a global temporary exclusion")
    disable.add_argument("metadata")
    disable.add_argument("--reason", required=True)
    enable = commands.add_parser("enable", help="Preview and confirm removal of an exclusion")
    enable.add_argument("metadata")
    commands.add_parser("apply", help="Reserved: version application is not implemented")
    args = parser.parse_args()
    try:
        if args.command == "report":
            result = assess(builder.ROOT, args.minecraft, args.fabric, args.online, args.include_prerelease)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"Current: {result['current']}\nTarget: {result['target']}\nFabric availability: {result['loader']['status']}")
                if result["loader"].get("error"):
                    print(f"  Fabric lookup failed: {result['loader']['error']}")
                for entry in result["entries"]:
                    candidate = entry["candidate"]["version_number"] if entry["candidate"] else "not established"
                    print(f"{entry['status']}: {entry['path']}: {entry['current_version_id']} ({entry['current_filename']}) -> {candidate}")
                    print("  affected: " + ", ".join(entry["selected_by"]))
                    for issue in entry["issues"]:
                        print(f"  {issue}")
                    if entry.get("reason"):
                        print(f"  disabled: {entry['reason']}")
                for finding in result["dependency_findings"]:
                    print("dependency review: " + json.dumps(finding))
                print(COVERAGE)
                print(result["confirmation"])
        elif args.command == "apply":
            raise builder.BuildError("Version application is not implemented; use the report and a reviewed upgrade branch")
        else:
            change_disabled(builder.ROOT, args.metadata, getattr(args, "reason", None), args.command == "enable")
    except (builder.BuildError, OSError, KeyError, TypeError, ValueError, tomllib.TOMLDecodeError) as error:
        parser.exit(1, f"Upgrade tool failed: {error}\n")


if __name__ == "__main__":
    main()
