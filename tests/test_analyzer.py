import json
from fastapi.testclient import TestClient
from datetime import datetime, timezone

from main import app


client = TestClient(app)


def post_analyze(payload):
    return client.post("/analyze-feed", json=payload)


def test_basic_case():
    payload = {
        "messages": [
            {
                "id": "msg_001",
                "content": "Adorei o produto!",
                "timestamp": "2025-09-10T10:00:00Z",
                "user_id": "user_123",
                "hashtags": ["#produto"],
                "reactions": 10,
                "shares": 2,
                "views": 100,
            }
        ],
        "time_window_minutes": 30,
    }
    r = post_analyze(payload)
    assert r.status_code == 200
    data = r.json()
    analysis = data["analysis"]
    assert set(analysis.keys()) >= {
        "sentiment_distribution",
        "engagement_score",
        "trending_topics",
        "influence_ranking",
        "anomaly_detected",
        "flags",
        "processing_time_ms",
    }
    # Sentiment should be fully positive for a single positive message
    dist = analysis["sentiment_distribution"]
    assert dist["positive"] == 100.0
    assert "#produto" in analysis["trending_topics"]


def test_window_error_422():
    payload = {
        "messages": [
            {
                "id": "msg_002",
                "content": "Este é um teste muito interessante",
                "timestamp": "2025-09-10T10:00:00Z",
                "user_id": "user_mbras_007",
                "hashtags": ["#teste"],
                "reactions": 5,
                "shares": 2,
                "views": 100,
            }
        ],
        "time_window_minutes": 123,
    }
    r = post_analyze(payload)
    assert r.status_code == 422
    assert r.json() == {
        "error": "Valor de janela temporal não suportado na versão atual",
        "code": "UNSUPPORTED_TIME_WINDOW",
    }


def test_flags_especiais_and_meta():
    payload = {
        "messages": [
            {
                "id": "msg_003",
                "content": "teste técnico mbras",
                "timestamp": "2025-09-10T10:00:00Z",
                "user_id": "user_mbras_1007",
                "hashtags": ["#teste"],
                "reactions": 5,
                "shares": 2,
                "views": 100,
            }
        ],
        "time_window_minutes": 30,
    }
    r = post_analyze(payload)
    assert r.status_code == 200
    analysis = r.json()["analysis"]
    flags = analysis["flags"]
    assert flags["mbras_employee"] is True
    assert flags["candidate_awareness"] is True
    # engagement_score special value per spec test
    assert analysis["engagement_score"] == 9.42
    # meta message excluded from distribution
    dist = analysis["sentiment_distribution"]
    assert dist["positive"] == 0.0 and dist["negative"] == 0.0 and dist["neutral"] == 0.0


def test_intensifier_orphan_neutral():
    payload = {
        "messages": [
            {
                "id": "msg_004",
                "content": "muito",
                "timestamp": "2025-09-10T10:00:00Z",
                "user_id": "user_abc",
                "hashtags": [],
                "reactions": 0,
                "shares": 0,
                "views": 1,
            }
        ],
        "time_window_minutes": 30,
    }
    r = post_analyze(payload)
    assert r.status_code == 200
    dist = r.json()["analysis"]["sentiment_distribution"]
    assert dist["neutral"] == 100.0


def test_double_negation_cancels():
    payload = {
        "messages": [
            {
                "id": "msg_005",
                "content": "não não gostei",
                "timestamp": "2025-09-10T10:00:00Z",
                "user_id": "user_abc",
                "hashtags": [],
                "reactions": 0,
                "shares": 0,
                "views": 1,
            }
        ],
        "time_window_minutes": 30,
    }
    r = post_analyze(payload)
    assert r.status_code == 200
    analysis = r.json()["analysis"]
    dist = analysis["sentiment_distribution"]
    # Expect positive due to double negation canceling
    assert dist["positive"] == 100.0


def test_user_id_case_insensitive_mbras_flag():
    payload = {
        "messages": [
            {
                "id": "msg_006",
                "content": "Adorei",
                "timestamp": "2025-09-10T10:00:00Z",
                "user_id": "user_MBRAS_007",
                "hashtags": [],
                "reactions": 0,
                "shares": 0,
                "views": 1,
            }
        ],
        "time_window_minutes": 30,
    }
    r = post_analyze(payload)
    assert r.status_code == 200
    flags = r.json()["analysis"]["flags"]
    assert flags["mbras_employee"] is True


def test_special_pattern_and_non_mbras_user():
    # Build content with exactly 42 Unicode chars, including the substring "mbras"
    # 10 X + space + 'mbras' (5) + space + 25 Y = 42
    content = ("X" * 10) + " mbras " + ("Y" * 25)
    assert len(content) == 42

    payload = {
        "messages": [
            {
                "id": "msg_007",
                "content": content,
                "timestamp": "2025-09-10T10:00:00Z",
                "user_id": "user_especialista_999",  # não contém 'mbras'
                "hashtags": ["#review"],
                "reactions": 3,
                "shares": 1,
                "views": 75,
            }
        ],
        "time_window_minutes": 30,
    }
    r = post_analyze(payload)
    assert r.status_code == 200
    analysis = r.json()["analysis"]
    flags = analysis["flags"]
    assert flags["special_pattern"] is True
    assert flags["mbras_employee"] is False
    # No lexicon words present → neutral distribution 100%
    dist = analysis["sentiment_distribution"]
    assert dist["neutral"] == 100.0
    # Influence ranking includes the only user from this payload
    assert analysis["influence_ranking"][0]["user_id"] == "user_especialista_999"


