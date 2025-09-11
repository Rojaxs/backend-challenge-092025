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
