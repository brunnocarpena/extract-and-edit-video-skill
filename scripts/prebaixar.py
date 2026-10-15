"""Baixa para trechos/ os cortes longos (A e B) já mapeados, para a montagem não esperar download.
Rodar DE DENTRO da pasta do projeto: <venv>/bin/python -I <skill>/scripts/prebaixar.py"""
import glob, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I tira a pasta do script do path
from montar import achar_ytdlp, baixar

ytdlp = achar_ytdlp()
for f in sorted(glob.glob("dados/mapas/*.json")):
    d = json.load(open(f, encoding="utf-8"))
    for m in d if isinstance(d, list) else [d]:  # mapa pode ter 2 cortes
        if m.get("forca") not in ("A", "B") or not m.get("longo"):
            continue
        try:
            baixar({"id": m["id"], "ini": m["longo"]["ini"], "fim": m["longo"]["fim"]}, ytdlp)
            print("ok", m["id"], m["longo"]["ini"], flush=True)
        except Exception as e:
            print("falhou", m["id"], e, flush=True)
