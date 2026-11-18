# Cola de defesa — ReciclaJá (respostas curtas pra banca)

**"Se eu tirar o LLM e colocar outro, o que quebra?"**
Nada no domínio. `src/domain` só conhece a porta `LLMClient.complete(Prompt) -> Completion`. Trocar = `LLM_MODEL=qwen2.5:7b` (ou `LLM_PROVIDER=openai_compat`). O teste `test_dominio_nao_importa_biblioteca_de_llm_nem_http` quebra o build se alguém importar lib de LLM no domínio. Provamos: rodamos o mesmo eval com llama3.2:3b e qwen2.5:7b sem mudar código.

**"E se o modelo errar?"**
- Inventou ponto, não citou ponto ou vazou PII → guardrail de saída reprova → **fallback** determinístico (`mode=fallback`).
- Modelo fora do ar/timeout 8 s → **503** `LLM_UNAVAILABLE` + `Retry-After`. `/v1/points` continua no ar.
- Pergunta insegura/fora do escopo → recusa **antes** de chamar o LLM.

**"Por que não LangChain?" (ADR-01)** Uma chamada por pergunta: framework grande pra pouco ganho, e acoplaria o domínio a tipos dele. Custo: retry/streaming/tools na mão. Se virar agente, LangGraph entra **dentro de um adaptador**.

**"Por que não RAG vetorial?" (ADR-02)** 24 pontos e 10 materiais: o filtro determinístico é testável, barato (~470 tokens/resposta) e dá lista fechada de IDs pro guardrail. Custo: sinônimo raro vira recusa indevida. Vigiamos com o alerta `RecusaForaDoPadrao`.

**"Por que Ollama local?" (ADR-03)** O dado do cidadão não sai da prefeitura (LGPD), custo zero por token, roda offline. Custo: modelo pequeno erra mais, por isso só piloto.

**"Por que fallback e não recusa ou retry?" (ADR-04)** O cidadão sempre recebe a orientação oficial. Retry dobra a latência e, com temperature 0, repete o erro. Custo: texto menos natural, vigiado pela meta fallback ≤ 20%.

**Números (todos medidos, não inventados)**
38 testes · cobertura 96% · CI verde (ruff, validador, pytest, evals, gitleaks, docker) · GET p95 0,8 ms · eval: v1 46,7% → v2 100% correta, guardrail 100%, fallback 31,8%, p95 3,8 s · qwen 7B 93,3%, p95 14 s.

**400 × 422?** 400 = requisição malformada (JSON quebrado, path/query inválido). 422 = JSON bem formado que viola o schema do corpo.

**Por que `/metrics` não está no YAML?** É endpoint operacional do Prometheus, fora do contrato de negócio. Isso está documentado e o teste de rotas o exclui de propósito.

**Observabilidade:** log JSON sem o texto da pergunta. Métricas de latência, 5xx, recusa, fallback e tokens. 5 alertas (p95 > 4 s/10 min; 5xx > 5%/5 min; fallback > 20%/30 min; recusa > 40%/1 h; tokens > 2 M/dia).

**Rollout:** interno → piloto Mooca ~5% (correta ≥ 90%, guardrail 100%, p95 ≤ 4 s) → público (+ fallback ≤ 20%, 0 PII, 2 semanas, amostra humana ≥ 95%). Rollback = voltar uma linha.
