#!/usr/bin/env python3
"""Exercise real Agent modifiers against synthetic, isolated destinations."""

import json
from pathlib import Path
import shutil
import tempfile
import tomllib
import unittest

from test_dotfiles import ROOT, run


class AgentConfigTests(unittest.TestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory(prefix="mac-dotfiles-agent-config-")
        self.addCleanup(workspace.cleanup)
        self.base = Path(workspace.name)
        self.source = self.base / "source"
        self.destination = self.base / "home"
        self.destination.mkdir()
        for name in (
            ".chezmoitemplates/claude/settings.json",
            ".chezmoitemplates/codex/config.toml",
            "dot_claude/modify_private_settings.json",
            "dot_codex/modify_private_config.toml",
        ):
            target = self.source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / "agent-policy" / name, target)
        self.environment = {
            "HOME": str(self.destination), "TMPDIR": str(self.base),
            "PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        }
        self.chezmoi = [
            "chezmoi", "--config", "/dev/null", "--config-format", "toml",
            "--source", str(self.source), "--destination", str(self.destination),
            "--persistent-state", str(self.base / "state"),
            "--cache", str(self.base / "cache"), "--refresh-externals=never", "--no-tty",
            "--override-data", json.dumps({"private": {
                "gitlabHost": "https://git.example.invalid",
                "npmHost": "https://npm.example.invalid",
                "rcGatewayBaseUrl": "https://gateway.example.invalid",
            }}),
        ]

    def apply(self, relative, contents=None):
        target = self.destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if contents is not None:
            target.write_text(contents)
        run(*self.chezmoi, "apply", "--exclude=scripts,encrypted", str(target), env=self.environment)
        return target

    def test_claude_shared_fields_survive(self):
        current = {
            "model": "host-model",
            "modelSettings": {"host-model": {"effort": "high"}},
            "env": {
                "ANTHROPIC_BASE_URL": "https://route.example.invalid",
                "HOST_SETTING": "keep",
                "CLAUDE_CODE_RETRY_WATCHDOG_MAX_WAIT_MS": "60000",
            },
            "sandbox": {"network": {"allowUnixSockets": ["/synthetic/ssh.sock"]}},
        }
        target = self.apply(".claude/settings.json", json.dumps(current))
        actual = json.loads(target.read_text())
        self.assertEqual(actual["model"], current["model"])
        self.assertEqual(actual["modelSettings"], current["modelSettings"])
        self.assertEqual(actual["env"]["ANTHROPIC_BASE_URL"], current["env"]["ANTHROPIC_BASE_URL"])
        self.assertEqual(actual["env"]["HOST_SETTING"], "keep")
        self.assertEqual(actual["env"]["CLAUDE_CODE_RETRY_WATCHDOG_MAX_WAIT_MS"], "1800000")
        self.assertEqual(actual["sandbox"]["network"]["allowUnixSockets"], ["/synthetic/ssh.sock"])

    def test_claude_empty_socket_choice_and_owned_subtree_replacement(self):
        current = {
            "sandbox": {"network": {"allowUnixSockets": []}},
            "enabledPlugins": {"obsolete@example": True},
        }
        actual = json.loads(self.apply(".claude/settings.json", json.dumps(current)).read_text())
        self.assertEqual(actual["sandbox"]["network"]["allowUnixSockets"], [])
        self.assertNotIn("obsolete@example", actual["enabledPlugins"])

    def test_fresh_configuration_and_idempotence(self):
        claude = self.apply(".claude/settings.json")
        codex = self.apply(".codex/config.toml")
        settings = json.loads(claude.read_text())
        self.assertEqual(settings["model"], "opus")
        self.assertEqual(settings["env"]["CLAUDE_CODE_RETRY_WATCHDOG_MAX_WAIT_MS"], "1800000")
        self.assertIn("~/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock",
                      settings["sandbox"]["network"]["allowUnixSockets"])
        config = tomllib.loads(codex.read_text())
        self.assertNotIn("model", config)
        self.assertNotIn("model_context_window", config)
        self.assertEqual(config["tui"]["copy_on_select"], "always")
        self.assertEqual(config["tui"]["status_line"], [
            "model-with-reasoning", "git-branch", "context-used", "context-window-size",
            "current-dir", "five-hour-limit", "thread-id",
        ])
        # Equal values must preserve existing text, including harmless formatting.
        claude.write_text(json.dumps(settings, indent=4) + "\n")
        codex.write_text("# Retain local formatting.\n" + codex.read_text())
        for target in (claude, codex):
            before = target.read_bytes()
            self.apply(str(target.relative_to(self.destination)))
            self.assertEqual(target.read_bytes(), before)
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            self.assertEqual(run(*self.chezmoi, "status", "--exclude=encrypted", str(target),
                                 env=self.environment).stdout, "")

    def test_codex_local_values_and_owned_server_replacement(self):
        current = '''model = "host-model"
model_provider = "host-provider"
model_reasoning_effort = "high"
model_context_window = 400000
[model_providers.host-provider]
base_url = "https://route.example.invalid"
[mcp_servers.node_repl]
url = "https://obsolete.example.invalid"
env_vars = ["SYNTHETIC_RUNTIME_FIELD"]
[mcp_servers.node_repl.env]
SYNTHETIC_RUNTIME_FIELD = "keep"
[mcp_servers.host_server]
command = "host-command"
[plugins."obsolete@example"]
enabled = true
[apps.connector_openai_pages]
host_authorization = "keep"
'''
        actual = tomllib.loads(self.apply(".codex/config.toml", current).read_text())
        original = tomllib.loads(current)
        for key in ("model", "model_provider", "model_reasoning_effort", "model_context_window", "model_providers"):
            self.assertEqual(actual[key], original[key])
        node = actual["mcp_servers"]["node_repl"]
        self.assertNotIn("url", node)
        self.assertEqual(node["env"], original["mcp_servers"]["node_repl"]["env"])
        self.assertEqual(node["env_vars"], ["SYNTHETIC_RUNTIME_FIELD"])
        self.assertEqual(actual["mcp_servers"]["host_server"], {"command": "host-command"})
        self.assertNotIn("obsolete@example", actual["plugins"])
        self.assertEqual(actual["apps"]["connector_openai_pages"]["host_authorization"], "keep")

    def test_source_removal_and_explicit_retirement_have_different_effects(self):
        relative = ".codex/config.toml"
        fragment = self.source / ".chezmoitemplates/codex/config.toml"
        original = fragment.read_text()
        fragment.write_text(original.replace("[features]\n", "[features]\nadoption_fixture = true\n"))
        target = self.apply(relative, "model_context_window = 400000\n")
        fragment.write_text(original)
        self.apply(relative)
        actual = tomllib.loads(target.read_text())
        self.assertTrue(actual["features"]["adoption_fixture"])
        self.assertEqual(actual["model_context_window"], 400000)
        # An operator retires the selected local override after its own review.
        target.write_text(target.read_text().replace("model_context_window = 400000\n", ""))
        self.apply(relative)
        self.assertNotIn("model_context_window", tomllib.loads(target.read_text()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
