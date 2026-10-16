# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Read-only Fabric dependency evidence from locally supplied, pinned JARs."""

import argparse
import hashlib
import io
import json
import re
import stat
import struct
import zipfile
import zlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

if __package__:
    from . import build_pack as builder
    from . import fabric_versions, validate_pack
else:
    import build_pack as builder
    import fabric_versions
    import validate_pack

MAX_JAR_BYTES = 128 * 1024 * 1024
MAX_TOTAL_BYTES = 512 * 1024 * 1024
MAX_JSON_BYTES = 1024 * 1024
MAX_ENTRIES = 20000
MAX_CANDIDATES = 2048
MAX_CONSTRAINTS = 10000
MAX_ALIASES = 128
MAX_REPORTED_PROVIDERS = 16
MAX_DEPTH = 8
MOD_ID = re.compile(r"[a-z][a-z0-9_-]{1,63}")
KINDS = ("depends", "breaks", "recommends", "conflicts", "suggests")
COVERAGE = (
    "Pinned JAR metadata evidence only, not Fabric's resolver or a runtime test. "
    "Nested candidates are conditional; ambiguous providers and unsupported evidence remain unknown. "
    "No downloads, extraction, execution, source changes or release approval."
)


class EvidenceError(ValueError):
    """Unusable archive evidence, not an absent dependency."""


@dataclass
class Budget:
    remaining: int = MAX_TOTAL_BYTES
    candidates: int = 0
    constraints: int = 0

    def consume(self, size):
        if size < 0 or size > self.remaining:
            raise EvidenceError("Total inspected-byte limit exceeded")
        self.remaining -= size


def archive_path(value):
    """ZIP-only path validation: never access a host path from a nested name."""
    if (not isinstance(value, str) or not value or "\\" in value or ":" in value
            or any(ord(character) < 32 or ord(character) == 127 for character in value)
            or value.startswith("/")
            or any(part in {"", ".", ".."} for part in value.split("/"))):
        raise EvidenceError("Unsafe archive member path")
    return value


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError("Duplicate JSON key")
        result[key] = value
    return result


def invalid_constant(value):
    raise EvidenceError("Non-finite JSON value")


def metadata(raw):
    try:
        data = json.loads(raw, object_pairs_hook=unique_object, parse_constant=invalid_constant)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise EvidenceError(f"Invalid Fabric JSON: {error}") from error
    if not isinstance(data, dict) or type(data.get("schemaVersion")) is not int or data["schemaVersion"] != 1:
        raise EvidenceError("Only Fabric metadata schema version 1 is supported")
    if not isinstance(data.get("id"), str) or not MOD_ID.fullmatch(data["id"]):
        raise EvidenceError("Invalid Fabric mod ID")
    if (not isinstance(data.get("version"), str) or not data["version"] or len(data["version"]) > 256
            or any(ord(character) < 32 or ord(character) == 127 for character in data["version"])):
        raise EvidenceError("Invalid Fabric mod version")
    # Loader 0.19.5's v1 parser accepts a string environment. Other shapes are
    # unknown here, even where older wiki schema prose permits an array.
    if data.get("environment", "*") not in ("*", "client", "server"):
        raise EvidenceError("Unsupported Fabric environment")
    aliases = data.get("provides", [])
    if (not isinstance(aliases, list) or len(aliases) > MAX_ALIASES
            or not all(isinstance(alias, str) and MOD_ID.fullmatch(alias) for alias in aliases)):
        raise EvidenceError("Invalid Fabric provides aliases")
    if len(aliases) != len(set(aliases)) or data["id"] in aliases:
        raise EvidenceError("Duplicate or self-providing Fabric alias")
    for kind in KINDS:
        dependencies = data.get(kind, {})
        if not isinstance(dependencies, dict):
            raise EvidenceError(f"Invalid Fabric {kind} map")
        for identifier, predicate in dependencies.items():
            alternatives = predicate if isinstance(predicate, list) else [predicate]
            if (not MOD_ID.fullmatch(identifier) or not alternatives or len(alternatives) > 128
                    or not all(isinstance(item, str) and len(item) <= 4096 for item in alternatives)):
                raise EvidenceError(f"Invalid Fabric {kind} predicate")
    jars = data.get("jars", [])
    if not isinstance(jars, list):
        raise EvidenceError("Invalid Fabric nested-JAR declarations")
    paths = []
    for jar in jars:
        if not isinstance(jar, dict) or not isinstance(jar.get("file"), str):
            raise EvidenceError("Invalid Fabric nested-JAR declaration")
        paths.append(archive_path(jar["file"]))
    if len(paths) != len(set(paths)):
        raise EvidenceError("Duplicate nested-JAR declaration")
    return data


