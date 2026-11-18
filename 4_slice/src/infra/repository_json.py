"""Adaptador de dados: lê o cadastro de um JSON. Trocar por Postgres/API aberta = novo adaptador, mesmo contrato."""

from __future__ import annotations

import json
from pathlib import Path

from domain.knowledge import normalize
from domain.models import CollectionPoint, Material, Page, PointStatus


class JsonPointRepository:
    def __init__(self, path: Path):
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        self._points = [
            CollectionPoint(
                **{
                    **item,
                    "materials": tuple(Material(m) for m in item["materials"]),
                    "status": PointStatus(item["status"]),
                }
            )
            for item in raw
        ]
        self._by_id = {p.id: p for p in self._points}

    def get(self, point_id: str) -> CollectionPoint | None:
        return self._by_id.get(point_id)

    def search(
        self,
        material: Material | None = None,
        neighborhood: str | None = None,
        status: PointStatus | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> Page:
        hood = normalize(neighborhood) if neighborhood else None
        found = [
            p
            for p in self._points
            if (material is None or p.accepts(material))
            and (hood is None or normalize(p.neighborhood) == hood)
            and (status is None or p.status == status)
        ]
        return Page(items=found[offset : offset + limit], total=len(found), limit=limit, offset=offset)

    def count(self) -> int:
        return len(self._points)
