# Agent configuration

This directory contains shared instructions, managed skills, hooks, and partial-configuration modifiers for Agent runtimes. It is outside `.chezmoiroot` and is applied independently from the default home configuration. Authentication and Pi model inventory remain local or application-owned; OMP has a managed Magpie model inventory with host-owned endpoint and authentication overrides.

Configure the sources for the target host before activation. Claude Code's filesystem sandbox declares tool-specific paths, and the Codex Browser modifier changes approval behavior. Check these selections against the host's actual tools and permission requirements. Claude Code model aliases and Pi provider, model, effort, and model inventory remain host-owned. Activation requires explicit approval for permission changes. Rebuild the shared skill registry with `scripts/install-skills` after backing up any existing `~/.agents/skills` content you may need.

The [Agent settings ownership contract](../docs/ownership.md#agent-settings) defines field replacement, shared environment variables, host socket seeds, and explicit retirement. Claude Code's missing socket list starts with 1Password and the sandbox temporary directory; an existing list is retained exactly. Codex preserves local model and provider choices while managing the selected TUI preferences.

Pi's `extensions/session-id-footer.ts` adds the session ID below the working directory while retaining the built-in statistics and extension statuses. It is adapted from [Pi Extensions](https://github.com/Entwining/pi-extensions/blob/687a8cc66ac5f7886e35438ddbb2727fce720e0c/extensions/session-id-footer.ts) under the [MIT license](../licenses/Entwining-MIT.txt). Apply that file as a selected target; the directory remains shared with independently owned extensions, including Herdr. The footer needs Pi's exported `FooterComponent` API; verify it after Pi upgrades and use `/reload` or a fresh session after deployment.

The managed hooks retain Claude Code's chezmoi edit warning and output scanner, and Codex's prompt-formatting hook. Agent Guard is not registered. On hosts with an existing installation, retire its Claude Code hook entries, Codex `PreToolUse` entry and `managed-hooks/guard-bash` script, and Pi `extensions/agent-guard.ts` adapter through the [configuration lifecycle](../docs/lifecycle.md#retire-or-stop-managing). The Codex requirements template at `.chezmoitemplates/codex/requirements.toml` supplies `/etc/codex/requirements.toml` separately; a home-directory apply does not update that system file. Coordinate active sessions before retiring scripts they may still call, and verify the new registrations in fresh sessions.

Run `scripts/validate` from the checkout root for configuration, hook, statusline, and skill checks. `python3 -m unittest discover -s tests -v` runs the configuration, hook, and statusline tests alone. These checks apply the actual modifiers to synthetic temporary destinations, without reading live Agent settings or invoking agents. They do not establish host activation or feature availability.

The Bash output scanner requires `jq` and Gitleaks on the hook's PATH and `post-bash-scan-secrets.toml` beside the executable. Deploy the script and rules together after installing the declared dependencies. Custom rules retain warnings for generic credential assignments, authentication headers, standalone Bearer values, and URL passwords alongside Gitleaks' vendor rules; only rule identifiers enter the reminder. Gitleaks' default allowlists still apply, including its exclusion of single-character repeated values.

From the checkout root, run `ruby agent-policy/dot_agents/exact_skills/scripts/validate-skills.rb --smoke` to validate the managed registry and its CLI contracts. Verify instruction and skill loading in fresh sessions of each affected runtime; structural and CLI checks alone do not prove loading. Default home application does not run an Agent policy installer.

## OMP

OMP retains its current installation owner; the managed sources target the default profile under `~/.omp/agent`. They contain no checkout path, username, credential, or session data. The `AGENTS.md` template renders the same shared instructions as Pi and Codex. OMP discovers the existing `~/.agents/skills` registry directly, so it needs no duplicate skill installation or absolute symlink. Named profiles and a relocated `PI_CODING_AGENT_DIR` need an explicit destination selection.

The YAML modifiers preserve undeclared settings and providers. `config.yml` manages the declared `modelRoles` entries and the six bundled agents' `task.agentModelOverrides`, retaining the bundled prompts, tool restrictions, and output schemas. Higher-precedence project settings, CLI flags, and explicit caller choices can affect effective selection; inspect `omp config get modelRoles --json` and `omp config get task.agentModelOverrides --json` in the intended working directory.

| Workload | Model through Magpie | Thinking |
| --- | --- | --- |
| Default conversation, general task, history consultation, vision, commit | `codex/gpt-6.1-sol` | `high` |
| Scout | `codex/gpt-6.1-sol` | `medium` |
| Sonic, smol, tiny background work, memory | `codex/gpt-6.1-sol` | `low` |
| Slow, planning, advisor, code review, security review | `codex/gpt-6-astra` | `xhigh` |

This allocation follows the existing host's Sol execution / Astra reasoning split, with lower effort for bounded discovery and mechanical work. It is an operating choice, not a measured quality ranking. The `vision` role analyzes images; neither chat model is assigned to image generation, speech, web search, or a dedicated judge runner. Assigning the advisor role does not enable automatic advisor execution.

`models.yml` owns Magpie's complete two-model inventory, including the context limits, effort ladders, and cost estimates adopted from the existing host configuration. Those estimates are not a verified billing rate card. Existing Magpie endpoint, API, authentication, headers, and compatibility overrides survive; missing values are seeded for the loopback OpenAI Responses gateway at `http://127.0.0.1:3425/v1`, without authentication, with the `x-session-affinity` cache header. Other providers survive unchanged. Reapplying restores the declared model inventory. A semantic no-op preserves file bytes. The three files declare private permissions (`0600`); their directories declare `0700`, which requires selecting the directory during apply rather than only its child files.

On another machine, install OMP through the selected vendor owner and make Magpie expose these model IDs. Run Magpie locally on the default endpoint or configure its host-owned endpoint and authentication before activation; the dotfiles do not install the gateway or copy credentials. Keep loopback in both `NO_PROXY` and `no_proxy`. Preserve recovery copies of existing non-secret targets and follow the [configuration lifecycle](../docs/lifecycle.md). The selected `.omp` directory deploys the three managed files and directory modes while retaining unmanaged application data:

```sh
chezmoi --source "$PWD/agent-policy" --refresh-externals=never diff --recursive --exclude=encrypted,scripts "$HOME/.omp"
chezmoi --source "$PWD/agent-policy" --refresh-externals=never apply --exclude=encrypted,scripts "$HOME/.omp"
scripts/check-home agent-policy "$HOME/.omp/agent/AGENTS.md" "$HOME/.omp/agent/config.yml" "$HOME/.omp/agent/models.yml"
omp models magpie --json --no-extensions
```

Start a fresh session to load the instructions. OMP deliberately omits context files named `AGENTS.md` from task subagents; model routing does not make those children inherit global or project instructions. Include the applicable constraints in each task's shared context and brief. Do not duplicate the full global policy into sticky `RULES.md` merely to bypass that runtime boundary.

## Shared skill ownership

The directories containing `dot_agents/exact_skills/*/SKILL.md` are the complete managed skill registry; `dot_agents/exact_skills/scripts/` contains their shared validator. `~/.agents/skills` is an exact chezmoi target at the top level, and `scripts/install-skills` performs the complete recursive rebuild with `rsync -a --delete`. The script resolves `HOME` and the target through symlinks and `..`, and refuses anything that does not resolve exactly to `$HOME/.agents/skills`. A selected-target `chezmoi apply` can leave nested files that are not in source; use the script for the registry. Back up the target before the first rebuild; add a skill to source to retain it. Do not edit or commit in the live registry.

Removing a managed skill requires source deletion and a rebuild with `scripts/install-skills`; verify both the source and target are absent and that this is the intended registry. A vendor or local skill that should survive must be added to the source or installed outside `~/.agents/skills`, because the rebuild does not preserve unmanaged siblings.

Release metadata records the upstream version compared, not byte identity with an unmodified vendor skill. Local routing and authorization remain part of the managed source. Run `scripts/check-skill-versions` after upgrading a covered CLI; a mismatch is evidence that its recorded release needs review, not that every skill instruction is obsolete.

The terminal skills retain Herdr and Rex together. `herdr` and `orc` route unnamed visible work by the caller's terminal environment and respect an explicit terminal choice. Rex's vendor stub loads its installed guide. The vendor-generated tldraw skill is retained unchanged; its application and external helper remain vendor-owned prerequisites. Compare vendor-written copies with source before rebuilding the registry after an application update.

The `tradingview` skill routes relevant financial research to the connected TradingView MCP for market data, fundamentals, documents, and macro series before generic data searches. It requires the connector to be available in the consuming Agent host; the skill does not configure the connection. Primary-source verification and explicit source restrictions still apply.
