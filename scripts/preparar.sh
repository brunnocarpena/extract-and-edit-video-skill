#!/bin/sh
# Cria o venv compartilhado da skill (yt-dlp + Pillow + segno) e confere o ffmpeg.
# Versões fixas e só wheels binários: passar pelo supply-chain-guard antes de subir versão.
set -e
VENV="${VIDEO_VENV:-$HOME/.cache/extract-and-edit-video/venv}"
if [ ! -x "$VENV/bin/python" ]; then
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q --only-binary=:all: "yt-dlp==2026.8.19" "pillow==12.3.0" "segno==1.6.6"
fi
command -v ffmpeg >/dev/null || { echo "falta ffmpeg (brew install ffmpeg)"; exit 1; }
echo "venv: $VENV"
"$VENV/bin/yt-dlp" --version
