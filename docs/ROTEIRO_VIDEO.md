# Roteiro do vídeo — ReciclaJá (GS Prompt & AI · 2CCPY)

**Duração do vídeo montado:** 2:50 (limite: 3:00). Arquivo mudo: `video/video_mudo.mp4`.
**Imagens:** cartelas + gravações **reais** de terminal (`video/*.tape`, gravadas com `vhs`, comandos executados de verdade).

## Como gravar e juntar

1. Abram `video/video_mudo.mp4` num player e gravem o áudio **olhando o vídeo**, cada um no seu bloco. Pode ser tudo numa ligação do Discord/Meet gravada, ou cada um grava o seu trecho e vocês colam na ordem.
2. Exportem um arquivo só: `video/audio.m4a` (ou .mp3/.wav), começando no 0:00 do vídeo.
3. Rodem `cd video && ./montar.sh audio.m4a`. Sai `video/video_final.mp4`, cortado em 3:00 com volume normalizado.
4. Subam no YouTube como **Não listado** e colem o link em `7_demo_video_url.txt`.

Ritmo: cerca de 2,3 palavras por segundo. Se sobrar fala, cortem a frase entre [colchetes].

---

| Tempo | Tela | Quem fala | Texto |
|---|---|---|---|
| **0:00–0:10** | Cartela: ReciclaJá + nomes/RMs | **Os 3** | **Gustavo Maia:** "Oi, eu sou o Gustavo Maia…" **Gabriel:** "…eu sou o Gabriel Fidalgo…" **Gustavo Rossi:** "…e eu sou o Gustavo Rossi. Esse é o ReciclaJá, da turma 2CCPY." |
| **0:10–0:25** | Cartela: problema e persona | **Gabriel** | "O problema: o morador não sabe onde nem como descartar pilha, óleo ou eletrônico, e isso vai parar no lixo comum ou na pia. A nossa persona é a Dona Cida, da Mooca. Ela pergunta em português comum e precisa saber o que fazer e onde levar, num ponto aberto e real." |
| **0:25–0:40** | Cartela: fluxo do /v1/ask | **Gustavo Rossi** | "Antes do código escrevemos o contrato em OpenAPI. No fluxo, o guardrail de entrada mascara CPF e telefone e recusa pergunta insegura ou fora do escopo sem chamar o modelo. O LLM só recebe pontos abertos do cadastro, e o guardrail de saída derruba resposta com ponto inventado." |
| **0:40–0:52** | Cartela: portas e adaptadores | **Gustavo Rossi** | "O domínio não conhece o LLM, só a porta. Fake, Ollama ou API externa são adaptadores: trocar o modelo é mudar uma linha de configuração. [Isso está nas quatro ADRs.]" |
| **0:52–1:02** | Terminal: GET PC-001 | **Gustavo Maia** | "Agora a API rodando no Docker Compose. Um ponto existente devolve 200, exatamente no schema do contrato…" |
| **1:02–1:12** | Terminal: 404 e 400 | **Gustavo Maia** | "…um ID que não existe dá 404, e um ID malformado dá 400, sempre com o mesmo corpo de erro." |
| **1:12–1:24** | Terminal: pergunta sobre pilhas | **Gustavo Maia** | "Perguntando onde jogar pilhas no Butantã: ele identifica o material, dá a orientação oficial e cita só pontos reais e abertos." |
| **1:24–1:38** | Terminal: recusas | **Gustavo Maia** | "Pergunta de futebol é recusada como fora do escopo, e 'queimar o lixo' é recusada como insegura. Nos dois casos o LLM nem é chamado: custo zero, risco zero." |
| **1:38–1:53** | Terminal: LLM real (porta 8001) | **Gustavo Maia** | "E aqui é o mesmo serviço com um modelo real, o Llama 3.2 rodando local no Ollama. Só mudamos a variável de ambiente. A resposta cita só pontos da Lapa que existem." |
| **1:53–2:08** | Terminal: pytest -v + cobertura | **Gabriel** | "São 38 testes: caminho feliz, erros, teste de contrato que valida cada resposta contra o YAML, e o LLM sempre fake, então o teste é determinístico. Cobertura de 96%." |
| **2:08–2:20** | Terminal: validador, evals, gh run list | **Gabriel** | "O YAML passa no validador, os evals de regressão rodam e o CI fica verde. O primeiro run falhou no scan de segredos, a gente corrigiu e ficou verde." |
| **2:20–2:27** | Cartela: print do GitHub Actions | **Gabriel** | "No GitHub Actions: lint, contrato, testes, evals, gitleaks e Docker." |
| **2:27–2:41** | Cartela: tabela de evals | **Gustavo Rossi** | "E se o modelo errar? Rodamos 30 casos com LLM real. O prompt v1 acertou só 47%. Com o prompt v2 e um guardrail novo, foi a 100%, mas com 32% de fallback. O Qwen 7B ficou lento demais." |
| **2:41–2:50** | Cartela: rollout | **Gustavo Maia** | "Por isso o gate libera só o piloto na Mooca. Público só com fallback abaixo de 20%. Valeu!" |

## Dicas de gravação

- Quem não estiver falando fica com o microfone mutado.
- Gravem com o vídeo tocando para bater o tempo. Se alguém atrasar, dá para regravar só aquele bloco e colar.
- Não precisa ler robótico: o importante é falar os **números** (38 testes, 96%, 47% → 100%, fallback 32%, piloto).
