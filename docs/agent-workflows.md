# Agent workflow baseline

The [workflow catalog](../maintenance/agent-workflows.toml) records bounded historical tasks, their requested outcomes, transcript evidence, and observable follow-ups. These are diagnostic cases, not held-out acceptance trials. The sample is deliberately selected and its historical configuration is unverified; neither an overall success rate nor a causal claim about the current instructions follows from it. `reported-complete` means the transcript contains that report, not that its product outcome was independently verified.

Refresh the local session index, then collect the metrics through [the measurement command](../scripts/measure-agent-workflows):

```sh
sessidx index
artifact_dir=$(mktemp -d "$TMPDIR/mac-dotfiles-workflows.XXXXXX")
scripts/measure-agent-workflows > "$artifact_dir/metrics.json"
```

The command runs read-only `sessidx sql` queries and records the installed CLI version and hashes of the collector and catalog. It never starts an agent or replays a task. It requires one indexed main transcript per case and verifies that the cited evidence lines exist. Incomplete or stale index results fail the command instead of becoming zero counts. Use `--cases PATH` to measure a different catalog with the same fields.

Each case is bounded by `first_line` and `last_line`. Check the native records after the final response: Codex can write that response's usage in a separate later record, while the sampled Claude Code and Pi messages carry their usage inline. Include the task's trailing usage without crossing into the next request. Tool-call outcomes come from `call_outcomes`, retaining failed, successful, and unknown populations separately. Usage is grouped by the model of each recorded pass; every token sum includes its recorded-pass count. An empty usage list means no pass usage was available. Input, cache-read, and cache-write tokens are separate, and reasoning tokens are already included in output. No latency or billing estimate is generated: transcript time includes human pauses, and token records do not establish the billed route.

The measurement output includes the transcript path for `sessidx show PATH:LINE --around 0`. Original records remain authoritative. The catalog's observations distinguish a user correction from a scope decision, a follow-up question, an interruption, and a reported blocker; none is inferred from the number of user messages.

For a future instruction change, freeze the candidate bytes, runtime-visible catalog, and cases before execution, and follow the [behavioral evaluation protocol](../agent-policy/dot_agents/exact_skills/write-skill/references/evaluation.md). Historical observations select regressions; fresh, separately held-out cases establish acceptance. A static check of this catalog only checks its structure and evidence bounds.
