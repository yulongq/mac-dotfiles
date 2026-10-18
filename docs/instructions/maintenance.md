# Repository maintenance

## Documentation and lessons

Keep each Markdown prose paragraph on one physical line. Preserve third-party license notices and record intentional ownership or behavior changes in the corresponding documentation. Project documentation describes supported capabilities and operating requirements; keep session-specific history and progress in the conversation.

During authorized corrective work, update the corresponding entry in [LESSONS.md](../../LESSONS.md) or add one when the evidence establishes a failure mechanism; include its rule, cause, and evidence. Keep detailed procedures and automated checks at their existing owners; lessons explain why those checks matter.

## Upstream changes

Upstream revisions in `maintenance/upstreams.toml` supply candidate changes; accepted changes belong in this checkout. Do not edit a reference checkout to make it match this machine.

Authorized adoption includes reconciling the inspected revision and unresolved work in that manifest; `reviewed_through` records accounted review coverage, independently of which changes were adopted. Read-only reviews report proposed record changes without writing them.
