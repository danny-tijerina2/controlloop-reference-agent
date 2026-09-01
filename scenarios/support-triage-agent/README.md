# support-triage-agent

The declared base for the **capability reduction** scenario
(ControlLoop issue
[#103](https://github.com/danny-tijerina2/controlloop/issues/103),
E10.7).

> **⚠️ Deliberately over-privileged. Never deploy this.**

## What it is

A ticket-triage agent that reads tickets, reads customer records, and
can permanently purge a customer's ticket history. Its IAM policy grants
`dynamodb:DeleteItem` on the tickets table and `s3:DeleteObject` on the
customer-records bucket.

`Purge ticket history` is declared `destructive: true`, so the agent's
worst reachable capability is a destructive action.

## Why it has no committed baseline

Deliberate, and load-bearing. `.controlloop/baseline.json` carries only
`effective_authority`, not the full node and edge graphs, so a scenario
with a committed baseline cannot have its material change classified —
`controlloop` reports `material change: not evaluated`.

Without one, the merge-base path engages instead: ControlLoop builds a
real ACBOM of this directory as it was at the merge base and compares
both graphs. That is what makes a reduction reportable at all. See
[controlloop#255](https://github.com/danny-tijerina2/controlloop/issues/255).

## The scenario built on it

[`scenario/capability-reduction`](https://github.com/danny-tijerina2/controlloop-reference-agent/tree/scenario/capability-reduction)
removes the purge tool and narrows the IAM policy, and the gate passes
while naming what was given up.
