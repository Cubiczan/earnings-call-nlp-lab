from earnings_call_nlp_lab.core import analyze_transcripts


def test_earnings_nlp_detects_deteriorating_tone():
    report = analyze_transcripts("examples/transcripts.csv")
    assert report.verification.status == "CLEAR"
    assert report.ticker == "ACME"
    assert report.tone_trend == "DETERIORATING"
    assert report.latest_tone in {"NEGATIVE", "MIXED"}
    assert len(report.quarter_tones) == 2

