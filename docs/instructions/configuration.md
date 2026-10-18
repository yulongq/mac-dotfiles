# Configuration changes

## Sources and generated files

`.chezmoiroot` selects `home/`; packages, tests, documentation, and Agent configuration are outside default deployment. Keep ordinary deployable files under `home/` in chezmoi's destination layout and package declarations under `packages/`. Agent configuration has its own source under `agent-policy/`.

Abbreviations belong in `home/.chezmoidata/abbreviations.yaml`; the Zsh target is generated at render time, so do not re-add its installed output or introduce a second generator. Re-adding a templated destination would replace the template, so edit its source directly.

## Preview and apply

From the checkout root, select ordinary home configuration with `chezmoi --source "$PWD"`. For Agent targets, satisfy [their host configuration requirements](../../agent-policy/README.md) before selecting them and use `chezmoi --source "$PWD/agent-policy"`.

For each changed non-secret target, inspect `status --exclude=encrypted` and `diff --recursive --exclude=encrypted,scripts` with that exact target and its selected source. Follow the [configuration lifecycle](../lifecycle.md) to preserve recovery copies, coordinate destination writers, apply selected targets, and verify their consumers.

## Migrate or retire

A migration that retires the previous configuration driver includes [default-source selection](../lifecycle.md#select-the-default-source) and verification of the effective source with bare `chezmoi source-path`. Check source-resolving hooks and validators against both `home/` and `agent-policy/`. A preview or selected-target apply alone does not switch the default.

Retirement removes the selected source and destination together after establishing a recovery copy for both; remove the caller and documentation references in the same change. Use `forget` only when the destination is intentionally retained. Follow the [retirement procedure](../lifecycle.md#retire-or-stop-managing) to account for unmanaged descendants and preserve unrelated state.
