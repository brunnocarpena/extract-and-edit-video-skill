"""Converte legenda json3 do YouTube em texto com minutagem a cada ~15 s.
Uso: <python da skill> -I <pasta da skill>/scripts/json3_para_txt.py legendas/ID.pt.json3 transcricoes/ID.txt
(o transcrever.py chama isto para cada candidato)"""
import json, sys
from pathlib import Path


def mmss(ms):
    s = ms // 1000
    return f"{s//3600}:{s%3600//60:02d}:{s%60:02d}" if s >= 3600 else f"{s//60:02d}:{s%60:02d}"


def converter(json3):
    d = json.loads(Path(json3).read_text(encoding="utf-8"))
    linhas, bloco, ini = [], [], None
    for ev in d.get("events", []):
        segs = ev.get("segs")
        if not segs:
            continue
        t = ev.get("tStartMs", 0)
        txt = "".join(s.get("utf8", "") for s in segs).replace("\n", " ")
        if not txt.strip():
            continue
        if ini is None:
            ini = t
        bloco.append(txt)
        if t - ini >= 15000:
            linhas.append(f"[{mmss(ini)}] " + " ".join(" ".join(bloco).split()))
            bloco, ini = [], None
    if bloco:
        linhas.append(f"[{mmss(ini)}] " + " ".join(" ".join(bloco).split()))
    return "\n".join(linhas) + "\n"


if __name__ == "__main__":
    # grava direto em UTF-8: redirecionar com > no Windows estragaria os acentos
    Path(sys.argv[2]).write_text(converter(sys.argv[1]), encoding="utf-8")
