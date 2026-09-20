"""Basic import tests for earnings-call-nlp-lab.

Validates that core modules can be imported without errors.
"""

def test_import_package():
    """Test that the package imports and exports analyze_transcripts."""
    from earnings_call_nlp_lab import analyze_transcripts
    assert callable(analyze_transcripts)


def test_import_core_dataclasses():
    """Test that core dataclasses are importable."""
    from earnings_call_nlp_lab.core import (
        QuarterTone,
        VerificationGate,
        EarningsNLPReport,
    )
    assert QuarterTone is not None
    assert VerificationGate is not None
    assert EarningsNLPReport is not None


def test_quarter_tone_dataclass():
    """Test QuarterTone dataclass creation."""
    from earnings_call_nlp_lab.core import QuarterTone
    qt = QuarterTone(
        ticker="AAPL", quarter="Q1 2026",
        confidence_score=10, risk_score=3,
        evasiveness_score=1, net_tone=6,
        summary="Management tone improved."
    )
    assert qt.ticker == "AAPL"
    assert qt.net_tone == 6


def test_verification_gate_dataclass():
    """Test VerificationGate dataclass creation."""
    from earnings_call_nlp_lab.core import VerificationGate
    gate = VerificationGate(status="CLEAR", confidence=100)
    assert gate.status == "CLEAR"
    assert gate.confidence == 100
    assert len(gate.violations) == 0


def test_report_to_dict():
    """Test that EarningsNLPReport.to_dict works."""
    from earnings_call_nlp_lab.core import (
        EarningsNLPReport, QuarterTone, VerificationGate
    )
    report = EarningsNLPReport(
        ticker="TEST", latest_quarter="Q1", latest_tone="POSITIVE",
        tone_trend="STABLE", quarter_tones=[],
        management_vs_analyst={}, verification=VerificationGate("CLEAR", 100),
    )
    d = report.to_dict()
    assert d["ticker"] == "TEST"
    assert isinstance(d["quarter_tones"], list)


def test_report_to_markdown():
    """Test that EarningsNLPReport.to_markdown produces a string."""
    from earnings_call_nlp_lab.core import (
        EarningsNLPReport, QuarterTone, VerificationGate
    )
    report = EarningsNLPReport(
        ticker="TEST", latest_quarter="Q1", latest_tone="MIXED",
        tone_trend="STABLE", quarter_tones=[],
        management_vs_analyst={}, verification=VerificationGate("CLEAR", 100),
    )
    md = report.to_markdown()
    assert "TEST" in md
    assert "Q1" in md


def test_import_report_json():
    """Test that report_json helper imports."""
    from earnings_call_nlp_lab.core import report_json
    assert callable(report_json)


def test_empty_transcript_gates_at_confidence_floor():
    """Regression (row 29 pre-merge review): an empty transcript is the WORST
    case and must score at the canonical confidence floor (50), not the
    equal-weight one-violation score (88). The floor now comes from the
    canonical build_gate severity-hint parameter (cubiczan-resilience 0.2.1);
    the former local override in core._verify is retired."""
    from earnings_call_nlp_lab.core import _verify

    gate = _verify([])
    assert gate.status == "REQUIRES_HUMAN_VERIFICATION"
    assert gate.confidence == 50
    assert gate.violations == ["transcript file is empty"]
