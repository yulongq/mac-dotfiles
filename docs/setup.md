# Environment setup

Configure an Apple Silicon Mac using the installation owners in [ownership.md](ownership.md). Application credentials, account state, and private environment files stay local; package installation and configuration application are separate operations.

## Install tools

1. Install Homebrew under `/opt/homebrew`, chezmoi 2.73.1 or newer, and Python 3.11+ for validation.
2. Review `packages/Brewfile`, then run `brew bundle --no-upgrade --file packages/Brewfile` from the checkout root. The declaration selects required packages; it is not a cleanup list for the whole machine.
3. Install the asdf plugins and versions needed by the selected projects. Set up the JVM, Maven, and Go distributions at the paths selected by `home/dot_pathrc`, verifying vendor checksums. Retain rustup ownership of Rust toolchains.
4. Install the CLI and editor dependencies declared in `packages/` with their owning runtimes. Keep Codex ACP in the selected asdf Node installation and regenerate its shims; do not create a competing global copy.
5. Install vendor-managed desktop applications and Maple Mono Normal NF CN through their selected owners. Set up application sync or exports for VS Code, Zed, Karabiner, Raycast, input methods, and other application-owned preferences.

## Apply configuration

1. On an existing machine, identify regular files, symlinks, and unmanaged children in each selected configuration directory. Preserve uncommitted configuration changes and a recovery copy for each non-secret target being replaced. Do not copy credential stores or private environment files through repository scripts.
2. Run `python3 -m unittest discover -s tests -v`. Use the scoped preview and apply commands in [lifecycle.md](lifecycle.md) for each configuration group, including `~/Brewfile` and any local shell or Git overrides. Replacing a directory symlink requires accounting for all its contents.
3. Apply the Zsh configuration, abbreviation target, `.pathrc`, Starship, Git preferences, and helper commands. Include the plugin directories declared in `home/.chezmoiexternal.toml`; selecting `.zshrc` alone does not restore the pinned archives.
4. Apply Neovim, Ghostty, kitty, tmux, and LazyGit configuration. Review Neovim plugin build steps; use TPM's install action for the plugins declared by `tmux.conf`. Register the managed script directory in Raycast.
5. Configure Agent sources for the host using [their runtime requirements](../agent-policy/README.md). Check provider routes, model selections, socket access, installed skills, and runtime-owned state. Permission changes require explicit approval, and the default home apply does not activate Agent policy.
6. Repeat application and inspect scoped status/diff output. Distinguish application write-backs from unexplained source drift.

## Verify the environment

- Open fresh interactive login shells and Agent/editor child processes. Confirm `c` expands to Codex, completion and history bindings work, and the selected JVM, Maven, Go, and Node executables win PATH resolution.
- Check Neovim plugin builds, language servers, Copilot Chat, Codex ACP, terminal font rendering, clipboard integration, splits, navigation, and shortcuts.
- Run representative Java, Node, Python, Go, and Rust projects for the languages used on the machine. The isolated tests use synthetic executables and do not establish project compatibility.
- Verify Git identity and authorized authentication/signing through the existing credential source. Check global instruction and skill loading in fresh sessions of every configured Agent runtime.
- Record application-specific permissions and portable settings in their owning documentation without storing account data. Keep each application's update owner explicit.
