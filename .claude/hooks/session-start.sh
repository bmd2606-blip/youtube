#!/bin/bash
# Prepara el entorno de Claude Code en la web para renderizar con HyperFrames.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# FFmpeg / FFprobe: necesarios para codificar el vídeo
if ! command -v ffmpeg >/dev/null 2>&1; then
  (apt-get update -qq && apt-get install -y -qq ffmpeg) >/dev/null 2>&1 || \
    echo "No se pudo instalar ffmpeg" >&2
fi

# Chrome headless que usa HyperFrames para capturar los frames
cd "$CLAUDE_PROJECT_DIR/animaciones"
npx --yes hyperframes@0.8.79 browser ensure >/dev/null 2>&1 || \
  echo "No se pudo preparar Chrome headless (npx hyperframes browser ensure)" >&2
