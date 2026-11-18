"""Camada HTTP. Traduz HTTP <-> domínio e aplica o corpo de erro único do contrato."""

from __future__ import annotations

import os
import time
import uuid
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, Query, Request
from fastapi import Path as PathParam
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.schemas import AskRequest, AskResponse, CollectionPointOut, HealthOut, PointPageOut
from domain.models import LLMUnavailable, Material, PointNotFound, PointStatus
from domain.ports import LLMClient, PointRepository
from domain.service import DISCLAIMER, DisposalAssistant, PointService
from infra import observability as obs

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "points.json"


def error_body(status: int, code: str, message: str, request_id: str, details=None, headers=None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "details": details or [], "request_id": request_id}},
        headers=headers,
    )


def create_app(repo: PointRepository | None = None, llm: LLMClient | None = None) -> FastAPI:
    """Composition root: injeta adaptadores. Testes passam fakes; produção lê do ambiente."""
    if repo is None:
        from infra.repository_json import JsonPointRepository

        repo = JsonPointRepository(Path(os.environ.get("POINTS_FILE", DATA_FILE)))
    if llm is None:
        from infra.llm import build_llm

        llm = build_llm()

    points = PointService(repo)
    assistant = DisposalAssistant(repo, llm)
    # O contrato oficial é o 2_contrato_api.yaml; desligamos o OpenAPI gerado para não haver duas fontes de verdade.
    app = FastAPI(title="ReciclaJá API", version="1.0.0", openapi_url=None, docs_url=None, redoc_url=None)

    @app.middleware("http")
    async def observe(request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        route = request.scope.get("route")
        route_path = route.path if route else "unmatched"
        obs.HTTP_REQUESTS.labels(route_path, request.method, str(response.status_code)).inc()
        obs.HTTP_LATENCY.labels(route_path).observe(elapsed)
        response.headers["X-Request-ID"] = request.state.request_id
        obs.log_event(
            "http_request",
            request_id=request.state.request_id,
            method=request.method,
            route=route_path,
            status=response.status_code,
            latency_ms=round(elapsed * 1000, 2),
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def on_validation(request: Request, exc: RequestValidationError):
        details = [{"field": ".".join(str(p) for p in err["loc"]), "issue": err["msg"]} for err in exc.errors()]
        malformed = any(err["loc"][0] in ("path", "query") or err["type"] == "json_invalid" for err in exc.errors())
        if malformed:
            return error_body(400, "BAD_REQUEST", "Requisição malformada", request.state.request_id, details)
        return error_body(422, "VALIDATION_ERROR", "Corpo da requisição inválido", request.state.request_id, details)

    @app.exception_handler(StarletteHTTPException)
    async def on_http(request: Request, exc: StarletteHTTPException):
        code = {404: "NOT_FOUND", 400: "BAD_REQUEST"}.get(exc.status_code, "BAD_REQUEST")
        return error_body(exc.status_code, code, str(exc.detail), request.state.request_id)

    @app.exception_handler(PointNotFound)
    async def on_not_found(request: Request, exc: PointNotFound):
        return error_body(404, "NOT_FOUND", str(exc), request.state.request_id)

    @app.exception_handler(LLMUnavailable)
    async def on_llm_down(request: Request, exc: LLMUnavailable):
        obs.ASK_OUTCOMES.labels("error", "llm_unavailable").inc()
        return error_body(
            503,
            "LLM_UNAVAILABLE",
            "Assistente temporariamente indisponível. Consulte GET /v1/points enquanto isso.",
            request.state.request_id,
            headers={"Retry-After": "30"},
        )

    @app.exception_handler(Exception)
    async def on_unexpected(request: Request, exc: Exception):
        obs.log_event("unhandled_error", request_id=request.state.request_id, error=exc.__class__.__name__)
        return error_body(500, "INTERNAL_ERROR", "Erro interno", request.state.request_id)

    @app.get("/v1/points", response_model=PointPageOut)
    def list_points(
        request: Request,
        material: Material | None = None,
        neighborhood: Annotated[str | None, Query(min_length=2, max_length=60)] = None,
        status: PointStatus | None = None,
        limit: Annotated[int, Query(ge=1, le=50)] = 10,
        offset: Annotated[int, Query(ge=0)] = 0,
    ):
        page = points.search(material, neighborhood, status, limit, offset)
        nxt = None
        if offset + limit < page.total:
            params = dict(request.query_params) | {"limit": str(limit), "offset": str(offset + limit)}
            nxt = "/v1/points?" + "&".join(f"{k}={v}" for k, v in params.items())
        return {"items": page.items, "total": page.total, "limit": limit, "offset": offset, "next": nxt}

    @app.get("/v1/points/{point_id}", response_model=CollectionPointOut)
    def get_point(point_id: Annotated[str, PathParam(pattern=r"^PC-[0-9]{3}$")]):
        return points.get(point_id)

    @app.post("/v1/ask", response_model=AskResponse)
    def ask(body: AskRequest, request: Request):
        start = time.perf_counter()
        try:
            result = assistant.ask(body.question, body.neighborhood)
        except LLMUnavailable:
            obs.LLM_CALLS.labels(llm.provider, llm.model, "error").inc()
            raise
        elapsed = time.perf_counter() - start
        if result.llm_called:
            obs.LLM_CALLS.labels(llm.provider, llm.model, "ok").inc()
            obs.LLM_LATENCY.labels(llm.provider).observe(elapsed)
            obs.LLM_TOKENS.labels(llm.provider, "in").inc(result.tokens_in)
            obs.LLM_TOKENS.labels(llm.provider, "out").inc(result.tokens_out)
        for violation in result.guardrail_violations:
            obs.GUARDRAIL_BLOCKS.labels(violation.split(":")[0]).inc()
        reason = result.refusal_reason.value if result.refusal_reason else "none"
        obs.ASK_OUTCOMES.labels(result.mode.value, reason).inc()
        obs.log_event(
            "ask",
            request_id=request.state.request_id,
            mode=result.mode.value,
            reason=reason,
            material=result.material.value if result.material else None,
            provider=llm.provider,
            model=llm.model,
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            violations=result.guardrail_violations,
            latency_ms=round(elapsed * 1000, 2),
        )
        return {
            "answer": result.answer,
            "mode": result.mode.value,
            "material": result.material,
            "cited_points": result.cited_points,
            "refusal_reason": result.refusal_reason.value if result.refusal_reason else None,
            "disclaimer": DISCLAIMER,
            "request_id": request.state.request_id,
        }

    @app.get("/v1/health", response_model=HealthOut)
    def health():
        return {"status": "ok", "llm_provider": llm.provider, "llm_model": llm.model, "points_loaded": repo.count()}

    @app.get("/metrics", include_in_schema=False)
    def metrics():
        # Endpoint operacional (scrape do Prometheus), fora do contrato de negócio.
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return app
