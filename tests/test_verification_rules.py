"""Focused evidence tests for the README "Verification" capability claims.

Binds evidence/matrix.yaml rows C007 and C010-C013: each README refusal
condition must produce a REQUIRES_HUMAN_VERIFICATION gate with the matching
violation, and unverified reports must render a blocking section (row 29 —
unverified results cannot look decision-ready).
"""
from __future__ import annotations

import csv
from pathlib import Path

from earnings_call_nlp_lab.core import _verify, analyze_transcripts

FIELDS = ["ticker", "quarter", "speaker", "role", "text", "source_url"]

MANAGEMENT_TEXT = (
    "We are confident in the strong demand outlook with resilient momentum across every region "
    "and we expect to expand record productivity while monitoring what we can manage "
    "We are confident in the strong demand outlook with resilient momentum across every region "
    "and we expect to expand record productivity while monitoring what we can manage"
)


def _clean_rows() -> list[dict[str, str]]:
    """Two quarters, all columns, source URLs, and >=50 words of management text."""
    return [
        {
            "ticker": "ACME",
            "quarter": "2025Q4",
            "speaker": "CEO",
            "role": "management",
            "text": MANAGEMENT_TEXT,
            "source_url": "https://example.com/acme-2025q4-call",
        },
        {
            "ticker": "ACME",
            "quarter": "2026Q1",
            "speaker": "CEO",
            "role": "management",
            "text": MANAGEMENT_TEXT,
            "source_url": "https://example.com/acme-2026q1-call",
        },
    ]


def test_missing_source_url_requires_human_verification():
    rows = _clean_rows()
    rows[0]["source_url"] = ""
    gate = _verify(rows)
    assert gate.status == "REQUIRES_HUMAN_VERIFICATION"
    assert "one or more transcript rows are missing source_url" in gate.violations
    assert len(gate.violations) == 1


def test_fewer_than_two_quarters_requires_human_verification():
    rows = _clean_rows()
    rows[1]["quarter"] = "2025Q4"
    gate = _verify(rows)
    assert gate.status == "REQUIRES_HUMAN_VERIFICATION"
    assert "longitudinal analysis requires at least two quarters" in gate.violations
    assert len(gate.violations) == 1


def test_short_management_text_requires_human_verification():
    rows = _clean_rows()
    for row in rows:
        row["text"] = "We are confident."
    gate = _verify(rows)
    assert gate.status == "REQUIRES_HUMAN_VERIFICATION"
    assert "management transcript text is too short for reliable tone analysis" in gate.violations
    assert len(gate.violations) == 1


def test_missing_columns_requires_human_verification():
    rows = _clean_rows()
    for row in rows:
        del row["source_url"]
    gate = _verify(rows)
    assert gate.status == "REQUIRES_HUMAN_VERIFICATION"
    assert "missing columns: source_url" in gate.violations


def test_report_renders_blocking_verification_section(tmp_path):
    rows = _clean_rows()
    rows[0]["source_url"] = ""
    path = tmp_path / "transcripts.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    report = analyze_transcripts(path)
    assert report.verification.status == "REQUIRES_HUMAN_VERIFICATION"
    markdown = report.to_markdown()
    assert "Verification: REQUIRES_HUMAN_VERIFICATION" in markdown
    assert "## Blocking Verification Issues" in markdown
