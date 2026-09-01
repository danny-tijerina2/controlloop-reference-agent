"""The `order-support-tools` MCP server `.mcp.json` declares.

Exposes the same three tools `agent-card.json` advertises over stdio
JSON-RPC, so the MCP server node in the ACBOM points at a server that
actually starts and actually lists those tools.

**No SDK dependency.** The official MCP Python SDK pulls in a
substantial dependency tree, and this repository is meant to be forked
and read. The three methods a client needs -- `initialize`,
`tools/list`, `tools/call` -- are newline-delimited JSON-RPC over stdin
and stdout, so they are implemented directly here. ControlLoop's own
`controlloop.adapters.mcp_live` makes the same call for the same reason.

**Reads stdin, writes stdout, opens nothing.** No socket, no
subprocess, no file outside the scenario's own `logs/`. A client starts
this process; this process starts nothing.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from order_support import tools

PROTOCOL_VERSION = "2025-06-18"
SERVER_NAME = "order-support-tools"
SERVER_VERSION = "0.1.0"

#: Tool schemas, keyed by the card skill id. The `name` a client sees is
#: the skill id, so an MCP client and an A2A client are talking about the
#: same three capabilities under the same three names.
_TOOL_SCHEMAS: dict[str, dict[str, Any]] = {
    tools.LOOKUP_ORDER.skill_id: {
        "description": "Retrieve order status and history for a customer.",
        "inputSchema": {
            "type": "object",
            "properties": {"orderId": {"type": "string"}},
            "required": ["orderId"],
        },
    },
    tools.ISSUE_REFUND.skill_id: {
        "description": "Issue a refund against a completed order.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "orderId": {"type": "string"},
                "amountCents": {"type": "integer"},
            },
            "required": ["orderId", "amountCents"],
        },
    },
    tools.REPLY_TO_CUSTOMER.skill_id: {
        "description": "Send a support reply email to the customer who opened the ticket.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticketId": {"type": "string"},
                "toAddress": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["ticketId", "toAddress", "subject", "body"],
        },
    },
}


def tool_listing() -> list[dict[str, Any]]:
    """The `tools/list` payload, built from the same `ToolSpec` values
    the agent itself uses."""

    return [
        {"name": skill_id, **_TOOL_SCHEMAS[skill_id]}
        for skill_id in tools.TOOLS
    ]


def _call_tool(name: str, arguments: dict[str, Any]) -> str:
    """Dispatch one `tools/call`. Returns a short text result."""

    if name == tools.LOOKUP_ORDER.skill_id:
        order = tools.look_up_an_order(str(arguments["orderId"]))
        return f"{order['orderId']} is {order['status']}"
    if name == tools.ISSUE_REFUND.skill_id:
        order = tools.issue_a_refund(
            str(arguments["orderId"]), int(arguments["amountCents"])
        )
        return f"{order['orderId']} refunded, status {order['status']}"
    if name == tools.REPLY_TO_CUSTOMER.skill_id:
        tools.reply_to_customer(
            str(arguments["ticketId"]),
            str(arguments["toAddress"]),
            str(arguments["subject"]),
            str(arguments["body"]),
        )
        return f"replied on {arguments['ticketId']}"
    raise KeyError(name)


def handle(request: dict[str, Any]) -> dict[str, Any] | None:
    """One request in, one response out. Returns `None` for a
    notification, which by JSON-RPC carries no `id` and takes no reply."""

    method = request.get("method")
    request_id = request.get("id")
    if request_id is None:
        return None

    if method == "initialize":
        result: dict[str, Any] = {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        }
    elif method == "tools/list":
        result = {"tools": tool_listing()}
    elif method == "tools/call":
        params = request.get("params") or {}
        try:
            text = _call_tool(
                str(params.get("name")), dict(params.get("arguments") or {})
            )
        except (KeyError, ValueError, LookupError) as error:
            # The message is authored here, never built from the
            # exception's own text, so a failure cannot echo a payload
            # back to the client.
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [{"type": "text", "text": "tool call failed"}],
                    "isError": True,
                },
            }
        result = {"content": [{"type": "text", "text": text}], "isError": False}
    else:
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": "method not found"},
        }

    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def main() -> int:
    """Console entry point for `order-support-mcp`. Serves until stdin
    closes."""

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(request, dict):
            continue
        response = handle(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
