# Agent configuration

This directory contains shared instructions, managed skills, hooks, and partial-configuration modifiers for Agent runtimes. It is outside `.chezmoiroot` and is applied independently from the default home configuration. Provider endpoints, authentication, and Pi model inventory remain local or application-owned.

Configure the sources for the target host before activation. Claude Code's filesystem sandbox declares tool-specific paths, and the Codex Browser modifier changes approval behavior. Check these selections against the host's actual tools and permission requirements. Claude Code model aliases and Pi provider, model, effort, and model inventory remain host-owned. Activation requires explicit approval for permission changes. Rebuild the shared skill registry with `scripts/install-skills` after backing up any existing `~/.agents/skills` content you may need.

The [Agent settings ownership contract](../docs/ownership.md#agent-settings) defines field replacement, shared environment variables, host socket seeds, and explicit retirement. Claude Code's missing socket list starts with 1Password and the sandbox temporary directory; an existing list is retained exactly. Codex preserves local model and provider choices while managing the selected TUI preferences.

Pi's `extensions/session-id-footer.ts` adds the session ID below the working directory while retaining the built-in statistics and extension statuses. It is adapted from [Pi Extensions](https://github.com/Entwining/pi-extensions/blob/687a8cc66ac5f7886e35438ddbb2727fce720e0c/extensions/session-id-footer.ts) under the [MIT license](../licenses/Entwining-MIT.txt). Apply that file as a selected target; the directory remains shared with independently owned extensions, including Agent Guard and Herdr. The footer needs Pi's exported `FooterComponent` API; verify it after Pi upgrades and use `/reload` or a fresh session after deployment.

Run `scripts/validate` from the checkout root for configuration, hook, statusline, and skill checks. `python3 -m unittest discover -s tests -v` runs the configuration, hook, and statusline tests alone. These checks apply the actual modifiers to synthetic temporary destinations, without reading live Agent settings or invoking agents. They do not establish host activation or feature availability.

From the checkout root, run `ruby agent-policy/dot_agents/exact_skills/scripts/validate-skills.rb --smoke` to validate the managed registry and its CLI contracts. Verify instruction and skill loading in fresh sessions of each affected runtime; structural and CLI checks alone do not prove loading. Default home application does not run an Agent policy installer.

## Shared skill ownership

The directories containing `dot_agents/exact_skills/*/SKILL.md` are the complete managed skill registry; `dot_agents/exact_skills/scripts/` contains their shared validator. `~/.agents/skills` is an exact chezmoi target at the top level, and `scripts/install-skills` performs the complete recursive rebuild with `rsync -a --delete`. A selected-target `chezmoi apply` can leave nested files that are not in source; use the script for the registry. Back up the target before the first rebuild; add a skill to source to retain it. Do not edit or commit in the live registry.

Removing a managed skill requires source deletion and a rebuild with `scripts/install-skills`; verify both the source and target are absent and that this is the intended registry. A vendor or local skill that should survive must be added to the source or installed outside `~/.agents/skills`, because the rebuild does not preserve unmanaged siblings.
