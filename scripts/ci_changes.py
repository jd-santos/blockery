"""Decide whether a pull request needs pack exports, not just offline checks."""

import os
import subprocess

PACK_PREFIXES = ("mods/", "resourcepacks/", "config/", "build/", "scripts/", "tests/", ".github/")
PACK_FILES = {"pack.toml", "index.toml", ".packwizignore", "LICENSE"}


def needs_exports(paths):
    """Unknown source paths trigger builds; known repository-only paths do not."""
    for path in paths:
        if path in PACK_FILES or path.startswith(PACK_PREFIXES):
            return True
        if path.startswith(("docs/", "todo/", ".agents/", "deploy/")):
            continue
        if "/" not in path and path.endswith(".md"):
            continue
        if path in {".gitignore", ".gitattributes"}:
            continue
        return True
    return False


def main():
    event = os.environ["GITHUB_EVENT_NAME"]
    build = event == "workflow_dispatch" and os.environ.get("BUILD_DRAFTS") == "true"
    if event == "pull_request":
        # Disable rename detection so moves report both the removed and added path.
        result = subprocess.run(
            ["git", "diff", "--name-only", "--no-renames", "-z",
             os.environ["BASE_SHA"], os.environ["HEAD_SHA"], "--"],
            check=True, capture_output=True,
        )
        paths = result.stdout.decode("utf-8").split("\0")
        build = needs_exports(path for path in paths if path)
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"build_drafts={str(build).lower()}\n")


if __name__ == "__main__":
    main()
