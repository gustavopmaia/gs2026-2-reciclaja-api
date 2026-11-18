"""Casos de uso. O serviço conhece só as portas — não sabe qual LLM está embaixo."""

from __future__ import annotations

from domain import guardrails
from domain.knowledge import GUIDANCE, detect_material
from domain.models import (
    Answer,
    AnswerMode,
    CollectionPoint,
    Material,
    Page,
    PointNotFound,
    PointStatus,
    Prompt,
    RefusalReason,
)
from domain.ports import LLMClient, PointRepository

MAX_CONTEXT_POINTS = 3

PROMPT_VERSION = "v2"

# v1 (reprovado no eval: 46,7% de acerto com llama3.2:3b) não exigia repetir a orientação
# e o modelo dizia "não há ponto cadastrado" mesmo com pontos na lista. Histórico em 5_evals_de_ia.md.
SYSTEM_PROMPT = """Você é o assistente de descarte da prefeitura (serviço ReciclaJá).
Regras obrigatórias:
1. Responda em português, em no máximo 4 frases curtas.
2. A primeira frase DEVE repetir a ORIENTAÇÃO OFICIAL com suas palavras, sem omitir cuidados.
3. A lista PONTOS já está filtrada para o material: se ela tiver itens, indique esses pontos.
4. Cite cada ponto sugerido pelo ID exato entre colchetes, ex.: [PC-001]. Nunca invente pontos, endereços ou horários.
5. Só diga que não há ponto se a lista PONTOS disser "nenhum ponto cadastrado".
6. Nunca peça nem repita dados pessoais (CPF, telefone, e-mail)."""

REFUSAL_SCOPE = (
    "Posso ajudar apenas com descarte de resíduos recicláveis e especiais "
    "(papel, plástico, vidro, metal, eletrônicos, pilhas, óleo, lâmpadas, volumosos e entulho). "
    "Diga qual material você quer descartar."
)
REFUSAL_UNSAFE = (
    "Não posso orientar essa forma de descarte: ela é ilegal ou perigosa. "
    "Descarte irregular pode ser denunciado no 156. Diga o material e eu indico um ponto de coleta."
)
DISCLAIMER = "Orientação automática baseada em dados sintéticos de demonstração. Confirme horários no local."


class PointService:
    def __init__(self, repo: PointRepository):
        self._repo = repo

    def get(self, point_id: str) -> CollectionPoint:
        point = self._repo.get(point_id)
        if point is None:
            raise PointNotFound(point_id)
        return point

    def search(
        self,
        material: Material | None = None,
        neighborhood: str | None = None,
        status: PointStatus | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> Page:
        return self._repo.search(material, neighborhood, status, limit, offset)


class DisposalAssistant:
    def __init__(self, repo: PointRepository, llm: LLMClient):
        self._repo = repo
        self._llm = llm

    def ask(self, question: str, neighborhood: str | None = None) -> Answer:
        safe_question = guardrails.mask_pii(question.strip())

        if guardrails.is_unsafe(safe_question):
            return Answer(REFUSAL_UNSAFE, AnswerMode.REFUSED, None, refusal_reason=RefusalReason.PERGUNTA_INSEGURA)

        material = detect_material(safe_question)
        if material is None:
            # Fora do escopo: nem chama o LLM (custo zero e sem risco de alucinar).
            return Answer(REFUSAL_SCOPE, AnswerMode.REFUSED, None, refusal_reason=RefusalReason.FORA_DO_ESCOPO)

        points = self._candidate_points(material, neighborhood)
        prompt = Prompt(system=SYSTEM_PROMPT, user=self._build_user_prompt(safe_question, material, points))
        completion = self._llm.complete(prompt)  # LLMUnavailable sobe para a API (503)

        allowed = {p.id for p in points}
        violations = guardrails.output_violations(completion.text, allowed, require_citation=bool(allowed))
        if violations:
            return Answer(
                self._fallback_text(material, points),
                AnswerMode.FALLBACK,
                material,
                cited_points=sorted(allowed),
                llm_called=True,
                tokens_in=completion.tokens_in,
                tokens_out=completion.tokens_out,
                guardrail_violations=violations,
            )
        return Answer(
            completion.text.strip(),
            AnswerMode.LLM,
            material,
            cited_points=guardrails.cited_ids(completion.text),
            llm_called=True,
            tokens_in=completion.tokens_in,
            tokens_out=completion.tokens_out,
        )

    def _candidate_points(self, material: Material, neighborhood: str | None) -> list[CollectionPoint]:
        """Grounding: pontos abertos que aceitam o material, priorizando o bairro informado."""
        found: list[CollectionPoint] = []
        if neighborhood:
            found = self._repo.search(material, neighborhood, PointStatus.ABERTO, MAX_CONTEXT_POINTS, 0).items
        if not found:
            found = self._repo.search(material, None, PointStatus.ABERTO, MAX_CONTEXT_POINTS, 0).items
        return found

    @staticmethod
    def _build_user_prompt(question: str, material: Material, points: list[CollectionPoint]) -> str:
        lines = [
            f"PERGUNTA DO CIDADÃO: {question}",
            f"MATERIAL IDENTIFICADO: {material.value}",
            f"ORIENTAÇÃO OFICIAL: {GUIDANCE[material]}",
            "PONTOS:",
        ]
        if points:
            lines += [f"- [{p.id}] {p.name} — {p.address}, {p.neighborhood} ({p.opening_hours})" for p in points]
        else:
            lines.append("- nenhum ponto cadastrado aceita este material")
        return "\n".join(lines)

    @staticmethod
    def _fallback_text(material: Material, points: list[CollectionPoint]) -> str:
        text = GUIDANCE[material]
        if points:
            listed = "; ".join(f"[{p.id}] {p.name} ({p.address}, {p.neighborhood})" for p in points)
            text += f" Pontos abertos que aceitam esse material: {listed}."
        else:
            text += " No momento não há ponto cadastrado aberto para esse material."
        return text
