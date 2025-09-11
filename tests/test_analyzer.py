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

