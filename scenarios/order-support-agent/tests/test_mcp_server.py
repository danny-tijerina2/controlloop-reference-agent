"""The server `.mcp.json` declares really starts and really lists the
three tools the agent card advertises."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from order_support import mcp_server, tools
from order_support.paths import MCP_CONFIG


def _request(method: str, **params: Any) -> dict[str, Any] | None:
    return mcp_server.handle(
        {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    )


def test_initialize_reports_the_server_name_mcp_json_declares() -> None:
    declared = set(json.loads(MCP_CONFIG.read_text(encoding="utf-8"))["mcpServers"])
    response = _request("initialize")

    assert response is not None
    assert response["result"]["serverInfo"]["name"] in declared


def test_tools_list_matches_the_agent_card_skills() -> None:
    response = _request("tools/list")

    assert response is not None
    listed = {tool["name"] for tool in response["result"]["tools"]}
    assert listed == set(tools.TOOLS)


def test_a_tool_call_runs_the_same_function_the_agent_runs() -> None:
    response = _request(
        "tools/call", name="lookup-order", arguments={"orderId": "WW-10041"}
    )

    assert response is not None
    assert response["result"]["isError"] is False
    assert "WW-10041" in response["result"]["content"][0]["text"]


def test_a_failing_tool_call_never_echoes_the_underlying_error() -> None:
    """The error text is authored in `mcp_server`, never built from an
    exception, so a failure cannot leak an argument back to the client."""

    response = _request(
        "tools/call", name="lookup-order", arguments={"orderId": "WW-00000"}
    )

    assert response is not None
    assert response["result"]["isError"] is True
    assert response["result"]["content"][0]["text"] == "tool call failed"
    assert "WW-00000" not in json.dumps(response)


def test_an_unknown_method_is_a_json_rpc_error() -> None:
    response = _request("resources/list")

    assert response is not None
    assert response["error"]["code"] == -32601


def test_a_notification_gets_no_reply() -> None:
    """A JSON-RPC notification carries no `id` and takes no response."""

    assert mcp_server.handle({"jsonrpc": "2.0", "method": "initialized"}) is None
