---
name: apply-config
description: Apply this mac-dotfiles repository's configuration to the local Mac and verify the selected consumers. Use for a full home configuration apply, a selected tool or file, an explicitly selected Agent configuration, or a deployment preview. Not for discovering upstream changes or installing software.
---

# Apply configuration

Resolve this repository from the skill directory's `../../..`, including when invoked from another working directory. Read its `AGENTS.md` and establish the selected source and destination before running chezmoi. An apply request authorizes the requested configuration changes; it does not by itself authorize changed Agent permissions, credential operations, package installation, or changes to another application's update owner. A preview request ends before writes.

## Select the deployment

1. Read [configuration ownership](../../../docs/ownership.md) and the relevant [setup prerequisites](../../../docs/setup.md). Use the requested tool, paths, or configuration group. With no narrower target, inventory the ordinary `home/` configuration as the requested group; do not silently include `agent-policy/`. Establish existing files, directory symlinks, unmanaged children, and local overrides before selecting directory targets. Report the concrete target list and any excluded targets with their reasons.
2. Use `config_source="$repo"` for ordinary configuration: `.chezmoiroot` selects `home/`. For explicitly selected Agent targets, read [their host requirements](../../../agent-policy/README.md) and use `config_source="$repo/agent-policy"`. Resolve each selected target with `chezmoi --source "$config_source" source-path "$target"`; a source owned by another checkout is not a reason to edit that checkout. Keep the active default chezmoi source unchanged.
3. Inspect the selected source's templates, modifiers, external declarations, and consumers. External archives can have a virtual `source-path` with no physical file; their owner is the corresponding entry in `home/.chezmoiexternal.toml`. Identify fields that source replaces, fields it preserves, and application write-back behavior. For Agent settings, include local model/provider choices, host socket lists, generated fields, and unique skills in the preservation contract. Verify template data and installed prerequisites through their normal clients; never obtain missing values by reading a credential store or declared environment file.

## Prepare and review

Run the repository's validation command from its root. The tests use synthetic destinations; a pass is preparation, not evidence that the real host has loaded the configuration.

For each selected non-secret target, use the [scoped lifecycle checks](../../../docs/lifecycle.md#validate):

```sh
chezmoi --source "$config_source" --refresh-externals=never status --exclude=encrypted "$target"
chezmoi --source "$config_source" --refresh-externals=never diff --recursive --exclude=encrypted,scripts "$target"
```

Read `-` as destination-only and `+` as rendered-source-only. Account for unrelated local changes and every child of a replaced directory symlink. A clean modifier diff can still preserve an obsolete undeclared field; inspect the selected field's actual presence when retirement is part of the request. Keep secrets and ciphertext out of previews and recovery copies; a mixed file whose protected bytes cannot be kept in place follows the ownership contract's user-operated edit boundary.

Before writing, state which behavior changes and preserve independent recovery copies of selected non-secret content and symlink targets. Keep recoverable state outside the checkout and report its location; do not delete the only copy needed to undo a replaced destination. Review any changed permission or approval settings as a separate authorization item, using the actual proposed delta. Continue independent authorized targets while that item is pending.

## Apply and activate

Establish one writer and bind the write to the reviewed source and destination according to [the apply procedure](../../../docs/lifecycle.md#apply). A hash check followed by an uncoordinated write does not prevent a race. If the application or another editing session cannot be coordinated, leave that target pending. Do not stop an in-use application to manufacture quiescence.

Once a target's prerequisites, recovery copy, diff, and authorization are satisfied:

```sh
mkdir -p "$(dirname "$target")"
chezmoi --source "$config_source" --refresh-externals=never apply --exclude=encrypted,scripts "$target"
chezmoi --source "$config_source" --refresh-externals=never status --exclude=encrypted "$target"
```

Select required pinned external directories explicitly alongside their consumers; applying a shell file alone does not install its plugins. Package installation, credential setup, and lifecycle scripts remain separate actions. If a call fails or its result is uncertain, inspect the resulting target before deciding whether to resume, restore the selected backup, or retry; do not rerun the whole group blindly.

Verify both the intended change and the preservation contract, then check for unexplained drift on a repeated apply. Reload or restart the actual consumer when that is safe: a new login shell for shell behavior, the selected application for its UI or configuration, and a fresh session of each affected Agent host for settings and instruction loading. Verify CLI and Desktop separately when both consume a setting; a nested process under another agent's sandbox cannot establish the normal host's behavior. Report unavailable runtime checks as unfinished validation, with the exact blocker.

## Completion

Report each target's source, destination, change, recovery location, and evidence as `runtime-verified`, `applied; activation pending`, `previewed only`, or `deferred`. An empty diff, successful parse, or zero exit code is not a runtime verdict. Include preserved local differences and any remaining prerequisite; do not compress a partly applied group into an overall success. Keep commits and pushes outside the task unless requested or required by the authorized delivery.
