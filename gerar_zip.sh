#!/usr/bin/env bash
# Gera GS2026_2_2CCPY_ReciclaJa.zip a partir dos arquivos versionados (sem .venv, .env, caches).
set -euo pipefail
cd "$(dirname "$0")"
OUT=../entregas/GS2026_2_2CCPY_ReciclaJa.zip
mkdir -p ../entregas && rm -f "$OUT"
git ls-files 1_visao_produto.md 2_contrato_api.yaml 3_arquitetura.md 4_slice 5_evals_de_ia.md 6_README.md \
  7_demo_video_url.txt 8_certificacao.txt 9_Chat_Log.txt docs | zip -q "$OUT" -@
unzip -l "$OUT" | tail -1
unzip -l "$OUT" | grep -E "\.env$|\.venv" && { echo "ERRO: segredo/venv no zip"; exit 1; } || echo "ok: sem .env/.venv"
