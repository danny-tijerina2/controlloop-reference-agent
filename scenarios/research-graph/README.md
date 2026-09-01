# research-graph

A LangGraph scenario (ControlLoop issue
[#283](https://github.com/danny-tijerina2/controlloop/issues/283),
E16.4). A four-node graph that plans, researches, writes, and publishes.

> **⚠️ Deliberately over-privileged. Never deploy this.**

## What it demonstrates

**Both branches of a runtime router are reachable.** `route` decides at
runtime whether to research or go straight to writing:

```python
builder.add_conditional_edges(
    "plan", route, {"research": "research", "write": "write"}
)
```

ControlLoop emits an edge to *both*:

```
plan --delegates-to--> research
plan --delegates-to--> write
```

Picking one would report a graph narrower than the one that actually
runs — a confident answer quietly smaller than reality.

**One binding cannot be read, and it is the risky one.** The publish
step builds its tools from the environment:

```python
builder.add_node("publish", ToolNode(build_publish_tools()))
```

Ordinary code, and exactly why it matters — publish is the node that
reaches the outside world. ControlLoop refuses to guess, and instead
emits a node whose attributes are literally `"unknown"`, which
classifies as `UNCLASSIFIED`, the worst material class:

```
! WORST REACHABLE  unclassified: research-graph can invokes
  unresolved-tools:research-graph
```

## It is not dirty on purpose

The manifest is complete: every tool approved by a named human, every
privileged tool given an audit path. **Zero policy rules fire.**

```
$ controlloop gate .
! PASSED WITH WARNINGS
• no findings
$ echo $?
0

$ CONTROLLOOP_COMPLETENESS_ENFORCEMENT=enforce controlloop gate .
! REVIEW REQUIRED
$ echo $?
3
```

A spotless manifest and no findings does not mean safe. It means nothing
*known* is wrong. What remains is what nobody could read.

## Privacy note

`langgraph.json` declares `"env": "./.env"`. ControlLoop records that an
environment file is declared and **never opens it** — a path contributes
only that fact, and only an inline `env` mapping contributes `env:NAME`
scopes, keys only. See
[CrewAI and LangGraph support](https://github.com/danny-tijerina2/controlloop/blob/main/docs/reference/langgraph-support.md).
