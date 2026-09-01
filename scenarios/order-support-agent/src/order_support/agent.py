"""The order-support agent loop.

**Deterministic by design, and not a model.** A production agent picks
its next action with an LLM. This one routes on an explicit `kind` field
and does the same thing on every run. That is a deliberate limitation,
not a simplification of convenience: ControlLoop analyzes an agent's
*capability structure* -- which tools it can reach, which identities it
can assume, what it can do transitively -- and that structure is
identical whether a model or a match statement chooses the next call.
Adding a real model would add an API key, a network dependency, and a
nondeterministic run to a repository whose whole value is being forkable
and offline. See SCAN.md.

**Ticket text is data, never instruction.** Routing reads `kind`, which
this module owns. Nothing in `summary` or `reason` can redirect the
agent, because nothing in those fields is ever interpreted. The agent is
deliberately over-privileged -- that is what the scenario demonstrates
-- but its demo harness is not a prompt-injection sandbox, and a reader
should not mistake one for the other.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Literal

from order_support import delegate, tools
from stubs import notifications, orders_api

TicketKind = Literal["order-status", "refund-request", "disputed-charge"]


@dataclass(frozen=True, slots=True)
class Ticket:
    """One fictional support ticket."""

    ticket_id: str
    kind: TicketKind
    order_id: str
    customer_address: str
    summary: str


#: The queue this agent works. Fictional, fixed, and ordered, so a run is
#: reproducible. `.example` is reserved by RFC 2606 and cannot resolve.
QUEUE: tuple[Ticket, ...] = (
    Ticket(
        ticket_id="TCK-501",
        kind="order-status",
        order_id="WW-10041",
        customer_address="a.buyer@customer.example",
        summary="Where is my order?",
    ),
    Ticket(
        ticket_id="TCK-502",
        kind="refund-request",
        order_id="WW-10042",
        customer_address="a.buyer@customer.example",
        summary="Item arrived damaged, requesting a refund.",
    ),
    Ticket(
        ticket_id="TCK-503",
        kind="disputed-charge",
        order_id="WW-10043",
        customer_address="b.shopper@customer.example",
        summary="I did not authorize this charge.",
    ),
)


def handle(ticket: Ticket) -> str:
    """Work one ticket and return a one-line description of what
    happened. Routing is on `kind` only."""

    match ticket.kind:
        case "order-status":
            order = tools.look_up_an_order(ticket.order_id)
            tools.reply_to_customer(
                ticket.ticket_id,
                ticket.customer_address,
                f"Order {ticket.order_id} status",
                f"Your order is currently {order['status']}.",
            )
            return f"{ticket.ticket_id}  looked up {ticket.order_id}, replied to customer"

        case "refund-request":
            order = tools.look_up_an_order(ticket.order_id)
            outstanding = int(order["totalCents"]) - int(order["refundedCents"])
            refunded = tools.issue_a_refund(ticket.order_id, outstanding)
            tools.reply_to_customer(
                ticket.ticket_id,
                ticket.customer_address,
                f"Refund for order {ticket.order_id}",
                "Your refund has been issued.",
            )
            return (
                f"{ticket.ticket_id}  refunded {ticket.order_id} "
                f"(status now {refunded['status']}), replied to customer"
            )

        case "disputed-charge":
            review = delegate.escalate_dispute(ticket.order_id, ticket.summary)
            return (
                f"{ticket.ticket_id}  escalated {ticket.order_id} to "
                f"billing-escalation-agent (accepted={review.accepted})"
            )


def run() -> list[str]:
    """Work the whole queue and return one line per ticket."""

    return [handle(ticket) for ticket in QUEUE]


def main() -> int:
    """Console entry point for `order-support`."""

    print("widgetworks-order-support-agent")
    print("deliberately over-privileged demo agent -- never deploy this\n")

    for line in run():
        print(line)

    print(
        f"\n{len(notifications.outbox())} message(s) would have left the "
        "trust boundary via ses:SendEmail"
    )
    print(f"{len(orders_api.ledger_snapshot())} orders in the ledger")
    print("audit lines written under logs/ -- see controlloop.yaml logged_tools")
    return 0


if __name__ == "__main__":
    sys.exit(main())
