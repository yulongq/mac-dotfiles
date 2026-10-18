# Linux port review

Review of `feat/linux-port` at `6d62792645570d1ecd6f24e992d747b4a6bcb800`, compared with `main` at `e0ac7b97976f4f8ffead9474f8cc74210b9126ee`. The branch adds only `docs/linux-port.md`; the findings concern the proposed implementation and acceptance criteria. No Linux port implementation is present in this revision.

The review identified two P2 findings and one P3 finding. The installation and validation design needs correction before implementation follows the plan.

## P2: Installation commands do not preserve the no-upgrade contract

When a declared package is already installed at an older version, the [installer commands proposed in `docs/linux-port.md:163`](https://github.com/yulongq/mac-dotfiles/blob/6d62792645570d1ecd6f24e992d747b4a6bcb800/docs/linux-port.md#L163) can upgrade it. The plan uses `apt-get install -y` and `pacman -S --needed`, although its [package-manager constraints require preserving `bb`'s `--no-upgrade` semantics](https://github.com/yulongq/mac-dotfiles/blob/6d62792645570d1ecd6f24e992d747b4a6bcb800/docs/linux-port.md#L157).

[APT's `install` command upgrades specified packages when newer versions are available](https://manpages.debian.org/trixie/apt/apt-get.8.en.html); its `--no-upgrade` option prevents already-installed command-line targets from being upgraded. [pacman's `--needed` option only skips targets that are already up to date](https://man.archlinux.org/man/pacman.8.en), so it does not preserve an older installed version. Avoiding a whole-system upgrade does not satisfy the stated constraint.

Define how each package-manager path installs missing declarations while preserving existing installations, and verify the case where a declared package has an older installed version. The current commands do not establish that behavior.

## P2: The minimal dependency set cannot run the complete validation gate

On a clean Linux container, the [nine-package `--minimal` set in `docs/linux-port.md:163`](https://github.com/yulongq/mac-dotfiles/blob/6d62792645570d1ecd6f24e992d747b4a6bcb800/docs/linux-port.md#L163) does not supply everything needed by the [container validation jobs proposed at line 180](https://github.com/yulongq/mac-dotfiles/blob/6d62792645570d1ecd6f24e992d747b4a6bcb800/docs/linux-port.md#L180).

The [shell contract test starts an interactive login shell and rejects missing-command errors](https://github.com/yulongq/mac-dotfiles/blob/6d62792645570d1ecd6f24e992d747b4a6bcb800/tests/test_dotfiles.py#L195), while [shell startup invokes `fzf` and `zoxide`](https://github.com/yulongq/mac-dotfiles/blob/6d62792645570d1ecd6f24e992d747b4a6bcb800/home/dot_zshrc#L69). Neither tool appears in the minimal set.

The [validation entry point also unconditionally runs the shared skill CLI smoke checks](https://github.com/yulongq/mac-dotfiles/blob/6d62792645570d1ecd6f24e992d747b4a6bcb800/scripts/validate#L5). Their [command inventory requires `ctx7`, `gh`, `glab`, `herdr`, `codex`, `oracle`, and `sessidx`](https://github.com/yulongq/mac-dotfiles/blob/6d62792645570d1ecd6f24e992d747b4a6bcb800/agent-policy/dot_agents/exact_skills/scripts/validate-skills.rb#L88). A [missing executable is recorded as an error](https://github.com/yulongq/mac-dotfiles/blob/6d62792645570d1ecd6f24e992d747b4a6bcb800/agent-policy/dot_agents/exact_skills/scripts/validate-skills.rb#L279), and [any recorded error makes the validator exit with status 1](https://github.com/yulongq/mac-dotfiles/blob/6d62792645570d1ecd6f24e992d747b4a6bcb800/agent-policy/dot_agents/exact_skills/scripts/validate-skills.rb#L297).

Include the complete dependency set and its installation sources, or explicitly define separate validation jobs with the prerequisites each requires. The planned PATH and platform-assertion changes alone do not make the proposed minimal container jobs pass the complete gate.

## P3: The render-matrix design assumes an unsupported chezmoi limitation

The [render-matrix proposal in `docs/linux-port.md:178`](https://github.com/yulongq/mac-dotfiles/blob/6d62792645570d1ecd6f24e992d747b4a6bcb800/docs/linux-port.md#L178) states that `--override-data` cannot override `.chezmoi.os` and uses that premise to justify a separate `.platform` data key.

An isolated probe with chezmoi 2.73.2 on macOS returned `darwin` for `{{ .chezmoi.os }}` without an override and `linux` with `--override-data '{"chezmoi":{"os":"linux"}}'`. Both calls exited successfully. This version satisfies the repository's minimum requirement of chezmoi 2.73.1 or newer, and the result contradicts the claimed limitation.

Correct the premise and use the existing override mechanism to exercise OS-dependent template branches. A separate platform selector is not required for that purpose. Template branch coverage still does not establish native Linux runtime behavior.

## Verification scope

The review checked the branch diff, the relevant source consumers and validation paths, the package-manager documentation, and isolated chezmoi probes. `git diff --check` passed, and all eight relative links in the reviewed plan resolved to existing files and headings. The original review did not run the complete `scripts/validate` gate or Linux container acceptance checks. Linux installation and runtime activation remain unverified.
