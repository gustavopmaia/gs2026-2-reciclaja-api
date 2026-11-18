"""Fixtures. Nenhum teste chama LLM de verdade: só fakes injetados pela porta LLMClient."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

from api.app import DATA_FILE, create_app
from domain.models import Completion, LLMUnavailable, Prompt
from infra.llm import FakeLLM
from infra.repository_json import JsonPointRepository

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_CANDIDATES = [ROOT.parent / "2_contrato_api.yaml", ROOT / "2_contrato_api.yaml"]
CONTRACT_FILE = next(p for p in CONTRACT_CANDIDATES if p.exists())


class SpyLLM:
    """Fake roteirizado: devolve texto fixo e guarda os prompts recebidos."""

    provider = "fake"
    model = "spy"

    def __init__(self, text: str | None = None):
        self.text = text
        self.prompts: list[Prompt] = []
        self._fake = FakeLLM()

    def complete(self, prompt: Prompt) -> Completion:
        self.prompts.append(prompt)
        if self.text is None:
            return self._fake.complete(prompt)
        return Completion(text=self.text, tokens_in=10, tokens_out=10)


class DownLLM:
    provider = "fake"
    model = "down"

    def complete(self, prompt: Prompt) -> Completion:
        raise LLMUnavailable("timeout simulado")


@pytest.fixture
def repo():
    return JsonPointRepository(DATA_FILE)


@pytest.fixture
def make_client(repo):
    def _make(llm=None) -> TestClient:
        return TestClient(create_app(repo=repo, llm=llm or FakeLLM()), raise_server_exceptions=False)

    return _make


@pytest.fixture
def client(make_client):
    return make_client()


@pytest.fixture(scope="session")
def contract():
    return yaml.safe_load(CONTRACT_FILE.read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def assert_contract(contract):
    """Valida o corpo real da resposta contra o schema declarado no YAML (schema × resposta)."""
    registry = Registry().with_resource("urn:contract", Resource.from_contents(contract, DRAFT202012))

    def _check(path: str, method: str, response) -> None:
        responses = contract["paths"][path][method]["responses"]
        status = str(response.status_code)
        assert status in responses, f"status {status} não documentado em {method.upper()} {path}"
        spec = responses[status]
        if "$ref" in spec:
            spec = contract["components"]["responses"][spec["$ref"].split("/")[-1]]
        ref = spec["content"]["application/json"]["schema"]["$ref"]
        validator = Draft202012Validator({"$ref": "urn:contract" + ref}, registry=registry)
        errors = [e.message for e in validator.iter_errors(response.json())]
        assert not errors, f"resposta fora do contrato: {errors}"

    return _check
