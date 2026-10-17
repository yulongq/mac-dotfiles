# Lessons from configuration work

These lessons record verified failure mechanisms from this repository's reviews. Each starts with a rule, explains why it matters, and records the supporting observations. Repeated incidents extend the existing lesson; a deterministic check belongs in the owning test or workflow, with its rationale retained here. The initial observations come from the 2026-10-17 review of `71397d3` and its subsequent corrections, not a complete review of upstream history.

## The effective configuration source

**Complete a driver migration at the default entry point and every reader that resolves ownership.** Applying with an explicit source can leave bare commands on the previous repository. Selecting the home source also leaves the independent Agent source outside the default lookup. Verify the effective default and both source lookups through the [source-selection procedure](docs/lifecycle.md#select-the-default-source).

At review time, the explicit `sourceDir` setting still selected the previous checkout. Its run scripts remained eligible for a bare apply. The apply workflow had told agents to preserve that default, contradicting the migration outcome; the pre-edit hook also depended on it. The default directory's presumed symlink was not the controlling input.

## Source paths inside a Git checkout

**Test path resolution with the repository's actual source layout.** chezmoi's `sourceDir` and `workingTree` serve different purposes: the nested `agent-policy/` source shares the enclosing Git working tree. A fixture where those paths coincide cannot detect confusing them. Source-relative hook paths must resolve from `sourceDir`; repository-relative package paths can require `workingTree`.

During the split-source hook repair, mock checks passed while a real Git layout exposed the wrong roots. `test_pre_edit_hook_resolves_both_sources_inside_a_git_checkout` in [the hook suite](tests/test_agent_hooks.py) now exercises that distinction and the managed home, Agent instruction, partial settings, skill, and unmanaged cases.

## Deployment and actual use

**Prove the selected live inventory and the consumer separately from rendering.** Include absent targets, symlinks, and modes in the [deployment check](docs/lifecycle.md#validate). A clean target still needs the consumer's runtime check: shell command resolution, hook registration and decisions, or instruction discovery and loading. Record which boundary was checked.

The live home was missing `~/Brewfile` and the managed `new-branch` skill despite passing temporary-home tests. `bb` consequently failed, and the source did not preserve the intended Homebrew directory mode. These are deployment gaps that synthetic rendering alone cannot detect.

**Declare the implementation a helper needs and run that helper through the installed shell.** A command name's presence does not establish support for its flags. `ct` needed Universal Ctags while the shell found BSD ctags. Its repair required the package declaration, actual installation, fresh-shell resolution, and generation of project and Bundler dependency tags.

## The validation entry point

**Put regression checks in the command that maintainers actually run.** [scripts/validate](scripts/validate) is the shared entry point for configuration, hook, statusline, and skill checks. Adding a test file requires connecting it to that gate and accounting for its dependencies; running a subset does not establish that the gate passed.

The Claude Code shell suites were outside the standard runner, and Codex tests depended on undeclared, unavailable Bun. The repair integrated the shell suites and Codex contracts into the existing Python runner and connected the complete command to the local pre-push hook. That gate still does not prove host activation.

## Shared skill ownership

**Define the shared skill registry as an exact output of source.** The [shared skill ownership contract](agent-policy/README.md#shared-skill-ownership) makes `~/.agents/skills` the target of `agent-policy/dot_agents/exact_skills`; [scripts/install-skills](scripts/install-skills) rebuilds it recursively with `rsync -a --delete`, while a selected-target chezmoi apply can leave nested extras. Back up the target before the first rebuild; add a skill to source to retain it; never edit or commit in the live registry. Retiring a skill is source deletion plus a rebuild, with target verification.

The live registry contained the managed skills and an independent Git working tree with uncommitted changes alongside unmanaged siblings. The follow-up backed up the pre-change registry and made the target a repo-rebuilt registry instead of preserving unowned siblings.

## Upstream review coverage

**Record selective adoption without inventing complete review coverage.** Under the [upstream review contract](.agents/skills/review-upstreams/SKILL.md#establish-the-comparison), `observed_revision` records discovery, `reviewed_through` records fully accounted coverage, and `pending` records unresolved work with a reconsideration condition. Reconcile those records when adopting changes; an empty cursor needs the initial capability review before it can advance.

The follow-up recovered the selected Pi footer and Herdr sidebar adoption, but could not establish a reconciled initial baseline. The later baseline review inspected the current `liby` and `joshukraine` trees at their pinned revisions, recorded the durable accepted and rejected layers in [ownership](docs/ownership.md#upstream-baseline), set `reviewed_through` to those revisions, and left unresolved candidates in `pending`; history before those revisions remains out of scope.

## Evidence boundaries

**Choose exact non-secret targets before live drift checks, and leave unread scope unverified.** A directory can contain protected inputs even when only a managed child concerns the task. A guard denial provides no evidence of cleanliness; an unread file provides no evidence about its contents.

The review established that the shell sourced `~/.env`, not that it contained credentials. During the follow-up, a check including all of `~/.config` was blocked: the selected targets were checked, while whole-home drift remained unverified. Neither gap justifies reading protected inputs or retrying a blocked action through another path.
