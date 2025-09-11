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

Guia Completo de Implementação — 1 Dia

Etapa 1 — Clarificações Críticas

1) Tokenização e Normalização Detalhada

- Processo de tokenização:
  1) Split por espaços e pontuação: `.,!?;:"()[]{}…`
  2) Manter hashtags intactas: `#produto-novo` conta como 1 token
  3) Para matching do lexicon: converter tokens para lowercase e aplicar NFKD (remover acentos)
  4) Para cálculos: usar o token original (case e acentos preservados)
- Normalização para matching:
  - "Adoré" → "adore" (busca no lexicon)
  - "NÃO" → "nao" (busca no lexicon)
  - Hashtags são ignoradas no processamento de sentimento
- Exemplo:
  - Input: "Não muito bom! #produto"
  - Tokens: ["Não", "muito", "bom", "#produto"]
  - Para lexicon: ["nao", "muito", "bom"] (hashtag excluída)

2) Janela Temporal (baseada no horário da requisição)

- Ponto de referência: timestamp atual da requisição em UTC
- Filtro: incluir apenas mensagens com `timestamp >= (now_utc - time_window_minutes)`
- Exemplo: `time_window_minutes = 30`, `now = 2025-09-10T11:00:00Z` → considerar `>= 2025-09-10T10:30:00Z`

3) Algoritmo de Sentimento (ordem fixa)

- Sequência por mensagem:
  1) Tokenizar/normalizar (conforme acima)
  2) Mapear intensificadores e negações (escopo de 3 tokens)
  3) Para cada palavra de polaridade:
     - a) valor base (+1 positivos, -1 negativos)
     - b) aplicar intensificador (×1.5)
     - c) aplicar negação conforme paridade (×-1 se ímpar)
     - d) aplicar regra MBRAS (×2 apenas para positivos após b/c)
  4) Score: `(Σpos - Σneg) / total_words`
- Exemplos:
  - "Não muito bom" (usuário normal): bom = +1 ×1.5 → -1.5 (negado) ⇒ score = -1.5/3 = -0.5 ⇒ negative
  - "Super adorei!" (user_mbras_123): adorei = +1 ×1.5 ×2 = +3.0 ⇒ score = 3.0/2 = 1.5 ⇒ positive

4) Edge Cases Fundamentais (casos obrigatórios)

- Teste 3A — Intensificador órfão: "muito" ⇒ neutral 100%
- Teste 3B — Negação dupla: "não não gostei" ⇒ negative > 0 (negações dentro do escopo não necessariamente se cancelam se intercaladas)
- Teste 3C — Case sensitivity MBRAS: `user_MBRAS_007` ⇒ `flags.mbras_employee = true`

Etapa 2 — Documentação Essencial

Exemplo Detalhado de Cálculo

Input (resumido):

```json
{
  "messages": [
    {
      "id": "msg_example",
      "content": "Super adorei o produto!",
      "timestamp": "2025-09-10T10:45:00Z",
      "user_id": "user_mbras_007",
      "hashtags": ["#review"],
      "reactions": 20,
      "shares": 5,
      "views": 200
    }
  ],
  "time_window_minutes": 30
}
```

Passo-a-passo (sentimento): tokens ["Super", "adorei", "o", "produto"], intensificador em "adorei" (+1 → +1.5), MBRAS dobra positivo (+3.0); score = 3.0/4 = 0.75 ⇒ positive.

Influência: aplica followers simulados via SHA-256, taxa de engajamento `(reactions+shares)/views = 25/200 = 0.125`, 007 reduz ×0.5 e bônus MBRAS +2.0 ao final.

Etapa 3 — Exemplos e Testes

- `examples/sample_request.json`: exemplo de payload básico
- `examples/edge_cases.json`: intensificador órfão, negação dupla, case MBRAS
- `tests/test_analyzer.py`: contém todos os 6 casos obrigatórios, incluindo 2A/2B
- Performance opcional: `tests/test_performance.py` (habilite com `RUN_PERF=1`)

Etapa 4 — Estrutura e Checklist Final

Estrutura mínima do projeto

```
projeto/
├── README.md                    # Setup e execução (≤ 5 comandos)
├── main.py | main.go            # Servidor web principal
├── sentiment_analyzer.py | sentiment.go  # Lógica de análise
├── tests/
│   └── test_analyzer.py | analyzer_test.go  # 6 casos obrigatórios
├── examples/
│   ├── sample_request.json
│   └── edge_cases.json
└── requirements.txt | go.mod
```

Arquivos obrigatórios para entrega

- Implementação funcional dos 6 casos:
  - Teste 1: Básico (positivo)
  - Teste 2A: 422 para janela 123
  - Teste 2B: Flags especiais + engagement_score 9.42
  - Teste 3A: Intensificador órfão → neutral 100%
  - Teste 3B: Negação dupla → negative > 0
  - Teste 3C: Case MBRAS → mbras_employee true
- README com setup em até 5 comandos
- Código organizado e determinístico

Checklist de conformidade final

- Testes obrigatórios passam (1, 2A, 2B, 3A, 3B, 3C)
- Tempo de resposta < 200ms (1000 msgs, opcional)
- Memória ≤ 20MB (10k msgs, meta de doc.)
- Validações 400/422 conforme especificado
- Tokenização/normalização, janela temporal e precedência corretas
- Flags MBRAS case-insensitive e anomalias ativas
- Trending topics com peso temporal

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
