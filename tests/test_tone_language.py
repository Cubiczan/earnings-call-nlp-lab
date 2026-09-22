"""Focused evidence tests for the README "It analyzes" capability claims.

Each test binds one claim in evidence/matrix.yaml (C002-C006) to deterministic
behavior of earnings_call_nlp_lab.core: a synthetic transcript with hand-counted
term frequencies must produce exactly the scores the claim implies.
"""
from __future__ import annotations

import csv
from pathlib import Path

from earnings_call_nlp_lab.core import analyze_transcripts

FIELDS = ["ticker", "quarter", "speaker", "role", "text", "source_url"]


def _write_csv(tmp_path: Path, rows: list[dict[str, str]]) -> Path:
    path = tmp_path / "transcripts.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def _row(quarter: str, role: str, text: str, source: str = "https://example.com/call") -> dict[str, str]:
    return {
        "ticker": "ACME",
        "quarter": quarter,
        "speaker": "CEO",
        "role": role,
        "text": text,
        "source_url": source,
    }


def test_confidence_language_is_counted(tmp_path):
    path = _write_csv(
        tmp_path,
        [_row("2026Q1", "management", "We are confident demand momentum is strong and resilient, and we will expand into the record.")],
    )
    report = analyze_transcripts(path)
    tone = report.quarter_tones[0]
    # confident, demand, momentum, strong, resilient, expand, record — exactly 7 hits.
    assert tone.confidence_score == 7
    assert tone.risk_score == 0
    assert tone.evasiveness_score == 0


def test_risk_language_is_counted(tmp_path):
    path = _write_csv(
        tmp_path,
        [_row("2026Q1", "management", "The outlook is uncertain and every headwind brings pressure: a decline with soft guidance means risk is volatile and a delay is challenging.")],
    )
    report = analyze_transcripts(path)
    tone = report.quarter_tones[0]
    # uncertain, headwind, pressure, decline, soft, risk, volatile, delay, challenging — exactly 9 hits.
    assert tone.risk_score == 9
    assert tone.confidence_score == 0
    assert tone.evasiveness_score == 0


def test_evasive_markers_are_counted(tmp_path):
    path = _write_csv(
        tmp_path,
        [_row("2026Q1", "management", "It is too early to guide, we do not disclose customer counts, and it depends on the mix.")],
    )
    report = analyze_transcripts(path)
    tone = report.quarter_tones[0]
    # "too early", "we do not disclose", "depends" — exactly 3 phrase hits.
    assert tone.evasiveness_score == 3
    # net tone = confidence(0) - risk(0) - evasiveness(3) * 2.
    assert tone.net_tone == -6


def test_role_split_separates_management_and_analyst(tmp_path):
    path = _write_csv(
        tmp_path,
        [
            _row("2026Q1", "management", "We are confident and strong."),
            _row("2026Q1", "analyst", "Headwinds and decline create risk."),
        ],
    )
    report = analyze_transcripts(path)
    assert report.management_vs_analyst == {"management": 2, "analyst": -3}


def test_qoq_trend_improving_then_stable(tmp_path):
    path = _write_csv(
        tmp_path,
        [
            _row("2026Q1", "management", "Risk remains and headwinds persist."),
            _row("2026Q2", "management", "We are confident and strong."),
            _row("2026Q3", "management", "We are confident and strong."),
        ],
    )
    report = analyze_transcripts(path)
    assert len(report.quarter_tones) == 3
    assert report.quarter_tones[0].net_tone == -1
    assert report.quarter_tones[1].net_tone == 2
    assert report.quarter_tones[2].net_tone == 2
    assert report.quarter_tones[1].net_tone > report.quarter_tones[0].net_tone
    assert report.tone_trend == "STABLE"
