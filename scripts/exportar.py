"""Exporta um roteiro para edição em outro programa. Rodar DE DENTRO da pasta do projeto.

Uso: <venv>/bin/python -I <skill>/scripts/exportar.py roteiros/<nome>.json [premiere,capcut,srt]
     (sem a lista: os três)

Gera editor/<nome>/ com:
  clipes/NN_<slug>.mp4   trecho bruto, sem tarja/countdown/QR (cache de trechos/, baixa o que faltar)
  tarjas/NN.png          tarja do perfil em quadro 1280x720 transparente, já na posição
  legendas/NN_<slug>.srt legenda de cada clipe, a partir de legendas/<id>.pt.json3 (se existir)
  <nome>.srt             legenda da sequência inteira, na ordem do roteiro
  <nome>.xml             (premiere) XML FCP7/xmeml: V1 clipes em fila, V2 tarjas do seg. 2 ao 14, A1 áudio.
                         Abre no Premiere e no DaVinci Resolve (Arquivo > Importar).
  LEIA-ME.txt            como abrir em cada editor

O CapCut não importa projeto de fora: o "pacote capcut" são os clipes numerados + tarjas + SRT.
"""
import json, re, shutil, subprocess, sys, urllib.parse
from pathlib import Path
from xml.sax.saxutils import escape
sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I tira a pasta do script do path
from montar import RAIZ, PY, SOBRE, SKILL, TARJA_SEG, achar_ytdlp, baixar, slug, rodar

FPS, W, H = 30, 1280, 720


def probe(arq):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(arq)],
                         capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    num, den = d["streams"][0]["r_frame_rate"].split("/")
    return {"w": d["streams"][0]["width"], "h": d["streams"][0]["height"],
            "fps": float(num) / float(den), "dur": float(d["format"]["duration"])}


def seg(t):
    s = 0.0
    for p in t.split(":"):
        s = s * 60 + float(p)
    return s


def srt_tempo(ms):
    ms = max(int(ms), 0)
    return f"{ms // 3600000:02d}:{ms % 3600000 // 60000:02d}:{ms % 60000 // 1000:02d},{ms % 1000:03d}"


def palavras(json3, ini_ms, fim_ms):
    """Palavras com tempo absoluto (ms) dentro da janela [ini, fim)."""
    d = json.loads(Path(json3).read_text(encoding="utf-8"))
    res = []
    for ev in d.get("events", []):
        t0 = ev.get("tStartMs", 0)
        for s in ev.get("segs") or []:
            w = s.get("utf8", "").replace("\n", " ").strip()
            t = t0 + s.get("tOffsetMs", 0)
            if w and ini_ms <= t < fim_ms:
                res.append((t, w))
    return res


def legendas(ps, ini_ms, fim_ms, desloc_ms=0, max_chars=42, max_ms=3500):
    """Agrupa palavras em falas de até 42 caracteres / 3,5 s, com tempo relativo ao clipe + desloc."""
    cues, atual, t_ini = [], [], None
    for i, (t, w) in enumerate(ps):
        if atual and (len(" ".join(atual + [w])) > max_chars or t - t_ini > max_ms):
            cues.append((t_ini, t, " ".join(atual)))
            atual, t_ini = [], None
        if t_ini is None:
            t_ini = t
        atual.append(w)
    if atual:
        cues.append((t_ini, min(t_ini + max_ms, fim_ms), " ".join(atual)))
    return [(a - ini_ms + desloc_ms, b - ini_ms + desloc_ms, txt) for a, b, txt in cues]


def escrever_srt(cues, arq):
    arq.write_text("".join(f"{n}\n{srt_tempo(a)} --> {srt_tempo(b)}\n{txt}\n\n"
                           for n, (a, b, txt) in enumerate(cues, 1)), encoding="utf-8")


