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

Documentation & Specs

- Normalização/Tokenização, ordem de precedência, exemplos e regras detalhadas em `docs/algorithm_examples.md`.
- OpenAPI schema em `docs/swagger.yaml`.
- Janela temporal relativa ao horário da requisição (UTC atual): somente mensagens no intervalo `[now - time_window, now]`.
- Timestamps obrigatórios em RFC 3339 estrito com sufixo `Z` (UTC). Erros de parsing retornam `400 INVALID_TIMESTAMP`.

Project Structure

```
projeto/
├── README.md
├── main.py
├── sentiment_analyzer.py
├── tests/
│   ├── test_analyzer.py
│   └── test_performance.py (habilite com RUN_PERF=1)
├── examples/
│   ├── sample_request.json
│   ├── edge_cases.json
│   └── generate_performance_data.py
└── docs/
    ├── swagger.yaml
    └── algorithm_examples.md
```

Performance

- Objetivo: < 200ms para 1000 mensagens; memória ≤ 20MB para 10k mensagens (meta de documentação).
- Rode o teste de performance localmente: `RUN_PERF=1 pytest -q tests/test_performance.py`.
