#!/usr/bin/env bash
# Monta o vídeo da GS (≤ 3:00).
#   ./montar.sh            -> gera video_mudo.mp4 (cartelas + gravações reais de terminal)
#   ./montar.sh audio.m4a  -> junta o áudio gravado pelo grupo e corta em 3:00 => video_final.mp4
set -euo pipefail
cd "$(dirname "$0")"
V="-c:v libx264 -pix_fmt yuv420p -r 30 -vf scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=0x1e1f29"
mkdir -p build
seg() { ffmpeg -v error -y -loop 1 -t "$2" -i "cards/$1.png" $V "build/$1.mp4"; }
# Duração de cada bloco = tempo de fala do roteiro (docs/ROTEIRO_VIDEO.md)
seg 01_abertura 10
seg 02_problema 15
seg 03_fluxo 15
seg 04_portas 12
ffmpeg -v error -y -i raw/demo_api.mp4 $V -an build/demo_api.mp4       # 61 s
ffmpeg -v error -y -i raw/demo_testes.mp4 $V -an build/demo_testes.mp4 # 27 s
seg 05_ci 7
seg 06_evals 14
seg 07_fim 9
printf "file '%s'\n" 01_abertura.mp4 02_problema.mp4 03_fluxo.mp4 04_portas.mp4 demo_api.mp4 demo_testes.mp4 05_ci.mp4 06_evals.mp4 07_fim.mp4 > build/lista.txt
ffmpeg -v error -y -f concat -safe 0 -i build/lista.txt -c copy video_mudo.mp4
echo "video_mudo.mp4: $(ffprobe -v error -show_entries format=duration -of csv=p=0 video_mudo.mp4) s"
if [ "${1:-}" != "" ]; then
  ffmpeg -v error -y -i video_mudo.mp4 -i "$1" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 160k -af "loudnorm=I=-16:TP=-1.5" -t 180 video_final.mp4
  echo "video_final.mp4: $(ffprobe -v error -show_entries format=duration -of csv=p=0 video_final.mp4) s"
fi
