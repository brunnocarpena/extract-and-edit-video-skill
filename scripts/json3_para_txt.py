"""Converte legenda json3 do YouTube em texto com minutagem a cada ~15 s.
Uso: python -I tools/json3_para_txt.py legendas/ID.pt.json3 > legendas/ID.txt"""
import json, sys

def mmss(ms):
    s = ms // 1000
    return f"{s//3600}:{s%3600//60:02d}:{s%60:02d}" if s >= 3600 else f"{s//60:02d}:{s%60:02d}"

d = json.load(open(sys.argv[1], encoding="utf-8"))
bloco, ini = [], None
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
        print(f"[{mmss(ini)}] " + " ".join(" ".join(bloco).split()))
        bloco, ini = [], None
if bloco:
    print(f"[{mmss(ini)}] " + " ".join(" ".join(bloco).split()))
