# Lessons from configuration work

These lessons record verified failure mechanisms from this repository's reviews. Each starts with a rule, explains why it matters, and records the supporting observations. Repeated incidents extend the existing lesson; a deterministic check belongs in the owning test or workflow, with its rationale retained here. The initial observations come from the 2026-10-17 review of `71397d3` and its subsequent corrections, not a complete review of upstream history.

## The effective configuration source

**Complete a driver migration at the default entry point and every reader that resolves ownership.** Applying with an explicit source can leave bare commands on the previous repository. Selecting the home source also leaves the independent Agent source outside the default lookup. Verify the effective default and both source lookups through the [source-selection procedure](docs/lifecycle.md#select-the-default-source).

At review time, the explicit `sourceDir` setting still selected the previous checkout. Its run scripts remained eligible for a bare apply. The apply workflow had told agents to preserve that default, contradicting the migration outcome; the pre-edit hook also depended on it. The default directory's presumed symlink was not the controlling input.

## Source paths inside a Git checkout

**Test path resolution with the repository's actual source layout.** chezmoi's `sourceDir` and `workingTree` serve different purposes: the nested `agent-policy/` source shares the enclosing Git working tree. A fixture where those paths coincide cannot detect confusing them. Source-relative hook paths must resolve from `sourceDir`; repository-relative package paths can require `workingTree`.

During the split-source hook repair, mock checks passed while a real Git layout exposed the wrong roots. `test_pre_edit_hook_resolves_both_sources_inside_a_git_checkout` in [the hook suite](tests/test_agent_hooks.py) now exercises that distinction and the managed home, Agent instruction, partial settings, skill, and unmanaged cases.

## Deployment and actual use

**Exclude unrelated external archives before asking chezmoi for the managed inventory.** With an empty cache, chezmoi resolves missing archives even with `--refresh-externals=never`. The [offline deployment test](tests/test_deploy.py) previews and applies ordinary files with a cold cache and an unreachable proxy. Selecting a Zsh or tmux archive still requires that archive.

**Prove the selected live inventory and the consumer separately from rendering.** Include absent targets, symlinks, and modes in the [deployment check](docs/lifecycle.md#validate). A clean target still needs the consumer's runtime check: shell command resolution, hook registration and decisions, or instruction discovery and loading. Record which boundary was checked.

The live home was missing `~/Brewfile` and the managed `new-branch` skill despite passing temporary-home tests. `bb` consequently failed, and the source did not preserve the intended Homebrew directory mode. These are deployment gaps that synthetic rendering alone cannot detect.

**Declare private permissions on modifiers that preserve account state.** Preserving undeclared JSON keys does not preserve the destination's permissions: chezmoi also derives mode from source attributes. The Claude Code account-state modifier lacked `private_` and changed a synthetic `0600` target to `0644`; the live target's metadata also showed `0644`. The [modifier tests](tests/test_agent_config.py) cover new and existing targets, retained account and MCP state, and byte preservation when only permissions need repair.

**Select a directory when deploying its declared permissions.** Applying only child files does not reconcile existing parent-directory modes, and a deep file target can fail before its missing parents are created. OMP's empty-home check applies the managed `.omp` directory before checking its private files and agent directory; a fixture that pre-created parents as `0755` exposed the difference between a file-only apply and the actual directory deployment contract. The [apply workflow](.agents/skills/apply-config/SKILL.md) and [lifecycle procedure](docs/lifecycle.md#apply) require selecting and reviewing managed parent directories when their creation or permissions are part of deployment, then checking their actual modes.

**Exercise both login and interactive shell entry points.** A non-interactive login shell skips `.zshrc`, so initialization held only there does not select the managed toolchains. The isolated shell check resolved Homebrew Node and system Java before the shared login setup; it also exposed duplicate PATH entries because string assignment bypassed Zsh's unique array handling. The shell contract now covers both entry points and preservation of existing login-profile initialization.

**Declare the implementation a helper needs and run that helper through the installed shell.** A command name's presence does not establish support for its flags. `ct` needed Universal Ctags while the shell found BSD ctags. Its repair required the package declaration, actual installation, fresh-shell resolution, and generation of project and Bundler dependency tags.

**Select connected clients when setup targets a running application.** Rex's client list retains disconnected app records after an update. Counting every local app rejected this host's single connected instance. The setup check covers a connected app alongside stale and remote records, and verifies that ambiguity, checksum failure, or rejected theme import stops before preference writes.

**Check both an asynchronous launch and the operation it starts.** Rex's Lua calls return `nil, error`, and a successfully launched close command can still exit unsuccessfully. The close action discarded both outcomes. The [close-action checks](tests/test_rex_close.py) exercise Lua failures and real subprocess launch and exit outcomes behind a stubbed dialog, preserving the selected pane identity and a finite CLI request deadline. Real dialog and focus behavior still require the deployment check.

## Inherited permission rules

**Check effective permission rules before grouping deployment targets, and trace inherited rules before treating them as host decisions.** Claude Code matches Bash deny patterns against the whole command text, so naming a target can block a read-only preview. Check the live rule and its managed source when a call is denied; continue independent authorized targets while leaving the blocked target pending. Permission changes require separate authorization under the [Agent host requirements](agent-policy/README.md).

The initial import in `367426a` inherited `Bash(*.zprofile*)` and `Edit(~/.zprofile*)` from the `liby` baseline. A home deployment combined the login-profile preview with four other targets, so the Bash deny blocked the whole command. The follow-up also stopped the independent targets. Tracing the import and the recorded migration approval established inherited policy and preservation of existing permissions, not a separate host decision to prohibit that file. The host later explicitly approved retiring both rules from the [managed settings fragment](agent-policy/.chezmoitemplates/claude/settings.json) and live settings.

## Local gateways and proxy bypass

**Export loopback exclusions in both `NO_PROXY` and `no_proxy` alongside shell proxy settings.** Clients can honor different variable spellings, and Surge's Global Proxy mode skips the LAN direct rules that protect local gateways in Rule mode. The shared shell contract checks both variables through login and interactive entry points.

Pi's installed network module connected to Surge's HTTP listener without the exclusions and directly to Magpie with them. Sending the local gateway request through the selected remote proxy returned EOF while DeepSeek's API remained reachable through that proxy. Upstream connectivity alone therefore did not establish that the client could reach its local gateway.

**Own caller identity when gateway routing depends on it.** HTTP header names are case-insensitive. OMP's model modifier preserved an existing `User-Agent` or emitted it alongside a differently cased key, so a correct model inventory did not establish the intended Magpie caller. The modifier owns that header while retaining unrelated host settings. The isolated checks exercise both fresh and existing configuration. A real tier check needs Magpie's request record.

## Destructive target paths

**Resolve the effective path before a recursive delete.** A string-prefix check does not constrain a trailing separator, `..`, or a symlinked parent, and `rsync --delete` acts on the resolved location. Resolve `HOME` and the target, require the exact registry path, re-check after creating it, and test rejection with `$HOME/`, `..`, and a symlinked parent while asserting that outside content survives.

The install helper accepted `$HOME/` and paths that resolved outside HOME, deleting a temporary home root and external placeholders. `test_install_skills_rejects_unsafe_targets` now covers those cases.

## The validation entry point

**Put regression checks in the command that maintainers actually run.** [scripts/validate](scripts/validate) is the shared entry point for configuration, hook, statusline, and skill checks. Adding a test file requires connecting it to that gate and accounting for its dependencies; running a subset does not establish that the gate passed.

The Claude Code shell suites were outside the standard runner, and Codex tests depended on undeclared, unavailable Bun. The repair integrated the shell suites and Codex contracts into the existing Python runner and connected the complete command to the local pre-push hook. That gate still does not prove host activation.

**Validate the commit named by the push.** Git supplies the object IDs of the proposed ref updates to `pre-push`. A fixture pushing another tip while the checked-out tip passed exposed that the hook ran the wrong validator. The hook now runs the committed validator in an isolated snapshot of each distinct pushed commit. Use `scripts/validate` separately to check uncommitted work.

**Recheck CLI behavior before advancing a skill's release metadata.** The glab skill still described a raw request body without Content-Type and treated a configured default host as a forced route. The installed CLI supplied JSON Content-Type and used a configured host as a remote preference; isolated requests also exposed the `gitlab.com` default-value exception. The skill correction followed those request and routing observations rather than changing its version record alone.

**Distinguish a clean scan from a scan that did not run.** The output scanner's previous missing-`jq` path exited successfully; its regular expressions also missed a standalone GitLab token and a URL password containing a colon. The hook now uses Gitleaks with local rules, and its tests exercise successful and failed tool output, retained generic formats, placeholders, and missing dependencies without printing synthetic credential values.

## Shared skill ownership

**Define the shared skill registry as an exact output of source.** The [shared skill ownership contract](agent-policy/README.md#shared-skill-ownership) makes `~/.agents/skills` the target of `agent-policy/dot_agents/exact_skills`; [scripts/install-skills](scripts/install-skills) rebuilds it recursively with `rsync -a --delete`, while a selected-target chezmoi apply can leave nested extras. Back up the target before the first rebuild; add a skill to source to retain it; never edit or commit in the live registry. Retiring a skill is source deletion plus a rebuild, with target verification.

The live registry contained the managed skills and an independent Git working tree with uncommitted changes alongside unmanaged siblings. The follow-up backed up the pre-change registry and made the target a repo-rebuilt registry instead of preserving unowned siblings.

**Reconcile both sides after a source rollback, and check nested extras before rebuilding.** A Git reset can remove adopted source while leaving its deployed skills intact. Compare the live files with the prior commit and the user's recorded decisions before deciding which side to retain. The Rex, Herdr, and tldraw reconciliation found exactly this split. A separate temporary-home regression showed that chezmoi status alone missed a destination-only nested skill file; `scripts/check-home` now also uses a recursive rsync dry run to report those extras without removing them.

## Upstream review coverage

**Record selective adoption without inventing complete review coverage.** Under the [upstream review contract](.agents/skills/review-upstreams/SKILL.md#establish-the-comparison), `observed_revision` records discovery, `reviewed_through` records fully accounted coverage, and `pending` records unresolved work with a reconsideration condition. Reconcile those records when adopting changes; an empty cursor needs the initial capability review before it can advance.

The follow-up recovered the selected Pi footer and Herdr sidebar adoption, but could not establish a reconciled initial baseline. The later baseline review inspected the current `liby` and `joshukraine` trees at their pinned revisions, recorded the durable accepted and rejected layers in [ownership](docs/ownership.md#upstream-baseline), set `reviewed_through` to those revisions, and left unresolved candidates in `pending`; history before those revisions remains out of scope.

## External process boundaries

**Pass the pane's server when a Rex action launches a separate CLI.** Rex routes an action's own calls through `ctx.server`, but a detached helper's CLI does not inherit that routing. The close confirmation passed only the session and block, so a remote pane's confirmation targeted the local server. The [close regression checks](tests/test_rex_close.py) failed at both helper and CLI boundaries before the fix and now verify the server alongside the target IDs and request deadline.

## Evidence boundaries

**Choose exact non-secret targets before live drift checks, and leave unread scope unverified.** A directory can contain protected inputs even when only a managed child concerns the task. A guard denial provides no evidence of cleanliness; an unread file provides no evidence about its contents.

The review established that the shell sourced `~/.env`, not that it contained credentials. During the follow-up, a check including all of `~/.config` was blocked: the selected targets were checked, while whole-home drift remained unverified. Neither gap justifies reading protected inputs or retrying a blocked action through another path.

**Keep an unknown measurement distinct from a measured zero.** Claude Code supplies null context usage before its first response and after compaction. Defaulting each missing token count to zero made the statusline report `0%` in both states. The [statusline checks](agent-policy/dot_claude/scripts/statusline.test.sh) distinguish unknown, measured zero, and nonzero usage while retaining the existing percentage calculation.

**Use filenames as classification hints, not proof of secret contents.** The review helper rejected a synthetic presentation path solely because it ended in `.key`, contradicting the purpose-based Protected Inputs contract. Ordinary classifications require non-value host, project, or user evidence; they do not override declared environment inputs, known credential stores, private keys, or ciphertext. The classifier and fix-baseline checks exercise the same classification boundary.
