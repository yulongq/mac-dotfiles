# Configuration and installation ownership

The repository owns durable configuration and the instructions needed to reconstruct the environment. Package managers and application updaters still own their installations. A configuration apply does not install software or change another owner's update channel.

| Surface | Owner and source | Installation and configuration contract |
| --- | --- | --- |
| Zsh | `home/modify_dot_zprofile`, `home/dot_zshrc`, `home/dot_config/zsh`, and pinned archives in `home/.chezmoiexternal.toml` | The login profile modifier owns only the source lines for `environment.zsh` and `.pathrc`, preserving other host initialization. Shared environment setup runs before interactive completion; non-login interactive shells load it themselves. Homebrew supplies fzf, zoxide, Starship, eza, zsh-abbr, and Universal Ctags for `ct`. `.zshrc.local` remains an optional local override. |
| Abbreviations | `home/.chezmoidata/abbreviations.yaml` and `home/dot_config/zsh-abbr/abbreviations.zsh.tmpl` | chezmoi generates the installed Zsh file during apply; edit the YAML instead of the generated target. |
| Private shell input | Existing local environment file | Consumed through the existing shell entrypoint; never imported, inspected, generated, or backed up by repository scripts. |
| PATH additions | `home/dot_pathrc` | Login and interactive shells use the same ordered paths and runtime exports. Interactive shells reapply them after private input and local overrides. Array assignment removes duplicates while retaining the selected asdf, npm-global, and `~/dep` owners; Java, Maven, and Go must exist before their commands can run. |
| Node, Python, Ruby, Lua, Neovim | asdf, with `home/dot_tool-versions` and `home/dot_asdfrc` | Install the corresponding asdf plugins and the versions required by actual projects. Python 2.7.18 remains declared; verify its project consumers before installing or retiring it. |
| Java/GraalVM | Vendor archive under `~/dep/graalvm-jdk-25.0.4.1+1.1/Contents/Home` | Restore the same selected distribution and verify the vendor checksum before extraction; `JAVA_HOME` selects it. |
| Maven | Apache archive under `~/dep/apache-maven-3.9.16` | Restore the vendor archive and checksum; `MAVEN_HOME` selects it. Prefer project wrappers where the project owns Maven's version. |
| Go | Vendor archive under `~/dep/golang` | Install the selected Go toolchain in this directory. Keep one active runtime owner. |
| Rust | Existing rustup installation | Retain toolchains and components; no background `rustup update` is installed. |
| npm CLIs | Existing `~/.npm-global` prefix, requirements in `packages/npm.txt` | Review versions and normal credential source before explicit installation. Codex is excluded because its active installation is standalone. |
| Codex ACP | Existing Node/asdf global installation, `packages/asdf-node-npm.txt` | Restore under the selected asdf Node installation and regenerate its shims; Avante currently invokes `codex-acp`. Do not also install a competing copy under another prefix. |
| Ruby editor tools | Ruby/asdf gems in `packages/ruby-gems.txt` | Install with the selected Ruby and regenerate asdf shims; Neovim commands target those shims. |
| Python CLIs | uv tools, requirements in `packages/uv.txt` | Preserve uv's installation owner and selected Python versions. |
| Codex / Claude / Grok | Their current vendor installations | Retain the working launchers; no Homebrew replacement or account login is performed. |
| Pi / Oracle / DSH | Current npm-global installations | Listed as package requirements; their installed data and provider routes remain application-owned. The selected Pi session ID footer is managed under `agent-policy/`; other extensions retain their current owners. |
| Herdr | Local executable and `home/dot_config/herdr/modify_config.toml` | Source manages only Agent sidebar rows, showing pane identity and terminal title. Shortcuts, integrations, themes, and worktree locations remain application-owned. |
| Kimi, browser automation, other external skills | Existing vendor installers | Retain installation ownership and browser/daemon registration. The shared registry is exact, so a vendor skill that should appear there must be added to `agent-policy/dot_agents/exact_skills`; installation alone does not retain it. |
| Neovim | `home/dot_config/nvim` with `lazy-lock.json` | Lazy installs plugins; review their normal build steps. Avante keeps Codex ACP and `<leader>av`; Copilot Chat retains its existing keys. |
| Ghostty and kitty | `home/dot_config/ghostty`, `home/dot_config/kitty` | Homebrew supplies Ioskeley Mono Term Nerd Font for Ghostty through `font-ioskeley-mono-term-nerd-font` in `packages/Brewfile`; Ghostty selects the `IoskeleyMonoTerm Nerd Font Mono` family. Restore kitty's Maple Mono Normal NF CN through its existing font installation owner. Verify font loading and rendering in each terminal; terminal application update channels remain unchanged. |
| tmux | `home/dot_config/tmux` and pinned TPM archive | After restoring TPM, use its install action for the plugins already declared by `tmux.conf`; verify navigation and clipboard behavior. |
| Git | `home/dot_gitconfig`, helpers, ignore, and message template | `~/.gitconfig.local` owns local identity and overrides. Authentication transport and signing identity require explicit host configuration. |
| Agent instructions, settings, and hooks | Independently configured sources under `agent-policy/` | Configure host settings before activation. Preserve selected API routes, authentication stores, models, and 1Password socket allowances. |
| Claude Code output scanning | `agent-policy/dot_claude/hooks/executable_post-bash-scan-secrets.sh` and its adjacent TOML rules | Homebrew supplies Gitleaks through `packages/Brewfile`. The post-tool hook scans successful and failed Bash output locally, reports only rule identifiers, and fails when scanning is unavailable. It warns after output exists; it does not prevent the original exposure. |
| Shared skill registry | `agent-policy/dot_agents/exact_skills` and `scripts/install-skills` | `scripts/install-skills` rebuilds `~/.agents/skills` recursively with `rsync -a --delete`; it resolves `HOME` and the target through symlinks and `..`, and refuses anything that does not resolve exactly to `$HOME/.agents/skills`. A selected-target chezmoi apply can leave nested extras. Back up the target before the first rebuild; add a skill to source to retain it; do not edit or commit in the live registry. |
| Raycast | Deployed script in `home/dot_config/raycast/scripts` | Preserve the existing Script Commands directory registration. Account state and extension settings stay with Raycast. |
| VS Code, Zed, Karabiner | Application sync, export, or local settings | Record the chosen sync/export owner for machine setup; do not copy mixed app databases or account state. |
| Desktop apps outside Homebrew | Vendor, App Store, or application-sync owners | These include 1Password, Chrome, ChatGPT, Ghostty, kitty, DeepSeek Harness, Typeless, OrbStack, Fork, Telegram, Discord, WeChat, Spotify, Shottr, CC Switch, tldraw offline, Surge, Raycast, VS Code, Obsidian, TradingView, Longbridge, Rectangle, and BetterDisplay. Retain their selected installation and update owners. |
| Homebrew updates | `packages/Brewfile`, explicit operator action, and self-updating apps | `~/Brewfile` links to the package declaration. No unattended upgrade job. With XDG enabled, the cask update policy is deployed at `~/.config/homebrew/brew.env`; its parent directory is private (`0700`), while Homebrew owns its other files. Unlisted installed packages remain outside cleanup authority. |

