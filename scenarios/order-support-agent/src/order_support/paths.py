"""Where the scenario's committed artifacts live.

Resolved from this file's own location so the agent runs correctly from
any working directory, and so the tests can read the same artifacts the
scanner reads.
"""

from __future__ import annotations

from pathlib import Path

#: `src/order_support/paths.py` -> `src/order_support` -> `src` -> root.
SCENARIO_ROOT = Path(__file__).resolve().parents[2]

AGENT_CARD = SCENARIO_ROOT / "agent-card.json"
MANIFEST = SCENARIO_ROOT / "controlloop.yaml"
OPENAPI_SPEC = SCENARIO_ROOT / "openapi" / "orders-api.yaml"
IAM_POLICY = SCENARIO_ROOT / "iam" / "policy.json"
MCP_CONFIG = SCENARIO_ROOT / ".mcp.json"
LOG_DIRECTORY = SCENARIO_ROOT / "logs"
