"""The billing-escalation sub-agent, in memory.

`sub-agents/billing-escalation/agent-card.json` advertises two skills,
`review-dispute` and `issue-chargeback-response`. Both are implemented
here so the `delegates-to` edge in the ACBOM points at something that
runs, rather than at a card describing an agent that does not exist.

This is a separate agent behind its own card. The order-support agent
reaches it only through `order_support.delegate`, which resolves the
target from the primary card's `x-controlloop-delegates-to` list.
"""

from __future__ import annotations

from dataclasses import dataclass

AGENT_NAME = "billing-escalation-agent"


@dataclass(frozen=True, slots=True)
class DisputeReview:
    """The outcome of `review-dispute`."""

    order_id: str
    accepted: bool
    rationale: str


_REVIEWS: list[DisputeReview] = []
_CHARGEBACK_RESPONSES: list[str] = []


def review_dispute(order_id: str, reason: str) -> DisputeReview:
    """Card skill `review-dispute`.

    Deterministic by design: a disputed charge is accepted for review
    when a reason was supplied. There is no model here and no
    randomness, so the scenario produces the same result on every run.
    """

    accepted = bool(reason.strip())
    review = DisputeReview(
        order_id=order_id,
        accepted=accepted,
        rationale="reason supplied" if accepted else "no reason supplied",
    )
    _REVIEWS.append(review)
    return review


def issue_chargeback_response(order_id: str) -> str:
    """Card skill `issue-chargeback-response`."""

    reference = f"CB-{order_id}"
    _CHARGEBACK_RESPONSES.append(reference)
    return reference


def reviews() -> tuple[DisputeReview, ...]:
    return tuple(_REVIEWS)


def reset() -> None:
    """Used only by tests."""

    _REVIEWS.clear()
    _CHARGEBACK_RESPONSES.clear()
