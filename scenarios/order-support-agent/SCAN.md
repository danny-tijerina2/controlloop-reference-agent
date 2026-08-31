# Scanning this agent

Every command and every line of output below was really run against this
directory. Nothing here is illustrative.

Prerequisites: Python 3.12, [uv](https://docs.astral.sh/uv/), and the
`controlloop` CLI. Run everything from `scenarios/order-support-agent/`.

---

## 0. Run the agent first

Scanning an agent you have never seen run is an abstraction. Start here:

```
$ uv run order-support
widgetworks-order-support-agent
deliberately over-privileged demo agent -- never deploy this

TCK-501  looked up WW-10041, replied to customer
TCK-502  refunded WW-10042 (status now refunded), replied to customer
TCK-503  escalated WW-10043 to billing-escalation-agent (accepted=True)

2 message(s) would have left the trust boundary via ses:SendEmail
3 orders in the ledger
audit lines written under logs/ -- see controlloop.yaml logged_tools
```

Three support tickets. The agent looked up an order, moved money, mailed
two customers, and handed a disputed charge to a different agent. No API
key, no credential, and no socket: the orders API, the mail service, and
the billing agent are all in-process stubs under `stubs/`.

That last line matters. `logs/` now contains three files:

```
$ cat logs/refund-audit.log
reference-scenario skill=issue-refund subject=WW-10042
```

Those paths are not arbitrary. `controlloop.yaml` declares an
`audit_path` for each tool, and the code writes to exactly the paths it
declares. A declaration nothing honors is the defect this repository
exists to demonstrate, so the agent honors its own.

---

## 1. `controlloop init` — draft a manifest

`init` reads the repository, works out which agents exist, and writes a
**reviewable draft** `controlloop.yaml`. It evaluates no policy and
enforces nothing.

This scenario already has a manifest, and `init` will not overwrite one:

```
$ controlloop init
✕ INVALID INPUT  controlloop.yaml already exists at .../controlloop.yaml;
  init never overwrites or modifies an existing manifest
```

To see what it would have produced, run it on a copy with the manifest
removed. The draft names what discovery actually found:

```yaml
schema_version: "1.2.0"

# TODO: owner
# ControlLoop cannot determine who is accountable for this
# repository's agents. Replace the placeholder below with an
# identifier for the responsible team or individual.
owner: "TODO-owner"

trust_boundaries:
  # Discovered candidate agents (from repository discovery):
  #   - widgetworks-order-support-agent  (tools observed: Issue a refund, Look up an order, Reply to customer)
  #   - billing-escalation-agent  (no tools observed)
  - name: "TODO-trust-boundary-name"
    agents:
      - "widgetworks-order-support-agent"
      - "billing-escalation-agent"
```

Every field is present even where ControlLoop could not determine a
value, marked `TODO` with a comment saying what to supply. You review it
and fill it in; nothing is enforced until you do.

`init` writes the file and prints nothing on success.

---

## 2. `controlloop bom` — build the capability graph

The **ACBOM** (Agent Capability Bill of Materials) is the canonical
artifact everything else is computed from: a normalized graph of agents,
tools, resources, identities, and permissions, with the evidence for
each. `bom` writes it to stdout as canonical JSON.

```
$ controlloop bom > acbom.json
$ echo $?
0
```

**15 nodes.** Every one names the file it came from:

| type | subtype | name | evidence |
| --- | --- | --- | --- |
| agent | `a2a-agent-card` | `widgetworks-order-support-agent` | `agent-card.json` |
| agent | `a2a-agent-card` | `billing-escalation-agent` | `agent-card.json` |
| tool | `a2a-skill` | `Look up an order` | `agent-card.json` |
| tool | `a2a-skill` | `Issue a refund` | `agent-card.json` |
| tool | `a2a-skill` | `Reply to customer` | `agent-card.json` |
| tool | `openapi-operation` | `getOrder` | `openapi/orders-api.yaml` |
| tool | `openapi-operation` | `issueRefund` | `openapi/orders-api.yaml` |
| tool | `openapi-operation` | `listCustomerOrders` | `openapi/orders-api.yaml` |
| tool | `mcp-server-stdio` | `order-support-tools` | `.mcp.json` |
| resource | `openapi-path` | `/orders/{orderId}` | `openapi/orders-api.yaml` |
| resource | `openapi-path` | `/orders/{orderId}/refund` | `openapi/orders-api.yaml` |
| resource | `openapi-path` | `/customers/{customerId}/orders` | `openapi/orders-api.yaml` |
| permission | `iam-statement` | `Allow: 3 actions` | `iam/policy.json` |
| permission | `iam-statement` | `Allow: 2 actions` | `iam/policy.json` |
| permission | `iam-statement` | `Allow: sqs:SendMessage` | `iam/policy.json` |

**7 edges:**

```
widgetworks-order-support-agent  --delegates-to--> billing-escalation-agent
widgetworks-order-support-agent  --invokes-->      Look up an order
widgetworks-order-support-agent  --invokes-->      Issue a refund
widgetworks-order-support-agent  --invokes-->      Reply to customer
getOrder                         --reads-->        /orders/{orderId}
listCustomerOrders               --reads-->        /customers/{customerId}/orders
issueRefund                      --writes-->       /orders/{orderId}/refund
```

Four adapters produced that, and no adapter ran any of this repository's
code, started the MCP server, or contacted
`internal-orders-api.widgetworks.example`. Scanning is a read of
committed files.

### What the graph does not know

The three `a2a-skill` tools and the three `openapi-operation` tools are
separate nodes with no edge between them. **ControlLoop does not know
that `Issue a refund` calls `issueRefund`** — nothing in a repository
states it. Only `src/order_support/tools.py` does, and only for a human
reading it.

That is a real limit, not an oversight to work around. Static discovery
reports what the artifacts say; it does not infer a call it cannot see.

### Why the manifest matters here

`bom` also applies what `controlloop.yaml` declares under
`tool_capabilities`. Compare the `Issue a refund` node:

```json
"name": "Issue a refund",
"security_attributes": {
  "financial_action": true,
  "read_only": false,
  "sensitivity": "confidential"
}
```

Nothing in an agent card or an OpenAPI document says that issuing a
refund moves money. Without that block, every scan of this repository
reports `no material capability is reachable` — a confident pass over an
agent that can move money. The manifest is where you say what your tools
actually do.

---

## 3. `controlloop scan` — evaluate policy

`scan` runs the same discovery, then evaluates every rule in the pack
and explains what it found. Run `controlloop rules` to see the rules and
what each one looks for.

```
$ controlloop scan
! WORST REACHABLE  financial-action: widgetworks-order-support-agent can invokes
  Issue a refund

✓ PASSED

• material change: not evaluated

! MEDIUM  policy.undeclared-tools: Tool 'Look up an order' is reachable but not
  declared in controlloop.yaml.
    at agent-card.json

! MEDIUM  policy.undeclared-tools: Tool 'Reply to customer' is reachable but not
  declared in controlloop.yaml.
    at agent-card.json

! MEDIUM  policy.undeclared-tools: Tool 'Issue a refund' is reachable but not
  declared in controlloop.yaml.
    at agent-card.json

Suppressions: none declared

$ echo $?
0
```

Three things are worth reading closely.

**The blast-radius line comes first.** `WORST REACHABLE` is the single
worst thing this agent can do, stated before any rule output:
`widgetworks-order-support-agent` can invoke `Issue a refund`, a
financial action. It is derived from the graph and the declared
capabilities, and it cannot be suppressed.

**`PASSED` with warnings is still a pass.** Three MEDIUM findings, exit
code 0. `policy.undeclared-tools` fires because `controlloop.yaml`
approves `order-support-tools` but never approves the three skills
themselves. That is a real gap in this manifest, deliberately left in
place — a scenario where everything is already correct teaches nothing.

**`material change: not evaluated`** means no baseline comparison
happened. Change detection needs something to compare against; that is
the next command.

---

## 4. `controlloop gate` — the CI decision

`gate` is the non-interactive form CI runs. Same pipeline, plus a
four-state verdict and an evidence artifact written on every run,
including a failing one.

```
$ controlloop gate
! WORST REACHABLE  financial-action: widgetworks-order-support-agent can invokes
  Issue a refund

✓ PASSED

• material change: not evaluated

! MEDIUM  policy.undeclared-tools: Tool 'Look up an order' is reachable but not
  declared in controlloop.yaml.
    at agent-card.json

! MEDIUM  policy.undeclared-tools: Tool 'Reply to customer' is reachable but not
  declared in controlloop.yaml.
    at agent-card.json

! MEDIUM  policy.undeclared-tools: Tool 'Issue a refund' is reachable but not
  declared in controlloop.yaml.
    at agent-card.json

Suppressions: none declared

Completeness enforcement: warn (default)
Evidence: evidence.json

$ echo $?
0
```

The verdicts and their exit codes:

| verdict | exit | meaning |
| --- | --- | --- |
| `PASSED` | 0 | nothing blocking |
| `PASSED WITH WARNINGS` | 0 | findings, none blocking |
| `REVIEW REQUIRED` | 3 | analysis incomplete, a human must look |
| `DEPLOYMENT BLOCKED` | 1 | a blocking rule fired |

`evidence.json` is written unconditionally. It is the retainable record
of what was scanned, which rules ran, and why the verdict came out the
way it did.

---

## 5. Seeing it block

This branch passes. The blocking scenarios live on their own branches,
each with a committed `expected/*.json` that
`.github/workflows/reference-scenarios.yml` in the ControlLoop
repository asserts against daily:

| branch | scenario |
| --- | --- |
| `scenario/ceiling-breach` | a capability breaching the declared ceiling with no rule matching it |
| `scenario/capability-expansion` | a pull request that widens what the agent can reach |

```
git checkout scenario/ceiling-breach
controlloop gate scenarios/order-support-agent
```

---

## What this agent is and is not

**It is deliberately over-privileged.** The IAM policy grants
`ses:SendEmail` on `Resource: "*"` — the agent may mail anyone at all.
That is the point. Never deploy this.

**It is deterministic, not model-driven.** A production agent chooses
its next action with an LLM. `src/order_support/agent.py` routes on an
explicit `kind` field and does the same thing every run. ControlLoop
analyzes an agent's *capability structure* — what it can reach, and what
it can reach through something else — and that structure is identical
whether a model or a match statement picks the next call. A real model
would add an API key, a network dependency, and a non-reproducible run
to a repository whose value is being forkable and offline.

So: **ControlLoop is not analyzing model behavior here, and neither this
scan nor any scan tells you the agent is safe.** It tells you what
powers the agent has, and what changed since you last approved them.
