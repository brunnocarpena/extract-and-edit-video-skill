"""Passo 3: baixa a legenda automática de cada ID de dados/candidatos.txt e grava
transcricoes/<id>.txt com minutagem. Rodar DE DENTRO da pasta do projeto:
  <python da skill> -I <pasta da skill>/scripts/transcrever.py
Retomável: pula quem já tem transcrição. Pausa de 2-3 s entre vídeos para não levar 429."""
import random, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I tira a pasta do script do path
from montar import achar_ytdlp
from json3_para_txt import converter

ids = [l.strip() for l in Path("dados/candidatos.txt").read_text(encoding="utf-8").splitlines()
       if l.strip() and not l.lstrip().startswith("#")]
Path("legendas").mkdir(exist_ok=True)
Path("transcricoes").mkdir(exist_ok=True)
ytdlp = achar_ytdlp()
falhas = []
for n, vid in enumerate(ids, 1):
    txt = Path(f"transcricoes/{vid}.txt")
    if txt.exists():
        continue
    subprocess.run([ytdlp, "-q", "--no-warnings", "--skip-download", "--write-auto-subs",
                    "--sub-langs", "pt", "--sub-format", "json3", "-o", "legendas/%(id)s",
                    f"https://www.youtube.com/watch?v={vid}"])
    j = Path(f"legendas/{vid}.pt.json3")
    if j.exists():
        txt.write_text(converter(j), encoding="utf-8")
        print(f"{n}/{len(ids)} ok {vid}", flush=True)
    else:
        falhas.append(vid)
        print(f"{n}/{len(ids)} sem legenda {vid}", flush=True)
    time.sleep(random.uniform(2, 3))
if falhas:
    print("sem legenda:", " ".join(falhas))
