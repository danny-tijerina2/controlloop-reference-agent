"""Handing a disputed charge to the billing-escalation agent.

`agent-card.json` declares:

    "x-controlloop-delegates-to": [
      "sub-agents/billing-escalation/agent-card.json"
    ]

A2A does not standardize a field for one agent declaring delegation to
another -- delegation happens at runtime -- so ControlLoop reads its own
`x-`-prefixed vendor extension, and `controlloop.adapters.a2a` turns each
entry into a `delegates-to` edge.

This module resolves the target **from that list at runtime** rather than
hardcoding the path. That is deliberate: it makes the extension
load-bearing. Delete the key from the card and this agent stops being
able to escalate, which is the same thing the ACBOM edge disappearing
means. A hardcoded path would leave the card decorative, and a
decorative declaration is the defect this whole issue exists to remove.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from order_support.paths import AGENT_CARD, SCENARIO_ROOT
from stubs import billing

DELEGATION_FIELD = "x-controlloop-delegates-to"


class DelegationError(RuntimeError):
    """The declared delegation target could not be resolved. Raised
    rather than falling back to a default, so a broken declaration fails
    loudly instead of silently escalating somewhere else."""


def _load_card(path: Path) -> dict[str, Any]:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DelegationError(f"{path.name} could not be read") from error
    if not isinstance(document, dict):
        raise DelegationError(f"{path.name} is not a JSON object")
    return document


def declared_targets() -> tuple[str, ...]:
    """The repository-relative target paths the primary card declares."""

    targets = _load_card(AGENT_CARD).get(DELEGATION_FIELD)
    if not isinstance(targets, list):
        return ()
    return tuple(target for target in targets if isinstance(target, str) and target)


def resolve_target_name(relative_path: str) -> str:
    """The `name` of the agent a declared target points at.

    The path comes from a committed card, which is untrusted data like
    any other repository content, so it is contained to the scenario
    root before being read.
    """

    candidate = (SCENARIO_ROOT / relative_path).resolve()
    if SCENARIO_ROOT.resolve() not in candidate.parents:
        raise DelegationError("a delegation target must stay inside the scenario")
    name = _load_card(candidate).get("name")
    if not isinstance(name, str) or not name:
        raise DelegationError(f"{relative_path} has no usable name")
    return name


def escalate_dispute(order_id: str, reason: str) -> billing.DisputeReview:
    """Delegate a disputed charge to the declared billing agent.

    Resolves the target from the card, confirms it is the
    billing-escalation agent, and calls that agent's `review-dispute`
    skill.
    """

    targets = declared_targets()
    if not targets:
        raise DelegationError("the agent card declares no delegation target")

    for relative_path in targets:
        if resolve_target_name(relative_path) == billing.AGENT_NAME:
            return billing.review_dispute(order_id, reason)

    raise DelegationError(
        "no declared delegation target implements dispute review"
    )
