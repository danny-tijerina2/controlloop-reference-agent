# Scenario: ceiling breach with no matching rule

Proves [ControlLoop issue #101](https://github.com/danny-tijerina2/controlloop/issues/101)
(E10.5). Diff this branch against `main` to see the whole change.

> This scenario is the proof of the product thesis. If it does not pass,
> the ceiling is decoration.

## What the pull request does

`scenarios/order-support-agent/agent-card.json` gains one skill,
`update-payment-method`, named `customer-payment-methods`. Support asked
for it so an agent can fix a customer's failed card without a human
touching the account. It is an ordinary, plausible feature request.

It is also authority the agent's declared capability ceiling has
prohibited since the base scenario was written:

```yaml
ceilings:
  - agent: widgetworks-order-support-agent
    prohibited_resources:
      - customer-payment-methods
```

**No shipped pattern rule anticipates this.** Nothing in the rule pack
knows what a payment method is, and the rule that *would* otherwise
notice a new tool -- `policy.undeclared-tools` -- is explicitly
suppressed here, along with every other pattern-rule finding this
scenario produces (see `suppressions:` in `controlloop.yaml`). The
ceiling is the only thing left that can block.

## What the gate does

```
$ controlloop gate scenarios/order-support-agent
✕ DEPLOYMENT BLOCKED

✕ CRITICAL  policy.capability-ceiling: agent 'widgetworks-order-support-agent'
  reaches 'customer-payment-methods', which is a prohibited resource or external
  destination under its capability ceiling
    at agent-card.json
```

Exit code `1`.

## Proving it is the ceiling, not an accident

`controlloop.amended.yaml` is the identical manifest with
`customer-payment-methods` removed from `prohibited_resources` and
nothing else changed. Run the gate against the same `agent-card.json`
with that manifest in place and it passes:

```
✓ PASSED
```

Exit code `0`. The agent's capability did not change between those two
runs -- only the declared ceiling did. That is the mechanism working.

## Requirement mapping

| Requirement | Where |
| --- | --- |
| REQ-1: authority outside the ceiling by a route no shipped rule matches | the `customer-payment-methods` skill; every pattern-rule finding suppressed |
| REQ-2: gate fails with every pattern rule disabled | `suppressions:` in `controlloop.yaml`; exit `1` |
| REQ-3: finding names the breached clause and the breaching path | `expected/ceiling-breach.json` -> `ceiling_finding.message`, `.capability_path` |
| REQ-4: amending the ceiling makes the same pull request pass | `controlloop.amended.yaml`; exit `0` |

`scenarios/order-support-agent/expected/ceiling-breach.json` holds the
committed expectations, produced by a real run and asserted by the
end-to-end proof in ControlLoop issue #104.
