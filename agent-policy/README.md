# Agent configuration

This directory contains shared instructions, managed skills, hooks, and partial-configuration modifiers for Agent runtimes. It is outside `.chezmoiroot` and is applied independently from the default home configuration. Provider endpoints, authentication, and Pi model inventory remain local or application-owned.

Configure the sources for the target host before activation. Claude Code's filesystem sandbox declares tool-specific paths, and the Codex Browser modifier changes approval behavior. Check these selections against the host's actual tools and permission requirements. Claude Code model aliases and Pi provider, model, effort, and model inventory remain host-owned. Activation requires explicit approval for permission changes. Preserve unique installed skills and vendor-managed skill ownership instead of replacing the whole live registry.

The [Agent settings ownership contract](../docs/ownership.md#agent-settings) defines field replacement, shared environment variables, host socket seeds, and explicit retirement. Claude Code's missing socket list starts with 1Password and the sandbox temporary directory; an existing list is retained exactly. Codex preserves local model and provider choices while managing the selected TUI preferences.

Pi's `extensions/session-id-footer.ts` adds the session ID below the working directory while retaining the built-in statistics and extension statuses. It is adapted from [Pi Extensions](https://github.com/Entwining/pi-extensions/blob/687a8cc66ac5f7886e35438ddbb2727fce720e0c/extensions/session-id-footer.ts) under the [MIT license](../licenses/Entwining-MIT.txt). Apply that file as a selected target; the directory remains shared with independently owned extensions, including Agent Guard and Herdr. The footer needs Pi's exported `FooterComponent` API; verify it after Pi upgrades and use `/reload` or a fresh session after deployment.

Run `scripts/validate` from the checkout root for configuration, hook, statusline, and skill checks. `python3 -m unittest discover -s tests -v` runs the configuration and hook tests alone. These checks apply the actual modifiers to synthetic temporary destinations, without reading live Agent settings or invoking agents. They do not establish host activation or feature availability.

From the checkout root, run `ruby agent-policy/dot_agents/skills/scripts/validate-skills.rb --smoke` to validate the managed registry and its CLI contracts. Verify instruction and skill loading in fresh sessions of each affected runtime; structural and CLI checks alone do not prove loading. Default home application does not run an Agent policy installer.

## Shared skill ownership

The directories containing `dot_agents/skills/*/SKILL.md` are the managed skill inventory; `dot_agents/skills/scripts/` contains their shared validator. Deploy these entries from this source and check them with `scripts/check-home agent-policy ~/.agents/skills`. Independently installed siblings retain their vendor or local owner. This repository reconstructs its managed subset, not the complete registry of external skills, and must not apply an `exact_` directory or replace the registry wholesale.

A Git checkout at `~/.agents/skills` does not own the deployed managed subset. Do not reset or clean that shared working tree to synchronize skills: its tracked files and untracked vendor installs have independent state. Removing a managed skill requires the source-and-destination recovery and retirement procedure in the configuration lifecycle, followed by checks that both selected paths are absent and independently owned siblings survive. Removing only its source leaves an installed skill discoverable and is incomplete retirement.
