# Scenario: capability reduction

Branch `scenario/capability-reduction`, for ControlLoop issue
[#103](https://github.com/danny-tijerina2/controlloop/issues/103)
(E10.7).

## The change

Against the declared base on `main`, this branch:

- **removes a tool** — the `purge-ticket-history` skill is deleted from
  `agent-card.json`;
- **narrows a permission** — `dynamodb:DeleteItem` and `s3:DeleteObject`
  are dropped from `iam/policy.json`.

Nothing is gained. Authority only shrinks.

## Real recorded output

```
$ controlloop gate scenarios/support-triage-agent
! WORST REACHABLE  sensitive-data-access: support-triage-agent can invokes Read
  a customer record

✓ PASSED

• REDUCED  destructive-action: support-triage-agent no longer invokes Purge
  ticket history
• REDUCED  sensitive-data-access: support-triage-agent no longer invokes Purge
  ticket history
• REDUCED  write-access: support-triage-agent no longer invokes Purge ticket
  history
✓ PASSED   capability reduced only -- no new authority gained

• no findings

$ echo $?
0
```

Each REQ of #103, against that output:

| | |
| --- | --- |
| REQ-1 | a tool removed and a permission narrowed |
| REQ-2 | the gate passes, exit 0 |
| REQ-3 | each reduction named **by material class** — `destructive-action`, `sensitive-data-access`, `write-access` |
| REQ-4 | `• no findings` — the reduction produces none |

## Why this needed issue #255 first

Naming a reduction by material class needs a `MaterialChangeSummary`,
which needs both sides' full graphs, which only the merge-base baseline
path builds. That path refused to run for any scan root that was a
subdirectory of a repository rather than a repository itself — which is
every scenario here. The lines above were unreachable until
[#255](https://github.com/danny-tijerina2/controlloop/issues/255) was
fixed.

It is also why the base scenario deliberately carries **no committed
baseline**: a committed baseline holds only `effective_authority`, not
the graphs, and short-circuits the merge-base path.
