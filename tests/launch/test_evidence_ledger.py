"""Acceptance tests for launch evidence ledger."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_LAUNCH_ROOT = Path(__file__).resolve().parent.parent
if str(__LAUNCH_ROOT) not in sys.path:
    sys.path.insert(0, str(_LAUNCH_ROOT))

from evidence_ledger import EvidenceLedger, EvidenceEntry, StatementClass


def test_evidence_ledger_add_and_get() -> None:
    ledger = EvidenceLedger()
    entry = EvidenceEntry(
        evidence_id="E1",
        source_uri="file://approved/source.pdf",
        page_or_section="page 12",
        statement_class=StatementClass.VERIFIED_FACT,
        confidence=0.95,
        owner_slot="Miles",
        linked_claims=["C1"],
    )
    ledger.add(entry)
    assert ledger.get("E1") is entry
    assert ledger.get("MISSING") is None


def test_evidence_ledger_package_shape() -> None:
    ledger = EvidenceLedger()
    ledger.add(
        EvidenceEntry(
            evidence_id="E2",
            source_uri="https://approved/source.pdf",
            statement_class=StatementClass.ESTIMATE,
        )
    )
    package = ledger.to_package()
    assert package["count"] == 1
    assert package["items"][0]["statement_class"] == "estimate"
    assert package["items"][0]["source_uri"] == "https://approved/source.pdf"
