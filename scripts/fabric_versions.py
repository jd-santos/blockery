"""Conservative Fabric predicates, following Loader 0.19.5, not PEP 440.

Unsupported syntax returns None (unknown). No Minecraft snapshot normalization.
"""

import re
from itertools import zip_longest

NUMERIC = re.compile(r"([0-9]+)(?:\.[0-9]+)*(?:-([0-9A-Za-z.-]*))?(?:\+[^\s]*)?")
UNSIGNED = re.compile(r"0|[1-9][0-9]*")
TERM = re.compile(r"(>=|<=|>|<|=|~|\^)?([^\s]+)")


def numeric_version(value) -> tuple[tuple[int, ...], tuple[str, ...] | None] | None:
    """Return numeric components and prerelease identifiers, or unknown."""
    if not isinstance(value, str) or len(value) > 256:
        return None
    match = NUMERIC.fullmatch(value)
    if not match:
        return None
    core = value.split("+", 1)[0].split("-", 1)[0]
    parts = tuple(int(part) for part in core.split("."))
    if len(parts) > 16 or any(part > 2147483647 for part in parts):
        return None
    prerelease = match[2]
    if prerelease not in {None, ""} and any(not part for part in prerelease.split(".")):
        return None
    return parts, None if prerelease is None else tuple(prerelease.split(".")) if prerelease else ()


def compare(left, right):
    """Compare extended numeric versions; absent components are zero."""
    for a, b in zip_longest(left[0], right[0], fillvalue=0):
        if a != b:
            return (a > b) - (a < b)
    a, b = left[1], right[1]
    if a is None or b is None:
        return (a is None) - (b is None)
    for x, y in zip(a, b, strict=False):
        if x == y:
            continue
        x_numeric, y_numeric = bool(UNSIGNED.fullmatch(x)), bool(UNSIGNED.fullmatch(y))
        if x_numeric and y_numeric:
            return (int(x) > int(y)) - (int(x) < int(y))
        if x_numeric != y_numeric:
            return -1 if x_numeric else 1
        return (x > y) - (x < y)
    return (len(a) > len(b)) - (len(a) < len(b))


def match_term(version, term):
    if term == "*":
        return True
    match = TERM.fullmatch(term)
    if not match:
        return None
    operator, reference = match[1] or "=", match[2]
    # Ordered comparisons of arbitrary strings and unimplemented range syntax
    # are deliberately unknown rather than approximated with Python packaging.
    actual = numeric_version(version)
    if any(part in {"x", "X", "*"} for part in reference.split(".")):
        if operator != "=" or actual is None:
            return None
        parts = reference.split(".")
        first = next(i for i, part in enumerate(parts) if part in {"x", "X", "*"})
        if (first == 0 or first > 2
                or not all(part in {"x", "X", "*"} for part in parts[first:])):
            return None
        prefix = numeric_version(".".join(parts[:first]))
        if prefix is None or prefix[1] is not None:
            return None
        padded = actual[0] + (0,) * first
        return padded[:first] == prefix[0]
    target = numeric_version(reference)
    if actual is None or target is None:
        # Numeric-looking input outside our bounded parser must not become a
        # string comparison: Loader could still normalize it numerically.
        if ((actual is None and version[:1].isdigit())
                or (target is None and reference[:1].isdigit())):
            return None
        if operator == "=" and reference and not any(c in reference for c in "*|<>=~^ \t\n"):
            return version == reference
        return None
    relation = compare(actual, target)
    if operator == "^":
        return relation >= 0 and actual[0][0] == target[0][0]
    if operator == "~":
        a = actual[0] + (0, 0)
        b = target[0] + (0, 0)
        return relation >= 0 and a[:2] == b[:2]
    return {"=": relation == 0, ">": relation > 0, ">=": relation >= 0,
            "<": relation < 0, "<=": relation <= 0}[operator]


def matches(version, predicate):
    """True/False/None for Fabric AND strings and OR arrays.

    Malformed or unsupported terms poison the whole predicate, even when another
    term could decide it. This avoids treating invalid metadata as useful evidence.
    """
    if not isinstance(version, str) or not version or len(version) > 256:
        return None
    alternatives = predicate if isinstance(predicate, list) else [predicate]
    if not alternatives or len(alternatives) > 128:
        return None
    results = []
    for alternative in alternatives:
        if not isinstance(alternative, str) or len(alternative) > 4096:
            return None
        terms = alternative.split(" ")
        terms = [term.strip() for term in terms if term.strip()]
        values = [match_term(version, term) for term in terms]
        if any(value is None for value in values):
            return None
        results.append(all(values))
    return any(results)
