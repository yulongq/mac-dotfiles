# Linux port

This document records the rationale, evidence, and plan for making this repository usable on Linux in addition to Apple Silicon macOS. The repository does not support Linux yet: `AGENTS.md`, `README.md`, and [setup.md](setup.md) remain the statement of supported capabilities until a phase below lands and updates them. Every finding in the evidence tables was checked against the tree at `e0ac7b9` with `rg` and `sed` and, where noted, by running chezmoi, the test suite, and shellcheck on Debian 13 (x86_64).

## Rationale

The configuration layer (chezmoi sources, Git, tmux, Neovim, Starship, lazygit, most helper scripts) is OS-neutral, but bootstrap, shell environment, agent policy, and tests assume macOS and Homebrew under `/opt/homebrew`. A Linux host, whether a development VM, a remote box, or a container, currently fails at the first line of `.zshrc` and cannot render the agent-policy source at all. Making the repository portable lets one source tree drive both machine types, and the test and CI work gives the repository its first automated gate beyond a local pre-push hook.

## Scope and non-goals

In scope: Debian/Ubuntu, Fedora, and Arch; x86_64 and arm64; interactive shell, Git, tmux, Neovim, helper commands, package declaration and installation, agent policy (Claude Code, Codex, Pi, shared skills), and the validation gate.

Non-goals until decided otherwise: Linux desktop GUI parity (Ghostty, kitty keymaps beyond a minimal Linux map, Karabiner, Raycast, 1Password GUI, OrbStack, input methods), WSL and BSD hosts, Nix or a second configuration driver, and replacing Homebrew on macOS. macOS behavior must not change; every change is gated so a darwin render stays byte-identical, and this is itself an acceptance criterion.