def preflight_directory(raw):
    """Bound actual central records before ZipFile allocates ZipInfo objects.

    Only ordinary single-disk ZIP layout is supported. Reject ZIP64 and prefixed
    or trailing layouts instead of guessing offsets differently from ZipFile.
    """
    end = raw.rfind(b"PK\x05\x06", max(0, len(raw) - 65557))
    if end < 0 or end + 22 > len(raw):
        raise EvidenceError("Missing or truncated ZIP end record")
    _, disk, central_disk, disk_count, count, size, offset, comment_size = struct.unpack_from("<4s4H2IH", raw, end)
    if end + 22 + comment_size != len(raw):
        raise EvidenceError("Unsupported trailing ZIP layout")
    if (disk or central_disk or disk_count != count or count == 65535
            or size == 4294967295 or offset == 4294967295
            or raw[max(0, end - 20):end - 16] == b"PK\x06\x07"):
        raise EvidenceError("Unsupported multi-disk or ZIP64 archive")
    if offset + size != end:
        raise EvidenceError("Unsupported ZIP central-directory layout")
    if count > MAX_ENTRIES:
        raise EvidenceError("JAR entry-count limit exceeded")
    position, actual = offset, 0
    while position < end:
        if position + 46 > end or raw[position:position + 4] != b"PK\x01\x02":
            raise EvidenceError("Malformed ZIP central directory")
        if struct.unpack_from("<H", raw, position + 34)[0] != 0:
            raise EvidenceError("Unsupported multi-disk ZIP entry")
        name_size, extra_size, entry_comment_size = struct.unpack_from("<3H", raw, position + 28)
        position += 46 + name_size + extra_size + entry_comment_size
        actual += 1
        if actual > MAX_ENTRIES:
            raise EvidenceError("JAR entry-count limit exceeded")
        if position > end:
            raise EvidenceError("Truncated ZIP central record")
    if actual != count:
        raise EvidenceError("ZIP central entry-count mismatch")


