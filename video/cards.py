"""Gera as cartelas do vídeo (HTML -> PNG 1920x1080 via Chrome headless)."""
import base64, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT.parent / "docs"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CSS = """
*{box-sizing:border-box;margin:0}
body{width:1920px;height:1080px;background:#0f1f17;color:#eaf5ee;font-family:-apple-system,'Helvetica Neue',Arial,sans-serif;padding:80px 110px;overflow:hidden}
.tag{display:inline-block;background:#1f7a4d;color:#fff;font-weight:700;padding:10px 22px;border-radius:999px;font-size:26px;letter-spacing:.5px}
h1{font-size:96px;line-height:1.05;margin:28px 0 18px;font-weight:800}
h2{font-size:60px;margin:22px 0 30px;font-weight:800}
p,li{font-size:34px;line-height:1.45;color:#cfe3d6}
.accent{color:#5fd89a}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:28px;margin-top:20px}
.card{background:#16301f;border:2px solid #24503a;border-radius:22px;padding:30px 36px}
.card b{color:#fff}
table{border-collapse:collapse;width:100%;font-size:30px;margin-top:10px}
th,td{padding:16px 18px;border-bottom:2px solid #24503a;text-align:left}
th{color:#5fd89a;font-size:26px;text-transform:uppercase;letter-spacing:1px}
.ok{color:#5fd89a;font-weight:800}.no{color:#ff7a7a;font-weight:800}.mid{color:#ffd166;font-weight:800}
.img{display:flex;justify-content:center;align-items:center;height:760px;background:#fff;border-radius:22px;padding:20px}
.img img{max-height:100%;max-width:100%}
.foot{position:absolute;bottom:50px;left:110px;font-size:26px;color:#7fa892}
ul{padding-left:36px}
"""

def img(p):
    return "data:image/png;base64," + base64.b64encode(Path(p).read_bytes()).decode()

