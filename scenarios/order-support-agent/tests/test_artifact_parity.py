"""The artifacts and the code cannot drift apart.

Every assertion here **reads a committed artifact at runtime**. None of
them restates an artifact's contents as a literal, because a test that
hardcodes the skill ids cannot notice when the card changes -- and
noticing is the entire point.

This is the file that makes the scenario honest. `controlloop bom`
produces 15 nodes and 7 edges from the artifacts in this directory; if
any of them stops describing the code beside it, one of these fails.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from order_support import delegate, tools
from order_support.paths import (
    AGENT_CARD,
    IAM_POLICY,
    MANIFEST,
    MCP_CONFIG,
    OPENAPI_SPEC,
    SCENARIO_ROOT,
)
from stubs import orders_api


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _card_skills() -> dict[str, str]:
    """`{skill id: display name}` from the committed agent card."""

    return {
        skill["id"]: skill["name"] for skill in _load_json(AGENT_CARD)["skills"]
    }


def _operation_ids() -> set[str]:
    """Every `operationId` in the committed OpenAPI document."""

    document = _load_yaml(OPENAPI_SPEC)
    return {
        operation["operationId"]
        for path_item in document["paths"].values()
        for operation in path_item.values()
        if isinstance(operation, dict) and "operationId" in operation
    }


# --------------------------------------------------------------------
# agent-card.json  <->  tools.py
# --------------------------------------------------------------------


def test_every_advertised_skill_has_an_implementation() -> None:
    assert set(_card_skills()) == set(tools.TOOLS)


def test_every_tool_carries_the_display_name_the_card_gives_it() -> None:
    """Discovery names an A2A skill node by the card's `name`, not its
    `id`, and `controlloop.yaml` must then use that same string. A tool
    whose `display_name` drifts from the card silently breaks the
    manifest's `logged_tools` and `tool_capabilities` matching."""

    skills = _card_skills()
    for skill_id, spec in tools.TOOLS.items():
        assert spec.display_name == skills[skill_id]


# --------------------------------------------------------------------
# openapi/orders-api.yaml  <->  stubs/orders_api.py
# --------------------------------------------------------------------


def test_every_tool_calls_an_operation_the_spec_declares() -> None:
    declared = _operation_ids()
    for spec in tools.TOOLS.values():
        if spec.operation_id is not None:
            assert spec.operation_id in declared


def test_the_stub_implements_exactly_the_declared_operations() -> None:
    """An operation added to the spec with nothing behind it, or a stub
    function with no operation, both fail here."""

    implemented = {
        "getOrder": orders_api.get_order,
        "issueRefund": orders_api.issue_refund,
        "listCustomerOrders": orders_api.list_customer_orders,
    }
    assert set(implemented) == _operation_ids()
    for function in implemented.values():
        assert callable(function)


# --------------------------------------------------------------------
# controlloop.yaml  <->  tools.py
# --------------------------------------------------------------------


def test_every_declared_audit_path_belongs_to_the_tool_beside_it() -> None:
    manifest = _load_yaml(MANIFEST)
    declared = {
        entry["tool"]: entry["audit_path"] for entry in manifest["logged_tools"]
    }
    by_display_name = {spec.display_name: spec for spec in tools.TOOLS.values()}

    assert set(declared) == set(by_display_name)
    for display_name, audit_path in declared.items():
        assert by_display_name[display_name].audit_path == audit_path


def test_every_declared_audit_path_is_actually_written(tmp_path: Path) -> None:
    """`policy.missing-action-logging` blocks the gate when a privileged
    tool has no audit path. A path nothing writes to satisfies the rule
    and produces no audit trail, which is worse than failing."""

    tools.look_up_an_order("WW-10041")
    tools.issue_a_refund("WW-10041", 100)
    tools.reply_to_customer("TCK-1", "a@customer.example", "s", "b")

    for spec in tools.TOOLS.values():
        assert (tmp_path / spec.audit_path).is_file(), spec.display_name


def test_no_audit_line_contains_a_payload(tmp_path: Path) -> None:
    """An audit line records that an action happened, never what it
    touched. A recipient address or an amount in a log turns the log
    into a second copy of the sensitive data."""

    tools.reply_to_customer(
        "TCK-1", "a.buyer@customer.example", "subject", "secret body"
    )
    tools.issue_a_refund("WW-10041", 4200)

    written = "\n".join(
        (tmp_path / spec.audit_path).read_text(encoding="utf-8")
        for spec in tools.TOOLS.values()
        if (tmp_path / spec.audit_path).exists()
    )
    for forbidden in ("a.buyer@customer.example", "secret body", "4200"):
        assert forbidden not in written


def test_every_declared_tool_capability_names_a_real_tool() -> None:
    manifest = _load_yaml(MANIFEST)
    declared = {entry["tool"] for entry in manifest["tool_capabilities"]}
    assert declared == {spec.display_name for spec in tools.TOOLS.values()}


# --------------------------------------------------------------------
# x-controlloop-delegates-to  <->  delegate.py
# --------------------------------------------------------------------


def test_every_declared_delegation_target_exists_and_names_an_agent() -> None:
    targets = delegate.declared_targets()
    assert targets, "the card must declare at least one delegation target"
    for relative_path in targets:
        assert (SCENARIO_ROOT / relative_path).is_file()
        assert delegate.resolve_target_name(relative_path)


def test_a_delegation_target_outside_the_scenario_is_refused() -> None:
    """Card content is untrusted data. A target path is contained to the
    scenario root before it is read."""

    with pytest.raises(delegate.DelegationError):
        delegate.resolve_target_name("../../../etc/passwd")


# --------------------------------------------------------------------
# .mcp.json and iam/policy.json
# --------------------------------------------------------------------


def test_the_mcp_server_declaration_still_names_the_scanned_server() -> None:
    """The ACBOM's MCP node is derived from the source path and this
    server name. Renaming it would change a node id and invalidate the
    committed baseline."""

    servers = _load_json(MCP_CONFIG)["mcpServers"]
    assert set(servers) == {"order-support-tools"}
    assert "ORDERS_API_BASE_URL" in servers["order-support-tools"]["env"]


def test_the_ses_grant_is_still_deliberately_over_broad() -> None:
    """`iam/policy.json` grants `ses:SendEmail` on `Resource: "*"`. That
    is the scenario's point, not an oversight -- if someone tightens it,
    this test says so out loud rather than letting the demo quietly stop
    demonstrating anything."""

    statements = _load_json(IAM_POLICY)["Statement"]
    ses = [s for s in statements if any("ses:" in a for a in s["Action"])]
    assert ses and ses[0]["Resource"] == "*"


def test_no_artifact_contains_a_real_looking_credential() -> None:
    """E10.3 REQ-4: no real credentials anywhere in the scenario."""

    for path in (AGENT_CARD, MANIFEST, MCP_CONFIG, IAM_POLICY, OPENAPI_SPEC):
        text = path.read_text(encoding="utf-8")
        for marker in ("AKIA", "-----BEGIN", "sk-", "ghp_"):
            assert marker not in text, f"{path.name} contains {marker}"
