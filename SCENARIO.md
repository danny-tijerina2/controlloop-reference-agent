# Scenario: capability expansion

Proves [ControlLoop issue #100](https://github.com/danny-tijerina2/controlloop/issues/100)
(E10.4), the scenario named in ControlLoop's own MVP acceptance line:

> The reference repo is published, and a PR that adds a refund tool is
> **blocked in CI** with a blast-radius sentence, a capability path, and
> a retained evidence artifact.

> **DO NOT MERGE.** This pull request *is* the artifact. Merging it puts
> the expansion onto `main`, which breaks the base scenario for everyone
> who forks this repository and removes the diff the proof depends on.
> That already happened once with the ceiling-breach scenario and had to
> be reverted.

## What the pull request does

Fulfilment keeps failing in batches, and support asked to stop refunding
those orders one at a time. So this pull request adds:

| | Change |
| --- | --- |
| a **tool** | the `bulk-refund-orders` skill, "Bulk refund orders" |
| a **resource** | `POST /orders/bulk-refund` in `openapi/orders-api.yaml` |
| an **identity change** | a `BulkRefundDisbursement` IAM statement granting `payments:CreateDisbursement` and `payments:ApproveDisbursement` on `Resource: "*"` |

It is an entirely reasonable feature request. It is also the single
largest expansion of this agent's authority since it was written, and
nobody reviewing three separate files would necessarily notice that.

The repository is well governed about it, too: the new tool is declared
in `tool_capabilities`, and it has an audit path in `logged_tools`. That
is deliberate — it means the block below is **not** a paperwork failure.
The gate is objecting to the capability itself.

## What the gate does

```
$ controlloop gate scenarios/order-support-agent
! WORST REACHABLE  destructive-action: widgetworks-order-support-agent can
  invokes Bulk refund orders

✕ DEPLOYMENT BLOCKED

✕ HIGH    policy.destructive-or-financial-action: Agent gained new direct
  invokes access to 'Bulk refund orders', classified as destructive-action and
  financial-action.
    at agent-card.json
```

Exit code `1`.

## How to read that

**The blast-radius line changed.** On `main` the worst thing this agent
can reach is `financial-action: ... can invokes Issue a refund`. With
this pull request it becomes `destructive-action: ... can invokes Bulk
refund orders`. The agent's worst case got worse, and the first line of
the report says so before any list of findings.

**The finding is diff-aware.** `change_state` is `added` — the rule is
not objecting to refunds existing, it is objecting to authority this
pull request *introduces* against the approved baseline in
`.controlloop/baseline.json`.

**The capability path names the route**: one `invokes` hop from
`widgetworks-order-support-agent` to `Bulk refund orders`.

## Requirement mapping

| Requirement | Where |
| --- | --- |
| REQ-1: adds a tool, a resource, and an identity change | `agent-card.json`, `openapi/orders-api.yaml`, `iam/policy.json` |
| REQ-2: gate fails with the expected finding, severity, and capability path | `policy.destructive-or-financial-action`, HIGH, one `invokes` hop; exit `1` |
| REQ-3: the blast-radius sentence matches a committed expected string exactly | `expected/capability-expansion.json` → `blocking_run.blast_radius` |
| REQ-4: the evidence artifact is produced and retained | `gate --evidence-path`, written on every run including a failing one; the release gate uploads it |

`expected/capability-expansion.json` holds the committed expectations,
produced by a real run and asserted by the end-to-end proof in
ControlLoop issue #104.
