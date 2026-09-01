"""The three tools `agent-card.json` advertises.

Each tool below names the card skill it implements and the OpenAPI
`operationId` it calls, and `tests/test_artifact_parity.py` reads the
committed artifacts and asserts those names still line up. That test is
the reason this file cannot quietly drift away from the card.

The declarations in `controlloop.yaml` under `tool_capabilities` are
claims about what these functions do:

    Issue a refund      financial_action: true,  read_only: false
    Look up an order    read_only: true
    Reply to customer   external_communication: true

Each claim is made true here, not merely asserted: `look_up_an_order`
never mutates the ledger, `issue_a_refund` moves money in it, and
`reply_to_customer` calls the notification stub that stands in for the
`ses:SendEmail` grant.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from order_support import audit
from stubs import notifications, orders_api


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """How one tool maps onto the artifacts that describe it."""

    #: `skills[].id` in `agent-card.json`.
    skill_id: str
    #: `skills[].name` in the card. This is also the string discovery
    #: uses as the node name, and therefore the string `controlloop.yaml`
    #: must use in `logged_tools` and `tool_capabilities`.
    display_name: str
    #: `operationId` in `openapi/orders-api.yaml`, or `None` for a tool
    #: that reaches a service the spec does not describe.
    operation_id: str | None
    #: The `audit_path` declared for this tool in `controlloop.yaml`.
    audit_path: str


LOOKUP_ORDER = ToolSpec(
    skill_id="lookup-order",
    display_name="Look up an order",
    operation_id="getOrder",
    audit_path="logs/order-lookup-audit.log",
)

ISSUE_REFUND = ToolSpec(
    skill_id="issue-refund",
    display_name="Issue a refund",
    operation_id="issueRefund",
    audit_path="logs/refund-audit.log",
)

REPLY_TO_CUSTOMER = ToolSpec(
    skill_id="reply-to-customer",
    display_name="Reply to customer",
    # The reply leaves through SES, which `openapi/orders-api.yaml` does
    # not describe. The grant is in `iam/policy.json` instead.
    operation_id=None,
    audit_path="logs/customer-reply-audit.log",
)

#: Every tool, keyed by the card skill id it implements.
TOOLS: dict[str, ToolSpec] = {
    LOOKUP_ORDER.skill_id: LOOKUP_ORDER,
    ISSUE_REFUND.skill_id: ISSUE_REFUND,
    REPLY_TO_CUSTOMER.skill_id: REPLY_TO_CUSTOMER,
}


def look_up_an_order(order_id: str) -> dict[str, Any]:
    """Card skill `lookup-order`. Calls `getOrder`.

    Mutates nothing. `orders_api.get_order` returns a deep copy, so the
    dictionary handed back cannot be used to reach the ledger. This is
    what `read_only: true` in `controlloop.yaml` refers to.
    """

    order = orders_api.get_order(order_id)
    audit.record(
        audit.resolve(LOOKUP_ORDER.audit_path),
        skill_id=LOOKUP_ORDER.skill_id,
        subject=order_id,
    )
    return order


def list_orders_for_customer(customer_id: str) -> list[dict[str, Any]]:
    """Calls `listCustomerOrders`.

    A helper on the lookup skill rather than a fourth tool: the card
    advertises three skills, and adding a tool the card does not
    advertise is exactly the undeclared capability this product exists
    to catch. It audits under the lookup tool's declared path because
    that is the skill it belongs to.
    """

    orders = orders_api.list_customer_orders(customer_id)
    audit.record(
        audit.resolve(LOOKUP_ORDER.audit_path),
        skill_id=LOOKUP_ORDER.skill_id,
        subject=customer_id,
    )
    return orders


def issue_a_refund(order_id: str, amount_cents: int) -> dict[str, Any]:
    """Card skill `issue-refund`. Calls `issueRefund`.

    Moves money. This is the concrete behavior behind
    `financial_action: true`, and the reason the capability ceiling
    treats this agent as able to take a material financial action.

    The audit line records the order id and no amount -- see
    `order_support.audit` for why the payload stays out of the log.
    """

    order = orders_api.issue_refund(order_id, amount_cents)
    audit.record(
        audit.resolve(ISSUE_REFUND.audit_path),
        skill_id=ISSUE_REFUND.skill_id,
        subject=order_id,
    )
    return order


def reply_to_customer(
    ticket_id: str, to_address: str, subject: str, body: str
) -> notifications.SentMessage:
    """Card skill `reply-to-customer`. Sends through the SES stand-in.

    This is the capability that leaves the trust boundary, which is what
    `external_communication: true` declares. The IAM grant behind it is
    scoped to `Resource: "*"`, so the agent may mail any address at all
    -- deliberately, as one of the things this scenario surfaces.

    The audit line records the ticket id and neither the recipient
    address nor the body.
    """

    message = notifications.send_email(to_address, subject, body)
    audit.record(
        audit.resolve(REPLY_TO_CUSTOMER.audit_path),
        skill_id=REPLY_TO_CUSTOMER.skill_id,
        subject=ticket_id,
    )
    return message
