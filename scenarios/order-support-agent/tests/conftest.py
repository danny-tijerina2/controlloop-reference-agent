"""Shared fixtures.

Every stub holds module-level state so the agent can be read as ordinary
code rather than as a dependency-injection exercise. Tests therefore
reset that state between cases, and write audit lines into a temporary
directory so a test run never appends to a developer's real `logs/`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from order_support import audit
from stubs import billing, notifications, orders_api


@pytest.fixture(autouse=True)
def clean_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset every stub and redirect audit output into `tmp_path`."""

    orders_api.reset_ledger()
    notifications.reset_outbox()
    billing.reset()

    def _resolve(declared_path: str) -> Path:
        return tmp_path / declared_path

    monkeypatch.setattr(audit, "resolve", _resolve)
