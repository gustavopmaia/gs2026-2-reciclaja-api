"""Logs estruturados (JSON) + métricas Prometheus. Nenhum texto de pergunta é logado: só metadados."""

from __future__ import annotations

import json
import logging
import sys

from prometheus_client import Counter, Histogram

HTTP_REQUESTS = Counter("reciclaja_http_requests_total", "Requisições HTTP", ["route", "method", "status"])
HTTP_LATENCY = Histogram(
    "reciclaja_http_request_seconds",
    "Latência HTTP",
    ["route"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 4, 8),
)
ASK_OUTCOMES = Counter("reciclaja_ask_outcomes_total", "Resultado do /ask", ["mode", "reason"])
LLM_CALLS = Counter("reciclaja_llm_calls_total", "Chamadas ao LLM", ["provider", "model", "outcome"])
LLM_LATENCY = Histogram("reciclaja_llm_seconds", "Latência do LLM", ["provider"], buckets=(0.1, 0.5, 1, 2, 4, 8, 16))
LLM_TOKENS = Counter("reciclaja_llm_tokens_total", "Tokens consumidos", ["provider", "direction"])
GUARDRAIL_BLOCKS = Counter("reciclaja_guardrail_blocks_total", "Respostas do LLM reprovadas", ["violation"])


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {"level": record.levelname, "event": record.getMessage()}
        payload.update(getattr(record, "fields", {}))
        return json.dumps(payload, ensure_ascii=False)


def get_logger() -> logging.Logger:
    logger = logging.getLogger("reciclaja")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_JsonFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def log_event(event: str, **fields) -> None:
    get_logger().info(event, extra={"fields": fields})
