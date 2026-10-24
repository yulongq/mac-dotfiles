"""Check installed CLI versions without package-manager or account access."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from test_dotfiles import ROOT


class SkillVersionTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory(prefix="mac-dotfiles-skill-versions-")
        self.addCleanup(self.workspace.cleanup)
        self.base = Path(self.workspace.name)
        self.script = self.base / "scripts/check-skill-versions"
        self.script.parent.mkdir()
        shutil.copy2(ROOT / "scripts/check-skill-versions", self.script)
        self.bin = self.base / "bin"
        self.bin.mkdir()
        for name in ("glab", "herdr", "oracle", "sessidx"):
            skill = self.base / "agent-policy/dot_agents/exact_skills" / name / "SKILL.md"
            skill.parent.mkdir(parents=True)
            owner = "gitlab" if name == "glab" else "github"
            skill.write_text(f"---\nmetadata:\n  {owner}-ref: refs/tags/v1.2.3\n---\n")
            self.command(name, f"printf '%s\\n' '{name} 1.2.3'")

    def command(self, name, body):
        path = self.bin / name
        path.write_text(f'#!/bin/sh\n[ "$#" = 1 ] && [ "$1" = --version ] || exit 9\n{body}\n')
        path.chmod(0o755)

    def check(self):
        return subprocess.run(
            ["/usr/bin/ruby", str(self.script)], text=True, capture_output=True, timeout=10,
            env={"HOME": str(self.base), "PATH": f"{self.bin}:/usr/bin:/bin"},
        )

    def test_versions_follow_resolved_clis_and_only_report_mismatches(self):
        result = self.check()
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, "", ""))
        self.command("oracle", "printf '1.2.4\\n'")
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("oracle: skill reviewed at 1.2.3; installed CLI is 1.2.4", result.stderr)
        self.assertEqual(result.stdout, "")

    def test_unavailable_or_failed_version_queries_fail_the_check(self):
        for body in ("exit 7", "printf 'unrecognized output\\n'", None):
            with self.subTest(body=body):
                if body is None:
                    (self.bin / "oracle").unlink()
                else:
                    self.command("oracle", body)
                result = self.check()
                self.assertEqual(result.returncode, 1)
                self.assertIn("oracle:", result.stderr)
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
