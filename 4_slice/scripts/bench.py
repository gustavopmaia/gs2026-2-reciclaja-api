"""Mede p50/p95 de latência contra o serviço no ar (RNF-01).

Uso: python scripts/bench.py [base_url] [n]
"""

import statistics
import sys
import time

import httpx

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
N = int(sys.argv[2]) if len(sys.argv) > 2 else 200
CALLS = {
    "GET /v1/points/{id}": lambda c: c.get("/v1/points/PC-001"),
    "GET /v1/points": lambda c: c.get("/v1/points", params={"material": "papel"}),
    "POST /v1/ask": lambda c: c.post("/v1/ask", json={"question": "onde jogo pilha?", "neighborhood": "Lapa"}),
}


def main() -> None:
    with httpx.Client(base_url=BASE, timeout=30) as client:
        print(f"alvo={BASE} provider={client.get('/v1/health').json()['llm_provider']} n={N}")
        for name, call in CALLS.items():
            samples = []
            for _ in range(N):
                start = time.perf_counter()
                assert call(client).status_code == 200
                samples.append((time.perf_counter() - start) * 1000)
            samples.sort()
            p95 = samples[int(0.95 * len(samples)) - 1]
            print(f"{name:22s} p50={statistics.median(samples):7.1f} ms  p95={p95:7.1f} ms  max={samples[-1]:7.1f} ms")


if __name__ == "__main__":
    main()
