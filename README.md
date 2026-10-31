# mac-dotfiles

Personal development environment for Apple Silicon macOS, managed with chezmoi. This repository defines shell, editor, terminal, Git, developer-tool, and Agent configuration, with explicit ownership and repeatable validation.

`home/` is the default chezmoi source through `.chezmoiroot`. Agent instructions, hooks, and settings live in `agent-policy/` and are configured separately for each host. Configuration application is separate from package installation, account setup, and application data.

The environment uses Zsh with YAML-defined abbreviations and pinned plugin archives, asdf for selected runtimes, `~/.npm-global` for npm CLIs, `~/.pathrc` for local toolchains, and the 1Password SSH agent. LazyVim, Ghostty, kitty, and tmux provide the editor and terminal workspace. Software updates are explicit operator actions.

## Layout

| Path | Responsibility |
| --- | --- |
| `home/` | Deployable chezmoi source, organized by destination path |
| `home/.chezmoidata/` | Structured inputs, including the abbreviation YAML |
| `packages/` | Homebrew and language-package declarations |
| `maintenance/` | Upstream sources, review cursors, and pending adoption decisions |
| `.agents/skills/` | Repository workflows, shared with Claude Code through `.claude/skills` |
| `tests/` | Isolated rendering, shell, and lifecycle checks |
| `scripts/` | Validation, live-target check, and skill-rebuild entry points |
| `agent-policy/` | Independently configured Agent instructions, settings, hooks, and exact skill registry |
| `docs/` | Environment setup, ownership, and configuration lifecycle |
| `LESSONS.md` | Verified failure mechanisms and the checks that prevent them |
| `licenses/` | Third-party license notices |

## Validate

With chezmoi 2.73.1 or newer, Python 3.11+, Ruby, and the shell dependencies installed, run:

```sh
scripts/validate
```

Validation renders into unique temporary homes, checks repeated application for drift, parses shell/config syntax, verifies PATH selection with synthetic runtimes and abbreviation loading with the installed zsh-abbr, and exercises configuration creation, application, and retirement. The Python suite also runs the Claude Code hook/statusline scripts and the Codex hook contracts; Bun is not required. Agent modifier tests use synthetic host settings to check field preservation, replacement, initialization, and explicit retirement. Both skill registries receive structural and CLI smoke checks. The shell suite downloads the declared plugin archives into a temporary cache, so internet access to GitHub is required. Validation never starts agents, installs packages, accesses real private environment files, or switches the active chezmoi source. Runtime-selection tests establish PATH behavior; they do not substitute for Java/Node/project builds or GUI acceptance.

Enable the same validation before pushes from this checkout with `git config --local core.hooksPath .githooks`. Inspect any existing local hook selection before replacing it. The hook runs `scripts/validate` and aborts the push if a check fails.

Historical Agent tasks and their measurement boundaries are recorded in the [workflow baseline](docs/agent-workflows.md). Its read-only collector measures existing session records without replaying actions or claiming instruction improvements.

## Repository workflows

Use [apply-config](.agents/skills/apply-config/SKILL.md) to preview or apply this repository's selected configuration and verify the actual consumers. For example, ask `$apply-config apply the shell configuration`, or `$apply-config preview the Codex settings without writing them`. Ordinary home configuration and explicitly selected Agent targets have separate deployment scopes.

Use [review-upstreams](.agents/skills/review-upstreams/SKILL.md) to extract lessons from the two recorded sources and assess what fits this environment. For example, ask `$review-upstreams check recent changes and explain what we can learn from them`. A review explains the problems, mechanisms, and local relevance; useful learning can require no configuration change. Implementing selected adaptations or applying them locally follows the requested scope.

The skills stay in this checkout, support automatic discovery, and can also be invoked by name. Validate their structure, links, and CLI contracts with:

```sh
ruby agent-policy/dot_agents/exact_skills/scripts/validate-skills.rb --root .agents/skills --smoke
```

## Edit abbreviations

Edit [home/.chezmoidata/abbreviations.yaml](home/.chezmoidata/abbreviations.yaml). Keep entries under `abbreviations → category → name`, with `command` and `description` fields. chezmoi renders [the Zsh template](home/dot_config/zsh-abbr/abbreviations.zsh.tmpl) during preview and application; no generated Zsh file or separate generator is maintained in Git. Commands retain literal variables, quotes, and shell operators until used.

With the shell configuration installed, preview and apply just the abbreviation target:

```sh
chezmoi --source "$PWD" --refresh-externals=never diff --exclude=encrypted,scripts ~/.config/zsh-abbr/abbreviations.zsh
chezmoi --source "$PWD" --refresh-externals=never apply --exclude=encrypted,scripts ~/.config/zsh-abbr/abbreviations.zsh
```

Open a new shell to load additions, edits, and removals. The installed `reload-abbr` helper performs the apply command and reminds you to start a fresh shell. Add permanent entries to the YAML: interactive `abbr` edits change the generated destination and are overwritten by apply.

## Set up and manage

From this checkout, inspect a selected target without changing it:

```sh
chezmoi --source "$PWD" --refresh-externals=never diff --exclude=encrypted,scripts ~/.zshrc
```

Follow [environment setup](docs/setup.md) to install prerequisites, configure the selected applications, and verify actual shell, editor, and project behavior. On an existing machine, account for symlink ownership and unmanaged directory contents before applying a configuration group.

The [configuration lifecycle](docs/lifecycle.md) covers selecting this checkout as the default source, adding a target, validating changes, applying a selected target, stopping management, and destroying a retired target. Deployment commands still select the intended source explicitly because Agent policy is a separate source.

Review candidate changes from the sources declared in `maintenance/upstreams.toml` using the [upstream adoption procedure](docs/lifecycle.md#review-upstream-changes). This repository records the intended personal configuration, including deliberate differences from those sources.

`packages/Brewfile` declares selected Homebrew-owned tools. `~/Brewfile` links to this package declaration. After reviewing package ownership, `brew bundle --no-upgrade --file packages/Brewfile` installs missing declarations; the `bb` helper performs the same operation. Unlisted packages are not removal candidates. Vendor-installed apps and language toolchains follow [their declared installation and update owners](docs/ownership.md).
