"""Entidades do domínio. Python puro: nada de FastAPI, HTTP ou biblioteca de LLM aqui."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Material(StrEnum):
    PAPEL = "papel"
    PLASTICO = "plastico"
    VIDRO = "vidro"
    METAL = "metal"
    ELETRONICO = "eletronico"
    PILHA_BATERIA = "pilha_bateria"
    OLEO_COZINHA = "oleo_cozinha"
    LAMPADA = "lampada"
    VOLUMOSO = "volumoso"
    ENTULHO = "entulho"


class PointStatus(StrEnum):
    ABERTO = "aberto"
    LOTADO = "lotado"
    MANUTENCAO = "manutencao"
    FECHADO = "fechado"


class AnswerMode(StrEnum):
    LLM = "llm"
    FALLBACK = "fallback"
    REFUSED = "refused"


class RefusalReason(StrEnum):
    FORA_DO_ESCOPO = "fora_do_escopo"
    PERGUNTA_INSEGURA = "pergunta_insegura"


@dataclass(frozen=True)
class CollectionPoint:
    id: str
    name: str
    type: str
    neighborhood: str
    address: str
    latitude: float
    longitude: float
    materials: tuple[Material, ...]
    status: PointStatus
    opening_hours: str
    updated_at: str
    data_source: str

    def accepts(self, material: Material) -> bool:
        return material in self.materials

    @property
    def is_usable(self) -> bool:
        """Só sugerimos ao cidadão pontos que de fato recebem resíduo agora."""
        return self.status == PointStatus.ABERTO


@dataclass(frozen=True)
class Page:
    items: list[CollectionPoint]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True)
class Prompt:
    """O que o domínio entrega ao LLM. Nenhum detalhe de provedor."""

    system: str
    user: str


@dataclass(frozen=True)
class Completion:
    text: str
    tokens_in: int = 0
    tokens_out: int = 0


@dataclass(frozen=True)
class Answer:
    answer: str
    mode: AnswerMode
    material: Material | None
    cited_points: list[str] = field(default_factory=list)
    refusal_reason: RefusalReason | None = None
    llm_called: bool = False
    tokens_in: int = 0
    tokens_out: int = 0
    guardrail_violations: list[str] = field(default_factory=list)


class PointNotFound(Exception):
    def __init__(self, point_id: str):
        super().__init__(f"Ponto de coleta {point_id} não encontrado")
        self.point_id = point_id


class LLMUnavailable(Exception):
    """Levantada pelo adaptador quando o provedor de IA falha ou estoura o tempo."""
