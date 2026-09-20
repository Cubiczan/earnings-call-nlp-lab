"""Earnings call NLP workflow."""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List

from cubiczan_resilience.verification_gate import (
    SEVERITY_FLOOR,
    VerificationGate,
    build_gate,
)

__all__ = ["QuarterTone", "VerificationGate", "EarningsNLPReport", "analyze_transcripts"]


REQUIRED_COLUMNS = {"ticker", "quarter", "speaker", "role", "text", "source_url"}
CONFIDENCE_TERMS = {"confident", "strong", "resilient", "accelerating", "record", "expand", "demand", "momentum"}
RISK_TERMS = {"uncertain", "headwind", "pressure", "challenging", "decline", "soft", "risk", "volatile", "delay"}
EVASIVE_TERMS = {"not going to", "hard to say", "too early", "we do not disclose", "cannot comment", "depends"}


@dataclass
class QuarterTone:
    ticker: str
    quarter: str
    confidence_score: int
    risk_score: int
    evasiveness_score: int
    net_tone: int
    summary: str


# VerificationGate moved to the canonical cubiczan_resilience.verification_gate
# module (row 29): one deterministic confidence rule for the whole portfolio
# (PENALTY_PER_VIOLATION=12, CONFIDENCE_FLOOR=50). This module re-exports it
# for backwards-compatible imports; construct gates with build_gate().
@dataclass
class EarningsNLPReport:
    ticker: str
    latest_quarter: str
    latest_tone: str
    tone_trend: str
    quarter_tones: List[QuarterTone]
    management_vs_analyst: Dict[str, int]
    verification: VerificationGate

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)

    def to_markdown(self) -> str:
        lines = [
            "# Earnings Call NLP Lab",
            f"- Ticker: {self.ticker}",
            f"- Latest Quarter: {self.latest_quarter}",
            f"- Latest Tone: {self.latest_tone}",
            f"- Tone Trend: {self.tone_trend}",
            f"- Verification: {self.verification.status}",
            "",
            "## Quarter Tone",
        ]
        for tone in self.quarter_tones:
            lines.append(f"- {tone.quarter}: net {tone.net_tone}, confidence {tone.confidence_score}, risk {tone.risk_score}, evasive {tone.evasiveness_score}")
        if self.verification.violations:
            lines.append("")
            lines.append("## Blocking Verification Issues")
            lines.extend(f"- {item}" for item in self.verification.violations)
        return "\n".join(lines)


def analyze_transcripts(transcripts_path: str | Path) -> EarningsNLPReport:
    rows = _read_csv(transcripts_path)
    by_quarter = defaultdict(list)
    ticker = rows[0].get("ticker", "UNKNOWN") if rows else "UNKNOWN"
    for row in rows:
        by_quarter[row["quarter"]].append(row)

    quarter_tones = [_score_quarter(ticker, quarter, records) for quarter, records in sorted(by_quarter.items())]
    latest = quarter_tones[-1] if quarter_tones else QuarterTone(ticker, "UNKNOWN", 0, 0, 0, 0, "No data.")
    prior = quarter_tones[-2] if len(quarter_tones) > 1 else None
    trend = "IMPROVING" if prior and latest.net_tone > prior.net_tone else "DETERIORATING" if prior and latest.net_tone < prior.net_tone else "STABLE"
    latest_tone = "POSITIVE" if latest.net_tone > 2 else "NEGATIVE" if latest.net_tone < -2 else "MIXED"
    verification = _verify(rows)
    return EarningsNLPReport(
        ticker=ticker,
        latest_quarter=latest.quarter,
        latest_tone=latest_tone,
        tone_trend=trend,
        quarter_tones=quarter_tones,
        management_vs_analyst=_role_split(rows),
        verification=verification,
    )


def _read_csv(path: str | Path) -> List[Dict[str, str]]:
    with Path(path).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _score_quarter(ticker: str, quarter: str, rows: List[Dict[str, str]]) -> QuarterTone:
    management_text = " ".join(row["text"] for row in rows if row.get("role", "").lower() == "management")
    lowered = management_text.lower()
    confidence = sum(len(re.findall(rf"\b{re.escape(term)}\b", lowered)) for term in CONFIDENCE_TERMS)
    risk = sum(len(re.findall(rf"\b{re.escape(term)}\b", lowered)) for term in RISK_TERMS)
    evasive = sum(lowered.count(term) for term in EVASIVE_TERMS)
    net = confidence - risk - evasive * 2
    summary = "Management tone improved." if net > 2 else "Management tone weakened." if net < -2 else "Management tone was mixed."
    return QuarterTone(
        ticker=ticker,
        quarter=quarter,
        confidence_score=confidence,
        risk_score=risk,
        evasiveness_score=evasive,
        net_tone=net,
        summary=summary,
    )


def _role_split(rows: List[Dict[str, str]]) -> Dict[str, int]:
    split = defaultdict(int)
    for row in rows:
        text = row.get("text", "").lower()
        score = sum(text.count(term) for term in CONFIDENCE_TERMS) - sum(text.count(term) for term in RISK_TERMS)
        split[row.get("role", "unknown")] += score
    return dict(split)


def _verify(rows: List[Dict[str, str]]) -> VerificationGate:
    violations: List[str] = []
    if not rows:
        # An empty transcript is categorically worse than one minor gap, so
        # the gate pins at the floor. The severity-hint parameter
        # (cubiczan-resilience 0.2.1) carries that decision in the canonical
        # module — this repo's former local override existed only until the
        # parameter did, per its keep-in-sync migration condition (row 29).
        violations.append("transcript file is empty")
        return build_gate(violations, severity_hint=SEVERITY_FLOOR)
    missing = REQUIRED_COLUMNS - set(rows[0].keys())
    if missing:
        violations.append(f"missing columns: {', '.join(sorted(missing))}")
    if len({row.get("quarter") for row in rows}) < 2:
        violations.append("longitudinal analysis requires at least two quarters")
    if any(not row.get("source_url") for row in rows):
        violations.append("one or more transcript rows are missing source_url")
    management_words = " ".join(row.get("text", "") for row in rows if row.get("role", "").lower() == "management").split()
    if len(management_words) < 50:
        violations.append("management transcript text is too short for reliable tone analysis")
    # Canonical arithmetic (row 29): confidence and status come from the
    # shared rule — PENALTY_PER_VIOLATION=12 per violation, CONFIDENCE_FLOOR=50.
    return build_gate(violations)


def report_json(report: EarningsNLPReport) -> str:
    return json.dumps(report.to_dict(), indent=2)