def inspect_jar(raw, source, side, budget, depth=0):
    """Return candidates only if the complete declared subtree was inspected."""
    if depth > MAX_DEPTH or len(raw) > MAX_JAR_BYTES:
        raise EvidenceError("JAR size or nesting-depth limit exceeded")
    budget.candidates += 1
    if budget.candidates > MAX_CANDIDATES:
        raise EvidenceError("JAR candidate-count limit exceeded")
    preflight_directory(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        if len(infos) > MAX_ENTRIES:
            raise EvidenceError("JAR entry-count limit exceeded")
        names = set()
        for info in infos:
            name = archive_path(info.filename[:-1] if info.is_dir() else info.filename)
            if name in names:
                raise EvidenceError("Duplicate archive member")
            names.add(name)
            if info.flag_bits & 1 or stat.S_ISLNK(info.external_attr >> 16):
                raise EvidenceError("Encrypted or symlink archive member")
            if info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
                raise EvidenceError("Unsupported archive compression method")

        def read_member(name, limit):
            info = archive.getinfo(name)
            if info.is_dir() or info.file_size > limit:
                raise EvidenceError("Inspected member exceeds size limit or is a directory")
            budget.consume(info.file_size)
            with archive.open(info) as stream:
                contents = stream.read(limit + 1)
            if len(contents) != info.file_size or len(contents) > limit:
                raise EvidenceError("Invalid inspected member size")
            return contents

        data = metadata(read_member("fabric.mod.json", MAX_JSON_BYTES))
        budget.constraints += sum(len(data.get(kind, {})) for kind in KINDS)
        if budget.constraints > MAX_CONSTRAINTS:
            raise EvidenceError("Dependency constraint-count limit exceeded")
        if data.get("environment", "*") not in {"*", side}:
            return [], [{"source": source, "id": data["id"], "reason": "wrong-environment"}]
        candidate = {
            "source": source, "id": data["id"], "version": data["version"],
            "provides": sorted(set(data.get("provides", []))), "nested": depth > 0,
            "dependencies": {kind: data.get(kind, {}) for kind in KINDS},
        }
        candidates, ignored = [candidate], []
        for jar in data.get("jars", []):
            child, excluded = inspect_jar(read_member(jar["file"], MAX_JAR_BYTES),
                                          source + "!/" + jar["file"], side, budget, depth + 1)
            candidates.extend(child)
            ignored.extend(excluded)
        return candidates, ignored


def read_pinned(jars, relative, download, budget):
    """Read exactly one declared file; refuse symlinks rather than follow them."""
    relative = builder.safe_path(relative)
    directory = Path(jars).absolute()
    # Check all existing ancestors too, not just the final directory entry.
    for path in [directory, *directory.parents]:
        if path.is_symlink():
            raise EvidenceError("JAR directory has a symlink ancestor")
    path = directory
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise EvidenceError("Pinned JAR path contains a symlink")
    if not path.is_file():
        raise EvidenceError("Pinned JAR is missing or not a regular file")
    size = path.stat().st_size
    if size > MAX_JAR_BYTES:
        raise EvidenceError("Pinned JAR exceeds size limit")
    budget.consume(size)
    with path.open("rb") as stream:
        raw = stream.read(MAX_JAR_BYTES + 1)
    if len(raw) != size or len(raw) > MAX_JAR_BYTES:
        raise EvidenceError("Pinned JAR changed size while reading")
    if hashlib.new(download["hash-format"], raw).hexdigest().lower() != download["hash"].lower():
        raise EvidenceError("Pinned JAR hash mismatch")
    return raw


def check_dependency(consumer, kind, identifier, predicate, providers, incomplete):
    candidates = providers.get(identifier, [])
    finding = {
        "source": consumer["source"], "mod": consumer["id"], "kind": kind,
        "dependency": identifier, "predicate": predicate,
        "severity": "error" if kind in {"depends", "breaks"} else "warning",
        "scope": "nested-candidate" if consumer["nested"] else "selected-mod",
        "provider_count": len(candidates),
        "providers": [{"id": candidate["id"], "version": candidate["version"],
                       "source": candidate["source"],
                       "matches": fabric_versions.matches(candidate["version"], predicate)}
                      for candidate in candidates[:MAX_REPORTED_PROVIDERS]],
    }
    if fabric_versions.matches("0", predicate) is None:
        return dict(finding, status="unknown", reason="Unsupported version predicate")
    if kind == "suggests":
        return dict(finding, status="informational", reason="Suggestions do not constrain resolution")
    if (incomplete or consumer["nested"] or len(candidates) > 1
            or any(candidate["nested"] for candidate in candidates)):
        return dict(finding, status="unknown", reason="Incomplete inventory or conditional/ambiguous provider selection")
    if not candidates:
        matched = False
    else:
        matched = finding["providers"][0]["matches"]
    if matched is None:
        return dict(finding, status="unknown", reason="Unsupported predicate or unavailable normalized platform version")
    violated = not matched if kind in {"depends", "recommends"} else matched
    status = ("violated" if kind in {"depends", "breaks"} else "warning") if violated else "satisfied"
    return dict(finding, status=status, reason="Declared metadata constraint")


def audit(root, profile, jars, minecraft=None, fabric=None, java=None):
    source = validate_pack.validate(root)
    if profile not in source["profiles"]:
        raise builder.BuildError(f"Unknown build profile: {profile}")
    selected = source["profiles"][profile]
    target = {"minecraft": minecraft or source["versions"]["minecraft"],
              "fabricloader": fabric or source["versions"]["fabric"], "java": java}
    if any(value is not None and (not isinstance(value, str) or not builder.VERSION.fullmatch(value))
           for value in target.values()):
        raise builder.BuildError("Platform versions must be explicit version strings")
    budget = Budget()
    candidates, ignored, artifacts, findings = [], [], [], []
    for value in selected["mods"]:
        if not value.startswith("mods/"):
            continue  # Resource packs do not supply Fabric mod dependencies.
        data = source["metadata"][value]
        installed = str(PurePosixPath(value).parent / data["filename"])
        artifact = {"metadata": value, "path": installed, "hash": data["download"]["hash"],
                    "hash_format": data["download"]["hash-format"]}
        try:
            if not installed.endswith(".jar"):
                raise EvidenceError("Selected mod download is not a JAR")
            raw = read_pinned(jars, data["filename"], data["download"], budget)
            mods, excluded = inspect_jar(raw, installed, selected["side"], budget)
            candidates.extend(mods)
            ignored.extend(excluded)
            artifact["status"] = "verified"
        except (OSError, ValueError, KeyError, TypeError, RecursionError, RuntimeError,
                NotImplementedError, zipfile.BadZipFile, zlib.error, EOFError) as error:
            artifact["status"] = "unknown"
            findings.append({"source": installed, "status": "unknown", "kind": "evidence",
                             "reason": str(error), "severity": "error"})
        artifacts.append(artifact)
    incomplete = any(artifact["status"] != "verified" for artifact in artifacts)
    providers = {}
    for identifier, version in target.items():
        providers[identifier] = [{"id": identifier,
                                  "version": version if fabric_versions.numeric_version(version) else None,
                                  "source": "target:" + identifier, "nested": False}]
    for candidate in candidates:
        for identifier in sorted({candidate["id"], *candidate["provides"]}):
            providers.setdefault(identifier, []).append(candidate)
    for identifier, choices in providers.items():
        if len(choices) > 1:
            findings.append({"source": identifier, "status": "unknown", "kind": "provider-selection",
                             "reason": "Competing IDs or provides aliases require Fabric resolver selection",
                             "severity": "error"})
    if any(candidate["nested"] for candidate in candidates):
        findings.append({"source": profile, "status": "unknown", "kind": "nested-selection",
                         "reason": "Nested candidates are inventoried, not assumed simultaneously loaded",
                         "severity": "error"})
    for consumer in candidates:
        for kind, dependencies in consumer["dependencies"].items():
            for identifier, predicate in dependencies.items():
                findings.append(check_dependency(consumer, kind, identifier, predicate, providers, incomplete))
    status = "violated" if any(f["status"] == "violated" for f in findings) else (
        "unknown" if any(f["status"] == "unknown" for f in findings) else "checked")
    return {"profile": profile, "side": selected["side"], "target": target,
            "status": status, "artifacts": artifacts, "candidates": candidates, "ignored": ignored,
            "disabled": selected["disabled"], "findings": findings, "coverage": COVERAGE}


def print_report(result, as_json=False):
    if as_json:
        print(json.dumps(result, indent=2))
        return
    print(f"{result['profile']}: {result['status']}\nTarget: {result['target']}")
    for artifact in result["artifacts"]:
        print(f"{artifact['status']}: {artifact['path']}")
    for candidate in result["candidates"]:
        scope = "nested candidate" if candidate["nested"] else "selected mod"
        print(f"{scope}: {candidate['id']} {candidate['version']}: {candidate['source']}")
    for excluded in result["ignored"]:
        print("ignored: " + json.dumps(excluded))
    if result["disabled"]:
        print("disabled: " + json.dumps(result["disabled"]))
    for finding in result["findings"]:
        print(json.dumps(finding))
    print(result["coverage"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile")
    parser.add_argument("--jars", type=Path, required=True, help="Read-only directory containing the selected pinned mod filenames")
    parser.add_argument("--minecraft", help="Target release version, defaults to pack.toml")
    parser.add_argument("--fabric", help="Target Loader version, defaults to pack.toml")
    parser.add_argument("--java", help="Explicit target Java version; unspecified checks remain unknown")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = audit(builder.ROOT, args.profile, args.jars, args.minecraft, args.fabric, args.java)
        print_report(result, args.json)
    except (builder.BuildError, OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Dependency audit failed: {error}\n")


if __name__ == "__main__":
    main()
