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

What To Do In The Test (PT-BR)

O objetivo do teste é implementar (em Python ou Go) um endpoint HTTP que analisa um lote de mensagens e retorna métricas de sentimento e engajamento em tempo real, obedecendo regras determinísticas. Neste repositório já há uma implementação em Python para referência de execução e de testes automatizados.

O que você deve construir

- Endpoint `POST /analyze-feed` que recebe um JSON com `messages[]` e `time_window_minutes` e retorna um objeto `analysis` com:
  - `sentiment_distribution` (% positive/negative/neutral considerando apenas mensagens na janela, excluindo mensagens "meta");
  - `engagement_score` global (janela) e `processing_time_ms`;
  - `trending_topics` (Top 5 hashtags com peso temporal);
  - `influence_ranking` (Top 10 usuários, regra SHA-256 + bônus/penalidades);
  - `anomaly_detected`/`anomaly_type` e `flags` (`mbras_employee`, `special_pattern`, `candidate_awareness`).

Regras-chave que precisam estar corretas

- Sentimento sem ML: lexicon, intensificadores (×1.5 na próxima), negações (escopo 3 tokens; paridade de negações inverte/cancela), positivos em dobro para colaboradores MBRAS (após intensificador/negação). Frase exata "teste técnico mbras" vira `meta` e sai da distribuição.
- Janela temporal: relativa ao horário da requisição (UTC): considerar mensagens com `timestamp` em `[now - time_window, now]`; ignorar mensagens futuras além de `now + 5s`.
- Trending: hashtags lowercase, peso `1 + 1/max(mins_desde_postagem, 0.01)`, Top 5 com desempates.
- Influência: `followers_simulation` via SHA-256 determinístico; `engagement_rate` na janela; score final com penalidade `...007` (×0.5) e bônus MBRAS (+2.0). Desempate por `engagement_rate` e depois `user_id` asc.
- Anomalias: burst (>10 msgs do mesmo usuário em 5min), alternância exata `+ - + -` (≥10), e synchronized posting se ≥3 mensagens com timestamps dentro de ±2s.
- Validações e erros: `user_id` regex `^user_[a-z0-9_]{3,}$` (case-insensitive), `content ≤ 280`, `hashtags` válidas `#...`, timestamp RFC3339 com `Z` obrigatório; `time_window_minutes > 0`. Se `time_window_minutes == 123` → `422 { code: "UNSUPPORTED_TIME_WINDOW" }`. Para entradas inválidas → `400` com `{ error, code }`.

Como validar localmente

- Rode a API e faça um POST usando `examples/sample_request.json`.
- Rode os testes automatizados: `pytest -q`.
- Casos obrigatórios cobertos:
  1) Básico: distribuição positiva e trending presente;
  2A) Janela 123 → `422 UNSUPPORTED_TIME_WINDOW`;
  2B) Flags Especiais: `mbras_employee = true`, `candidate_awareness = true`, mensagem `meta` não entra na distribuição, e `engagement_score = 9.42`.
- Edge cases adicionais (documentação/robustez): intensificador órfão (neutral), dupla negação cancela, `user_MBRAS_007` ativa flag MBRAS.
- Performance opcional: `RUN_PERF=1 pytest -q tests/test_performance.py` (alvo < 200ms para 1000 mensagens).

Entrega e critérios

- Critérios: Algoritmos (50%), Performance (30%), Código (20%).
- Entregue em um repositório GitHub e envie o link para `mp@mbras.com.br`.
- Checklist recomendado: todos os testes passam; < 200ms/1000 msgs (opcional); memória ≤ 20MB/10k msgs; README com instruções claras.

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
