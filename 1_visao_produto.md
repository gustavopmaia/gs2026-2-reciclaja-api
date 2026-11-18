# 1. Visão de Produto — ReciclaJá

**GS2026.2 · Prompt and Artificial Intelligence · Engenharia de Software · Turma 2CCPY-2026**
**Frente C — ♻️ Descarte e sustentabilidade** · Modalidade: **trio**

| Integrante | RM |
|---|---|
| Gabriel Fidalgo | RM563213 |
| Gustavo Maia | RM562240 |
| Gustavo Rossi | RM566075 |

---

## Contexto

A Secretaria de Meio Ambiente tem um piloto de assistente de descarte que roda num notebook: responde no chat, mas ninguém sabe o que ele promete, quando erra ou como testá-lo. Nossa equipe foi contratada para transformá-lo em **serviço**: com contrato (OpenAPI), fronteiras claras entre domínio e IA, testes determinísticos, evals e critério de rollout.

## Problema (uma frase)

> **O morador não sabe onde nem como descartar corretamente um resíduo (pilha, óleo, eletrônico, entulho), então ele acaba no lixo comum, na pia ou na rua, porque a informação oficial está espalhada e desatualizada.**

## Persona primária

| Campo | Descrição |
|---|---|
| **Nome** | **Dona Cida**, 58 anos, moradora da Mooca (SP) |
| **Contexto** | Usa WhatsApp e o app da prefeitura pelo celular. Faz faxina na casa da filha e junta pilhas, óleo de fritura e uma TV velha. Não sabe qual ecoponto aceita o quê, nem o horário. |
| **Necessidade** | Perguntar em português comum ("onde jogo pilha?") e receber **o que fazer** (preparo do resíduo) e **onde levar** (ponto aberto, com endereço e horário), sem precisar de cadastro. |
| **Ganho esperado** | Descartar certo na primeira tentativa, sem viagem perdida até ponto fechado ou lotado. |
| **O que ela NÃO é** | Não é gestora de resíduos, não é catadora, não quer agendar coleta nem denunciar descarte irregular por este canal. Não é usuária técnica: não lê JSON nem sabe o nome "PEV". |

**Persona secundária:** *Marcos*, gestor da cooperativa de reciclagem do Tatuapé. Consome `GET /v1/points` no painel da cooperativa para saber quais pontos estão lotados e redirecionar a coleta. Ele é o "outro time que consome o serviço".

## Requisitos funcionais

| ID | Requisito | Endpoint / evidência |
|---|---|---|
| **RF-01** | Listar pontos de coleta com filtros por material, bairro (sem acento/caixa) e status, paginados por `limit`/`offset` com link `next`. | `GET /v1/points` · `test_list_points_filtra_e_pagina` |
| **RF-02** | Detalhar um ponto pelo ID (`PC-000`), com materiais aceitos, horário, status, data de atualização e origem do dado. | `GET /v1/points/{point_id}` · `test_get_point_happy_path` |
| **RF-03** | Responder em linguagem natural como e onde descartar um resíduo, identificando o material e sugerindo até 3 pontos **abertos** que o aceitam, priorizando o bairro informado. | `POST /v1/ask` · `test_ask_happy_path_com_fake` |
| **RF-04** | Recusar perguntas fora do escopo de descarte **sem chamar o LLM**, explicando o que o serviço cobre. | `mode=refused`, `refusal_reason=fora_do_escopo` · `test_ask_fora_do_escopo_recusa_sem_chamar_llm` |
| **RF-05** | Recusar pedidos de descarte ilegal/perigoso (queimar, jogar em córrego/terreno) e tentativas de *prompt injection*. | `refusal_reason=pergunta_insegura` · `test_ask_pergunta_insegura_recusa`, `test_ask_prompt_injection_recusa` |
| **RF-06** | Quando a resposta do LLM violar um guardrail (ponto inventado, sem citação, dado pessoal), entregar resposta determinística com a orientação oficial (*fallback*). | `mode=fallback` · `test_ask_llm_inventa_ponto_cai_no_fallback` |
| **RF-07** | Informar saúde do serviço e qual provedor/modelo de IA está ativo. | `GET /v1/health` · `test_health_informa_provedor` |

