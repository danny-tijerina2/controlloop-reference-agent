"""Append-only audit lines for privileged tool calls.

`controlloop.yaml` declares an `audit_path` for each of this agent's
three tools under `logged_tools`. The `policy.missing-action-logging`
rule blocks the gate when a tool declared privileged has no audit path,
so those paths are part of the agent's approved posture -- and a path
that nothing ever writes to is a declaration with nothing behind it.
This module is what makes them true.

**What an audit line may contain.** The tool, the skill id, and the
identifier of the thing acted on. Nothing else. Not the order total, not
the customer's email address, not the ticket body, and never a
credential. An audit trail is evidence that an action happened; it is
not a second copy of the data the action touched. Writing the payload
into a log is how a privileged action's log becomes a more attractive
target than the action itself.
"""

from __future__ import annotations

from pathlib import Path

from order_support.paths import LOG_DIRECTORY

#: Written into every line so a reader can tell this is demo output.
_MARKER = "reference-scenario"


def record(audit_path: Path, *, skill_id: str, subject: str) -> Path:
    """Append one line to `audit_path`, creating `logs/` if needed.

    `subject` is an identifier -- an order id, a ticket id -- never a
    payload. Callers pass an identifier or nothing.
    """

    if "\n" in subject or "\r" in subject:
        raise ValueError("an audit subject may not contain a newline")
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    with audit_path.open("a", encoding="utf-8") as handle:
        handle.write(f"{_MARKER} skill={skill_id} subject={subject}\n")
    return audit_path


def resolve(declared_path: str) -> Path:
    """Turn an `audit_path` string from `controlloop.yaml` into a real
    path under the scenario root."""

    candidate = (LOG_DIRECTORY.parent / declared_path).resolve()
    root = LOG_DIRECTORY.parent.resolve()
    if root not in candidate.parents:
        raise ValueError("an audit path must stay inside the scenario")
    return candidate
