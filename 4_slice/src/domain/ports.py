"""Portas do domínio. Trocar LLM ou fonte de dados = trocar o adaptador que implementa estas interfaces."""

from __future__ import annotations

from typing import Protocol

from domain.models import CollectionPoint, Completion, Material, Page, PointStatus, Prompt


class PointRepository(Protocol):
    def get(self, point_id: str) -> CollectionPoint | None: ...

    def search(
        self,
        material: Material | None = None,
        neighborhood: str | None = None,
        status: PointStatus | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> Page: ...

    def count(self) -> int: ...


class LLMClient(Protocol):
    """Contrato único com qualquer modelo (fake, Ollama, API compatível com OpenAI).

    Deve levantar ``LLMUnavailable`` em erro de rede, timeout ou resposta inválida.
    """

    provider: str
    model: str

    def complete(self, prompt: Prompt) -> Completion: ...
