# controlloop-reference-agent

> **⚠️ DELIBERATELY VULNERABLE — DO NOT DEPLOY, DO NOT REUSE CODE FROM THIS REPOSITORY.**
>
> Every agent, tool declaration, and capability manifest in this repository is
> constructed on purpose to exhibit specific, unsafe capability patterns —
> capability expansion, ceiling breaches, exfiltration triangles, hardcoded
> secrets, unauthorized delegation, and similar findings — so that
> [ControlLoop](https://github.com/danny-tijerina2/controlloop) has a real,
> versioned target to scan in CI and in its own documentation. None of it is
> safe, none of it is production code, and none of it should be copied into a
> real agent.

## What this is

A fixture repository maintained alongside the `controlloop` CLI. It holds a
small set of scenario agents, each demonstrating one class of capability
finding that ControlLoop detects. It exists to prove — with real, runnable,
scanned output, not a description — that the scanner behaves as documented
against an agent that isn't a synthetic unit-test fixture.

## Relationship to `controlloop` and release coupling

- This repository is a companion to
  [`danny-tijerina2/controlloop`](https://github.com/danny-tijerina2/controlloop),
  the Community CLI implementing the scanner itself. It contains no scanner
  code of its own.
- Scenario content here is versioned independently, but is expected to track
  `controlloop`'s rule pack: a scenario is only meaningful evidence against
  the rule pack version it was authored and last verified against. Any
  content here that stops matching current `controlloop` behavior is a bug
  in this repository, not a change to the scanner's contract.
- CI in this repository, once implemented, scans its own scenarios with a
  pinned `controlloop` release and checks the recorded verdict — see
  `controlloop#104` (E10.8 — End-to-end proof in CI) — rather than trusting
  a description of expected output.

## Scope

- **In scope:** minimal, individually-labeled scenario agents (one capability
  pattern per scenario), each with a short note on which `controlloop` rule
  it is meant to trigger.
- **Out of scope:** anything resembling a real, deployable agent; any
  capability, credential, or integration that could function outside this
  demonstration; production hardening of any kind.

## Issues and pull requests

This repository is for demonstration only and does not accept support
requests — see `.github/ISSUE_TEMPLATE/config.yml`. For questions, bugs, or
support related to the ControlLoop CLI itself, use
[`danny-tijerina2/controlloop`](https://github.com/danny-tijerina2/controlloop/issues).

## Scenarios

| Directory | Demonstrates | Issue |
| --- | --- | --- |
| [`scenarios/order-support-agent/`](scenarios/order-support-agent/) | The base, "currently approved" reference agent every other scenario builds on | [controlloop#99](https://github.com/danny-tijerina2/controlloop/issues/99) (E10.3) |

Each scenario is its own self-contained scan root — point `controlloop`
at a scenario's directory, not the repository root, to scan it.

## Status

Namespace and repository ownership reserved per the decision recorded in
[controlloop#134](https://github.com/danny-tijerina2/controlloop/issues/134)
(E14.7). The base scenario above is written
([controlloop#99](https://github.com/danny-tijerina2/controlloop/issues/99)).
The four scenario variations built on top of it — capability expansion,
a ceiling breach, an exfiltration triangle, a capability reduction — are
[controlloop#100](https://github.com/danny-tijerina2/controlloop/issues/100)
through
[controlloop#103](https://github.com/danny-tijerina2/controlloop/issues/103),
and end-to-end CI proof against a pinned `controlloop` release is
[controlloop#104](https://github.com/danny-tijerina2/controlloop/issues/104)
(epic E10 — Reference agent and scenarios) — all still open.
