# Repository scope

This repository manages a personal development environment for Apple Silicon macOS. `.chezmoiroot` selects `home/`; packages, tests, documentation, and Agent configuration are outside default deployment. Project documentation describes supported capabilities and operating requirements; keep session-specific history and progress in the conversation.

## Source ownership

Edit this checkout's sources. Read [docs/ownership.md](docs/ownership.md) before changing a tool's installer, update channel, configuration path, or runtime owner.

Upstream revisions in `maintenance/upstreams.toml` supply candidate changes; accepted changes belong in this checkout. Do not edit a reference checkout to make it match this machine.

Keep deployable files under `home/` in chezmoi's destination layout and package declarations under `packages/`. Abbreviations belong in `home/.chezmoidata/abbreviations.yaml`; the Zsh target is generated at render time, so do not re-add its installed output or introduce a second generator.

## Configuration lifecycle

Select this checkout explicitly with `chezmoi --source "$PWD"` from its root. For each changed non-secret target, inspect `status --exclude=encrypted` and `diff --recursive --exclude=encrypted,scripts` with that exact target. Re-adding a templated destination would replace the template, so edit its source directly.

Retirement removes the selected source and destination together after establishing a recovery copy for both; remove the caller and documentation references in the same change. Use `forget` only when the destination is intentionally retained. The command sequence and recovery requirements are in [docs/lifecycle.md](docs/lifecycle.md).

## Verification

Run `python3 -m unittest discover -s tests -v` after changing managed configuration. These checks use temporary destinations and synthetic runtime inputs; they do not prove real project builds, GUI behavior, or Agent instruction loading. Validate the affected real consumer after applying its configuration.

Keep each Markdown prose paragraph on one physical line. Preserve third-party license notices and record intentional ownership or behavior changes in the corresponding documentation.

## Agent configuration

`agent-policy/` is configured independently for each host. Read [its configuration requirements](agent-policy/README.md) before selecting any of its targets. Behavior-bearing instructions and skills retain their owner at [write-skill](agent-policy/dot_agents/skills/write-skill/SKILL.md); keep application code cleanup separate from instruction changes.

Repository workflows live in `.agents/skills/` and stay outside deployment; `.claude/skills` is a relative link to that same directory. For these skills, run `ruby agent-policy/dot_agents/skills/scripts/validate-skills.rb --root .agents/skills --smoke`. For shared deployable skills under `agent-policy/dot_agents/skills/`, run the validator without `--root`. Run the affected runtime loading checks, and distinguish structural and CLI validation from evidence that a new session loaded the intended instructions.
