#!/bin/bash
# Monta el vídeo final: despliegue (simulador) + parte HTML + arrugado (simulador).
set -euo pipefail
cd "$(dirname "$0")"
B=build
rm -rf "$B" && mkdir -p "$B/unfold" "$B/crumple" renders

# 1 · Bola que cae y se despliega (hoja en blanco)
python3 -I tools/papel_sim.py unfold assets/papel.png "$B/unfold"

# 2 · Parte central HTML (hoja plana, la fecha se escribe)
npx hyperframes@0.8.79 render --fps 30 --quality high -o "$B/medio.mp4"
[ -f "$B/medio.mp4" ] || npx hyperframes@0.8.79 render --fps 30 --quality high -o "$B/medio.mp4"

# 3 · Textura de la hoja con el texto: último fotograma de la parte central, recortado
ffmpeg -loglevel error -y -sseof -0.04 -i "$B/medio.mp4" -frames:v 1 -vf "crop=1200:780:360:150" "$B/hoja_con_texto.png"
python3 -I tools/papel_sim.py crumple "$B/hoja_con_texto.png" "$B/crumple"

# 4 · Unir las tres partes
ffmpeg -loglevel error -y \
  -framerate 30 -i "$B/unfold/f%04d.png" \
  -i "$B/medio.mp4" \
  -framerate 30 -i "$B/crumple/f%04d.png" \
  -filter_complex "[0:v]format=yuv420p,setsar=1[a];[1:v]format=yuv420p,setsar=1[b];[2:v]format=yuv420p,setsar=1[c];[a][b][c]concat=n=3:v=1[v]" \
  -map "[v]" -c:v libx264 -crf 16 -preset slow -pix_fmt yuv420p -r 30 -movflags +faststart renders/papel-1945.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 renders/papel-1945.mp4