Machine setup combines managed configuration with runtime archives, application sync or exports, and host-specific Agent settings. Complete the project and GUI checks in [environment setup](setup.md) to verify the environment beyond configuration rendering.

## Upstream baseline

The initial capability baseline reviewed `liby/dotfiles` at `75ab909` and `joshukraine/dotfiles` at `cf24722` for the surfaces in this table; history before those revisions was not inspected. `liby` supplies the current shell, Agent, and selected app structure; its `.chezmoiscripts` installers, macOS defaults, package declarations, and remaining Pi extension package are not adopted wholesale. `joshukraine` supplies the older editor, terminal, and Git-helper assets; its Stow/Laptop setup, Zsh/Fish history, Claude skill and preset layer, and package declarations are superseded or application-owned. Open candidates are tracked in `maintenance/upstreams.toml`; accepted behavior belongs in this checkout.

Retain Herdr, Ghostty, and the Raycast script independently of upstream retirements. Git transport, credential storage, Agent permission rules, model inventories, and macOS notification preferences remain host choices; an upstream change to them is not an environment migration. The local Python/Ruby validation entry point remains authoritative rather than adopting upstream's Bun and GitHub Actions layout.

## Agent settings

The modifiers own how source and destination combine. Review their field boundaries before adopting a candidate setting; a directory or a top-level JSON object is not automatically one ownership unit.

| Surface | Ownership and removal behavior |
| --- | --- |
| Claude Code `env` | Source owns each declared variable. Host routes and `ANTHROPIC_DEFAULT_*_MODEL` mappings remain undeclared and survive. Removing a declaration leaves its destination value until explicit retirement. |
| Claude Code `sandbox.network.allowUnixSockets` | The existing host list survives, including an intentionally empty list. A missing list is seeded with the sandbox temporary directory and the 1Password SSH socket. Changing the seed does not update existing hosts. |
| Claude Code `model` and `modelSettings` | A missing model is seeded as `opus`; subsequent model choices and saved effort levels remain application-owned. |
| Other Claude Code settings | Declared top-level values replace their complete subtrees. Nested removals apply; removing a top-level declaration stops management without deleting its destination value. Undeclared top-level settings survive. |
| Codex `plugins`, `permissions.development`, and source-declared MCP servers | Source replaces these complete subtrees, removing stale nested fields. `node_repl.env` and `node_repl.env_vars` remain Desktop-owned. Undeclared MCP servers survive. |
| Other Codex settings | Declared fields are deep-overlaid. Model selection, reasoning effort, provider routes, undeclared context-window overrides, and per-app authorization remain local. Source removal alone does not remove a destination field. |
| Codex legacy sandbox selectors | While `default_permissions` is declared, the modifier removes `sandbox_mode` and `sandbox_workspace_write` because they can override that profile. This conditional invariant is distinct from a one-time retirement. |
| Pi settings | Source replaces declared top-level values. Provider, model, thinking level, enabled models, and per-model thinking levels remain undeclared and host-owned. |

The personal baseline keeps Codex copy-on-select enabled and displays context use, context size, the five-hour limit, and thread ID alongside model, directory, and branch. Claude Code's retry watchdog is capped at 1,800,000 milliseconds; a larger value permits longer retry waits. Socket seeds select 1Password without installing or changing the SSH provider. These choices are reviewed independently of unrelated permission changes.

On a semantic no-op, modifiers return the original text. A changed JSON or TOML document may be reserialized; tests establish preservation of unrelated values, not arbitrary formatting during a change. Credential stores and declared environment files are outside these modifiers' scope. If a mixed configuration contains protected values, an edit must preserve those bytes in place without exposing them; otherwise the user performs that edit.

For a field outside a fully owned subtree, complete retirement requires both source removal and selected destination cleanup under the [configuration lifecycle](lifecycle.md#retire-or-stop-managing). Keep an unresolved retirement in `maintenance/upstreams.toml` until its owning runtime has established that removal is appropriate; an ordinary clean diff is not evidence that the old field is absent.
