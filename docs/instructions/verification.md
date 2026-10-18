# Verification

## Source checks

`scripts/validate` is the shared gate for managed configuration, hooks, skills, and their checks. New regression suites must be reachable from this command and use declared dependencies. Reproduce the relevant source and Git layout when testing path resolution.

The gate uses temporary destinations and synthetic runtime inputs; it does not prove live deployment, real project builds, GUI behavior, or Agent instruction loading.

## Deployment and activation

After applying configuration, reconcile the selected live targets with `scripts/check-home home TARGET...` or `scripts/check-home agent-policy TARGET...`, including missing files, symlink destinations, and intended modes, then validate the affected real consumer. Supply explicit non-secret targets as required by the [deployment check](../lifecycle.md#validate).

Check a shell helper's resolved executable and required options in a fresh login shell. Report unresolved deployment or activation per target; a blocked check does not establish a clean result for its scope.

For Agent instruction or skill changes, run the affected runtime loading checks. Distinguish structural and CLI validation from evidence that a new session loaded the intended instructions.
