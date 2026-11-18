"""Guardrails de entrada e de saída. Regras não-negociáveis viram código testável.

G1 — Não inventar dado: a resposta só pode citar pontos que vieram do cadastro (contexto).
G1b — Se há ponto aberto no cadastro, a resposta tem que citar pelo menos um (o modelo não pode "negar" dado).
G2 — Não expor dado pessoal: CPF, telefone e e-mail são mascarados antes do LLM e bloqueados na saída.
G3 — Não orientar descarte ilegal/perigoso nem obedecer instrução injetada na pergunta.
"""

from __future__ import annotations

import re

from domain.knowledge import normalize

POINT_ID_RE = re.compile(r"\bPC-\d{3}\b")

_PII_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"), "[CPF]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[EMAIL]"),
    (re.compile(r"(?:\(?\d{2}\)?\s?)?9?\d{4}[-\s]?\d{4}\b"), "[TELEFONE]"),
]

_UNSAFE_TERMS = (
    "queimar",
    "queimo",
    "tacar fogo",
    "por fogo",
    "jogar no rio",
    "jogo no rio",
    "corrego",
    "terreno baldio",
    "bueiro",
    "esconder da fiscalizacao",
    "sem ser multado",
)

_INJECTION_TERMS = (
    "ignore as instrucoes",
    "ignore suas instrucoes",
    "ignore todas",
    "esqueca as regras",
    "system prompt",
    "prompt do sistema",
    "voce agora e",
)

MAX_ANSWER_CHARS = 1200


def mask_pii(text: str) -> str:
    for pattern, token in _PII_PATTERNS:
        text = pattern.sub(token, text)
    return text


def contains_pii(text: str) -> bool:
    return any(pattern.search(text) for pattern, _ in _PII_PATTERNS)


def is_unsafe(question: str) -> bool:
    norm = normalize(question)
    return any(term in norm for term in _UNSAFE_TERMS + _INJECTION_TERMS)


def cited_ids(text: str) -> list[str]:
    return sorted(set(POINT_ID_RE.findall(text)))


def output_violations(text: str, allowed_ids: set[str], require_citation: bool = False) -> list[str]:
    """Lista de violações da resposta do LLM. Lista vazia = resposta aprovada."""
    violations: list[str] = []
    if not text.strip():
        violations.append("resposta_vazia")
    if len(text) > MAX_ANSWER_CHARS:
        violations.append("resposta_longa")
    invented = [pid for pid in cited_ids(text) if pid not in allowed_ids]
    if invented:
        violations.append("ponto_inventado:" + ",".join(invented))
    if require_citation and not cited_ids(text):
        # Havia ponto aberto e o modelo não indicou nenhum (ou disse que "não há"): resposta inútil/falsa.
        violations.append("sem_citacao")
    if contains_pii(text):
        violations.append("dado_pessoal")
    return violations
