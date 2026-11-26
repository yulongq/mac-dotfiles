import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


DEPLOY = Path(__file__).resolve().parents[1] / "scripts/deploy"


class DeployTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="mac-dotfiles-selection-")
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name)
        self.dest = self.base / "home"
        self.dest.mkdir()
        # A cold, offline .gitmessage deploy must never fetch unrelated externals.
        self.env = {**os.environ, "HTTP_PROXY": "http://127.0.0.1:1", "HTTPS_PROXY": "http://127.0.0.1:1",
                    "NO_PROXY": "", "no_proxy": ""}

    def deploy(self, *args, success=True):
        result = subprocess.run([DEPLOY, "--dest", self.dest, *args], env=self.env, text=True,
                                capture_output=True, timeout=30)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def test_cold_mixed_group_and_file_deploy(self):
        args = ("kitty", ".config/homebrew/brew.env", ".gitmessage")
        preview = self.deploy("diff", *args)
        self.assertEqual(list(self.dest.iterdir()), [])
        self.assertIn("kitty runtime:", preview.stderr)
        self.assertIn(".gitmessage runtime:", preview.stderr)
        self.assertNotIn("git runtime:", preview.stderr)
        self.assertIn("new file mode 40700", preview.stdout)
        self.assertEqual(self.deploy("apply", *args).stdout, preview.stdout)
        kitty = self.dest / ".config/kitty"
        self.assertEqual({p.name for p in kitty.iterdir()}, {"kitty.conf", "enabled-layouts.conf", "current-theme.conf"})
        self.assertEqual((self.dest / ".config/homebrew").stat().st_mode & 0o777, 0o700)
        self.assertEqual({p.name for p in self.dest.iterdir()}, {".gitmessage", ".config"})
        self.assertEqual(self.deploy("apply", *args).stdout, "")

    def test_only_selected_leaf_and_required_parents(self):
        shared = self.dest / ".config"
        shared.mkdir(mode=0o700)
        applied = self.deploy("apply", ".config/kitty/kitty.conf")
        self.assertIn("enabled-layouts.conf and current-theme.conf", applied.stderr)
        self.assertEqual(shared.stat().st_mode & 0o777, 0o700)
        self.assertEqual(list((shared / "kitty").iterdir()), [shared / "kitty/kitty.conf"])
        self.assertFalse((self.dest / ".codex").exists())

    def test_invalid_batch_writes_nothing(self):
        outside = self.base / "outside"
        outside.mkdir()
        (self.dest / ".config").symlink_to(outside)
        for selector in ("../outside", ".config", ".env", "pi=invalid", ".config/kitty/kitty.conf"):
            with self.subTest(selector=selector):
                self.deploy("apply", ".gitmessage", selector, success=False)
                self.assertFalse((self.dest / ".gitmessage").exists())
                self.assertEqual(list(outside.iterdir()), [])
        self.deploy("apply", success=False)
        self.deploy("apply", ".gitmessage", "claude=host", "claude=sandbox", success=False)
        self.assertFalse((self.dest / ".gitmessage").exists())

    def test_modifier_preview_suppresses_unowned_values(self):
        config = self.dest / ".claude/settings.json"
        config.parent.mkdir()
        config.write_text('{"sandbox":{"enabled":true},"model":"synthetic-local-choice"}')
        preview = self.deploy("diff", "claude=host")
        self.assertIn("sandbox", preview.stdout)
        self.assertIn("false", preview.stdout)
        self.assertNotIn("synthetic-local-choice", preview.stdout + preview.stderr)
        self.assertNotIn("approval", preview.stdout)
        self.assertIn("true", config.read_text())

    def test_tool_preview_names_changed_setting_and_desired_value(self):
        target = self.dest / ".omp/agent/config.yml"
        target.parent.mkdir(parents=True)
        target.write_text("modelRoles:\n  default: prior-model\n  custom: local-only\n")
        preview = self.deploy("diff", ".omp/agent/config.yml").stdout
        self.assertIn("modelRoles", preview)
        self.deploy("apply", ".omp/agent/config.yml")
        expected = subprocess.check_output(
            ["/usr/bin/ruby", "-ryaml", "-e", 'puts YAML.load_file(ARGV.first).fetch("modelRoles").fetch("default")',
             str(target)], text=True,
        ).strip()
        self.assertIn("modelRoles.default = " + json.dumps(expected), preview)
        self.assertNotIn("local-only", preview)

    def test_switching_one_agent_preserves_existing_siblings(self):
        (self.dest / ".agents/skills").mkdir(parents=True)
        args = ("pi", "pi=sandbox", "claude", "claude=host", "codex=sandbox")
        self.deploy("apply", *args)
        self.assertEqual((self.dest / ".claude/skills").resolve(), self.dest.resolve() / ".agents/skills")
        self.assertEqual(self.deploy("diff", *args).stdout, "")
        pi = self.dest / ".pi/agent/settings.json"
        claude = self.dest / ".claude/settings.json"
        codex = self.dest / ".codex/config.toml"
        for path in (pi, claude):
            settings = json.loads(path.read_text())
            settings["hostPreference"] = "keep"
            path.write_text(json.dumps(settings, indent=4))
        codex.write_text("# host formatting\n" + codex.read_text())
        siblings = {p: p.read_bytes() for p in (claude, codex)}
        pi.parent.chmod(0o750)
        for mode in ("host", "sandbox"):
            self.deploy("apply", "pi=" + mode)
            self.assertEqual(self.deploy("diff", "pi=" + mode).stdout, "")
            self.assertEqual(pi.parent.stat().st_mode & 0o777, 0o750)
            settings = json.loads(pi.read_text())
            self.assertEqual(settings["hostPreference"], "keep")
            self.assertEqual("shellPath" in settings, mode == "sandbox")
            self.assertEqual({p: p.read_bytes() for p in siblings}, siblings)
