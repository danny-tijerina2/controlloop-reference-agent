# Storefront agent configuration

A fictional storefront ("Widgetworks") whose coding agents are configured
the way a careful team would configure them, used by ControlLoop epic E18
(the agent authority diff, controlloop#434) and story E18.10
(controlloop#444).

On `main` it is the approved starting point:

| File | What it grants |
| --- | --- |
| `.claude/settings.json` | A Prettier hook after edits, `Bash(npm test)` without asking, `Read(./.env)` denied, and a marketplace pinned to a commit |
| `.mcp.json` | One MCP server, `catalog-docs`, pinned to version `1.4.2` |
| `.github/workflows/claude-review.yml` | A review workflow with a read-only token |

Each scenario branch changes one thing, the way a real pull request would:

| Branch | The change | The incident pattern |
| --- | --- | --- |
| `scenario/session-start-harvester-hook` | A `SessionStart` hook that runs `node .github/setup.js` | The committed-hook payloads of the Miasma worm, Mini Shai-Hulud, and CVE-2026-25725 |
| `scenario/mcp-package-drift` | `catalog-docs` moves from `1.4.2` to `1.5.0` under the same name | A server's code changing behind a name a reviewer already trusts |
| `scenario/allow-list-widened` | `Bash(npm test)` becomes `Bash(*)` | A one-line change that hands the agent every shell command |
| `scenario/agent-workflow-id-token` | The review workflow gets `id-token: write` and `--dangerously-skip-permissions` | An agent that can mint cloud credentials and never asks |
| `scenario/pinned-plugin-added` | A plugin from the pinned marketplace is enabled | A benign change that must not fail |

## Everything here is inert

- `.github/setup.js` on the hook branch does nothing and exits. It stands
  in for a harvester; it reads no file, no environment variable, and no
  network.
- `@widgetworks-example/catalog-docs-mcp` is a fictional package. Nothing
  in this repository installs or runs it.
- The workflow lives under `scenarios/`, so GitHub never runs it, and it
  names a secret without holding one.
- `widgetworks-example/claude-plugins` is a fictional repository and the
  commit it is pinned to is made up.

## Expectations

Each branch commits `expected/<scenario>.json`, recorded from a real
`controlloop gate` run: the verdict, the exit code, the rules that fired,
the authority statements, and the blast radius. The ControlLoop
reference-scenario workflow runs the published Action against each branch
and asserts them.
