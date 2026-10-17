# Agent configuration

This directory contains shared instructions, managed skills, hooks, and partial-configuration modifiers for Agent runtimes. It is outside `.chezmoiroot` and is applied independently from the default home configuration. Provider endpoints, authentication, and Pi model inventory remain local or application-owned.

Configure the sources for the target host before activation. The Claude Code template requires machine data and its filesystem sandbox still declares tool-specific paths, the Codex Browser modifier changes approval behavior, and the Pi settings declare provider and model defaults. Check these selections against the host's actual tools, routes, and permission requirements. Activation requires explicit approval for permission changes. Preserve unique installed skills and vendor-managed skill ownership instead of replacing the whole live registry.

The [Agent settings ownership contract](../docs/ownership.md#agent-settings) defines field replacement, shared environment variables, host socket seeds, and explicit retirement. Claude Code's missing socket list starts with 1Password and the sandbox temporary directory; an existing list is retained exactly. Codex preserves local model and provider choices while managing the selected TUI preferences.

Run `python3 tests/test_agent_config.py` from the checkout root for the isolated configuration checks, or `python3 -m unittest discover -s tests -v` for the complete suite. These checks apply the actual modifiers to synthetic temporary destinations, without reading live Agent settings or invoking agents. They do not establish host activation or feature availability.

From the checkout root, run `ruby agent-policy/dot_agents/skills/scripts/validate-skills.rb --smoke` to validate the managed registry and its CLI contracts. Verify instruction and skill loading in fresh sessions of each affected runtime; structural and CLI checks alone do not prove loading. Default home application does not run an Agent policy installer.
