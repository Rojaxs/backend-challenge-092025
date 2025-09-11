# MBRAS Analyzer — Algoritmos Explicados e Especificações

## Normalização de Texto

- Regra: matching acentos-insensível (NFKD) para o lexicon; cálculo usa o token original.
- Não há stemming/lematização: apenas remoção de diacríticos.
- Exemplo:
  - "Adorei" → normaliza para "adorei" → corresponde a lexicon "adorei".
  - "adoré" → normaliza para "adore" → só corresponde se o lexicon contiver exatamente "adore" (não corresponde a "adorei").

Algoritmo:
```python
def normalize_for_matching(token: str) -> str:
    # 1) lowercase
    # 2) NFKD
    # 3) remove diacríticos
    # 4) retorna token normalizado
```

## Tokenização Detalhada

- Pontuação considerada: `.,!?;:"()[]{}…`
- Contrações/hífens: `"não-é"` → `["não", "é"]`
- Hashtags compostas: `"#produto-novo"` → mantém como um único token.
- Emojis: ignorados (não contam como tokens).
- Regex usada: `r'(?:#\w+(?:-\w+)*)|\b\w+\b'` (Unicode).

## Janela Temporal

- Referência: `now_utc` (timestamp da requisição).
- Mensagens consideradas: `timestamp in [now - time_window_minutes, now]` (UTC).
- Exemplo: janela 30 min; `now = 2025-09-10T11:00:00Z` → considerar `>= 2025-09-10T10:30:00Z`.

## Ordem de Precedência (Sentimento)

1. Identificar intensificadores e suas posições (×1.5 na próxima palavra de polaridade).
2. Identificar negações (escopo: próximas 3 tokens). Várias negações acumulam; paridade ímpar inverte; paridade par cancela.
3. Para cada palavra de polaridade:
   a) aplicar intensificador;
   b) aplicar negação (paridade);
   c) aplicar regra MBRAS (×2 apenas para positivos após (a) e (b)).

## Meta-sentimento

- Rígido: somente a frase exata `"teste técnico mbras"` (case-insensitive; sem pontuação extra) é marcada como `meta` e excluída da distribuição.

## Anomalias — Synchronized Posting

- Tolerância: se houver ≥3 mensagens e todas estiverem dentro de uma janela total de ±2s (mesmo segundo ±2), reportar `synchronized_posting`.

## Exemplo 4.1.1 — Sentimento Complexo

Entrada: `"Super adorei!"` | `user_mbras_123`

- Tokenização → `["Super", "adorei"]`
- Lexicon → `adorei = +1`, `super = intensificador`
- Intensificador → `adorei = +1.5`
- Regra MBRAS (positivo em dobro) → `adorei = +3.0`
- Score = `3.0 / 2 = 1.5` ⇒ `positive`

## Exemplo 4.1.2 — Influence Score

```
user_id: "user_mbras_007"
followers = (int(sha256(user_id),16) % 10000) + 100
reactions: 50, shares: 10, views: 500
engagement_rate = 60/500 = 0.12
influence_base = (followers * 0.4) + (0.12 * 0.6)
ajuste 007: ×0.5
MBRAS bonus: +2.0
```

## Timezone e Parsing

- Formato obrigatório: RFC 3339 UTC com `Z` estrito: `YYYY-MM-DDTHH:MM:SSZ`.
- Timestamps malformados ⇒ `400 INVALID_TIMESTAMP`.

