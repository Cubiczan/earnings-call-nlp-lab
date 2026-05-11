"""CLI for Earnings Call NLP Lab."""
from __future__ import annotations

import argparse
import sys

from earnings_call_nlp_lab.core import analyze_transcripts, report_json


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="earnings-call-nlp-lab")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze", help="Analyze earnings-call transcripts.")
    analyze.add_argument("--transcripts", required=True)
    analyze.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if args.command == "analyze":
        report = analyze_transcripts(args.transcripts)
        sys.stdout.write((report_json(report) if args.json else report.to_markdown()) + "\n")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