## Requisitos não funcionais (todos com número e forma de medir)

| ID | Atributo | Meta | Como medimos | Resultado atual |
|---|---|---|---|---|
| **RNF-01** | Desempenho | **p95 de `GET /v1/points/{id}` ≤ 200 ms** e **p95 de `POST /v1/ask` ≤ 4 s** com LLM real carregado | `scripts/bench.py` (300 req.) + histograma `reciclaja_http_request_seconds` no Prometheus + `latencia_p95_s` do eval | GET p95 = **0,8 ms** (Docker, fake). Ask com llama3.2:3b: p95 = **3,73 s** (modelo carregado, sem carga paralela). Sob carga (build Android em paralelo) foi a 6,96 s e o gate barrou — ver `5_evals_de_ia.md`. |
| **RNF-02** | Testabilidade | **Cobertura ≥ 80%**: o CI falha abaixo disso | `pytest --cov --cov-fail-under=80` no GitHub Actions | **96%** (38 testes) |
| **RNF-03** | Disponibilidade / degradação | **99% em horário comercial (7h–19h)**. Com o LLM fora, `/v1/ask` responde **503 em ≤ 8 s** (timeout) e `/v1/points` continua **100%** disponível | Alerta `TaxaErro5xxAlta` (> 5% em 5 min) + teste `test_ask_llm_indisponivel_retorna_503` | Testado com o adaptador derrubado |
| **RNF-04** | Segurança | **0 chaves/segredos no repositório**. Chave de LLM só por variável de ambiente | Gitleaks no CI + `.env` no `.gitignore` + regras `ruff S` (bandit) | CI verde |
| **RNF-05** | Privacidade (LGPD) | **100% dos CPFs, telefones e e-mails mascarados** antes do LLM e dos logs; logs sem texto da pergunta | `test_ask_mascara_dado_pessoal_antes_do_llm`, `test_mask_pii`, caso E28 do eval | 100% |
| **RNF-06** | Custo | **≤ 600 tokens por pergunta respondida** (média) | `reciclaja_llm_tokens_total` / respostas; `tokens_total` do eval | **472 tokens/resposta** (10.387 tokens / 22 respostas, llama3.2:3b) |

## Critérios de aceite (Dado / Quando / Então)

| # | Critério | Teste automatizado |
|---|---|---|
| **CA-01** | **Dado** que existe o ponto `PC-001`, **quando** o cliente faz `GET /v1/points/PC-001`, **então** recebe `200` com o corpo no schema `CollectionPoint` e `data_source = "sintetico"`. | `test_get_point_happy_path` |
| **CA-02** | **Dado** que `PC-999` não existe, **quando** o cliente faz `GET /v1/points/PC-999`, **então** recebe `404` com `error.code = "NOT_FOUND"` no corpo de erro único. | `test_get_point_inexistente_retorna_404` |
| **CA-03** | **Dado** um ID fora do padrão (`abc`), **quando** o cliente faz `GET /v1/points/abc`, **então** recebe `400` e `details[0].field = "path.point_id"`. | `test_get_point_id_malformado_retorna_400` |
| **CA-04** | **Dado** que a Dona Cida mora no Butantã, **quando** pergunta "Onde jogo pilhas usadas?", **então** recebe `mode = "llm"`, `material = "pilha_bateria"`, a orientação de não jogar no lixo comum e só pontos **abertos e existentes** (`PC-008`, `PC-016`, `PC-024`). | `test_ask_happy_path_com_fake` |
| **CA-05** | **Dado** uma pergunta sobre futebol, **quando** ela chega ao `/v1/ask`, **então** o serviço responde `mode = "refused"`, `refusal_reason = "fora_do_escopo"` e **o LLM não é chamado**. | `test_ask_fora_do_escopo_recusa_sem_chamar_llm` |
| **CA-06** | **Dado** que o LLM responde citando `[PC-777]` (inexistente), **quando** a resposta passa pelo guardrail, **então** o cidadão recebe `mode = "fallback"` com a orientação oficial e **sem** o ponto inventado. | `test_ask_llm_inventa_ponto_cai_no_fallback` |
| **CA-07** | **Dado** que o provedor de IA está fora do ar, **quando** o cliente chama `/v1/ask`, **então** recebe `503`, `error.code = "LLM_UNAVAILABLE"` e cabeçalho `Retry-After: 30`. | `test_ask_llm_indisponivel_retorna_503` |
| **CA-08** | **Dado** que a pergunta contém CPF e telefone, **quando** o serviço monta o prompt, **então** o LLM recebe `[CPF]` e `[TELEFONE]`, nunca os números. | `test_ask_mascara_dado_pessoal_antes_do_llm` |