def main(roteiro_path, formatos):
    r = json.loads(Path(roteiro_path).read_text(encoding="utf-8"))
    for it in r["itens"]:
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", it["id"]):
            sys.exit(f"id do YouTube inválido: {it['id']!r}")
    perfil_arq = Path(r["perfil"]) if r.get("perfil") else SKILL / "perfis/mari.json"
    perfil = json.loads(perfil_arq.read_text(encoding="utf-8"))
    nome = Path(r["saida"]).stem
    if not re.fullmatch(r"[\w.-]+", nome) or set(nome) == {"."}:
        sys.exit(f"saida com nome inválido: {r['saida']}")
    out = RAIZ / "editor" / nome
    for sub in ("clipes", "tarjas", "legendas"):
        (out / sub).mkdir(parents=True, exist_ok=True)

    ytdlp = achar_ytdlp()
    itens = []
    for n, it in enumerate(r["itens"], 1):
        bruto = baixar(it, ytdlp)
        base = f"{n:02d}_{slug(it.get('nome') or it.get('tarja') or it['id'])}"
        clipe = out / "clipes" / f"{base}.mp4"
        if not clipe.exists():
            shutil.copyfile(bruto, clipe)
        info = probe(clipe)
        tarja = None
        if it.get("tarja"):
            tarja = out / "tarjas" / f"{n:02d}.png"
            if not tarja.exists():
                rodar([PY, "-I", SOBRE, "--perfil", perfil_arq, "tarja",
                       it.get("rotulo", perfil.get("rotulo_tarja", "Depoimento")), it["tarja"], tarja])
                from PIL import Image  # quadro cheio: o editor não precisa reposicionar
                t = Image.open(tarja)
                q = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                q.paste(t, (40, H - t.height - 92), t)
                q.save(tarja)
        itens.append({"it": it, "base": base, "clipe": clipe, "info": info, "tarja": tarja})
        print(f"  {n}/{len(r['itens'])} {clipe.name}")

    if "srt" in formatos or "capcut" in formatos:
        todas, desloc = [], 0
        for x in itens:
            j3 = RAIZ / "legendas" / f"{x['it']['id']}.pt.json3"
            dur_ms = int(x["info"]["dur"] * 1000)
            if j3.exists():
                ini = int(seg(x["it"]["ini"]) * 1000)
                ps = palavras(j3, ini, ini + dur_ms)
                escrever_srt(legendas(ps, ini, ini + dur_ms), out / "legendas" / f"{x['base']}.srt")
                todas += legendas(ps, ini, ini + dur_ms, desloc)
            else:
                print(f"  sem legendas/{x['it']['id']}.pt.json3: clipe {x['base']} fica sem SRT")
            desloc += dur_ms
        if todas:
            escrever_srt(todas, out / f"{nome}.srt")

    if "premiere" in formatos:
        rate = f"<rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate>"
        url = lambda p: "file://localhost" + urllib.parse.quote(str(Path(p).resolve()))
        v1, v2, a1, pos = [], [], [], 0
        for n, x in enumerate(itens, 1):
            fr = int(round(x["info"]["dur"] * FPS))
            fid = f"file-{n}"
            fxml = (f'<file id="{fid}"><name>{escape(x["clipe"].name)}</name><pathurl>{url(x["clipe"])}</pathurl>'
                    f"{rate}<duration>{fr}</duration><media><video><samplecharacteristics><width>{x['info']['w']}"
                    f"</width><height>{x['info']['h']}</height></samplecharacteristics></video>"
                    f"<audio><channelcount>2</channelcount></audio></media></file>")
            clip = lambda cid, f, extra="", ini=pos, fim=pos + fr: (
                f'<clipitem id="{cid}"><name>{escape(x["base"])}</name><enabled>TRUE</enabled>'
                f"<duration>{fr}</duration>{rate}<start>{ini}</start><end>{fim}</end><in>0</in>"
                f"<out>{fim - ini}</out>{f}{extra}</clipitem>")
            v1.append(clip(f"v-{n}", fxml))
            a1.append(clip(f"a-{n}", f'<file id="{fid}"/>',
                           "<sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack>"))
            if x["tarja"]:
                a, b = TARJA_SEG
                ini, fim = pos + a * FPS, min(pos + b * FPS, pos + fr)
                txml = (f'<file id="tarja-{n}"><name>{x["tarja"].name}</name><pathurl>{url(x["tarja"])}</pathurl>'
                        f"{rate}<duration>{fim - ini}</duration><media><video><samplecharacteristics>"
                        f"<width>{W}</width><height>{H}</height></samplecharacteristics></video></media></file>")
                v2.append(f'<clipitem id="t-{n}"><name>tarja {n:02d}</name><enabled>TRUE</enabled>'
                          f"<duration>{fim - ini}</duration>{rate}<start>{ini}</start><end>{fim}</end>"
                          f"<in>0</in><out>{fim - ini}</out>{txml}</clipitem>")
            pos += fr
        xml = (f'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="4"><sequence id="seq-1">'
               f"<name>{escape(nome)}</name><duration>{pos}</duration>{rate}<media><video><format>"
               f"<samplecharacteristics>{rate}<width>{W}</width><height>{H}</height>"
               f"<pixelaspectratio>square</pixelaspectratio></samplecharacteristics></format>"
               f"<track>{''.join(v1)}</track><track>{''.join(v2)}</track></video>"
               f"<audio><track>{''.join(a1)}</track></audio></media></sequence></xmeml>\n")
        (out / f"{nome}.xml").write_text(xml, encoding="utf-8")

    (out / "LEIA-ME.txt").write_text(f"""Pacote de edição: {nome}
Mantenha esta pasta inteira junta: o XML aponta para os arquivos de clipes/ e tarjas/.

Premiere Pro: Arquivo > Importar > {nome}.xml. Abre a sequência com os clipes em ordem (V1),
  as tarjas por cima (V2, do segundo {TARJA_SEG[0]} ao {TARJA_SEG[1]} de cada clipe) e o áudio (A1).
  Legenda: Arquivo > Importar > {nome}.srt e arraste para a timeline.
DaVinci Resolve: File > Import > Timeline > {nome}.xml (mesmo XML do Premiere).
CapCut: arraste os arquivos de clipes/ na ordem dos números; as tarjas de tarjas/ vão numa
  camada por cima. Legenda: arquivos .srt de legendas/ (um por clipe) ou {nome}.srt (sequência toda).
Outro editor (Final Cut, iMovie...): mesma lógica do CapCut.

Os clipes são brutos (sem tarja, countdown ou QR). A legenda vem da legenda automática do
YouTube: revise nomes próprios e números antes de publicar.
""", encoding="utf-8")
    print(f"pronto: {out}")


if __name__ == "__main__":
    fm = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else {"premiere", "capcut", "srt"}
    if fm - {"premiere", "capcut", "srt"}:
        sys.exit(f"formato desconhecido: {', '.join(fm - {'premiere', 'capcut', 'srt'})}")
    main(sys.argv[1], fm)