FOOT = '<div class="foot">GS2026.2 · Prompt and Artificial Intelligence · 2CCPY · Grupo ReciclaJá</div>'
CARDS = {
"01_abertura": f"""<span class="tag">GS2026.2 · CitizenTech · Frente C — Descarte</span>
<h1>Recicla<span class="accent">Já</span></h1>
<p style="font-size:42px">Serviço de orientação de descarte com IA — pronto para produção</p>
<div class="grid" style="grid-template-columns:1fr 1fr 1fr;margin-top:70px">
<div class="card"><b style="font-size:40px">Gabriel Fidalgo</b><p>RM563213</p></div>
<div class="card"><b style="font-size:40px">Gustavo Maia</b><p>RM562240</p></div>
<div class="card"><b style="font-size:40px">Gustavo Rossi</b><p>RM566075</p></div></div>
<p style="margin-top:50px">Engenharia de Software · Turma 2CCPY-2026 · Prof. Jorge Luiz Gomes</p>""",
"02_problema": f"""<span class="tag">Problema e persona</span>
<h2>“Onde eu jogo isso?”</h2>
<div class="grid"><div class="card"><p><b>Problema:</b> o morador não sabe onde nem como descartar pilha, óleo, eletrônico ou entulho — e acaba no lixo comum, na pia ou na rua.</p></div>
<div class="card"><p><b>Dona Cida, 58, Mooca.</b> Pergunta em português comum e precisa de: <span class="accent">o que fazer</span> + <span class="accent">onde levar</span> (ponto aberto e real).</p></div>
<div class="card"><p><b>Contrato:</b> OpenAPI 3.1 · 4 endpoints · erro único 400/404/422/503 · paginação</p></div>
<div class="card"><p><b>Pergunta da banca:</b> e se o modelo errar? → guardrail + fallback + 503 documentado</p></div></div>{FOOT}""",
"03_fluxo": f"""<span class="tag">Arquitetura · fluxo do POST /v1/ask</span>
<div class="grid" style="grid-template-columns:1.5fr 1fr;align-items:center;margin-top:10px">
<div class="img" style="height:920px"><img src="{img(DOCS/'diagramas/arq_1.png')}"></div>
<div><ul><li>Guardrail de entrada: mascara CPF/telefone, bloqueia inseguro e <i>prompt injection</i></li>
<li>Fora do escopo → recusa <b>sem chamar o LLM</b></li><li>LLM recebe só até 3 pontos <b>abertos</b> do cadastro</li>
<li>Guardrail de saída: ponto inventado / sem citação / PII → <span class="accent">fallback</span></li><li>LLM fora do ar → <b>503</b> + Retry-After</li></ul></div></div>""",
"04_portas": f"""<span class="tag">Fronteira · trocar o LLM = trocar uma peça</span>
<div class="img" style="height:600px;margin-top:30px"><img src="{img(DOCS/'diagramas/arq_2.png')}"></div>
<p style="margin-top:30px;font-size:38px">Domínio não importa biblioteca de LLM (teste de AST quebra o build) · <span class="accent">LLM_MODEL=qwen2.5:7b</span> — 1 linha · 4 ADRs</p>""",
"05_ci": f"""<span class="tag">Prova · GitHub Actions (run real)</span>
<div class="img" style="height:820px;margin-top:30px;background:#000"><img src="{img(DOCS/'prints/ci_run_verde.png')}"></div>
<p style="margin-top:20px">ruff · openapi-spec-validator · 38 testes (96%) · evals · gitleaks · docker compose</p>""",
"06_evals": f"""<span class="tag">Evals · 30 casos com LLM real</span>
<h2>O gate decide quem vai pra produção</h2>
<table><tr><th>Candidato</th><th>Resposta correta</th><th>Guardrail</th><th>Fallback</th><th>p95</th><th>Veredito</th></tr>
<tr><td>llama3.2:3b · prompt v1</td><td class="no">46,7%</td><td class="no">83,3%</td><td>4,5%</td><td>3,0 s</td><td class="no">Bloqueado</td></tr>
<tr><td>llama3.2:3b · prompt v2 + G1b</td><td class="ok">100%</td><td class="ok">100%</td><td class="mid">31,8%</td><td>3,7 s</td><td class="mid">Só piloto</td></tr>
<tr><td>qwen2.5:7b · prompt v2</td><td>93,3%</td><td class="no">83,3%</td><td>9,1%</td><td class="no">14,4 s</td><td class="no">Bloqueado</td></tr></table>
<p style="margin-top:40px">Metas: correta ≥ 90% · guardrail 100% · p95 ≤ 4 s · público exige fallback ≤ 20%</p>{FOOT}""",
"07_fim": f"""<span class="tag">Como entregamos para a prefeitura e dormimos tranquilos</span>
<h2>Interno → <span class="mid">Piloto (Mooca, 5%)</span> → Público</h2>
<div class="grid"><div class="card"><p><b>Público só com:</b> fallback ≤ 20%, 0 incidente de PII, 2 semanas de piloto, amostra humana ≥ 95%</p></div>
<div class="card"><p><b>Rollback:</b> volta LLM_MODEL / PROMPT_VERSION anterior — 1 linha</p></div></div>
<p style="margin-top:60px;font-size:38px">github.com/gustavopmaia/<span class="accent">gs2026-2-reciclaja-api</span></p>
<p style="margin-top:20px">Gabriel Fidalgo RM563213 · Gustavo Maia RM562240 · Gustavo Rossi RM566075</p>""",
}

out = ROOT / "cards"
out.mkdir(exist_ok=True)
for name, body in CARDS.items():
    html = out / f"{name}.html"
    html.write_text(f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{body}</body></html>', encoding="utf-8")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1920,1080",
                    f"--screenshot={out / (name + '.png')}", html.as_uri()], capture_output=True, check=True)
    html.unlink()
    print(name)
