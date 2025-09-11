# backend-challenge-092025

MBRAS — Backend Challenge (Python ou Go)

This repository contains a Python (FastAPI) implementation of the real-time feed analyzer as specified.

Quickstart — Python

- Prereqs: Python 3.11+
- Create venv (optional): `python -m venv .venv && source .venv/bin/activate`
- Install deps: `pip install fastapi uvicorn pytest`
- Run server: `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
- Test: `pytest -q`

API

- POST `/analyze-feed`
- See `examples/sample_request.json` for a sample body.

Notes

- Implements lexicon-based sentiment, MBRAS-specific rules, trending topics, influence ranking, anomalies, and strict validations according to the brief.
- Business rule: `time_window_minutes == 123` returns HTTP 422 with `{ code: "UNSUPPORTED_TIME_WINDOW" }`.
- Processing time is measured as wall clock and returned in `analysis.processing_time_ms`.
