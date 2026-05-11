# Earnings Call NLP Lab

Earnings Call NLP Lab is a lightweight, auditable Python app for transcript sentiment, management tone, and longitudinal earnings-call analysis.

It analyzes:

- executive confidence language
- risk and caution language
- evasiveness markers
- quarter-over-quarter tone change
- management vs analyst Q&A tone split
- CHP-style verification before conclusions are decision-ready

## Quick Start

```bash
PYTHONPATH=src python3 -m earnings_call_nlp_lab.cli analyze \
  --transcripts examples/transcripts.csv \
  --json
```

## Required Columns

`ticker,quarter,speaker,role,text,source_url`

`role` should usually be `management` or `analyst`.

## Verification

The verifier returns `REQUIRES_HUMAN_VERIFICATION` if:

- source URLs are missing
- fewer than two quarters are supplied
- management text is too short
- required columns are missing

This is a research assistant, not investment advice.
