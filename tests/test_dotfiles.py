#!/usr/bin/env python3
"""Render and exercise dotfiles using temporary homes, without installing tools."""

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
ABBREVIATIONS = ".config/zsh-abbr/abbreviations.zsh"


def run(*args, **kwargs):
    try:
        return subprocess.run(args, check=True, text=True, capture_output=True, timeout=60, **kwargs)
    except subprocess.CalledProcessError as error:
        error.add_note(error.stderr)
        raise


class DotfilesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = tempfile.TemporaryDirectory(prefix="mac-dotfiles-validation-")
        cls.addClassCleanup(cls.workspace.cleanup)
        cls.base = Path(cls.workspace.name)
        cls.destination = cls.base / "home"
        cls.destination.mkdir()
        cls.chezmoi = [
            "chezmoi", "--config", "/dev/null", "--config-format", "toml",
            "--source", str(ROOT), "--destination", str(cls.destination),
            "--persistent-state", str(cls.base / "state"),
            "--cache", str(cls.base / "cache"),
            "--refresh-externals=never", "--no-tty",
        ]
        run(*cls.chezmoi, "apply", "--exclude=scripts,encrypted")

    def expansions(self, destination, names):
        # abbr expand interprets escapes when printing; inspect loaded values verbatim.
        result = run(
            "/bin/zsh", "-fc",
            "source /opt/homebrew/share/zsh-abbr/zsh-abbr.zsh || exit; "
            "abbr list >/dev/null || exit; "
            "for name in \"$@\"; do key=${(qqq)name}; "
            "value=${ABBR_REGULAR_USER_ABBREVIATIONS[$key]}; "
            "print -rn -- \"${(Q)value}\"$'\\0'; done",
            "zsh", *names,
            env={
                "HOME": str(destination), "ZDOTDIR": str(destination),
                "PATH": "/opt/homebrew/bin:/usr/bin:/bin",
                "ABBR_USER_ABBREVIATIONS_FILE": str(destination / ABBREVIATIONS),
                "TMPDIR": str(self.base), "TERM": "dumb",
            },
            cwd=destination,
        )
        return result.stdout.split("\0")[:-1]

    def test_abbreviations_match_yaml(self):
        categories = json.loads(run(*self.chezmoi, "execute-template", "{{ .abbreviations | toJson }}").stdout)
        expected = {}
        for entries in categories.values():
            for name, entry in entries.items():
                self.assertNotIn(name, expected, f"Duplicate abbreviation: {name}")
                expected[name] = entry["command"]
        self.assertEqual(self.expansions(self.destination, list(expected)), list(expected.values()))

    def test_abbreviation_literal_rendering(self):
        command = 'printf \'%s\\n\' "$HOME" "$(touch "$HOME/SHOULD_NOT_EXIST")" *.md'
        overrides = json.dumps({"abbreviations": {"literal_test": {"literal-test": {"command": command}}}})
        rendered = run(*self.chezmoi, "--override-data", overrides, "cat", str(self.destination / ABBREVIATIONS)).stdout
        with tempfile.TemporaryDirectory(dir=self.base, prefix="literal-") as directory:
            destination = Path(directory)
            target = destination / ABBREVIATIONS
            target.parent.mkdir(parents=True)
            target.write_text(rendered)
            self.assertEqual(self.expansions(destination, ["literal-test"]), [command])
            self.assertFalse((destination / "SHOULD_NOT_EXIST").exists())

    def test_configuration_lifecycle(self):
        with tempfile.TemporaryDirectory(dir=self.base, prefix="lifecycle-") as directory:
            base = Path(directory)
            checkout = base / "checkout"
            shutil.copytree(ROOT / "home", checkout / "home")
            shutil.copy2(ROOT / ".chezmoiroot", checkout)
            (checkout / "packages").mkdir()
            shutil.copy2(ROOT / "packages/Brewfile", checkout / "packages/Brewfile")
            destination = base / "home"
            target = destination / ".config/lifecycle/config"
            target.parent.mkdir(parents=True)
            target.write_text("version = 1\n")
            sibling = target.with_name("unmanaged")
            sibling.write_text("keep\n")
            chezmoi = [
                *self.chezmoi, "--source", str(checkout), "--destination", str(destination),
                "--persistent-state", str(base / "state"),
            ]
            run(*chezmoi, "add", str(target))
            source = Path(run(*chezmoi, "source-path", str(target)).stdout.strip())
            self.assertEqual(source.read_text(), target.read_text())
            source.write_text("version = 2\n")
            self.assertIn("+version = 2", run(*chezmoi, "diff", "--exclude=encrypted", str(target)).stdout)
            run(*chezmoi, "apply", str(target))
            self.assertEqual(target.read_text(), "version = 2\n")
            self.assertEqual(run(*chezmoi, "status", "--exclude=encrypted", str(target)).stdout, "")
            run(*chezmoi, "--force", "forget", str(target))
            self.assertFalse(source.exists())
            self.assertEqual(target.read_text(), "version = 2\n")
            run(*chezmoi, "add", str(target))
            run(*chezmoi, "--force", "destroy", str(target))
            self.assertFalse(source.exists())
            self.assertFalse(target.exists())
            run(*chezmoi, "apply", "--exclude=externals,scripts,encrypted")
            self.assertFalse(target.exists())
            self.assertEqual(sibling.read_text(), "keep\n")
            self.assertEqual((destination / "Brewfile").resolve(), (checkout / "packages/Brewfile").resolve())
            loaded = run("/bin/zsh", "-fc", 'source "$1"; print -r -- "$DOTFILES"',
                         "zsh", str(destination / ".config/zsh/source.zsh"),
                         env={"HOME": str(destination), "PATH": "/usr/bin:/bin"})
            self.assertEqual(Path(loaded.stdout.strip()).resolve(), checkout.resolve())

    def test_reload_abbreviations_applies_changes_and_preserves_target_on_error(self):
        with tempfile.TemporaryDirectory(dir=self.base, prefix="reload-") as directory:
            base = Path(directory)
            checkout = base / "checkout"
            template = checkout / "home/dot_config/zsh-abbr/abbreviations.zsh.tmpl"
            template.parent.mkdir(parents=True)
            shutil.copy2(ROOT / "home/dot_config/zsh-abbr/abbreviations.zsh.tmpl", template)
            shutil.copy2(ROOT / ".chezmoiroot", checkout)
            data = checkout / "home/.chezmoidata/abbreviations.yaml"
            data.parent.mkdir()
            data.write_text(json.dumps({"abbreviations": {"test": {
                "removed-entry": {"command": "printf removed"},
                "edited-entry": {"command": "printf before"},
            }}}))
            destination = base / "home"
            (destination / ABBREVIATIONS).parent.mkdir(parents=True)
            environment = {
                "HOME": str(destination), "ZDOTDIR": str(destination),
                "DOTFILES": str(checkout), "TMPDIR": str(base),
                "PATH": "/opt/homebrew/bin:/usr/bin:/bin",
            }
            command = ["/bin/zsh", "-fc", 'source "$1"; reload-abbr',
                       "zsh", str(ROOT / "home/dot_config/zsh/functions.zsh")]
            run(*command, env=environment, cwd=destination)
            self.assertEqual(self.expansions(destination, ["removed-entry", "edited-entry"]),
                             ["printf removed", "printf before"])
            data.write_text(json.dumps({"abbreviations": {"test": {
                "added-entry": {"command": "printf added"},
                "edited-entry": {"command": "printf after"},
            }}}))
            run(*command, env=environment, cwd=destination)
            self.assertEqual(self.expansions(destination, ["removed-entry", "edited-entry", "added-entry"]),
                             ["", "printf after", "printf added"])
            target = destination / ABBREVIATIONS
            previous = target.read_bytes()
            data.write_text("abbreviations: [\n")
            with self.assertRaises(subprocess.CalledProcessError):
                run(*command, env=environment, cwd=destination)
            self.assertEqual(target.read_bytes(), previous)

    def test_render_and_reapply(self):
        expected = [
            ".zshrc", ".pathrc", ".gitconfig", ".tool-versions",
            ".config/ghostty/config.ghostty", ".config/kitty/kitty.conf",
            ".config/nvim/init.lua", ".config/nvim/lazy-lock.json",
            ".config/tmux/tmux.conf", ".config/starship.toml",
            ".config/raycast/scripts/copy-markdown-url-and-title.js",
            ".local/bin/git-check-uncommitted", ".local/bin/markdown-validate",
        ]
        for name in expected:
            self.assertTrue((self.destination / name).is_file(), name)
        self.assertFalse((self.destination / ".codex").exists())
        self.assertFalse((self.destination / "AGENTS.md").exists())
        self.assertFalse((self.destination / ".chezmoidata").exists())
        self.assertEqual((self.destination / "Brewfile").resolve(), ROOT / "packages/Brewfile")
        self.assertEqual((self.destination / ".config/homebrew").stat().st_mode & 0o777, 0o700)
        self.assertIn(str(ROOT), (self.destination / ".config/zsh/source.zsh").read_text())
        run(*self.chezmoi, "apply", "--exclude=externals,scripts,encrypted")
        result = run(*self.chezmoi, "diff", "--recursive", "--exclude=externals,scripts,encrypted")
        self.assertEqual(result.stdout, "")

    def test_syntax_and_structured_configs(self):
        for source in (self.destination / ".config/zsh").glob("*.zsh"):
            run("zsh", "-n", str(source))
        run("zsh", "-n", str(self.destination / ".zshrc"))
        run("zsh", "-n", str(self.destination / ".pathrc"))
        for source in (self.destination / ".config/nvim").glob("*.json"):
            json.loads(source.read_text())
        run("zsh", "-n", str(self.destination / ".config/zsh-abbr/abbreviations.zsh"))
        run("git", "config", "--file", str(self.destination / ".gitconfig"), "--get", "core.editor")

    def test_shell_contract_with_pinned_plugins(self):
        for name in ("node", "npm", "nvim"):
            executable = self.destination / ".asdf/shims" / name
            executable.parent.mkdir(parents=True, exist_ok=True)
            executable.write_text("#!/bin/sh\nexit 0\n")
            executable.chmod(0o755)
        for name in ("dep/graalvm-jdk-25.0.4.1+1.1/Contents/Home/bin/java", "dep/apache-maven-3.9.16/bin/mvn", "dep/golang/bin/go"):
            executable = self.destination / name
            executable.parent.mkdir(parents=True, exist_ok=True)
            executable.write_text("#!/bin/sh\nexit 0\n")
            executable.chmod(0o755)
        environment = {
            "HOME": str(self.destination), "ZDOTDIR": str(self.destination),
            "PATH": "/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
            "TERM": "xterm-256color", "TERM_PROGRAM": "Apple_Terminal",
            "LANG": "en_US.UTF-8", "TMPDIR": str(self.base),
        }
        result = run("/bin/zsh", "-lic", "command -v node java mvn go; abbr list | /usr/bin/grep -F '\"c\"='; print -r -- $SSH_AUTH_SOCK; whence -w gcom reload-abbr; bindkey '^[[A'; alias la tree", env=environment, cwd=self.destination)
        self.assertNotIn("no such file", result.stderr.lower())
        self.assertNotIn("command not found", result.stderr.lower())
        self.assertIn(str(self.destination / ".asdf/shims/node"), result.stdout)
        self.assertIn(str(self.destination / "dep/graalvm-jdk-25.0.4.1+1.1/Contents/Home/bin/java"), result.stdout)
        self.assertIn(str(self.destination / "dep/apache-maven-3.9.16/bin/mvn"), result.stdout)
        self.assertIn(str(self.destination / "dep/golang/bin/go"), result.stdout)
        self.assertIn('"c"="codex"', result.stdout)
        self.assertIn("2BUA8C4S2C.com.1password/t/agent.sock", result.stdout)
        self.assertIn("gcom: function", result.stdout)
        self.assertIn("history-substring-search-up", result.stdout)
        self.assertIn("ll --tree --level=2", result.stdout)

    def test_herdr_sidebar_preserves_host_settings(self):
        target = self.destination / ".config/herdr/config.toml"
        original = '''onboarding = false
[theme]
name = "host-theme"
[ui]
copy_on_select = false
[ui.sidebar.agents]
row_gap = 2
[ui.sidebar.agents.rows_by_agent]
codex = [["agent"]]
[worktrees]
directory = "~/host-worktrees"
'''
        target.write_text(original)
        run(*self.chezmoi, "apply", str(target))
        expected = tomllib.loads(original)
        expected["ui"]["sidebar"]["agents"]["rows"] = [
            ["state_icon", "workspace", "agent", "pane"], ["terminal_title_stripped"],
        ]
        self.assertEqual(tomllib.loads(target.read_text()), expected)
        before = target.read_bytes()
        run(*self.chezmoi, "apply", str(target))
        self.assertEqual(target.read_bytes(), before)

    def test_declared_shell_dependencies(self):
        brewfile = (ROOT / "packages/Brewfile").read_text()
        for name in ("fzf", "zoxide", "starship", "eza", "asdf", "universal-ctags"):
            self.assertIn(f'brew "{name}"', brewfile)
        self.assertIn('brew "olets/tap/zsh-abbr"', brewfile)
        self.assertIn(".config/tmux/plugins/tpm", tomllib.loads((ROOT / "home/.chezmoiexternal.toml").read_text()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
