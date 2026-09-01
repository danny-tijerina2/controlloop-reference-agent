# support-desk

An OpenAI Agents SDK scenario (ControlLoop issue
[#287](https://github.com/danny-tijerina2/controlloop/issues/287),
E17.4).

> **⚠️ Deliberately over-privileged. Never deploy this.**

## The chain is the point

A customer talks to **Triage**. Triage never issues a refund and has no
refund tool in its own list. But it can hand off to **Billing**, and
Billing can hand off to **Escalation**, which holds `issue-refund`.

```
Triage --delegates-to--> Billing --delegates-to--> Escalation --invokes--> issue-refund
```

**Three hops from the agent a customer talks to, to the agent that can
move money.** No flat tool inventory shows that. Neither agent's own
definition shows it either — you have to compose the graph.

Removing the `Router` agent (below) makes ControlLoop state it directly:

```
! WORST REACHABLE  financial-action: Billing can reach issue-refund via invokes
  (2-hop chain)
    1. delegates-to -> ...
    2. invokes -> ...
```

## Why the committed scan reports something else

With `Router` present, the headline is:

```
! WORST REACHABLE  unclassified: Router can invokes unresolved-tools:Router
! PASSED WITH WARNINGS
• no findings
exit 0
```

That is correct, not a bug. `Router` builds its tools from configuration
at runtime, so ControlLoop cannot read them — and an unreadable
capability classifies as `UNCLASSIFIED`, which the material taxonomy
ranks **worst of all**. A tool nobody can read outranks a refund,
because it could be anything.

Both facts are in the graph. The headline reports the worse one.

## A tool wired to nothing is still found

```python
@function_tool
def purge_customer(customer_id: str) -> str:
    ...
```

Nothing references `purge_customer`. It is still discovered, and
ControlLoop says so:

```
! tool 'purge_customer' is defined but wired to no agent, so nothing in
  this module can reach it
```

This is the structural advantage the SDK has over CrewAI and LangGraph:
`@function_tool` marks a tool at its **definition site**, so the set of
tools that exist is knowable even when the set an agent holds is not. An
unreferenced destructive function is exactly what a reviewer wants told
about, and an adapter that only read agent wiring would never see it.

## `as_tool` is not a handoff

A handoff transfers the conversation. `Agent.as_tool()` calls into an
agent and returns. ControlLoop models them as `delegates-to` and
`invokes` respectively, because they carry different authority.

## It is not dirty on purpose

Every tool is approved, every privileged tool audited, every delegation
declared. **Zero policy rules fire**, and the scan still cannot claim
safety — because one agent's tools could not be read.

## Files

| File | |
| --- | --- |
| `desk.py` | Four agents, three function tools, one unresolvable binding |
| `controlloop.yaml` | What each tool does; discovery cannot know |
| `expected/openai-agents-chain.json` | Recorded verdict and blast radius |