Repository rules that constrain the work: package declarations live under `packages/` and the Brewfile remains the macOS owner ([configuration rules](instructions/configuration.md)); ownership changes are recorded in [ownership.md](ownership.md) in the same change ([maintenance rules](instructions/maintenance.md)); new regression suites must be reachable from `scripts/validate` and use declared dependencies ([verification rules](instructions/verification.md), [LESSONS.md](../LESSONS.md#the-validation-entry-point)); and rendering evidence is not deployment evidence ([LESSONS.md](../LESSONS.md#deployment-and-actual-use)), so each distro needs a consumer check, not only a render.

## Evidence

Format is `path:line` followed by the quoted code. "Verified" means read at the stated line; "Run" means observed by executing on Linux.

### Shell and environment

| Finding | Evidence |
| --- | --- |
| The shell fails on its first line without Homebrew | `home/dot_zshrc:1: eval "$(env -u HOMEBREW_BREW_FILE -u HOMEBREW_PATH /opt/homebrew/bin/brew shellenv)"` |
| zsh-abbr is sourced from the Homebrew prefix | `home/dot_zshrc:48: source /opt/homebrew/share/zsh-abbr/zsh-abbr.zsh` |
| Homebrew-only cask option exported | `home/dot_config/zsh/environment.zsh:5: export HOMEBREW_CASK_OPTS='--appdir=/Applications'` |
| Ruby build and pkg-config paths point at the Homebrew prefix (four `--with-opt-dir` entries; `PKG_CONFIG_PATH` holds only libpq) | `environment.zsh:13: export RUBY_CONFIGURE_OPTS="--with-opt-dir=/opt/homebrew/opt/openssl:...:/opt/homebrew/opt/gdbm"` and `environment.zsh:14: export PKG_CONFIG_PATH=/opt/homebrew/opt/libpq/lib/pkgconfig` |
| 1Password agent socket is the macOS container path | `environment.zsh:16: export SSH_AUTH_SOCK="$HOME/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"` |
| Surge directory is under iCloud | `environment.zsh:18: export SURGE_HOME="$HOME/Library/Mobile Documents/iCloud~com~nssurge~inc/Documents"` |
| Unconditional loopback proxy (the draft cited lines 27-29; the file has 26 lines) | `environment.zsh:24-26: export https_proxy=http://127.0.0.1:6152`, `http_proxy=...:6152`, `all_proxy=socks5://127.0.0.1:6153` |
| JDK path uses the macOS bundle layout; Maven and Go live in hand-managed `~/dep` | `home/dot_pathrc:1: export JAVA_HOME="$HOME/dep/graalvm-jdk-25.0.4.1+1.1/Contents/Home"`, `:3` Maven, `:5` Go |
| `o` uses macOS `open` | `home/dot_config/zsh/aliases.zsh:29: alias o='open . &'` |
| `pbcopy` in the path-copy function | `home/dot_config/zsh/functions.zsh:49`, `:53`, `:57`: `... \| pbcopy` |
| Hardcoded macOS home display | `functions.zsh:44: echo "3) /Users/$(whoami)"` |
| Postgres helpers use `brew services` | `functions.zsh:492: brew services start postgresql`, `:505: brew services stop postgresql` |
| Finder hidden-file toggles use `defaults` | `functions.zsh:532` and `:547: defaults write com.apple.finder AppleShowAllFiles FALSE\|TRUE` |
| Portable already: `ps aux \| rg postgres` and `xargs -0 ls -t` | `functions.zsh:518`, `functions.zsh:577` |
| `copy` helper requires `pbcopy` | `home/dot_local/bin/executable_copy:7: printf "%s" "$*" \| tr -d "\n" \| pbcopy` |
| `bb` and `bubo` are Homebrew wrappers | `executable_bb:10: brew bundle --no-upgrade --file "${HOME}/Brewfile"`, `executable_bubo:8: brew update && brew outdated` |
| Abbreviations: one Homebrew category, nothing else macOS-specific (audited every entry; no `open`, `pbcopy`, `defaults`, `osascript`, `launchctl`) | `home/.chezmoidata/abbreviations.yaml:109-158` (`homebrew:` group, 13 `brew ...` commands) |
| OrbStack and Otty integration are already guarded by existence checks | `home/dot_zshrc:72: [[ ! -r "$HOME/.orbstack/shell/init.zsh" ]] \|\| source ...`, `:73: if [[ -n "$OTTY_SHELL_INTEGRATION" && -r ... ]]` |
| macOS-only ignore entries are harmless on Linux | `home/dot_ignore:4: /Library/`, `home/dot_ripgreprc:22: --glob=!Library/*` |
| `pager.diff = diffnav` makes `git diff` depend on a tap-only binary; no `osxkeychain` credential helper exists | `home/dot_gitconfig:85-86: [pager]` / `diff = diffnav`; no `credential` match in the file |

### Chezmoi layer and packages

| Finding | Evidence |
| --- | --- |
| No template branches on OS or architecture | `rg 'chezmoi\.(os\|arch\|osRelease)'` over the tree returns nothing; templates use only `workingTree`, `homeDir`, `sourceDir`, `uid` |
| No `run_*` scripts, so nothing bootstraps packages | `git ls-files` lists no `run_` entries |
| Ignore files are static and shared with macOS | `home/.chezmoiignore:1-2: **/*.test.*`, `**/.DS_Store`; `agent-policy/.chezmoiignore:1-3` adds `README.md`. The Raycast script therefore deploys on Linux |
| Minimum chezmoi version | `home/.chezmoiversion: 2.73.1` |
| Externals are pinned archives (zsh plugins, TPM) and OS-neutral | `home/.chezmoiexternal.toml`: four `type = "archive"` entries pinned by commit SHA |
| Brewfile: 7 taps, 31 formulae, 7 casks (the draft said about 30 formulae) | `packages/Brewfile:1-7` taps, `:10-40` formulae, `:42-48` casks; `:14 brew "coreutils"`, `:16 brew "entwining/tap/agent-guard"`, `:29 brew "olets/tap/zsh-abbr"`, `:15 brew "dlvhdr/formulae/diffnav"` |
| `~/Brewfile` is a template symlink | `home/symlink_Brewfile.tmpl:1: {{ .chezmoi.workingTree }}/packages/Brewfile`; `home/dot_config/private_homebrew/brew.env:1: HOMEBREW_NO_UPGRADE_AUTO_UPDATES_CASKS=1` |
| `sha256` helper is already portable | `home/dot_local/bin/executable_sha256:11: ... \| sha256sum --check` |
| `scripts/install-skills` needs `rsync` (absent from the Linux box, exit 127 in the suite) | `scripts/install-skills:55: rsync -a --delete "$source_dir/" "$target/"` |
| Documentation states macOS-only support | `README.md:3`, `AGENTS.md:3`, `docs/setup.md:3` ("Apple Silicon"); `docs/setup.md:7` Homebrew under `/opt/homebrew`; `docs/ownership.md:7,20,25,30-33` |

### Editor, terminal, and multiplexer

| Finding | Evidence |
| --- | --- |
| Neovim probes Marked 2 with AppleScript | `home/dot_config/nvim/lua/plugins/knowledge-base.lua:10: vim.fn.system("osascript -e 'exists application \"Marked 2\"'")`; the probe has no `has("mac")` guard |
| avante build is already gated | `home/dot_config/nvim/lua/plugins/avante.lua:6: build = vim.fn.has("mac") == 1` with the `xcrun --sdk macosx26.5` branch at `:8` |
| Arrow-key mappings removed for macOS | `home/dot_config/nvim/lua/config/keymaps.lua:8-12: vim.keymap.del("n", "<C-Up>")` and three more; the comment says they conflict with macOS, so on Linux these defaults are simply absent |
| tmux sets no clipboard options; copy goes through the `tmux-yank` plugin, which shells out to `pbcopy`, `xclip`, `xsel`, or `wl-copy` | `home/dot_config/tmux/tmux.conf:97: bind-key -T copy-mode-vi y send-keys -X copy-selection-and-cancel`, `:119: set -g @plugin 'tmux-plugins/tmux-yank'`; no `set-clipboard` or `copy-command` match. Linux needs one of those tools installed (not yet declared anywhere) |
| tmux inherits the shell | `tmux.conf:74: set -g default-shell ${SHELL}` |
| `otty.vim` files are generated syntax and filetype detection for the Otty terminal config, not OS-specific code | `home/dot_config/nvim/ftdetect/otty.vim:1: " GENERATED by resources/editors/generate.py`, `syntax/otty.vim:1-5`. They load harmlessly anywhere. The draft's link to the `openinterminal` cask is unverified and should not be assumed |
| Ghostty macOS keys | `home/dot_config/ghostty/config.ghostty:15: font-thicken = true`, `:27: window-save-state = always`, `:37-40: keybind = super+ctrl+...`, `:43: keybind = global:super+period=toggle_quick_terminal`, `:47: background-blur-radius = 20` |
| kitty macOS keys and font | `home/dot_config/kitty/kitty.conf:35: font_family Maple Mono Normal NF CN`, `:254: macos_option_as_alt yes`, `:261: map cmd+enter new_window_with_cwd`, `:300: map ctrl+cmd+f toggle_fullscreen`, `:305: map ctrl+cmd+, load_config_file` |
| Raycast script is macOS-only | `home/dot_config/raycast/scripts/executable_copy-markdown-url-and-title.js:1: #!/usr/bin/env osascript -l JavaScript` |

### Agent policy

| Finding | Evidence |
| --- | --- |
| **Not in the draft, Run:** the Claude settings template shells out to a macOS-only `getconf` variable, so rendering `agent-policy` fails on Linux | `agent-policy/.chezmoitemplates/claude/settings.json:114: "{{ output "getconf" "DARWIN_USER_TEMP_DIR" \| trim \| trimSuffix "/" }}"`. Observed: `getconf: Unrecognized variable 'DARWIN_USER_TEMP_DIR'` and `chezmoi: .claude/CLAUDE.md: template: dot_claude/CLAUDE.md.tmpl:16:10: ... exit status 2` |
| **Not in the draft:** the same sandbox block is macOS-specific elsewhere | `settings.json:115-116: /private/tmp/.pnpm-store`, `/private/tmp/pnpm-store-operation-locks-{{ .chezmoi.uid }}`; `:135: ~/Library/Caches`; `:166-167: allowMachLookup` with `com.apple.trustd.agent`; `:170-171: /private/tmp/claude-{{ .chezmoi.uid }}` and the 1Password `agent.sock` |
| `agent-guard` is hardcoded to the Homebrew path in three places | `settings.json:182` and `:192: "command": "/opt/homebrew/bin/agent-guard --runtime claude"`; `agent-policy/dot_codex/managed-hooks/executable_guard-bash:3-4`; `agent-policy/dot_claude/hooks/settings-registration.test.sh:58` |
| **Verified (draft said "verify"):** `guard-bash` is a zsh script and fails closed when the guard is missing | `executable_guard-bash:1: #!/bin/zsh -f`, `:3: [[ -x /opt/homebrew/bin/agent-guard ]] \|\| { print -u2 -- '... this call is blocked. Install Entwining/tap/agent-guard with Homebrew ...'; exit 2 }`, `:4: exec /opt/homebrew/bin/agent-guard --runtime codex`. The existing missing-binary behavior is already fail-closed; the port must preserve it |
| Another hook also requires `/bin/zsh` | `agent-policy/dot_codex/managed-hooks/executable_contextual-markdown-links:1: #!/bin/zsh` |
| Other hooks and the statusline are bash | `executable_post-bash-scan-secrets.sh:1: #!/usr/bin/env bash`; `executable_statusline.sh:1: #!/bin/bash` |
| Statusline uses BSD `stat` and `date` and the macOS Keychain | `executable_statusline.sh:42: stat -f %m "$1" 2>/dev/null \|\| echo 0`; `:239: { security find-generic-password -s "Claude Code-credentials" -w 2>/dev/null \|\| cat "$HOME/.claude/.credentials.json" ...`; `:417: ... date -j -f '%a %b %e %T %Y' "$(LC_ALL=C ps -o lstart= -p "$PPID")" +%s`; `:521: date -j -r $(( (reset_epoch + 150) / 300 * 300 )) +"%m-%d %H:%M"` |
| Codex gpg sockets are under `~/.gnupg` (the draft cited lines 98-100) | `agent-policy/.chezmoitemplates/codex/config.toml:99: "{{ .chezmoi.homeDir }}/.gnupg/S.gpg-agent" = "allow"`, `:100` `S.gpg-agent.ssh`, `:101` `S.keyboxd` |
| **Not in the draft:** Codex config references a macOS app bundle | `config.toml:127: command = "/Applications/ChatGPT.app/Contents/Resources/cua_node/bin/node_repl"` |
| Policy prose assumes Keychain and launchd | `agents/protected-inputs.md:9: Personal API credentials live in the macOS Keychain under envchain namespaces`; `claude/settings.json:46` ("namespaces in the macOS Keychain"); `agents/execution-host.md:9` (`~/Library`), `:11` ("launchd owns startup"), `:13: ... launchctl kickstart gui/$UID/org.gnupg.gpg-agent`, `:14: ... launchctl kickstart gui/$UID/org.gnupg.keyboxd` |
| Statusline and registration tests encode macOS semantics | `agent-policy/dot_claude/scripts/statusline.test.sh:61-66` (`/bin/date -r`, `/bin/date -j -r`), `:72,74` (`date -u -r`), `:80,159,167` (`touch -t "$(date -r ...)"`), `:109,112` (`stat -f %m`) |

### Tests and gate

| Finding | Evidence |
| --- | --- |
| Tests hardcode the Homebrew PATH, which hides any chezmoi installed in a user prefix | `tests/test_dotfiles.py:53,143: "PATH": "/opt/homebrew/bin:/usr/bin:/bin"`, `:208` (adds `/usr/sbin:/sbin`); `tests/test_agent_config.py:36` |
| Tests hardcode `/bin/zsh` and the Homebrew zsh-abbr path | `test_dotfiles.py:44,119,145,212: "/bin/zsh"`, `:45: source /opt/homebrew/share/zsh-abbr/zsh-abbr.zsh`; `tests/test_agent_hooks.py:101: run("/bin/zsh", "-f", ...)` |
| Tests assert macOS-only values | `test_dotfiles.py:201,216: .../Contents/Home/bin/java`, `:220: 2BUA8C4S2C.com.1password/t/agent.sock`, `:253-254: brew "{name}"` and `brew "olets/tap/zsh-abbr"`; `test_agent_config.py:95: ~/Library/Group Containers/...` |
| There is no CI; the only gate is a pre-push hook that is not enabled by cloning | no `.github/`; `.githooks/pre-push:3: exec "$(git rev-parse --show-toplevel)/scripts/validate"`; `git config core.hooksPath` is unset in a fresh clone (enabled per `docs/setup.md` step 2 of "Apply configuration") |
| **Run:** the unmodified suite on Debian 13 without zsh, ruby, rsync, or Homebrew paths | `python3 -m unittest discover -s tests`: `Ran 23 tests ... FAILED (failures=1, errors=15)`. Causes: `/bin/zsh` not found (6), `zsh` not found (1), `chezmoi` not found because of the fixed PATH even though chezmoi 2.73.1 was installed in `/tmp/bin` (7), `scripts/install-skills` exit 127 (no rsync), and the statusline suite failing at `date: 1792344379: No such file or directory` (GNU `date -r` takes a file) |
| **Run:** shellcheck 0.11.0 over `home/dot_local/bin/executable_*`, hooks, statusline, and `scripts/*` | Only SC2174 at `executable_statusline.sh:266,371,478` (`mkdir -p -m`; the mode applies only to the deepest directory, on macOS too) and SC1071 for the perl and ruby scripts `executable_colortest` and `executable_git-publish`, which shellcheck cannot parse. No GNU/BSD flag diagnostics in helper scripts |
| **Run:** home source renders and applies on Linux with externals and scripts excluded | `chezmoi --source $PWD --destination $T/h apply --exclude externals,scripts` exited 0 and wrote `.zshrc`, `Brewfile -> /workspace/mac-dotfiles/packages/Brewfile`, `.config/zsh-abbr/abbreviations.zsh`, `.local/bin/{bb,bubo,copy,...}`; the rendered tree still contains every macOS line listed above |
| README dependency list | `README.md:27: With chezmoi 2.73.1 or newer, Python 3.11+, Ruby, and the shell dependencies installed` (rsync and zsh are implied but not named) |

### Already portable (verified)

`.chezmoiroot`, the pinned externals, `sha256`, `scripts/check-home`, `scripts/validate` (POSIX sh plus Python and Ruby), the Git, ripgrep, Starship, lazygit, tmux, Neovim (apart from the lines above), uv, asdf, and yamllint/markdownlint configurations, and the helper commands other than `copy`, `bb`, and `bubo`. The helpers `colortest` (perl) and `git-publish` (ruby) are interpreter scripts with no BSD-only flags found. Not verified here: runtime behavior of any helper on Linux, Neovim plugin builds, and the contents of the agent skills, which were not audited line by line.

## Plan

Effort estimates are focused engineering time for one maintainer and exclude waiting on upstream packaging. A first milestone, "the shell and helpers work on Debian/Ubuntu and Arch; GUI and agent-guard degraded", is phases 0-2 plus the Ubuntu job from phase 5, about one week. Full parity is about three to four weeks.

### Phase 0: Decisions and scaffolding (1-2 days)

- Resolve the open decisions below for hosts in scope.
- Add chezmoi data for the OS family and package manager through `.chezmoi.toml.tmpl` or derive it from `.chezmoi.os` and `.chezmoi.osRelease.id`; prefer deriving, because the repository selects its source with `--source` and a `.chezmoi.toml.tmpl` only takes effect after `chezmoi init`.
- Convert `home/.chezmoiignore` and `agent-policy/.chezmoiignore` to `.chezmoiignore.tmpl` and gate macOS-only targets (Raycast script, `private_homebrew`, `Brewfile` symlink).
- Acceptance: a darwin render is byte-identical to today's (compare `chezmoi dump` or the applied tree before and after); on Linux the macOS-only targets are absent.

### Phase 1: Shell starts cleanly on Linux (2-3 days, highest priority)

- Guard `home/dot_zshrc:1` with a prefix probe (`/opt/homebrew`, `/usr/local`, `/home/linuxbrew/.linuxbrew`) and skip when none exists; locate zsh-abbr by probing, or pin it as an external archive on all platforms so the tests can use the same path.
- Make `environment.zsh:5,13,14,16,18,24-26` OS-aware: Homebrew options only when a prefix exists, Linux 1Password socket `~/.1password/agent.sock` only if it exists (otherwise leave `SSH_AUTH_SOCK` alone), `SURGE_HOME` darwin-only, and the proxy exports only when the loopback port answers or on darwin. The unconditional proxy is a silent outage on any host without Surge.
- Make `dot_pathrc:1` OS-aware (`Contents/Home` only on darwin) and decide how `~/dep` toolchains are provisioned.
- Add `copy`, `paste`, and `open` shims (`pbcopy`, `wl-copy`, `xclip`, `xsel`, then OSC 52) in `home/dot_config/zsh` or `~/.local/bin`; use them in `executable_copy`, `functions.zsh:49,53,57`, and `aliases.zsh:29`. Gate `functions.zsh:44`, `:482-505`, and `:532,547` to darwin or give Linux equivalents.
- Decide between hiding the Homebrew abbreviation group on Linux or keeping it (it is inert without brew).
- Acceptance: on each target distro `zsh -lic 'echo ok'` prints no errors and `command -v` resolves the declared tools; `copy` and `o` work or fail with a clear message.

### Phase 2: Package abstraction and bootstrap (4-7 days)

- Implement the design in the next section.
- Acceptance: `scripts/install-packages --dry-run` lists the right packages per distro; a fresh container reaches a working shell with one documented command; `docs/setup.md` and `docs/ownership.md` carry a per-OS install-owner table.

### Phase 3: Agent policy (2-4 days)

- Replace `claude/settings.json:114` with an OS-conditional temp directory: `getconf DARWIN_USER_TEMP_DIR` on darwin and `$TMPDIR` or `/tmp` on Linux. This is the single change that unblocks rendering `agent-policy` on Linux and should land first.
- Gate the remaining sandbox entries (`/private/tmp/...`, `~/Library/Caches`, `allowMachLookup`, the 1Password socket) to darwin, and derive Linux gpg socket paths with `gpgconf --list-dirs` for `codex/config.toml:99-101`.
- Resolve `agent-guard` through a single probe (`command -v agent-guard`, then known prefixes) in `guard-bash` and in the Claude hook commands (`settings.json:182,192`) while keeping the fail-closed branch. If no Linux build exists, the hook must still block, and the documentation must say that agent policy is not enforced on that host.
- Replace the zsh shebangs in `guard-bash` and `contextual-markdown-links` only if the zsh dependency is judged too costly; otherwise declare zsh as a required package on Linux.
- Add portable `file_mtime` and `fmt_epoch` helpers to `executable_statusline.sh` (GNU versus BSD probe) and guard `security` with `command -v`; keep the `~/.claude/.credentials.json` fallback.
- Template the OS-specific prose in `execution-host.md`, `protected-inputs.md`, and `claude/settings.json:46` (launchd and Keychain on darwin; `systemctl --user` and libsecret or `pass` on Linux). Follow [agents.md](instructions/agents.md): use the write-skill rules for behavior-bearing instruction edits and check loading in each runtime.
- Acceptance: `chezmoi --source agent-policy` renders on Linux; the darwin render is unchanged; Claude and Codex load the instructions in a fresh session on a Linux host (runtime check, not only a render).

### Phase 4: Editor and terminal (1-2 days)

- Guard the `osascript` probe in `knowledge-base.lua:10` with `vim.fn.has("mac") == 1`.
- Add Linux keymaps to kitty (`kitty.conf` near `:261,300,305`) or document that kitty keymaps are macOS-only; leave Ghostty as is unless Linux Ghostty is adopted, and verify it tolerates `font-thicken` and `background-blur-radius`, which this plan assumes but has not run.
- Declare a clipboard tool for `tmux-yank` on Linux and add `urlview` if the plugin at `tmux.conf:120` is to work.
- Make `pager.diff = diffnav` conditional or provide a release binary; otherwise `git diff` breaks without it.
- Acceptance: Neovim starts headless without errors; tmux copy reaches the system clipboard on a desktop host and OSC 52 over SSH.

### Phase 5: Tests and CI (3-5 days)

See the next sections. Acceptance: `scripts/validate` passes on macOS and on each Linux target, and a pull request cannot merge red.

## Package-manager abstraction design

Constraints: chezmoi stays the only orchestrator; `packages/` owns package declarations and the Brewfile keeps being the macOS owner; the pre-push gate and `scripts/validate` must keep working with only declared dependencies; and `bb` must keep its `--no-upgrade` semantics.

Design: add `packages/packages.yaml` as the logical source of truth, one entry per tool with per-manager names. Keep it under `packages/` rather than `home/.chezmoidata`, because `packages/` is outside default deployment and the installer runs before chezmoi has applied anything. Example entries: `fd: {brew: fd, apt: fd-find, dnf: fd-find, pacman: fd}`, `bat: {brew: bat, apt: bat, dnf: bat, pacman: bat}`, `starship: {brew: starship, apt: null, dnf: null, pacman: starship, fallback: {github: starship/starship}}`. A `null` means "use the fallback", `os: [darwin]` marks macOS-only entries, and `gui: true` marks desktop applications that headless hosts skip.

Generation: a small script (Python, already a required dependency) writes `packages/Brewfile` and `packages/generated/{apt,dnf,pacman}.txt`. The generated files are committed, and a unit test in `tests/` regenerates them and fails on any diff, so the Brewfile cannot drift from the manifest and `test_declared_shell_dependencies` keeps reading a real Brewfile. If the hand-written Brewfile is preferred during migration, the test instead asserts that every Brewfile formula has a manifest entry.

Installer: `scripts/install-packages` (POSIX sh, like `scripts/install-skills` and `scripts/check-home`) detects the manager from `/etc/os-release` (`ID`, `ID_LIKE`) and `uname -m`, then runs `brew bundle --no-upgrade`, `apt-get install -y`, `dnf install -y`, or `pacman -S --needed`. It never upgrades the whole machine, matching the existing statement that the declaration "is not a cleanup list". `--dry-run` prints the plan and `--minimal` installs only what `scripts/validate` needs (zsh, python3, ruby, rsync, jq, git, tmux, shellcheck, chezmoi).

Fallbacks: tools missing or too old in distro repositories are installed as pinned release binaries with per-architecture asset names and SHA-256 checksums into `~/.local/bin`, either through `.chezmoiexternal.toml.tmpl` (mapping `{{ .chezmoi.arch }}`) or from the installer, whichever the open decision selects. Candidates are chezmoi, starship, git-delta, lazygit, yazi, uv, tlrc, asdf, zsh-abbr, and diffnav. `fzf --zsh` in `home/dot_zshrc` needs fzf 0.48 or newer, which Debian and Ubuntu LTS repositories may not ship; this is unverified here and needs a version check in the installer.

Distro shims: Debian and Ubuntu install `bat` as `batcat` and `fd` as `fdfind`; create `~/.local/bin` symlinks. The `ls` alias in `home/dot_zshrc` and the fzf commands in `environment.zsh:20-23` call `eza`, `rg`, and `fd` by name.

Wrappers: `bb` calls the installer; `bubo` maps to `brew outdated`, `apt list --upgradable`, `dnf check-update`, or `checkupdates`.

Out of scope for the manifest: language runtimes (`packages/npm.txt`, `asdf-node-npm.txt`, `ruby-gems.txt`, `uv.txt`), which keep their own owners per `AGENTS.md`.

## Test and CI strategy

1. Make the tests platform-aware: replace `/opt/homebrew/bin` in the fixed PATHs with a helper that prepends the directories of `shutil.which` results for chezmoi, zsh, and the tools under test; replace `/bin/zsh` with `shutil.which("zsh")`; locate zsh-abbr from the discovered install or a pinned external; gate the 1Password socket, `Contents/Home`, and Brewfile assertions by platform and assert the generated package lists on Linux.
2. Rewrite `statusline.test.sh` to stub `date` and `stat` for the flavor under test, or to call the script's new helpers directly. This must land together with the Phase 3 script change, because the current stubs encode BSD semantics.
3. Declare `rsync`, `zsh`, `ruby`, and `chezmoi` as test dependencies in the README and the installer's `--minimal` set; the Linux run above failed on all four.
4. Render matrix: `chezmoi execute-template --override-data` cannot override the built-in `.chezmoi.os`, so cover the non-native OS by parameterising the OS decision behind a data key (for example `.platform`) that tests can override, and render both values on any host. Assert that macOS-only targets are absent when the value is `linux` and that the darwin render is unchanged.
5. Add shellcheck over the shell scripts with the two interpreter scripts excluded, after fixing or suppressing SC2174 at `executable_statusline.sh:266,371,478`.
6. GitHub Actions `validate` workflow on pull requests and pushes: `macos-14`, `ubuntu-24.04`, and `ubuntu-24.04-arm` running `scripts/validate`; container jobs for `debian:stable`, `fedora:latest`, and `archlinux:latest` that run `scripts/install-packages --minimal` first. Cache the pinned plugin archives. Nothing in the suite needs secrets, so a standard runner works; keep third-party actions pinned by SHA.
7. Keep `.githooks/pre-push` as the local gate. Enabling it is a documented setup step, not automatic, so CI is what makes the gate mandatory.
8. Acceptance per distro (document in `docs/verification` rules when implemented): fresh login shell without errors, `chezmoi diff` clean after apply, `copy` and `o` work, `git diff` pages, Neovim starts headless, tmux plugins install, and `scripts/check-home` passes for explicit non-secret targets. A nightly job may add a full install smoke test per distro.

## Risks and open decisions

| Risk or decision | Impact | Mitigation or recommendation |
| --- | --- | --- |
| `agent-guard` has no known Linux build (unverified) | Agent policy unenforced or Codex hooks always blocking | Keep fail-closed; check upstream for a Linux release before Phase 3; document the degraded state if none |
| Tap-only tools (`diffnav`, `zsh-abbr`, `envchain`, `cmux`, `codexbar`, `longbridge-terminal`) may lack Linux packages | Missing features; `git diff` breaks via `pager.diff` | Per-tool fallback or darwin-only flag; conditional pager |
| Old distro packages (chezmoi, fzf, delta, starship, uv, yazi, lazygit) | Bootstrap breaks on LTS releases | Pinned checksummed binaries, minimum-version checks |
| Credential storage differs: envchain uses libsecret on Linux and headless hosts have no secret service | Credential workflow breaks | Decide on libsecret versus `pass`/gpg; document |
| Sandbox semantics differ (Seatbelt versus bubblewrap) and socket paths differ | Tools blocked or over-permissive | Test the agent configs on Linux; derive paths from `gpgconf`; install bubblewrap |
| Test PATH and zsh assumptions | Green on macOS, red or vacuous on Linux | Phase 5 helpers and dual CI |
| Zsh required on Linux because of two hook shebangs and the shell contract | Extra dependency | Declare it; do not rewrite hooks to bash unless needed |
| Matching macOS output | Regression on the primary platform | Byte-identical darwin render as an acceptance gate |
| Proxy exports are unconditional | All HTTP clients fail on a host without Surge | Phase 1 guard |
| Open decision: supported Linux targets (desktop, headless, WSL) and whether Linuxbrew is allowed | Determines package design | Recommend headless and desktop Debian/Ubuntu and Arch first, no Linuxbrew by default |
| Open decision: fallback installs via chezmoi externals or the installer | Where checksums live | Recommend the installer for binaries and externals for archives |
| Open decision: scope of GUI parity | Ghostty has no Debian or Fedora package (unverified) | Treat GUI as non-goal initially |
| Open decision: documentation wording | `AGENTS.md`, `README.md`, `setup.md`, and `ownership.md` say macOS-only | Change them in the same commit as the phase that adds support |

## Verification log

Method: read-only inspection of the checkout at `e0ac7b9` with `rg`, `sed`, and `cat -n`; tool executions in a scratch directory under `/tmp`, with no tracked file modified other than this document. Environment: Debian GNU/Linux 13, x86_64, Python 3.13.5, bash, tmux, jq, git, ripgrep; chezmoi v2.73.1 and shellcheck 0.11.0 installed in user space; zsh, ruby, and rsync were not available, and no root access.

- Every path, line number, and quotation in the Evidence tables was re-read against the tree. Corrected from the earlier analysis: the proxy exports are `environment.zsh:24-26`, not 27-29; `RUBY_CONFIGURE_OPTS` lists four directories and `PKG_CONFIG_PATH` only libpq; the Codex gpg sockets are `config.toml:99-101`; the Brewfile has 31 formulae.
- Resolved the draft's "verify" items: `guard-bash` is `#!/bin/zsh -f` and already fails closed; tmux sets no clipboard options and relies on the `tmux-yank` plugin; `otty.vim` is generated Otty-terminal syntax and detection, harmless on Linux, with no verified relation to the `openinterminal` cask.
- New findings from execution: `claude/settings.json:114` breaks the agent-policy render on Linux; the suite's fixed PATH hides a user-installed chezmoi; `scripts/install-skills` needs `rsync`; the statusline test fails on GNU `date -r`.
- Confirmed absences with `rg` and `git ls-files`: no `.chezmoi.os`, `.chezmoi.arch`, or `.chezmoi.osRelease` use; no `run_*` scripts; no `.github/`.
- Ran `python3 -m unittest discover -s tests` (23 tests, 1 failure, 15 errors, causes above), shellcheck (only SC2174 and the two interpreter-script SC1071 notices), and `chezmoi apply` of `home/` into a temporary destination (succeeded) and of `agent-policy/` (failed at the `getconf` call).
- Not verified: any claim about third-party packaging (distro versions, Ghostty and `agent-guard` Linux availability, the Linux 1Password socket path, Claude Code and Codex Linux sandbox behavior), the content of agent skills, Neovim plugin behavior on Linux, and `scripts/validate`'s Ruby skill validator (no Ruby installed). These need a distro container run in Phase 5 before the corresponding acceptance criteria can be claimed.
