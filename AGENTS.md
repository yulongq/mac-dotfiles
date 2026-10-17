# Repository scope

This repository manages a personal development environment for Apple Silicon macOS. `.chezmoiroot` selects `home/`; packages, tests, documentation, and Agent configuration are outside default deployment. Project documentation describes supported capabilities and operating requirements; keep session-specific history and progress in the conversation.

## Lessons

Read [LESSONS.md](LESSONS.md) at the start of each repository task. During authorized corrective work, update the corresponding lesson or add one when the evidence establishes a failure mechanism; include its rule, cause, and evidence. Keep detailed procedures and automated checks at their existing owners; lessons explain why those checks matter.

## Source ownership

Edit this checkout's sources. Read [docs/ownership.md](docs/ownership.md) before changing a tool's installer, update channel, configuration path, or runtime owner.

Upstream revisions in `maintenance/upstreams.toml` supply candidate changes; accepted changes belong in this checkout. Do not edit a reference checkout to make it match this machine. Authorized adoption includes reconciling the inspected revision and unresolved work in that manifest; `reviewed_through` records accounted review coverage, independently of which changes were adopted. Read-only reviews report proposed record changes without writing them.

Keep deployable files under `home/` in chezmoi's destination layout and package declarations under `packages/`. Abbreviations belong in `home/.chezmoidata/abbreviations.yaml`; the Zsh target is generated at render time, so do not re-add its installed output or introduce a second generator.

## Configuration lifecycle

Select this checkout explicitly with `chezmoi --source "$PWD"` from its root. For each changed non-secret target, inspect `status --exclude=encrypted` and `diff --recursive --exclude=encrypted,scripts` with that exact target. Re-adding a templated destination would replace the template, so edit its source directly.

A migration that retires the previous configuration driver includes [default-source selection](docs/lifecycle.md#select-the-default-source) and verification of the effective source with bare `chezmoi source-path`. Check source-resolving hooks and validators against both `home/` and `agent-policy/`. A preview or selected-target apply alone does not switch the default.

Retirement removes the selected source and destination together after establishing a recovery copy for both; remove the caller and documentation references in the same change. Use `forget` only when the destination is intentionally retained. The command sequence and recovery requirements are in [docs/lifecycle.md](docs/lifecycle.md).

## Verification

Run `scripts/validate` after changing managed configuration, hooks, skills, or their checks. New regression suites must be reachable from this command and use declared dependencies. Reproduce the relevant source and Git layout when testing path resolution. The gate uses temporary destinations and synthetic runtime inputs; it does not prove live deployment, real project builds, GUI behavior, or Agent instruction loading.

After applying configuration, reconcile the selected live targets with `scripts/check-home home TARGET...` or `scripts/check-home agent-policy TARGET...`, including missing files, symlink destinations, and intended modes, then validate the affected real consumer. Check a shell helper's resolved executable and required options in a fresh login shell. Report unresolved deployment or activation per target; a blocked check does not establish a clean result for its scope.

Keep each Markdown prose paragraph on one physical line. Preserve third-party license notices and record intentional ownership or behavior changes in the corresponding documentation.

## Agent configuration

`agent-policy/` is configured independently for each host. Read [its configuration requirements](agent-policy/README.md) before selecting any of its targets. For skill deployment, reconcile the selected source inventory with installed targets, preserving independently owned siblings and the shared registry's Git state. Behavior-bearing instructions and skills retain their owner at [write-skill](agent-policy/dot_agents/skills/write-skill/SKILL.md); keep application code cleanup separate from instruction changes.

Repository workflows live in `.agents/skills/` and stay outside deployment; `.claude/skills` is a relative link to that same directory. `scripts/validate` runs the skill validator for both this directory and `agent-policy/dot_agents/skills/`. Run the affected runtime loading checks, and distinguish structural and CLI validation from evidence that a new session loaded the intended instructions.
