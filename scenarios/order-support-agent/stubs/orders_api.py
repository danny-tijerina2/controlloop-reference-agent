"""The Widgetworks Orders API, in memory.

Implements exactly the three operations declared in
`openapi/orders-api.yaml` -- `getOrder`, `issueRefund`, and
`listCustomerOrders` -- and nothing else. `tests/test_artifact_parity.py`
reads that file and asserts this set matches it, so an operation added to
the spec without an implementation fails the suite.

The IAM policy grants `dynamodb:GetItem`, `dynamodb:Query`, and
`dynamodb:UpdateItem` on the orders table. Read operations here
correspond to the first two; `issueRefund` is the only one that
corresponds to `UpdateItem`, and it is the only one that mutates state.
"""

from __future__ import annotations

import copy
from typing import Any

#: Fictional orders. No real customer, address, card, or account appears
#: here, and none may be added -- this repository is public.
_ORDERS: dict[str, dict[str, Any]] = {
    "WW-10041": {
        "orderId": "WW-10041",
        "customerId": "CUST-7781",
        "status": "delivered",
        "totalCents": 4200,
        "refundedCents": 0,
    },
    "WW-10042": {
        "orderId": "WW-10042",
        "customerId": "CUST-7781",
        "status": "delivered",
        "totalCents": 15900,
        "refundedCents": 0,
    },
    "WW-10043": {
        "orderId": "WW-10043",
        "customerId": "CUST-9002",
        "status": "disputed",
        "totalCents": 8800,
        "refundedCents": 0,
    },
}


class OrderNotFoundError(LookupError):
    """The requested order does not exist. Raised instead of returning
    `None` so a caller cannot mistake a miss for an empty order."""


def get_order(order_id: str) -> dict[str, Any]:
    """`GET /orders/{orderId}` -- `getOrder`.

    Returns a deep copy. A caller holding the result cannot reach back
    into the ledger and mutate it, which is what makes the
    `read_only: true` declaration in `controlloop.yaml` true rather than
    merely intended.
    """

    try:
        return copy.deepcopy(_ORDERS[order_id])
    except KeyError:
        raise OrderNotFoundError(order_id) from None


def list_customer_orders(customer_id: str) -> list[dict[str, Any]]:
    """`GET /customers/{customerId}/orders` -- `listCustomerOrders`."""

    return [
        copy.deepcopy(order)
        for order in sorted(_ORDERS.values(), key=lambda o: str(o["orderId"]))
        if order["customerId"] == customer_id
    ]


def issue_refund(order_id: str, amount_cents: int) -> dict[str, Any]:
    """`POST /orders/{orderId}/refund` -- `issueRefund`.

    The only mutating operation. This is the concrete reason
    `controlloop.yaml` declares `financial_action: true` for the refund
    tool: money really moves in the ledger below.
    """

    if amount_cents <= 0:
        raise ValueError("refund amount must be positive")
    order = _ORDERS.get(order_id)
    if order is None:
        raise OrderNotFoundError(order_id)
    outstanding = int(order["totalCents"]) - int(order["refundedCents"])
    if amount_cents > outstanding:
        raise ValueError("refund exceeds the outstanding order total")
    order["refundedCents"] = int(order["refundedCents"]) + amount_cents
    order["status"] = "refunded" if order["refundedCents"] == order["totalCents"] else order["status"]
    return copy.deepcopy(order)


def ledger_snapshot() -> dict[str, dict[str, Any]]:
    """A deep copy of the whole ledger, for tests that prove a read-only
    tool changed nothing."""

    return copy.deepcopy(_ORDERS)


def reset_ledger() -> None:
    """Restore the starting state. Used only by tests."""

    for order in _ORDERS.values():
        order["refundedCents"] = 0
    _ORDERS["WW-10041"]["status"] = "delivered"
    _ORDERS["WW-10042"]["status"] = "delivered"
    _ORDERS["WW-10043"]["status"] = "disputed"
