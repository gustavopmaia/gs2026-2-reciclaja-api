"""Adaptadores de LLM. Todos implementam domain.ports.LLMClient.

Trocar de modelo/provedor = mudar LLM_PROVIDER / LLM_MODEL no ambiente. O domínio não muda.
"""

from __future__ import annotations

import os
import re

import httpx

from domain.models import Completion, LLMUnavailable, Prompt


class FakeLLM:
    """Fake determinístico e documentado: monta a resposta a partir do próprio prompt.

    Usado em testes, CI, evals de regressão e quando não há modelo disponível.
    Mesma entrada => mesma saída. Nunca acessa rede.
    """

    provider = "fake"
    model = "fake-deterministic-v1"

    def complete(self, prompt: Prompt) -> Completion:
        guidance = re.search(r"ORIENTAÇÃO OFICIAL: (.+)", prompt.user)
        points = re.findall(r"- \[(PC-\d{3})\] ([^—]+)", prompt.user)
        text = guidance.group(1) if guidance else ""
        if points:
            text += " Você pode levar em: " + "; ".join(f"[{pid}] {name.strip()}" for pid, name in points) + "."
        else:
            text += " Não há ponto cadastrado aberto para esse material no momento."
        return Completion(text=text, tokens_in=len(prompt.user.split()), tokens_out=len(text.split()))


class OllamaLLM:
    """Ollama local ou Ollama Cloud (mesma API /api/chat)."""

    provider = "ollama"

    def __init__(self, model: str, base_url: str, timeout_s: float, api_key: str | None = None):
        self.model = model
        self._url = base_url.rstrip("/") + "/api/chat"
        self._timeout = timeout_s
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    def complete(self, prompt: Prompt) -> Completion:
        payload = {
            "model": self.model,
            "stream": False,
            "options": {"temperature": 0},
            "messages": [{"role": "system", "content": prompt.system}, {"role": "user", "content": prompt.user}],
        }
        try:
            resp = httpx.post(self._url, json=payload, headers=self._headers, timeout=self._timeout)
            resp.raise_for_status()
            data = resp.json()
            return Completion(
                text=data["message"]["content"],
                tokens_in=data.get("prompt_eval_count", 0),
                tokens_out=data.get("eval_count", 0),
            )
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise LLMUnavailable(f"ollama: {exc.__class__.__name__}") from exc


class OpenAICompatLLM:
    """Qualquer API compatível com OpenAI /v1/chat/completions (LM Studio, vLLM, provedores externos)."""

    provider = "openai_compat"

    def __init__(self, model: str, base_url: str, timeout_s: float, api_key: str | None = None):
        self.model = model
        self._url = base_url.rstrip("/") + "/chat/completions"
        self._timeout = timeout_s
        self._headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    def complete(self, prompt: Prompt) -> Completion:
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [{"role": "system", "content": prompt.system}, {"role": "user", "content": prompt.user}],
        }
        try:
            resp = httpx.post(self._url, json=payload, headers=self._headers, timeout=self._timeout)
            resp.raise_for_status()
            data = resp.json()
            usage = data.get("usage", {})
            return Completion(
                text=data["choices"][0]["message"]["content"],
                tokens_in=usage.get("prompt_tokens", 0),
                tokens_out=usage.get("completion_tokens", 0),
            )
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as exc:
            raise LLMUnavailable(f"openai_compat: {exc.__class__.__name__}") from exc


def build_llm(env: dict[str, str] | None = None):
    """Ponto único de troca do modelo. Chaves vêm SÓ do ambiente (nunca do código)."""
    env = dict(os.environ) if env is None else env
    provider = env.get("LLM_PROVIDER", "fake")
    timeout = float(env.get("LLM_TIMEOUT_S", "8"))
    if provider == "fake":
        return FakeLLM()
    if provider == "ollama":
        return OllamaLLM(
            env.get("LLM_MODEL", "llama3.2:3b"),
            env.get("LLM_BASE_URL", "http://localhost:11434"),
            timeout,
            env.get("LLM_API_KEY"),
        )
    if provider == "openai_compat":
        return OpenAICompatLLM(
            env.get("LLM_MODEL", "local-model"),
            env.get("LLM_BASE_URL", "http://localhost:1234/v1"),
            timeout,
            env.get("LLM_API_KEY"),
        )
    raise ValueError(f"LLM_PROVIDER desconhecido: {provider}")
