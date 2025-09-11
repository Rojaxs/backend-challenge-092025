from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import time

from sentiment_analyzer import analyze_feed, ValidationError as AnalyzerValidationError


class MessageModel(BaseModel):
    id: str
    content: str
    timestamp: str
    user_id: str
    hashtags: List[str] = Field(default_factory=list)
    reactions: int = 0
    shares: int = 0
    views: int = 0


class AnalyzeFeedRequest(BaseModel):
    messages: List[MessageModel]
    time_window_minutes: int


app = FastAPI(title="MBRAS — Backend Challenge")


@app.post("/analyze-feed")
async def analyze_feed_endpoint(req: Request, payload: AnalyzeFeedRequest):
    # Basic content-type check → 400
    content_type = req.headers.get("content-type", "").lower()
    if "application/json" not in content_type:
        raise HTTPException(status_code=400, detail={
            "error": "Content-Type inválido. Use application/json",
            "code": "INVALID_CONTENT_TYPE",
        })

    # Business rule 422 for time_window_minutes == 123
    if payload.time_window_minutes == 123:
        return JSONResponse(status_code=422, content={
            "error": "Valor de janela temporal não suportado na versão atual",
            "code": "UNSUPPORTED_TIME_WINDOW",
        })

    started = time.perf_counter()
    now_utc = datetime.now(timezone.utc)

    try:
        result = analyze_feed(
            messages=[m.model_dump() for m in payload.messages],
            time_window_minutes=payload.time_window_minutes,
            now_utc=now_utc,
        )
    except AnalyzerValidationError as e:
        raise HTTPException(status_code=400, detail={"error": str(e), "code": e.code})

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    result["analysis"]["processing_time_ms"] = elapsed_ms
    return JSONResponse(status_code=200, content=result)


@app.exception_handler(HTTPException)
async def http_exception_handler(_, exc: HTTPException):
    # Ensure error format matches the spec
    if isinstance(exc.detail, dict) and "error" in exc.detail and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={
        "error": str(exc.detail) if exc.detail else "Erro",
        "code": "ERROR",
    })

