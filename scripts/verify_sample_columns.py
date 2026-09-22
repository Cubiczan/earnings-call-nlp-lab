#!/usr/bin/env python3
"""Verify the README's documented required columns match the analyzer and the sample data.

Binds the README "Required Columns" claim (evidence/matrix.yaml C009): three
surfaces must name exactly the same column set —

  1. the backticked column list under README.md "## Required Columns",
  2. REQUIRED_COLUMNS in src/earnings_call_nlp_lab/core.py,
  3. the header of examples/transcripts.csv (the Quick Start dataset).

Stdlib-only, deterministic, no network.
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    parts = readme.split("## Required Columns", 1)
    if len(parts) != 2:
        print("FAIL: README.md no longer documents a '## Required Columns' section")
        return 1
    documented_match = re.search(r"`([a-z_,\s]+)`", parts[1])
    if not documented_match:
        print("FAIL: no backticked column list found under README '## Required Columns'")
        return 1
    documented = {c.strip() for c in documented_match.group(1).split(",") if c.strip()}

    core_text = (ROOT / "src" / "earnings_call_nlp_lab" / "core.py").read_text(encoding="utf-8")
    required_match = re.search(r"REQUIRED_COLUMNS\s*=\s*\{([^}]*)\}", core_text)
    if not required_match:
        print("FAIL: REQUIRED_COLUMNS set not found in src/earnings_call_nlp_lab/core.py")
        return 1
    required = set(re.findall(r'"([^"]+)"', required_match.group(1)))

    with (ROOT / "examples" / "transcripts.csv").open(newline="", encoding="utf-8") as handle:
        header = set(next(csv.reader(handle)))

    if not documented:
        print("FAIL: README documented column list is empty")
        return 1
    if documented != required:
        print(f"FAIL: README columns {sorted(documented)} != core.py REQUIRED_COLUMNS {sorted(required)}")
        return 1
    if header != required:
        print(f"FAIL: examples/transcripts.csv header {sorted(header)} != required columns {sorted(required)}")
        return 1
    print(f"OK: README, core.py REQUIRED_COLUMNS, and sample header agree on {len(required)} columns: {sorted(required)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
