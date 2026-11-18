"""Gera data/points.json com pontos de coleta SINTÉTICOS (seed fixa = reprodutível).

Uso: python scripts/gen_points.py
Os bairros são reais (São Paulo), mas nomes, endereços, horários e status são fictícios.
O formato imita o cadastro aberto de ecopontos da prefeitura para facilitar troca por fonte real.
"""

import json
import random
from pathlib import Path

random.seed(2026)

NEIGHBORHOODS = [
    ("Mooca", -23.5600, -46.5990),
    ("Pinheiros", -23.5670, -46.6930),
    ("Tatuapé", -23.5400, -46.5760),
    ("Lapa", -23.5270, -46.7040),
    ("Santana", -23.5020, -46.6250),
    ("Vila Mariana", -23.5890, -46.6340),
    ("Itaquera", -23.5400, -46.4560),
    ("Butantã", -23.5710, -46.7080),
]
STREETS = ["Rua das Acácias", "Av. Central", "Rua do Comércio", "Rua Projetada", "Av. das Flores", "Rua da Escola"]
TYPES = {
    "ecoponto": ["papel", "plastico", "vidro", "metal", "volumoso", "entulho", "eletronico"],
    "pev": ["papel", "plastico", "vidro", "metal"],
    "cooperativa": ["papel", "plastico", "metal", "oleo_cozinha"],
    "ponto_comercio": ["pilha_bateria", "lampada", "eletronico", "oleo_cozinha"],
}
STATUS = ["aberto"] * 7 + ["lotado", "manutencao", "fechado"]
HOURS = ["Seg a Sáb, 6h às 22h", "Seg a Sex, 8h às 17h", "Todos os dias, 7h às 19h", "Ter a Sáb, 9h às 18h"]


def main() -> None:
    points = []
    for i in range(1, 25):
        hood, lat, lon = NEIGHBORHOODS[(i - 1) % len(NEIGHBORHOODS)]
        ptype = list(TYPES)[(i - 1) % len(TYPES)]
        base = TYPES[ptype]
        materials = sorted(random.sample(base, k=random.randint(max(2, len(base) - 2), len(base))))
        points.append(
            {
                "id": f"PC-{i:03d}",
                "name": f"{ptype.replace('_', ' ').title()} {hood} {i}",
                "type": ptype,
                "neighborhood": hood,
                "address": f"{random.choice(STREETS)}, {random.randint(10, 999)}",
                "latitude": round(lat + random.uniform(-0.01, 0.01), 5),
                "longitude": round(lon + random.uniform(-0.01, 0.01), 5),
                "materials": materials,
                "status": "aberto" if i <= 4 else random.choice(STATUS),
                "opening_hours": random.choice(HOURS),
                "updated_at": f"2026-11-{random.randint(1, 15):02d}T{random.randint(6, 20):02d}:00:00Z",
                "data_source": "sintetico",
            }
        )
    out = Path(__file__).resolve().parents[1] / "data" / "points.json"
    out.write_text(json.dumps(points, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(points)} pontos sintéticos gravados em {out}")


if __name__ == "__main__":
    main()
