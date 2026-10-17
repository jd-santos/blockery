"""CI routing tests: docs stay cheap; pack input changes build drafts."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import ci_changes


class ChangesTests(unittest.TestCase):
    def test_docs_and_skills_do_not_need_exports(self):
        self.assertFalse(ci_changes.needs_exports([
            "README.md", "AGENTS.md", "docs/tooling.md", "todo/TODO.md",
            ".agents/skills/blockery-release-notes/SKILL.md", "deploy/README.md",
        ]))
        self.assertFalse(ci_changes.needs_exports([]))

    def test_pack_build_and_unknown_paths_need_exports(self):
        for path in (
            "pack.toml", "index.toml", ".packwizignore", "LICENSE",
            "mods/example.pw.toml", "resourcepacks/example.pw.toml",
            "config/example.json", "build/NOTICE.txt", "build/profiles.toml",
            "scripts/build_pack.py", "tests/test_build_pack.py",
            ".github/workflows/validate.yml", "unknown/new-input.txt",
        ):
            with self.subTest(path=path):
                self.assertTrue(ci_changes.needs_exports(["README.md", path]))

    def run_event(self, event, drafts="false", changed=b"README.md\0"):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            environment = {
                "GITHUB_EVENT_NAME": event, "BUILD_DRAFTS": drafts,
                "BASE_SHA": "a" * 40, "HEAD_SHA": "b" * 40,
                "GITHUB_OUTPUT": str(output),
            }
            with patch.dict(os.environ, environment), patch(
                "scripts.ci_changes.subprocess.run",
                return_value=subprocess.CompletedProcess([], 0, stdout=changed),
            ) as git:
                ci_changes.main()
                result = output.read_text()
                return result, git.call_args

    def test_main_push_never_builds(self):
        result, call = self.run_event("push", drafts="true")
        self.assertEqual(result, "build_drafts=false\n")
        self.assertIsNone(call)

    def test_dispatch_requires_explicit_opt_in(self):
        self.assertEqual(self.run_event("workflow_dispatch")[0], "build_drafts=false\n")
        self.assertEqual(
            self.run_event("workflow_dispatch", drafts="true")[0],
            "build_drafts=true\n",
        )

    def test_pr_routing_uses_full_diff_without_rename_detection(self):
        self.assertEqual(self.run_event("pull_request")[0], "build_drafts=false\n")
        result, call = self.run_event(
            "pull_request", changed=b"README.md\0mods/deleted.pw.toml\0"
        )
        self.assertEqual(result, "build_drafts=true\n")
        self.assertIsNotNone(call)
        self.assertIn("--no-renames", call.args[0])
        self.assertIn("-z", call.args[0])

    def test_git_failure_does_not_silently_skip_builds(self):
        with patch.dict(os.environ, {"GITHUB_EVENT_NAME": "pull_request",
                                     "BASE_SHA": "a" * 40, "HEAD_SHA": "b" * 40}), patch(
            "scripts.ci_changes.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, ["git"]),
        ), self.assertRaises(subprocess.CalledProcessError):
            ci_changes.main()


if __name__ == "__main__":
    unittest.main()
