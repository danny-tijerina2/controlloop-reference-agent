# research-crew

A CrewAI scenario (ControlLoop issue
[#276](https://github.com/danny-tijerina2/controlloop/issues/276),
E15.4). Three agents research, write, and publish a competitor brief.

> **⚠️ Deliberately over-privileged. Never deploy this.**

## The point of this scenario

Two agents wire their tools in a shape ControlLoop can read. The third —
the one holding publishing credentials — does not:

```python
def publisher(self) -> Agent:
    return Agent(
        config=self.agents_config["publisher"],
        tools=tools_for_environment(),   # computed at runtime
    )
```

Nothing about that is exotic. Picking tools from the environment is
ordinary, which is exactly why it matters: a scanner that quietly
reported this agent as having no tools would report a confident pass
over the one agent that can publish.

ControlLoop does not do that. The unresolved list becomes a tool node
whose attributes are literally `"unknown"`, which classifies as
`UNCLASSIFIED` — the worst-ranked material class — so it surfaces as the
worst thing in the graph:

```
! WORST REACHABLE  unclassified: Senior Research Analyst can reach
  unresolved-tools:publisher via invokes (2-hop chain)
    1. delegates-to -> ...
    2. invokes -> ...
```

Read that path. The **researcher** reaches the publisher's unknowable
tool, because `allow_delegation: true` lets it hand work to any agent in
the crew. Neither agent's own definition shows this. That transitive
reach through delegation is the thing a flat tool inventory cannot tell
you.

## It is not dirty on purpose

Unlike `order-support-agent`, this scenario's manifest is **complete**:
every tool approved by a named human, every delegation declared, every
privileged tool given an audit path. **Zero policy rules fire.**

```
$ controlloop gate .
! WORST REACHABLE  unclassified: Senior Research Analyst can reach
  unresolved-tools:publisher via invokes (2-hop chain)

! PASSED WITH WARNINGS

• no findings

$ echo $?
0
```

That is the lesson. A spotless manifest and no findings still does not
mean the crew is safe — it means nothing *known* is wrong. What remains
is what nobody could read.

Turn on completeness enforcement, which is what a team gating a real
deployment should do:

```
$ CONTROLLOOP_COMPLETENESS_ENFORCEMENT=enforce controlloop gate .
! REVIEW REQUIRED

$ echo $?
3
```

A human has to look.

## Files

| File | Declares |
| --- | --- |
| `config/agents.yaml` | Three agents; the researcher may delegate to anyone |
| `src/research_crew/crew.py` | The wiring — two resolvable tool lists, one not |
| `src/research_crew/dynamic.py` | The runtime tool selection ControlLoop refuses to guess at |
| `controlloop.yaml` | Approvals, declared delegation, audit paths, tool capabilities |
| `expected/crewai-incomplete.json` | Recorded verdicts for both enforcement modes |
| `pyproject.toml` | `crewai>=0.86.0`, inside the supported range |

## Regenerating

From `cli/` in a checkout of `danny-tijerina2/controlloop`:

```
uv run controlloop scan <path-to-this-directory>
uv run controlloop gate <path-to-this-directory> --evidence-path evidence.json
```

See [CrewAI support](https://github.com/danny-tijerina2/controlloop/blob/main/docs/reference/crewai-support.md)
for what is discovered, what is reported as unknown, and what is not
read at all.
