# Prova: pytest, contrato, evals e CI (execucao real)
Output raw/demo_testes.mp4
Set Shell bash
Set FontSize 19
Set Width 1920
Set Height 1080
Set Padding 36
Set Theme "Dracula"
Set TypingSpeed 28ms
Hide
Type "cd /Users/gustavo/projects/gs2-2026/eng-software/4_slice && source .venv/bin/activate && export PS1='\[\e[32m\]reciclaja\[\e[0m\] $ ' && clear"
Enter
Show
Type "pytest -o addopts='' -v -p no:warnings | grep -E 'PASSED|FAILED|passed' | sed -E 's/ +[[] *[0-9]+%[]]//' | cut -c1-110"
Enter
Sleep 6s
Type "clear"
Enter
Type "pytest --cov --cov-fail-under=80 -p no:warnings | tail -3"
Enter
Sleep 4s
Type "clear"
Enter
Type "openapi-spec-validator ../2_contrato_api.yaml"
Enter
Sleep 2s
Type "python evals/run_evals.py | tail -12"
Enter
Sleep 4s
Type "gh run list --repo gustavopmaia/gs2026-2-reciclaja-api -L 3"
Enter
Sleep 5s
