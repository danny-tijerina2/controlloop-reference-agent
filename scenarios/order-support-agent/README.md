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
| `src/order_support/` | **The agent itself.** The loop, the three tools, the delegation, and the MCP server the declarations above describe |
| `stubs/` | In-process stand-ins for the orders API, the mail service, and the billing agent. No socket is ever opened |
| `tests/` | Including a parity suite that reads the artifacts above and fails if the code drifts from them |
| `SCAN.md` | A walkthrough of `init` → `bom` → `scan` → `gate` against this directory, with real recorded output |

## Run it

```
uv sync
uv run order-support
```

No API key, no credential, and no network. The orders API, the mail
service, and the billing agent are in-process stubs.

This matters more than it looks. Until
[controlloop#268](https://github.com/danny-tijerina2/controlloop/issues/268)
this scenario was six files declaring an agent's capabilities and **no
agent** — declarations with nothing behind them, in a repository whose
whole purpose is demonstrating a product built on *evidence over
declarations*. Every capability the artifacts claim is now backed by
code that runs:

- the three card skills are three real tools, each calling the OpenAPI
  operation the spec declares;
- `read_only`, `financial_action`, and `external_communication` in
  `controlloop.yaml` are true of the code, not merely asserted — the
  lookup mutates nothing, the refund moves money in the ledger, and the
  reply leaves through the SES stand-in;
- each tool writes the exact `audit_path` the manifest declares for it;
- `x-controlloop-delegates-to` is resolved at runtime, so deleting that
  declaration really removes the escalation capability.

`tests/test_artifact_parity.py` reads the committed artifacts rather
than restating them, so an artifact and its code cannot drift apart
silently.

Then read [`SCAN.md`](SCAN.md), which walks the same directory through
`init`, `bom`, `scan`, and `gate` with real recorded output.

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

See [`SCAN.md`](SCAN.md) for what each of these produces, explained.
From `cli/` in a checkout of `danny-tijerina2/controlloop`:

```
uv run controlloop scan <path-to-this-directory>
uv run controlloop gate <path-to-this-directory> --evidence-path evidence.json
uv run controlloop diff <path-to-this-directory>
```
