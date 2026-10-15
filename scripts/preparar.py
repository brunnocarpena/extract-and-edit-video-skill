"""Cria o venv compartilhado da skill (yt-dlp + Pillow + segno) e confere o ffmpeg.
Funciona em macOS, Windows e Linux. Rodar uma vez por máquina:

  macOS/Linux:  python3 <pasta da skill>/scripts/preparar.py
  Windows:      py <pasta da skill>\\scripts\\preparar.py

Versões fixas e só wheels binários: passar pelo supply-chain-guard antes de subir versão.
No fim imprime o caminho do python do venv - é ele que roda os outros scripts.
Outro lugar para o venv: variável VIDEO_VENV.
"""
import os, platform, shutil, subprocess, sys, venv
from pathlib import Path

PACOTES = ["yt-dlp==2026.8.19", "pillow==12.3.0", "segno==1.6.6"]
VENV = Path(os.environ.get("VIDEO_VENV") or Path.home() / ".cache/extract-and-edit-video/venv")
BIN = VENV / ("Scripts" if os.name == "nt" else "bin")
PY = BIN / ("python.exe" if os.name == "nt" else "python")

if sys.version_info < (3, 11):
    sys.exit(f"precisa de Python 3.11+ (este é {platform.python_version()})")

if not PY.exists():
    print("criando venv em", VENV, flush=True)
    venv.create(VENV, with_pip=True)
    subprocess.run([str(PY), "-m", "pip", "install", "-q", "--only-binary=:all:", *PACOTES], check=True)

if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
    dica = {"Darwin": "brew install ffmpeg",
            "Windows": "winget install Gyan.FFmpeg  (depois feche e abra o terminal)",
            "Linux": "sudo apt install ffmpeg  (ou dnf/pacman)"}.get(platform.system(), "instale o ffmpeg")
    sys.exit(f"falta ffmpeg/ffprobe no PATH: {dica}")

ver = subprocess.run([str(PY), "-m", "yt_dlp", "--version"], capture_output=True, text=True).stdout.strip()
print(f"ok - yt-dlp {ver}, ffmpeg em {shutil.which('ffmpeg')}")
print(f"python da skill: {PY}")
