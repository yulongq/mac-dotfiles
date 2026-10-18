# Agent configuration

## Host requirements and ownership

`agent-policy/` is configured independently for each host. Read [its configuration requirements](../../agent-policy/README.md) before selecting any of its targets.

Before authoring or changing behavior-bearing instructions or skills, use [write-skill](../../agent-policy/dot_agents/exact_skills/write-skill/SKILL.md) to preserve their semantic and loading contracts; keep application code cleanup separate from instruction changes.

## Shared skill registry

The shared skill registry is rebuilt from `agent-policy/dot_agents/exact_skills` with `scripts/install-skills`; a selected-target chezmoi apply can leave nested extras. Back up `~/.agents/skills` before the first rebuild, and add a skill to source to retain it. Do not edit or commit in the live registry.

## Repository workflows

Repository workflows live in `.agents/skills/` and stay outside deployment; `.claude/skills` is a relative link to that same directory. `scripts/validate` runs the skill validator for both this directory and `agent-policy/dot_agents/exact_skills/`.

Before validating instruction or skill changes, read the [verification rules](verification.md) and check loading in the affected runtimes.
