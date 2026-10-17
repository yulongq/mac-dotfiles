# Configuration lifecycle

chezmoi owns the source-to-destination lifecycle. Run the examples from the checkout root, and select one known non-secret target:

```sh
repo="$PWD"
target="$HOME/.config/example/config.toml"
```

The example path is a placeholder. Establish the target's installation prerequisites and ownership using [environment setup](setup.md), and preserve a recovery copy before replacing live configuration. A directory symlink can lead outside the checkout; inspect its complete ownership before applying any child. Private environment files and credential stores remain outside this workflow. Apply Agent settings only after satisfying [their host configuration requirements](../agent-policy/README.md).

## Select the default source

Set `sourceDir` to this checkout's root; `.chezmoiroot` selects `home/`, so `chezmoi source-path` returns the checkout's `home/` directory. On an existing host, inspect the effective `sourceDir` setting before changing any default-directory symlink: an explicit setting takes precedence. Preserve the old source selection, then change only `sourceDir` in the existing chezmoi configuration to this checkout. Retain encryption settings and unrelated template data. If no configuration exists, create a minimal configuration with this `sourceDir`.

Verify `chezmoi source-path` and `chezmoi source-path ~/.zshrc` after selection. Selecting the default does not apply files or run lifecycle scripts. Agent targets still require `--source "$repo/agent-policy"`; the deployed Claude Code pre-edit hook queries both sources explicitly, and must be reapplied if the checkout moves.

## Create or adopt

For a new configuration, create its source under `home/` using [chezmoi's source attributes](https://www.chezmoi.io/reference/source-state-attributes/), such as `home/dot_config/example/config.toml`. To adopt an existing regular non-secret file instead:

```sh
chezmoi --source "$repo" add "$target"
chezmoi --source "$repo" source-path "$target"
```

Review the resulting source and record any new installation or runtime owner in [ownership.md](ownership.md). Do not use `add` or `re-add` to update an existing template: they replace the source with destination content. Edit YAML-backed abbreviations in their data file, retaining the template that generates the installed file.

## Validate

```sh
scripts/validate
chezmoi --source "$repo" --refresh-externals=never status --exclude=encrypted "$target"
chezmoi --source "$repo" --refresh-externals=never diff --recursive --exclude=encrypted,scripts "$target"
```

Read `-` as destination-only and `+` as rendered-source-only. Preserve unrelated destination drift. Scope every real-home status and diff to explicit non-secret targets; `--recursive` is necessary for a directory diff. The test suite alone operates on a complete temporary home. Its lifecycle fixture checks add, source edits, apply, forget, destroy, and preservation of an unmanaged sibling.

Use `scripts/check-home home "$target"` or `scripts/check-home agent-policy "$target"` for a read-only deployment check. Supply explicit non-secret targets; the command exits nonzero for drift or a chezmoi error and prints only status paths, without configuration contents. Modifiers preserve the application-owned values defined in the ownership contract, so those write-backs are clean; reported differences require a scoped diff and an ownership decision. The check does not certify runtime activation. For example, check `~/Brewfile` and `~/.config/homebrew` in the home source, and `~/.agents/skills` in the Agent source.

## Apply

Establish one writer for the selected destination before applying. Coordinate other editing sessions and use the application's own setting API or a quiescent application when it writes this file itself. Re-read the target before writing; if it differs from the reviewed version, regenerate the candidate and review its actual changes. A pre-write hash check alone does not prevent a concurrent write: when writers cannot be coordinated and no atomic version precondition is available, leave deployment pending.

Once the selected group's prerequisites and diff are satisfied:

```sh
mkdir -p "$(dirname "$target")"
chezmoi --source "$repo" --refresh-externals=never apply --exclude=encrypted,scripts "$target"
chezmoi --source "$repo" --refresh-externals=never status --exclude=encrypted "$target"
```

Restart or reload the actual consumer and check its behavior. Apply again and confirm no unexplained drift. A plugin declaration is a separate target: selecting `.zshrc` alone does not install plugin archives. Package installation remains an explicit action owned by `packages/` and the selected package manager.

Record results per target as source-validated, applied but awaiting activation, runtime-verified, or deferred, with the check or blocker. An exit code or parsed configuration proves only that stage. Verify CLI and Desktop hosts separately when both consume the setting; a process launched under another agent's sandbox is not a substitute for the normal host. Do not restart an in-use session merely to upgrade its result label.

## Review upstream changes

The [review-upstreams workflow](../.agents/skills/review-upstreams/SKILL.md) refreshes the sources in `maintenance/upstreams.toml`, compares immutable revisions, evaluates personal applicability, and records authorized decisions. It owns the review cursor and pending-item semantics. A review can recommend changes without adopting them; selected implementation and local deployment follow the requested scope.

Before deploying, compare the actual source and target versions with those validated. If either changed, repeat the affected review and validation. A source-only task finishes with deployment explicitly unperformed; a requested deployment remains incomplete until its required runtime checks pass or a concrete blocker is reported.

## Retire or stop managing

To retain the destination while dropping its source, use [forget](https://www.chezmoi.io/reference/commands/forget/):

```sh
chezmoi --source "$repo" forget "$target"
```

To destroy a retired target, first inspect its exact source and destination, resolve all callers, and verify independent recovery copies for both. Git only protects committed source content; it does not preserve uncommitted source changes or destination drift. Back up only the selected non-secret files, including their type and symlink destination when applicable. For a directory, account for every descendant, including unmanaged files, before choosing recursive removal.

After those checks, [destroy](https://www.chezmoi.io/reference/commands/destroy/) removes the selected source, destination, and chezmoi state:

```sh
chezmoi --source "$repo" destroy "$target"
```

Verify that the selected source and destination are absent, remove obsolete references and declarations, and rerun validation. Do not add `remove_` entries or retirement scripts that could delete later replacements. Removing configuration does not authorize uninstalling its application, deleting application data, or cleaning unlisted packages.

For one field in a shared file, preserve an independent recovery copy of the selected non-secret target, edit the source and that exact destination field, and verify both its absence and the retained values. Do not destroy the containing file. A field removed only from source remains locally owned until this cleanup is completed; do not add a permanent deletion list for a one-time retirement.