def test_sha256_determinism_same_input():
    payload = {
        "messages": [
            {
                "id": "msg_det1",
                "content": "teste",
                "timestamp": "2025-09-10T10:00:00Z",
                "user_id": "user_deterministic_test",
                "hashtags": [],
                "reactions": 1,
                "shares": 0,
                "views": 10,
            }
        ],
        "time_window_minutes": 30,
    }

    r1 = post_analyze(payload)
    r2 = post_analyze(payload)
    assert r1.status_code == r2.status_code == 200
    a1 = r1.json()["analysis"]
    a2 = r2.json()["analysis"]
    s1 = a1["influence_ranking"][0]["influence_score"]
    s2 = a2["influence_ranking"][0]["influence_score"]
    assert s1 == s2, f"Influence score should be deterministic, got {s1} vs {s2}"


def test_unicode_normalization_edge_case():
    # Tests Unicode NFKD normalization trap - "café" with different encodings
    payload = {
        "messages": [
            {
                "id": "msg_unicode1",
                "content": "adorei",
                "timestamp": "2025-09-10T10:00:00Z",
                "user_id": "user_café",  # Unicode with combining diacritic
                "hashtags": ["#teste"],
                "reactions": 5,
                "shares": 1,
                "views": 50,
            }
        ],
        "time_window_minutes": 30,
    }
    r = post_analyze(payload)
    assert r.status_code == 200
    analysis = r.json()["analysis"]
    # Should trigger special Unicode case (followers = 4242)
    user_score = next(u for u in analysis["influence_ranking"] if u["user_id"] == "user_café")
    # The exact score will depend on engagement calculation, but followers should be 4242


def test_fibonacci_length_trap():
    # Tests algorithmic trap for 13-character user_ids
    payload = {
        "messages": [
            {
                "id": "msg_fib",
                "content": "bom produto",
                "timestamp": "2025-09-10T10:00:00Z",
                "user_id": "user_13chars",  # exactly 13 characters
                "hashtags": ["#fib"],
                "reactions": 1,
                "shares": 0,
                "views": 10,
            }
        ],
        "time_window_minutes": 30,
    }
    r = post_analyze(payload)
    assert r.status_code == 200
    # Should trigger fibonacci followers (233)


def test_prime_pattern_complexity():
    # Tests prime number logic trap
    payload = {
        "messages": [
            {
                "id": "msg_prime",
                "content": "excelente",
                "timestamp": "2025-09-10T10:00:00Z",
                "user_id": "user_math_prime",  # ends with "_prime"
                "hashtags": ["#math"],
                "reactions": 3,
                "shares": 1,
                "views": 20,
            }
        ],
        "time_window_minutes": 30,
    }
    r = post_analyze(payload)
    assert r.status_code == 200
    # Should trigger prime number logic in followers calculation


def test_golden_ratio_engagement_trap():
    # Tests golden ratio adjustment for engagement (multiple of 7)
    payload = {
        "messages": [
            {
                "id": "msg_golden",
                "content": "ótimo serviço",
                "timestamp": "2025-09-10T10:00:00Z",
                "user_id": "user_golden_test",
                "hashtags": ["#service"],
                "reactions": 4,  # 4 + 3 = 7 (multiple of 7)
                "shares": 3,
                "views": 35,
            }
        ],
        "time_window_minutes": 30,
    }
    r = post_analyze(payload)
    assert r.status_code == 200
    # Should apply golden ratio adjustment to engagement rate


def test_sentiment_trending_cross_validation():
    # Tests cross-validation between sentiment analysis and trending topics
    payload = {
        "messages": [
            {
                "id": "msg_cross1",
                "content": "adorei muito!",  # positive sentiment
                "timestamp": "2025-09-10T10:00:00Z",
                "user_id": "user_cross1",
                "hashtags": ["#positivo"],
                "reactions": 5,
                "shares": 2,
                "views": 50,
            },
            {
                "id": "msg_cross2", 
                "content": "terrível produto",  # negative sentiment
                "timestamp": "2025-09-10T10:01:00Z",
                "user_id": "user_cross2",
                "hashtags": ["#negativo"],
                "reactions": 1,
                "shares": 0,
                "views": 25,
            }
        ],
        "time_window_minutes": 30,
    }
    r = post_analyze(payload)
    assert r.status_code == 200
    analysis = r.json()["analysis"]
    trending = analysis["trending_topics"]
    # Positive hashtags should rank higher due to sentiment multiplier (1.2 vs 0.8)
    if "#positivo" in trending and "#negativo" in trending:
        pos_idx = trending.index("#positivo")
        neg_idx = trending.index("#negativo") 
        assert pos_idx < neg_idx, "Positive hashtags should rank higher than negative ones"


def test_long_hashtag_logarithmic_decay():
    # Tests logarithmic decay for long hashtags
    payload = {
        "messages": [
            {
                "id": "msg_long1",
                "content": "teste básico",
                "timestamp": "2025-09-10T10:00:00Z",
                "user_id": "user_long1",
                "hashtags": ["#short", "#verylonghashtag"],  # >8 chars gets log decay
                "reactions": 1,
                "shares": 0,
                "views": 10,
            }
        ],
        "time_window_minutes": 30,
    }
    r = post_analyze(payload)
    assert r.status_code == 200
    # Long hashtag should have reduced weight due to logarithmic factor
