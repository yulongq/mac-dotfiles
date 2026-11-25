# Environment setup

Configure an Apple Silicon Mac using the installation owners in [ownership.md](ownership.md). Application credentials, account state, and private environment files stay local; package installation and configuration application are separate operations.

## Install tools

1. Install Homebrew under `/opt/homebrew`, chezmoi 2.73.1 or newer, and Python 3.11+ for selected deployment and validation.
2. Review `packages/Brewfile`, then run `brew bundle --no-upgrade --file packages/Brewfile` from the checkout root. The declaration selects required packages; it is not a cleanup list for the whole machine.
3. Install the asdf plugins and versions needed by the selected projects. Set up the JVM, Maven, and Go distributions at the paths selected by `home/dot_pathrc`, verifying vendor checksums. Retain rustup ownership of Rust toolchains.
4. Install the CLI and editor dependencies declared in `packages/` with their owning runtimes. Keep Codex ACP in the selected asdf Node installation and regenerate its shims; do not create a competing global copy.
5. Install vendor-managed desktop applications through their selected owners. Install `JetBrainsMapleMono-NF-XX-XX-XX.zip` from the [official JetBrains Maple Mono stable release](https://github.com/SpaceTimee/Fusion-JetBrainsMapleMono/releases/latest), verify its published SHA-256, and install its TTF files through Font Book for All Users (`/Library/Fonts`). Select the internal family `JetBrains Maple Mono` in application-owned font settings, including Herdr, VS Code, and Zed. Set up application sync or exports for VS Code, Zed, Karabiner, Raycast, input methods, and other application-owned preferences.

Before running `scripts/validate`, make sure `asdf which nvim` resolves the declared Neovim version, and that Ruby, Codex, Herdr, Oracle, and Rex are on `PATH`. Use the [installation owners](ownership.md) for Codex, [Herdr](https://github.com/herdrdev/herdr), Oracle (`packages/npm.txt`), and the Rex CLI bundled with the Rex app. The Brewfile supplies `ctx7`, `gh`, `glab`, and `sessidx`. The skill checks run local CLI contract probes; the shell checks also need network access to GitHub for the pinned archives.

## Apply configuration

For a selected rebuild, start with `scripts/deploy list` at the checkout root. Run `scripts/deploy diff .gitconfig` for one file or `scripts/deploy diff pi pi=sandbox codex codex=host` for two independently configured tools. Review the expanded target list, prerequisites, and changes. Once the destination is ready, repeat the same selectors with `apply`, then run `diff` again. A repeat diff should report the same scope and no pending changes. Use `--dest` with an absolute disposable home path to rehearse the deployment. Install each selected runtime through its declared owner.

The inventory and prerequisite notes go to standard error. File diffs go to standard output. For shared settings, the preview lists added or replaced fields with their desired values and names fields being removed. Coordinate destination writers and use only non-secret files with this command. Claude Code account state, Codex Desktop state, and the exact skill registry have separate [deployment and recovery procedures](lifecycle.md).

1. On an existing machine, identify regular files, symlinks, and unmanaged children in each selected configuration directory. Preserve uncommitted configuration changes and a recovery copy for each non-secret target being replaced. Do not copy credential stores or private environment files through repository scripts.
2. Run `scripts/validate` and enable the local pre-push check with `git config --local core.hooksPath .githooks` after accounting for existing hooks. Select this checkout as the default source and use the scoped preview and apply commands in [lifecycle.md](lifecycle.md) for each configuration group, including `~/Brewfile` and any local shell or Git overrides. Replacing a directory symlink requires accounting for all its contents.
3. Apply `.zprofile`, `.zshrc`, `.pathrc`, and `.config/zsh` together, then the abbreviation target, Starship, Git preferences, and helper commands. The login profile preserves existing host initialization while adding the shared environment and PATH sources. Include the plugin directories declared in `home/.chezmoiexternal.toml`; selecting `.zshrc` alone does not restore the pinned archives.
4. Apply Neovim, Ghostty, kitty, tmux, and LazyGit configuration. Review Neovim plugin build steps; use TPM's install action for the plugins declared by `tmux.conf`. Register the managed script directory in Raycast.
5. Select [each agent's execution mode](../agent-policy/README.md#execution-modes) for the host. Check provider routes, model selections, socket access, the exact skill registry, and runtime-owned state. Back up `~/.agents/skills` before the first rebuild, then run `scripts/install-skills`; it reconstructs the registry recursively from `agent-policy/dot_agents/exact_skills`. Review permission changes separately. Agent deployment uses its own source.
6. Repeat application and inspect scoped status/diff output. Distinguish application write-backs from unexplained source drift.

## Set up Rex

Install and open Rex through its vendor installer, then install JetBrains Maple Mono through Font Book as described above. Apply `~/.config/rex` and `~/.local/bin/setup-rex` from this checkout using the scoped lifecycle procedure. The Lua configuration binds Command-N to a session, Command-Shift-N to an app window, Command-Z to terminal undo, and Command-W to confirmation when a program is still running.

Enable Remote Control in Rex Settings under Rex Server, keep exactly one local Rex app connected, and run `setup-rex` in a fresh shell. It downloads and verifies the pinned Snazzy Soft theme, checks Lua configuration, imports the theme, writes the selected appearance and terminal preferences, and reloads Lua. It selects JetBrains Maple Mono at 14 pt. Reopen the Rex app when convenient to load launch-time preferences, leaving Rex Server running so its sessions survive. The command does not install Rex, rexume, or Agent integrations; shared skills remain under this repository's Agent configuration workflow.

Run `rex config check` and `rex keymap` to check Lua loading and the running server's bindings. Verify font rendering, theme colors, and the close confirmation in Rex after reopening the app.

## Verify the environment

- Open fresh interactive login shells, non-interactive login shells, and Agent/editor child processes. Confirm `c` expands to Codex in interactive shells, completion and history bindings work, and the selected JVM, Maven, Go, and Node executables win PATH resolution.
- Check Neovim plugin builds, language servers, Copilot Chat, Codex ACP, terminal font rendering, clipboard integration, splits, navigation, and shortcuts.
- Run representative Java, Node, Python, Go, and Rust projects for the languages used on the machine. The isolated tests use synthetic executables and do not establish project compatibility.
- Verify Git identity and authorized authentication/signing through the existing credential source. Check global instruction and skill loading in fresh sessions of every configured Agent runtime.
- Run `scripts/check-skill-versions` after CLI upgrades. It compares the managed `glab`, Herdr, Oracle, and `sessidx` skills' recorded release tags with the executables resolved on PATH, covering their different installation owners. Differences require a release comparison, not an automatic update; unavailable or failed version queries fail the check. `scripts/validate` also runs it.
- Record application-specific permissions and portable settings in their owning documentation without storing account data. Keep each application's update owner explicit.
