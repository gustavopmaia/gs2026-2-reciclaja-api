"""DTOs HTTP espelhando components/schemas do 2_contrato_api.yaml (mesmos nomes de campo)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from domain.models import Material, PointStatus


class CollectionPointOut(BaseModel):
    id: str
    name: str
    type: Literal["ecoponto", "pev", "cooperativa", "ponto_comercio"]
    neighborhood: str
    address: str
    latitude: float
    longitude: float
    materials: list[Material]
    status: PointStatus
    opening_hours: str
    updated_at: str
    data_source: Literal["sintetico", "dados_abertos"]


class PointPageOut(BaseModel):
    items: list[CollectionPointOut]
    total: int
    limit: int
    offset: int
    next: str | None


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=3, max_length=500)
    neighborhood: str | None = Field(default=None, min_length=2, max_length=60)


class AskResponse(BaseModel):
    answer: str
    mode: Literal["llm", "fallback", "refused"]
    material: Material | None
    cited_points: list[str]
    refusal_reason: Literal["fora_do_escopo", "pergunta_insegura"] | None
    disclaimer: str
    request_id: str


class HealthOut(BaseModel):
    status: Literal["ok"]
    llm_provider: Literal["fake", "ollama", "openai_compat"]
    llm_model: str
    points_loaded: int
