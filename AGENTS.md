# mac-dotfiles

This repository manages a personal development environment for Apple Silicon macOS with chezmoi.

Edit this checkout's sources. Homebrew packages are declared in `packages/Brewfile`; language tools retain their own installation and runtime owners.

Before investigation, edits, or deployment, scan the headings in [LESSONS.md](LESSONS.md) and read only sections relevant to the affected component or operation. Skip the body when no section applies.

Before changing a tool's installer, update channel, configuration path, or runtime owner, establish its declared owner in [docs/ownership.md](docs/ownership.md).

Before editing, previewing, applying, or retiring managed configuration, read and follow the [configuration rules](docs/instructions/configuration.md) for source selection, generated files, and recovery copies.

Run `scripts/validate` after changing managed configuration, hooks, skills, or their checks. Before changing tests or validating source or deployment, read and follow the [verification rules](docs/instructions/verification.md) for test coverage and consumer checks.

When changing repository files or reviewing upstreams, read and follow the [maintenance rules](docs/instructions/maintenance.md) for documentation, lessons, and review records.

Before changing Agent instructions, skills, hooks, or runtime settings, read and follow the [Agent configuration rules](docs/instructions/agents.md) for host requirements, registry ownership, and loading checks.
