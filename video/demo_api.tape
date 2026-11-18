# Demo real da API (docker compose em :8000 com FakeLLM; uvicorn em :8001 com Ollama llama3.2:3b)
Output raw/demo_api.mp4
Set Shell bash
Set FontSize 24
Set Width 1920
Set Height 1080
Set Padding 36
Set Theme "Dracula"
Set TypingSpeed 28ms
Hide
Type "cd /Users/gustavo/projects/gs2-2026/eng-software/4_slice && export PS1='\[\e[32m\]reciclaja\[\e[0m\] $ ' && clear"
Enter
Show
Type "# 1) Ponto existente -> 200 no schema do contrato"
Enter
Type "curl -s localhost:8000/v1/points/PC-001 | jq -c"
Enter
Sleep 3s
Type "# 2) Ponto inexistente -> 404 | ID malformado -> 400 (mesmo corpo de erro)"
Enter
Type "curl -s -w '  HTTP %{http_code}\n' localhost:8000/v1/points/PC-999"
Enter
Sleep 2s
Type "curl -s -w '  HTTP %{http_code}\n' localhost:8000/v1/points/abc"
Enter
Sleep 3s
Type "clear"
Enter
Type "# 3) Pergunta ao assistente -> material, pontos ABERTOS e reais"
Enter
Type `curl -s -X POST localhost:8000/v1/ask -H 'Content-Type: application/json' -d '{"question":"Onde jogo pilhas usadas?","neighborhood":"Butantã"}' | jq '{mode, material, cited_points, answer}'`
Enter
Sleep 4s
Type "# 4) Fora do escopo e pedido inseguro -> recusa SEM chamar o LLM"
Enter
Type `curl -s -X POST localhost:8000/v1/ask -H 'Content-Type: application/json' -d '{"question":"Quem ganhou o jogo ontem?"}' | jq -c '{mode, refusal_reason}'`
Enter
Sleep 2s
Type `curl -s -X POST localhost:8000/v1/ask -H 'Content-Type: application/json' -d '{"question":"Posso queimar o lixo no quintal?"}' | jq -c '{mode, refusal_reason}'`
Enter
Sleep 3s
Type "clear"
Enter
Type "# 5) Mesmo servico com LLM REAL: so mudou LLM_PROVIDER=ollama LLM_MODEL=llama3.2:3b"
Enter
Type "curl -s localhost:8001/v1/health | jq -c"
Enter
Sleep 2s
Type `curl -s -X POST localhost:8001/v1/ask -H 'Content-Type: application/json' -d '{"question":"Onde levo lampada fluorescente queimada?","neighborhood":"Lapa"}' | jq '{mode, cited_points, answer}'`
Enter
Sleep 8s
