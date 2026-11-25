#!/usr/bin/env python3
"""Exercise real Agent modifiers against synthetic, isolated destinations."""

import json
from pathlib import Path
import shutil
import subprocess
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
            ".chezmoitemplates/execution-mode",
            ".chezmoitemplates/claude/claude.json",
            ".chezmoitemplates/claude/settings.json",
            ".chezmoitemplates/codex/config.toml",
            ".chezmoitemplates/pi/settings.json",
            ".chezmoitemplates/omp/config.yml",
            ".chezmoitemplates/omp/models.yml",
            "dot_claude/modify_private_settings.json",
            "dot_codex/modify_private_config.toml",
            "private_dot_pi/private_agent/modify_private_settings.json",
            "private_dot_pi/private_agent/private_AGENTS.md.tmpl",
            "private_dot_omp/private_agent/private_AGENTS.md.tmpl",
            "private_dot_omp/private_agent/modify_private_config.yml",
            "private_dot_omp/private_agent/modify_private_models.yml",
            "modify_private_dot_claude.json",
        ):
            target = self.source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / "agent-policy" / name, target)
        shutil.copytree(ROOT / "agent-policy/.chezmoitemplates/agents",
                        self.source / ".chezmoitemplates/agents")
        self.environment = {
            "HOME": str(self.destination), "TMPDIR": str(self.base),
            "PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
        }
        self.chezmoi = [
            "chezmoi", "--config", "/dev/null", "--config-format", "toml",
            "--source", str(self.source), "--destination", str(self.destination),
            "--persistent-state", str(self.base / "state"),
            "--cache", str(self.base / "cache"), "--refresh-externals=never", "--no-tty",
        ]

    def apply(self, relative, contents=None, *, mode=""):
        target = self.destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if contents is not None:
            target.write_text(contents)
        run(*self.chezmoi, "apply", "--exclude=scripts,encrypted", str(target),
            env={**self.environment, "MAC_DOTFILES_EXECUTION_MODE": mode})
        return target

    def test_claude_execution_mode_owns_only_isolation(self):
        relative = ".claude/settings.json"
        shared = {
            "model": "local", "permissions": {"defaultMode": "default"},
            "env": {"ANTHROPIC_BASE_URL": "https://route.invalid"},
            "enabledPlugins": {"only-local": True},
        }
        previous = {**shared, "sandbox": {
            "autoAllowBashIfSandboxed": False, "network": {"allowUnixSockets": []},
            "filesystem": {"disabled": True},
        }}
        target = self.apply(relative, json.dumps(previous), mode="host")
        for mode in ("host", "sandbox", "host"):
            self.apply(relative, mode=mode)
            actual = json.loads(target.read_text())
            sandbox = actual.pop("sandbox")
            self.assertEqual(actual, shared)
            self.assertEqual(sandbox["enabled"], mode == "sandbox")
            self.assertFalse(sandbox["autoAllowBashIfSandboxed"])
            self.assertEqual(sandbox["network"]["allowUnixSockets"], [])
            if mode == "sandbox":
                self.assertFalse(sandbox["filesystem"].get("disabled", False))
                self.assertIn("~/.ssh", sandbox["filesystem"]["denyRead"])
            before = target.read_bytes()
            self.apply(relative, mode=mode)
            self.assertEqual(target.read_bytes(), before)
        self.apply(relative)
        self.assertFalse(json.loads(target.read_text())["sandbox"]["enabled"])
        self.apply(relative, mode="baseline-sandbox")
        self.assertTrue(json.loads(target.read_text())["sandbox"]["enabled"])

    def test_codex_execution_mode_owns_only_isolation(self):
        relative = ".codex/config.toml"
        existing = '''model = "local"
approval_policy = "never"
model_provider = "local"
cli_auth_credentials_store = "file"
sandbox_mode = "workspace-write"
[sandbox_workspace_write]
network_access = false
[permissions.other.filesystem]
":root" = "read"
[plugins."only-local"]
enabled = true
'''
        target = self.apply(relative, existing, mode="sandbox")
        shared = tomllib.loads(existing)
        del shared["sandbox_mode"], shared["sandbox_workspace_write"], shared["permissions"]
        for mode in ("sandbox", "host", "sandbox"):
            self.apply(relative, mode=mode)
            config = tomllib.loads(target.read_text())
            self.assertEqual(config.pop("default_permissions"),
                             ":danger-full-access" if mode == "host" else "development")
            profiles = config.pop("permissions")
            self.assertEqual(profiles["other"], {"filesystem": {":root": "read"}})
            if mode == "sandbox":
                self.assertEqual(profiles["development"]["filesystem"][str(self.destination / ".ssh")], "deny")
            self.assertEqual(config, shared)
            before = target.read_bytes()
            self.apply(relative, mode=mode)
            self.assertEqual(target.read_bytes(), before)
        self.apply(relative, mode="baseline-host")
        self.apply(relative)
        config = tomllib.loads(target.read_text())
        self.assertEqual(config["default_permissions"], ":danger-full-access")
        self.assertEqual(config["tui"]["copy_on_select"], "always")

    def test_invalid_mode_leaves_settings_untouched(self):
        for relative, initial in ((".claude/settings.json", "{}"), (".codex/config.toml", "# empty\n")):
            target = self.destination / relative
            with self.assertRaises(subprocess.CalledProcessError):
                self.apply(relative, initial, mode="hots")
            self.assertEqual(target.read_text(), initial)

    def test_claude_shared_fields_survive(self):
        current = {
            "model": "host-model",
            "modelSettings": {"host-model": {"effort": "high"}},
            "env": {
                "ANTHROPIC_BASE_URL": "https://route.example.invalid",
                "HOST_SETTING": "keep",
                "ANTHROPIC_DEFAULT_HAIKU_MODEL": "host-fast",
                "ANTHROPIC_DEFAULT_OPUS_MODEL": "host-capable",
                "ANTHROPIC_DEFAULT_SONNET_MODEL": "host-balanced",
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
        for alias in ("HAIKU", "OPUS", "SONNET"):
            key = f"ANTHROPIC_DEFAULT_{alias}_MODEL"
            self.assertEqual(actual["env"][key], current["env"][key])
        self.assertNotIn("ANTHROPIC_DEFAULT_FABLE_MODEL", actual["env"])
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

    def test_claude_account_state_stays_private(self):
        current = {
            "hostState": {"preference": "keep"},
            "externalEditorContext": False,
            "mcpServers": {
                "chrome-devtools": {"type": "http", "url": "https://obsolete.example.invalid"},
                "host-server": {"command": "host-command"},
            },
        }
        target = self.destination / ".claude.json"
        target.write_text(json.dumps(current))
        target.chmod(0o600)
        self.apply(".claude.json")
        actual = json.loads(target.read_text())
        self.assertEqual(actual["hostState"], current["hostState"])
        self.assertTrue(actual["externalEditorContext"])
        self.assertEqual(actual["mcpServers"]["host-server"], current["mcpServers"]["host-server"])
        self.assertEqual(actual["mcpServers"]["chrome-devtools"]["type"], "stdio")
        self.assertNotIn("url", actual["mcpServers"]["chrome-devtools"])
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)

        target.write_text(json.dumps(actual, indent=4) + "\n")
        target.chmod(0o644)
        before = target.read_bytes()
        self.apply(".claude.json")
        self.assertEqual(target.read_bytes(), before)
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)

    def test_fresh_configuration_and_idempotence(self):
        account = self.apply(".claude.json")
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
        for target in (account, claude, codex):
            before = target.read_bytes()
            self.apply(str(target.relative_to(self.destination)))
            self.assertEqual(target.read_bytes(), before)
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)
            self.assertEqual(run(*self.chezmoi, "status", "--exclude=encrypted", str(target),
                                 env=self.environment).stdout, "")

    def test_skill_registry_is_exact(self):
        managed = self.source / "dot_agents/exact_skills/managed"
        managed.mkdir(parents=True)
        (managed / "SKILL.md").write_text("managed\n")
        target = self.destination / ".agents/skills"
        (target / "managed").mkdir(parents=True)
        (target / "managed/SKILL.md").write_text("old\n")
        (target / "extra").mkdir()
        (target / "extra/SKILL.md").write_text("extra\n")
        (target / ".git").mkdir()
        (target / ".git/config").write_text("git\n")
        self.apply(".agents/skills")
        self.assertEqual((target / "managed/SKILL.md").read_text(), "managed\n")
        self.assertFalse((target / "extra").exists())
        self.assertFalse((target / ".git").exists())
        self.apply(".agents/skills")
        self.assertEqual(run(*self.chezmoi, "status", "--exclude=encrypted", str(target), env=self.environment).stdout, "")

    def test_install_skills_rebuilds_registry_recursively(self):
        target = self.destination / ".agents/skills"
        (target / "commit/references").mkdir(parents=True)
        (target / "commit/SKILL.md").write_text("old\n")
        (target / "commit/references/extra.md").write_text("extra\n")
        (target / "extra").mkdir()
        (target / "extra/SKILL.md").write_text("extra\n")
        run(str(ROOT / "scripts/install-skills"), env=self.environment)
        source = ROOT / "agent-policy/dot_agents/exact_skills/commit/SKILL.md"
        self.assertEqual((target / "commit/SKILL.md").read_text(), source.read_text())
        self.assertFalse((target / "commit/references").exists())
        self.assertFalse((target / "extra").exists())
        before = (target / "commit/SKILL.md").read_bytes()
        run(str(ROOT / "scripts/install-skills"), env=self.environment)
        self.assertEqual((target / "commit/SKILL.md").read_bytes(), before)

    def test_check_home_detects_nested_skill_drift(self):
        checkout = self.base / "checkout"
        source = checkout / "agent-policy/dot_agents/exact_skills/managed"
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text("managed\n")
        script = checkout / "scripts/check-home"
        script.parent.mkdir()
        shutil.copy2(ROOT / "scripts/check-home", script)
        target = self.destination / ".agents/skills"
        shutil.copytree(source.parent, target)
        command = [str(script), "agent-policy", str(target)]
        self.assertEqual(run(*command, env=self.environment).stdout, "")

        extra = target / "managed/references/unmanaged.md"
        extra.parent.mkdir()
        extra.write_text("keep until reviewed\n")
        result = subprocess.run(command, text=True, capture_output=True, env=self.environment)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("managed/references/unmanaged.md", result.stdout)
        self.assertEqual(extra.read_text(), "keep until reviewed\n")

    def test_install_skills_rejects_unsafe_targets(self):
        outside = self.base / "outside"
        outside.mkdir()
        (outside / "keep.txt").write_text("keep\n")
        home_keep = self.destination / "keep-home.txt"
        home_keep.write_text("keep\n")
        agents = self.destination / ".agents"
        agents.mkdir()
        (agents / "keep.txt").write_text("keep\n")
        cases = (
            ("home root", str(self.destination) + "/"),
            ("direct outside", str(outside)),
            ("dot-dot outside", str(self.destination / ".." / "outside")),
            ("agents directory", str(agents)),
        )
        for label, target in cases:
            with self.subTest(label=label):
                result = subprocess.run(
                    [str(ROOT / "scripts/install-skills"), target],
                    text=True,
                    capture_output=True,
                    env=self.environment,
                )
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertTrue(home_keep.exists(), label)
                self.assertTrue((outside / "keep.txt").exists(), label)
                self.assertTrue((agents / "keep.txt").exists(), label)

        (agents / "skills").symlink_to(outside)
        result = subprocess.run(
            [str(ROOT / "scripts/install-skills")],
            text=True,
            capture_output=True,
            env=self.environment,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertTrue((outside / "keep.txt").exists())

        shutil.rmtree(agents)
        agents.symlink_to(outside)
        result = subprocess.run(
            [str(ROOT / "scripts/install-skills")],
            text=True,
            capture_output=True,
            env=self.environment,
        )
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertTrue((outside / "keep.txt").exists())

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

    def test_pi_host_model_choices_survive(self):
        current = {
            "defaultProvider": "host-provider",
            "defaultModel": "host-model",
            "defaultThinkingLevel": "xhigh",
            "enabledModels": ["host-provider/*"],
            "modelThinkingLevels": {"host-provider/host-model": "xhigh"},
        }
        actual = json.loads(self.apply(".pi/agent/settings.json", json.dumps(current)).read_text())
        for key, value in current.items():
            self.assertEqual(actual[key], value)
        self.assertEqual(actual["defaultTools"], ["+codemode"])

    def test_pi_execution_mode_preserves_host_settings(self):
        relative = ".pi/agent/settings.json"
        settings = {"defaultProvider": "local", "defaultTools": ["read"], "shellCommandPrefix": "set -u"}
        target = self.apply(relative, json.dumps(settings), mode="sandbox")
        helper = "~/.pi/agent/bin/sandbox-bash"
        for mode in ("sandbox", "host", "sandbox"):
            self.apply(relative, mode=mode)
            expected = settings | ({"shellPath": helper} if mode == "sandbox" else {})
            self.assertEqual(json.loads(target.read_text()), expected)
            before = target.read_bytes()
            self.apply(relative, mode=mode)
            self.assertEqual(target.read_bytes(), before)
        self.apply(relative)
        self.assertEqual(json.loads(target.read_text())["shellPath"], helper)
        self.apply(relative, mode="baseline-host")
        actual = json.loads(target.read_text())
        self.assertNotIn("shellPath", actual)
        self.assertEqual(actual["defaultTools"], ["+codemode"])

    def test_pi_custom_shell_conflict_preserves_original(self):
        relative = ".pi/agent/settings.json"
        original = '{ "shellPath": "/custom/bash" }\n'
        target = self.apply(relative, original, mode="host")
        with self.assertRaises(subprocess.CalledProcessError):
            self.apply(relative, mode="sandbox")
        self.assertEqual(target.read_text(), original)

    def read_yaml(self, target):
        return json.loads(run(
            "ruby", "-ryaml", "-rjson", "-e",
            "puts JSON.generate(YAML.load_file(ARGV.fetch(0)))", str(target),
        ).stdout)

    def test_omp_fresh_home_routes_and_shared_instructions(self):
        run(*self.chezmoi, "apply", "--exclude=scripts,encrypted",
            str(self.destination / ".omp"), env=self.environment)
        config = self.read_yaml(self.apply(".omp/agent/config.yml"))
        models = self.read_yaml(self.apply(".omp/agent/models.yml"))
        provider = models["providers"]["magpie"]
        self.assertEqual(provider["baseUrl"], "http://127.0.0.1:3425/v1")
        self.assertEqual(provider["auth"], "none")
        self.assertEqual(provider["headers"], {"User-Agent": "omp"})
        available = {"magpie/" + model["id"]: model for model in provider["models"]}
        astra_roles = {"slow", "plan", "advisor", "review"}
        for role, selector in config["modelRoles"].items():
            model, effort = selector.rsplit(":", 1)
            expected = "gpt-6.2-astra" if role in astra_roles else "gpt-6.2-sol"
            self.assertEqual(model, f"magpie/codex/{expected}", role)
            self.assertIn(model, available, role)
            self.assertIn(effort, available[model]["thinking"]["efforts"], role)
        for agent, alias in config["task"]["agentModelOverrides"].items():
            selector = config["modelRoles"][alias.removeprefix("@")]
            expected = "gpt-6.2-astra" if agent in {"reviewer", "security-reviewer"} else "gpt-6.2-sol"
            self.assertEqual(selector.split(":")[0], f"magpie/codex/{expected}", agent)
        instructions = self.apply(".omp/agent/AGENTS.md")
        shared = self.apply(".pi/agent/AGENTS.md")
        self.assertEqual(instructions.read_bytes(), shared.read_bytes())
        self.assertNotIn(str(Path.home()), instructions.read_text())
        self.assertNotIn(str(ROOT), instructions.read_text())
        self.assertEqual(instructions.stat().st_mode & 0o777, 0o600)
        self.assertEqual(instructions.parent.stat().st_mode & 0o777, 0o700)

    def test_omp_host_settings_and_other_providers_survive(self):
        config = self.apply(".omp/agent/config.yml", """# Host preferences.
theme: {dark: titanium}
modelRoles: {custom: local/private-model, default: old/model}
task: {maxConcurrency: 3, agentModelOverrides: {custom: local/worker}}
dev: {autoqaConsent: granted}
tier: {openai: priority}
""")
        models = self.apply(".omp/agent/models.yml", """providers:
  other: {baseUrl: 'http://localhost:9000/v1', auth: none}
  magpie:
    baseUrl: http://localhost:7777/v1
    auth: oauth
    headers: {User-Agent: old-client, user-agent: host-client, X-Host: retained}
    models: [{id: retired-model}]
""")
        actual = self.read_yaml(config)
        self.assertEqual(actual["theme"], {"dark": "titanium"})
        self.assertEqual(actual["modelRoles"]["custom"], "local/private-model")
        self.assertEqual(actual["task"]["maxConcurrency"], 3)
        self.assertEqual(actual["task"]["agentModelOverrides"]["custom"], "local/worker")
        self.assertEqual(actual["dev"], {"autoqaConsent": "granted"})
        self.assertEqual(actual["tier"], {"openai": "priority"})
        providers = self.read_yaml(models)["providers"]
        self.assertEqual(providers["other"], {"baseUrl": "http://localhost:9000/v1", "auth": "none"})
        self.assertEqual(providers["magpie"]["baseUrl"], "http://localhost:7777/v1")
        self.assertEqual(providers["magpie"]["auth"], "oauth")
        self.assertEqual(providers["magpie"]["headers"], {"User-Agent": "omp", "X-Host": "retained"})
        self.assertEqual({model["id"] for model in providers["magpie"]["models"]},
                         {"codex/gpt-6.2-sol", "codex/gpt-6.2-astra"})
        for target in (config, models):
            before = "# Retain formatting on a semantic no-op.\n" + target.read_text()
            target.write_text(before)
            self.apply(str(target.relative_to(self.destination)))
            self.assertEqual(target.read_text(), before)
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)

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
