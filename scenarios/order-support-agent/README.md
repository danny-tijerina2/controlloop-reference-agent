# order-support-agent

The base reference scenario (issue
[controlloop#99](https://github.com/danny-tijerina2/controlloop/issues/99),
E10.3). Every other scenario in this repository is a variation built on
top of this one — this is the "current, approved" starting point they
diff against, not a finished or hardened example.

## What it is

A fictional internal customer-support assistant for "Widgetworks," a
made-up online store. It looks up orders, issues refunds, and replies to
support tickets, escalating disputed charges to a separate billing
agent. Nothing here is a real company, a real credential, or code copied
from anywhere.

| File | Declares |
| --- | --- |
| `agent-card.json` | The primary agent (A2A Agent Card), its skills, and a delegation edge to the sub-agent below |
| `sub-agents/billing-escalation/agent-card.json` | The delegated sub-agent |
| `.mcp.json` | The MCP server the agent uses for its order/refund/email tools |
| `openapi/orders-api.yaml` | The internal orders service the agent calls |
| `iam/policy.json` | The AWS-shaped IAM policy granting the agent's runtime identity its permissions |
| `controlloop.yaml` | The security manifest: a trust boundary, one approval record, one prohibited capability, a data classification, a capability ceiling, and a logged-tool declaration |
| `.controlloop/baseline.json` | The committed, approved baseline (REQ-5) — see below |

## It is not clean on purpose

`controlloop scan` against this directory currently reports **3 MEDIUM
`policy.undeclared-tools` findings** (the agent's `lookup-order`,
`issue-refund`, and `reply-to-customer` skills are reachable but not
individually declared in `controlloop.yaml`) and otherwise **passes**.
That's deliberate, not an oversight: a real team's manifest drifts out
of sync with reality, and a real "approved" baseline is rarely
spotless — it is whatever was actually reviewed and accepted, known
gaps included. This is the state the committed baseline below
attests to.

## Baseline and approval provenance (REQ-5)

`.controlloop/baseline.json` was generated for real, from this exact
directory, using the `controlloop` CLI's own internal
`compute_effective_authority`/baseline-serialization functions (the
CLI itself has no `baseline`-writing subcommand yet — see
`docs/reference/baseline-artifact-format.md` in the main repo), not
hand-written. Its `provenance` block records who approved it, when,
and at what commit of this repository. `controlloop diff` and
`controlloop gate` both resolve it automatically with no flag needed.

## Regenerating

From `cli/` in a checkout of `danny-tijerina2/controlloop`:

```
uv run controlloop scan <path-to-this-directory>
uv run controlloop gate <path-to-this-directory> --evidence-path evidence.json
uv run controlloop diff <path-to-this-directory>
```
