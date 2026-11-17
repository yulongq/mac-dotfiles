import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_dotfiles import ROOT, run


class PrePushTests(unittest.TestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory(prefix="mac-dotfiles-pre-push-")
        self.addCleanup(workspace.cleanup)
        self.repo = Path(workspace.name)
        self.environment = {"HOME": str(self.repo), "PATH": os.environ["PATH"],
                            "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null"}
        self.git("init", "--quiet")
        (self.repo / "scripts").mkdir()
        self.validator = self.repo / "scripts/validate"
        self.validator.touch(mode=0o755)

    def git(self, *args):
        return run("git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                   *args, cwd=self.repo, env=self.environment).stdout.strip()

    def commit(self, label, status):
        self.validator.write_text(f"#!/bin/sh\necho {label}\nexit {status}\n")
        self.git("add", "scripts/validate")
        self.git("commit", "--quiet", "-m", label)
        return self.git("rev-parse", "HEAD")

    def hook(self, *updates):
        return subprocess.run([ROOT / ".githooks/pre-push", "origin", "fixture"], cwd=self.repo,
                              env=self.environment, text=True, capture_output=True,
                              input="".join(f"{ref} {oid} refs/heads/remote-{i} {'0' * len(oid)}\n"
                                            for i, (ref, oid) in enumerate(updates)), timeout=30)

    def test_push_checks_all_distinct_commit_tips_instead_of_the_worktree(self):
        good = self.commit("good", 0)
        self.git("tag", "-am", "good tag", "good-tag")
        tag = self.git("rev-parse", "refs/tags/good-tag")
        bad = self.commit("bad", 7)
        self.commit("checked-out", 0)
        result = self.hook(("(delete)", "0" * len(good)), ("refs/tags/good-tag", tag),
                           ("refs/heads/good", good), ("refs/heads/bad", bad))
        self.assertEqual(result.stdout.splitlines(), ["good", "bad"], result.stderr)
        self.assertNotEqual(result.returncode, 0)

    def test_push_accepts_validated_commit_and_ignores_non_commit_refs(self):
        good = self.commit("good", 0)
        blob = self.git("rev-parse", "HEAD:scripts/validate")
        self.commit("checked-out", 7)
        result = self.hook(("refs/tags/blob", blob), ("refs/heads/good", good))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ["good"])
