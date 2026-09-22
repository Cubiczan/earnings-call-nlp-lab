"""Binds the README Quick Start claim (evidence/matrix.yaml C008).

The documented one-command run must work as committed: the exact README
invocation against the committed sample dataset emits a JSON report.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_readme_quick_start_command_emits_json():
    env = dict(os.environ, PYTHONPATH=str(REPO_ROOT / "src"))
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "earnings_call_nlp_lab.cli",
            "analyze",
            "--transcripts",
            "examples/transcripts.csv",
            "--json",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    report = json.loads(proc.stdout)
    assert report["ticker"] == "ACME"
    assert report["verification"]["status"] == "CLEAR"
    assert len(report["quarter_tones"]) == 2
