#!/usr/bin/env python3
"""Verify pyproject.toml pins cubiczan-resilience to the audited commit.

The README's "CHP-style verification" claim (evidence/matrix.yaml C007) is
enforced by the canonical VerificationGate — cubiczan_resilience.verification_gate
(portfolio propagation row 29). This script binds that claim to the dependency
pin itself: pyproject.toml must resolve cubiczan-resilience to the exact audited
commit this repo's verification behavior was checked against. A moved, loosened,
or removed pin fails the gate. Stdlib-only, deterministic, no network.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDITED_COMMIT = "2a35120bd21ed967a8d72a34c2d0f3e6807cad67"


def main() -> int:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(
        r"cubiczan-resilience @ git\+https://github\.com/icohangar-ops/"
        r"cubiczan-resilience\.git@([0-9a-f]{40})",
        text,
    )
    if not match:
        print("FAIL: cubiczan-resilience git commit pin not found in pyproject.toml")
        return 1
    if match.group(1) != AUDITED_COMMIT:
        print(f"FAIL: cubiczan-resilience pinned at {match.group(1)}, audited commit is {AUDITED_COMMIT}")
        return 1
    print(f"OK: cubiczan-resilience pinned at audited commit {AUDITED_COMMIT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