## Fora de escopo (explícito)

1. **Agendar coleta** (cata-bagulho) ou caçamba: o serviço só orienta e indica pontos.
2. **Denúncia de descarte irregular**: o serviço direciona ao canal 156, mas não registra denúncia.
3. **Resíduos de saúde e perigosos fora da logística reversa** (remédio, seringa, pneu, agrotóxico): o serviço recusa (`fora_do_escopo`) em vez de improvisar uma resposta.
4. **Cadastro, login ou histórico do cidadão**: o serviço é anônimo e não guarda pergunta.
5. **Mapa/rotas e frontend**: entregamos a API, e outro time constrói a interface.

## Riscos e mitigação

| # | Risco | Prob. | Impacto | Mitigação no produto |
|---|---|---|---|---|
| R1 | **LLM alucina** um ponto, endereço ou horário | Alta (vimos isso no eval v1) | Cidadão viaja até lugar que não existe | Guardrail G1/G1b: só IDs do contexto, citação obrigatória. Se reprovar, entra o **fallback** determinístico. Métrica e alerta `FallbackGuardrailAlto`. |
| R2 | **Vazamento de dado pessoal** (cidadão digita CPF/telefone) | Média | LGPD | Mascaramento antes do LLM e do log (G2); logs só com metadados; saída com PII reprovada. |
| R3 | **Provedor de IA fora do ar ou lento** | Média | Serviço "quebra silenciosamente" | Timeout de 8 s → `503` documentado + `Retry-After`; `/v1/points` continua no ar; alerta de 5xx. |
| R4 | **Cadastro desatualizado** (ponto fechou) | Média | Orientação errada | Só sugerimos `status = aberto`; `updated_at` em todo ponto; fonte de dados atrás de porta (troca por base oficial sem tocar o domínio). |
| R5 | **Prompt injection** ("ignore as instruções…") | Média | Modelo sai do papel | Detecção na entrada (G3) + o modelo só recebe contexto filtrado + guardrail de saída. |
| R6 | **Custo de tokens explode** com tráfego | Baixa | Orçamento | Recusa sem LLM fora do escopo (custo zero); contexto limitado a 3 pontos; alerta `ConsumoTokensAlto` (> 2 M tokens/dia). |

## Dados

Os pontos de coleta são **sintéticos**, gerados por `4_slice/scripts/gen_points.py` com seed fixa. Os bairros são reais (São Paulo), mas nomes, endereços, horários e status são fictícios. Todo registro traz `data_source = "sintetico"`, e a resposta do `/v1/ask` traz um `disclaimer` dizendo isso. O formato imita o cadastro aberto de ecopontos para que a troca por dado oficial seja só um novo adaptador. A orientação de descarte (`src/domain/knowledge.py`) resume regras públicas da PNRS (Lei 12.305/2010).
