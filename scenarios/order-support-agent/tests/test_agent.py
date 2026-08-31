"""The agent runs, and does what its artifacts say it does."""

from __future__ import annotations

from pathlib import Path

import pytest

from order_support import agent, audit, delegate, tools
from stubs import billing, notifications, orders_api


def test_the_whole_queue_runs_and_reports_one_line_per_ticket() -> None:
    lines = agent.run()

    assert len(lines) == len(agent.QUEUE)
    for ticket, line in zip(agent.QUEUE, lines, strict=True):
        assert line.startswith(ticket.ticket_id)


def test_main_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert agent.main() == 0
    assert "never deploy this" in capsys.readouterr().out


def test_a_disputed_charge_reaches_the_billing_agent() -> None:
    agent.handle(
        agent.Ticket(
            ticket_id="TCK-900",
            kind="disputed-charge",
            order_id="WW-10043",
            customer_address="someone@customer.example",
            summary="not authorized",
        )
    )

    reviewed = billing.reviews()
    assert [review.order_id for review in reviewed] == ["WW-10043"]


def test_the_delegation_target_is_read_from_the_card_not_hardcoded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Point the card at nothing and escalation must fail.

    This is what makes `x-controlloop-delegates-to` load-bearing: remove
    the declaration and the capability really goes away, exactly as the
    `delegates-to` edge disappearing from the ACBOM would imply.
    """

    monkeypatch.setattr(delegate, "declared_targets", lambda: ())

    with pytest.raises(delegate.DelegationError):
        delegate.escalate_dispute("WW-10043", "not authorized")


def test_looking_up_an_order_mutates_nothing() -> None:
    """`controlloop.yaml` declares `read_only: true` for this tool."""

    before = orders_api.ledger_snapshot()
    tools.look_up_an_order("WW-10041")
    assert orders_api.ledger_snapshot() == before


def test_a_refund_really_moves_money() -> None:
    """`controlloop.yaml` declares `financial_action: true` for this
    tool. A declaration nothing backs is the defect this repository
    exists to demonstrate, so assert the money actually moves."""

    before = orders_api.ledger_snapshot()["WW-10042"]["refundedCents"]
    tools.issue_a_refund("WW-10042", 100)
    after = orders_api.ledger_snapshot()["WW-10042"]["refundedCents"]

    assert after == before + 100


def test_a_reply_really_leaves_the_boundary() -> None:
    """`controlloop.yaml` declares `external_communication: true`."""

    assert notifications.outbox() == ()
    tools.reply_to_customer(
        "TCK-901", "someone@customer.example", "subject", "body"
    )
    assert len(notifications.outbox()) == 1


def test_a_refund_cannot_exceed_the_order_total() -> None:
    with pytest.raises(ValueError):
        tools.issue_a_refund("WW-10041", 999_999)


def test_an_unknown_order_is_a_miss_not_an_empty_order() -> None:
    with pytest.raises(orders_api.OrderNotFoundError):
        tools.look_up_an_order("WW-00000")


def test_an_audit_subject_may_not_smuggle_a_newline(tmp_path: Path) -> None:
    """An audit line is one line. A subject carrying a newline could
    forge a second entry."""

    with pytest.raises(ValueError):
        audit.record(
            tmp_path / "a.log", skill_id="lookup-order", subject="a\nb"
        )
