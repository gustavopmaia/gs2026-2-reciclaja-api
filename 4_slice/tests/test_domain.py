"""Domínio puro: guardrails, base de conhecimento e fronteira com o LLM."""

import ast
from pathlib import Path

import pytest

from domain import guardrails
from domain.knowledge import detect_material
from domain.models import Material
from infra.llm import FakeLLM, OllamaLLM, OpenAICompatLLM, build_llm

DOMAIN_DIR = Path(__file__).resolve().parents[1] / "src" / "domain"


@pytest.mark.parametrize(
    ("question", "expected"),
    [
        ("onde jogo óleo de fritura?", Material.OLEO_COZINHA),
        ("Tenho um CELULAR quebrado", Material.ELETRONICO),
        ("garrafa PET", Material.PLASTICO),
        ("vendi meu carpete", None),  # "pet" dentro de outra palavra não conta
        ("qual a previsão do tempo?", None),
    ],
)
def test_detect_material(question, expected):
    assert detect_material(question) == expected


def test_mask_pii():
    masked = guardrails.mask_pii("cpf 12345678909, email ana@x.com, tel 11 91234-5678")
    assert masked == "cpf [CPF], email [EMAIL], tel [TELEFONE]"


def test_output_violations_detecta_ponto_inventado():
    assert guardrails.output_violations("Vá ao [PC-001].", {"PC-001"}) == []
    assert guardrails.output_violations("Vá ao [PC-002].", {"PC-001"}) == ["ponto_inventado:PC-002"]
    assert guardrails.output_violations("", set()) == ["resposta_vazia"]


def test_dominio_nao_importa_biblioteca_de_llm_nem_http():
    """Evidência da fronteira: src/domain só depende da stdlib e de si mesmo."""
    forbidden = {"httpx", "requests", "openai", "ollama", "langchain", "fastapi", "pydantic"}
    for file in DOMAIN_DIR.glob("*.py"):
        tree = ast.parse(file.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = {a.name.split(".")[0] for a in node.names}
            elif isinstance(node, ast.ImportFrom):
                names = {(node.module or "").split(".")[0]}
            else:
                continue
            assert not names & forbidden, f"{file.name} importa {names & forbidden}"


def test_trocar_llm_e_uma_linha_de_configuracao():
    assert isinstance(build_llm({"LLM_PROVIDER": "fake"}), FakeLLM)
    ollama = build_llm({"LLM_PROVIDER": "ollama", "LLM_MODEL": "qwen2.5:7b"})
    assert isinstance(ollama, OllamaLLM) and ollama.model == "qwen2.5:7b"
    assert isinstance(build_llm({"LLM_PROVIDER": "openai_compat"}), OpenAICompatLLM)
    with pytest.raises(ValueError):
        build_llm({"LLM_PROVIDER": "desconhecido"})


def test_fake_llm_e_deterministico():
    from domain.models import Prompt

    prompt = Prompt("s", "ORIENTAÇÃO OFICIAL: texto\nPONTOS:\n- [PC-001] Ecoponto X — Rua A, Mooca (24h)")
    assert FakeLLM().complete(prompt) == FakeLLM().complete(prompt)


def _fake_post(response_json=None, exc=None):
    import httpx

    def _post(url, json, headers, timeout):
        if exc:
            raise exc
        return httpx.Response(200, json=response_json, request=httpx.Request("POST", url))

    return _post


def test_ollama_adapter_traduz_resposta(monkeypatch):
    import httpx

    from domain.models import Prompt

    monkeypatch.setattr(
        httpx, "post", _fake_post({"message": {"content": "ok [PC-001]"}, "prompt_eval_count": 50, "eval_count": 7})
    )
    out = OllamaLLM("m", "http://x", 1).complete(Prompt("s", "u"))
    assert (out.text, out.tokens_in, out.tokens_out) == ("ok [PC-001]", 50, 7)


def test_adapters_convertem_falha_em_llm_unavailable(monkeypatch):
    import httpx

    from domain.models import LLMUnavailable, Prompt

    monkeypatch.setattr(httpx, "post", _fake_post(exc=httpx.ConnectTimeout("t")))
    for adapter in (OllamaLLM("m", "http://x", 1), OpenAICompatLLM("m", "http://x", 1)):
        with pytest.raises(LLMUnavailable):
            adapter.complete(Prompt("s", "u"))


def test_output_exige_citacao_quando_ha_ponto_aberto():
    assert guardrails.output_violations("Não há ponto.", {"PC-001"}, require_citation=True) == ["sem_citacao"]
    assert guardrails.output_violations("Não há ponto.", set(), require_citation=False) == []
