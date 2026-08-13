"""Fail-closed scientific verification receipt tests."""

import pytest

from omicsrepro.verification.models import (
    AssuranceLevel,
    VerificationCheck,
    VerificationOutcome,
    VerificationReceipt,
)


def _receipt(*outcomes: VerificationOutcome) -> VerificationReceipt:
    return VerificationReceipt.build(
        tool_version="0.2.0",
        contract="test/v0",
        contract_status="experimental",
        project="fixture",
        subject={},
        assurance=AssuranceLevel.ARTIFACT_INSPECTION,
        checks=[
            VerificationCheck(code=f"T{index}", outcome=outcome, message="fixture")
            for index, outcome in enumerate(outcomes)
        ],
    )


def test_receipt_precedence_is_fail_closed() -> None:
    assert _receipt(VerificationOutcome.PASS).verdict == VerificationOutcome.PASS
    assert (
        _receipt(VerificationOutcome.PASS, VerificationOutcome.WARN).verdict
        == VerificationOutcome.WARN
    )
    assert (
        _receipt(VerificationOutcome.WARN, VerificationOutcome.INDETERMINATE).verdict
        == VerificationOutcome.INDETERMINATE
    )
    assert (
        _receipt(VerificationOutcome.INDETERMINATE, VerificationOutcome.FAIL).verdict
        == VerificationOutcome.FAIL
    )


def test_receipt_is_deterministic_and_has_no_timestamp() -> None:
    first = _receipt(VerificationOutcome.INDETERMINATE)
    second = _receipt(VerificationOutcome.INDETERMINATE)

    assert first.model_dump() == second.model_dump()
    assert "timestamp" not in first.model_dump()
    assert first.summary.indeterminate == 1


def test_empty_receipt_is_rejected_instead_of_passing() -> None:
    with pytest.raises(ValueError, match="at least one check"):
        VerificationReceipt.build(
            tool_version="0.2.0",
            contract="test/v0",
            contract_status="experimental",
            project="fixture",
            subject={},
            assurance=AssuranceLevel.ARTIFACT_INSPECTION,
            checks=[],
        )


def test_only_not_applicable_checks_abstain() -> None:
    receipt = _receipt(VerificationOutcome.NOT_APPLICABLE)

    assert receipt.verdict == VerificationOutcome.INDETERMINATE
