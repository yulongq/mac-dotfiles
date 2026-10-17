"""Run Agent hook contracts through the repository's standard test runner."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest

from test_dotfiles import ROOT, run


POLICY = ROOT / "agent-policy"


class AgentHookTests(unittest.TestCase):
    def test_pre_edit_hook_resolves_both_sources_inside_a_git_checkout(self):
        with tempfile.TemporaryDirectory(prefix="mac-dotfiles-hook-") as directory:
            base = Path(directory)
            checkout = base / "checkout"
            policy = checkout / "agent-policy"
            destination = base / "home"
            destination.mkdir()
            files = {
                ".chezmoiroot": "home\n",
                "home/dot_zshrc": "# shell fixture\n",
                "agent-policy/dot_codex/AGENTS.md": "Instruction fixture.\n",
                "agent-policy/dot_claude/modify_private_settings.json": "#!/bin/sh\ncat\n",
                "agent-policy/dot_agents/exact_skills/example/SKILL.md": "Skill fixture.\n",
            }
            for relative, content in files.items():
                path = checkout / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            run("git", "init", "--quiet", str(checkout))
            relative = "dot_claude/hooks/executable_pre-edit-warn-chezmoi.sh.tmpl"
            (policy / relative).parent.mkdir(parents=True)
            shutil.copy2(POLICY / relative, policy / relative)
            rendered = run("chezmoi", "--config", "/dev/null", "--config-format", "toml",
                           "--source", str(policy), "--destination", str(destination),
                           "cat", str(destination / ".claude/hooks/pre-edit-warn-chezmoi.sh")).stdout
            hook = base / "hook.sh"
            hook.write_text(rendered)
            environment = {"HOME": str(destination), "XDG_CONFIG_HOME": str(base / "config"),
                           "PATH": os.environ["PATH"]}
            for relative, decision in ((".zshrc", "deny"), (".codex/AGENTS.md", "deny"),
                                       (".claude/settings.json", "ask"),
                                       (".agents/skills/example/SKILL.md", "deny"),
                                       ("unmanaged.txt", None)):
                with self.subTest(target=relative):
                    result = run("/bin/bash", str(hook), env=environment,
                                 input=json.dumps({"tool_input": {"file_path": str(destination / relative)}}))
                    actual = json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"] if result.stdout else None
                    self.assertEqual(actual, decision)

    def test_claude_hooks_and_statusline(self):
        for script in sorted((POLICY / "dot_claude").glob("*/*.test.sh")):
            with self.subTest(script=script.name):
                result = subprocess.run(["bash", str(script)], text=True,
                                        capture_output=True, timeout=60)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_codex_required_permission_mode(self):
        templates = POLICY / ".chezmoitemplates/codex"
        requirements = tomllib.loads((templates / "requirements.toml").read_text())
        config = tomllib.loads((templates / "config.toml").read_text())
        self.assertEqual(requirements["default_permissions"], config["default_permissions"])
        self.assertEqual(requirements["allowed_approval_policies"], [config["approval_policy"]])
        self.assertEqual(requirements["allowed_approvals_reviewers"], [config["approvals_reviewer"]])
        self.assertEqual(requirements["allowed_permission_profiles"], {config["default_permissions"]: True})

    def test_codex_hook_registration(self):
        requirements = tomllib.loads((POLICY / ".chezmoitemplates/codex/requirements.toml").read_text())
        hooks = requirements["hooks"]
        managed_dir = "{{ .chezmoi.homeDir }}/.codex/managed-hooks"
        self.assertEqual(hooks["managed_dir"], managed_dir)
        for event, matcher, script in (
            ("PreToolUse", {"matcher": "^Bash$"}, "guard-bash"),
            ("UserPromptSubmit", {}, "contextual-markdown-links"),
        ):
            with self.subTest(event=event):
                entries = hooks[event]
                self.assertEqual(len(entries), 1)
                entry = dict(entries[0])
                commands = entry.pop("hooks")
                self.assertEqual(entry, matcher)
                self.assertEqual(len(commands), 1)
                command = dict(commands[0])
                self.assertGreater(command.pop("timeout"), 0)
                self.assertEqual(command, {"type": "command", "command": f"{managed_dir}/{script}"})
        for event, entries in hooks.items():
            if event == "managed_dir":
                continue
            for entry in entries:
                for command in entry["hooks"]:
                    self.assertTrue(command["command"].startswith(managed_dir + "/"))

    def test_codex_prompt_hook_without_urls(self):
        result = run("/bin/zsh", "-f", str(POLICY / "dot_codex/managed-hooks/executable_contextual-markdown-links"),
                     input=json.dumps({"prompt": "Draft a concise note."}))
        self.assertEqual(result.stderr, "")
        payload = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(payload["hookEventName"], "UserPromptSubmit")
        self.assertIsInstance(payload["additionalContext"], str)
        self.assertTrue(payload["additionalContext"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
