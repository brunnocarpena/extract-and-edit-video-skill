"""Exporta um roteiro para edição em outro programa. Rodar DE DENTRO da pasta do projeto.

Uso: <python da skill> -I <pasta da skill>/scripts/exportar.py roteiros/<nome>.json [premiere,capcut,srt]
     (sem a lista: os três)

Gera editor/<nome>/ com:
  clipes/NN_<slug>.mp4   trecho bruto em 1280x720, sem tarja/countdown/QR e sem o selo da live
                         (vem do montar.py --cru, que também grava brutos/<nome>.mp4)
  tarjas/NN.png          tarja do perfil em quadro 1280x720 transparente, já na posição
  camadas/countdown.mov  (se o roteiro tem countdown) relógio com alfa, codec Animation, quadro cheio
  camadas/countdown-chroma.mp4  o mesmo relógio sobre verde, para editor sem alfa (chroma key)
  camadas/qr.png         (se o roteiro tem qr) QR em quadro 1280x720 transparente
  legendas/NN_<slug>.srt legenda de cada clipe, a partir de legendas/<id>.pt.json3 (se existir)
  <nome>.srt             legenda da sequência inteira, na ordem do roteiro
  <nome>.xml             (premiere) XML FCP7/xmeml: V1 clipes em fila, V2 tarjas do seg. 2 ao 14,
                         V3 countdown, V4 QR, A1 áudio.
                         Abre no Premiere e no DaVinci Resolve (Arquivo > Importar).
  LEIA-ME.txt            como abrir em cada editor

O CapCut não importa projeto de fora: o "pacote capcut" são os clipes numerados + tarjas + SRT.
"""
import json, re, shutil, subprocess, sys, urllib.parse
from pathlib import Path
from xml.sax.saxutils import escape
sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I tira a pasta do script do path
import montar
from montar import RAIZ, PY, SOBRE, SKILL, TARJA_SEG, slug, rodar, validar

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
    validar(r["itens"])
    perfil_arq = Path(r["perfil"]) if r.get("perfil") else SKILL / "perfis/mari.json"
    perfil = json.loads(perfil_arq.read_text(encoding="utf-8"))
    nome = Path(r["saida"]).stem
    if not re.fullmatch(r"[\w.-]+", nome) or set(nome) == {"."}:
        sys.exit(f"saida com nome inválido: {r['saida']}")
    out = RAIZ / "editor" / nome
    for sub in ("clipes", "tarjas", "legendas", "camadas"):
        (out / sub).mkdir(parents=True, exist_ok=True)

    montar.main(roteiro_path, cru=True)  # partes cruas em montagem/<nome>-cru/NNN.mp4
    itens = []
    for n, it in enumerate(r["itens"], 1):
        base = f"{n:02d}_{slug(it.get('nome') or it.get('tarja') or it.get('id') or Path(it['arquivo']).stem)}"
        clipe = out / "clipes" / f"{base}.mp4"
        if not clipe.exists():
            shutil.copyfile(RAIZ / "montagem" / f"{nome}-cru" / f"{n - 1:03d}.mp4", clipe)
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
            j3 = RAIZ / "legendas" / f"{x['it'].get('id')}.pt.json3"
            dur_ms = int(x["info"]["dur"] * 1000)
            if j3.exists():
                ini = int(seg(x["it"]["ini"]) * 1000)
                ps = palavras(j3, ini, ini + dur_ms)
                escrever_srt(legendas(ps, ini, ini + dur_ms), out / "legendas" / f"{x['base']}.srt")
                todas += legendas(ps, ini, ini + dur_ms, desloc)
            else:
                print(f"  sem legenda automática para {x['base']}: clipe fica sem SRT")
            desloc += dur_ms
        if todas:
            escrever_srt(todas, out / f"{nome}.srt")

    total_fr = sum(int(round(x["info"]["dur"] * FPS)) for x in itens)
    cd_mov = out / "camadas" / "countdown.mov"
    if r.get("countdown") and not cd_mov.exists():
        pngs = out / "camadas" / "_countdown_png"
        total = -(-total_fr // FPS)
        rodar([PY, "-I", SOBRE, "--perfil", perfil_arq, "countdown", total, r["countdown"], pngs])
        base_cd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", "1", "-start_number", "0",
                   "-i", pngs / "%06d.png", "-frames:v", total_fr]
        quadro = f"fps={FPS},format=rgba,pad={W}:{H}:(ow-iw)/2:24:color=black@0"
        # Animation (qtrle) com GOP longo: alfa e ~30 MB/hora, porque o quadro quase não muda
        rodar(base_cd + ["-vf", quadro, "-c:v", "qtrle", "-g", "300", "-pix_fmt", "argb", cd_mov])
        rodar(base_cd + ["-vf", f"fps={FPS},pad={W}:{H}:(ow-iw)/2:24:color=0x00FF00,format=yuv420p",
                         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-tune", "stillimage",
                         out / "camadas" / "countdown-chroma.mp4"])
        shutil.rmtree(pngs)
    qr_png = out / "camadas" / "qr.png"
    if r.get("qr") and not qr_png.exists():
        rodar([PY, "-I", SOBRE, "--perfil", perfil_arq, "qr", r["qr"]["url"],
               r["qr"].get("legenda", "Ficha de interesse"), qr_png])
        from PIL import Image
        t = Image.open(qr_png)
        q = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        q.paste(t, (W - t.width - 32, H - t.height - 92), t)
        q.save(qr_png)

    if "premiere" in formatos:
        rate = f"<rate><timebase>{FPS}</timebase><ntsc>FALSE</ntsc></rate>"
        # file://localhost/Users/... no Mac/Linux e file://localhost/C:/Users/... no Windows
        url = lambda p: "file://localhost" + urllib.parse.quote("/" + Path(p).resolve().as_posix().lstrip("/"), safe="/:")
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
        camada = lambda cid, nome_c, arq, fr_arq: (
            f'<track><clipitem id="{cid}"><name>{nome_c}</name><enabled>TRUE</enabled><duration>{fr_arq}</duration>'
            f"{rate}<start>0</start><end>{pos}</end><in>0</in><out>{pos}</out>"
            f'<file id="{cid}-f"><name>{arq.name}</name><pathurl>{url(arq)}</pathurl>{rate}<duration>{fr_arq}'
            f"</duration><media><video><samplecharacteristics><width>{W}</width><height>{H}</height>"
            f"</samplecharacteristics></video></media></file></clipitem></track>")
        extra = ""
        if cd_mov.exists():
            extra += camada("countdown", "countdown", cd_mov, pos)
        if qr_png.exists():
            extra += camada("qr", "QR", qr_png, pos)
        xml = (f'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n<xmeml version="4"><sequence id="seq-1">'
               f"<name>{escape(nome)}</name><duration>{pos}</duration>{rate}<media><video><format>"
               f"<samplecharacteristics>{rate}<width>{W}</width><height>{H}</height>"
               f"<pixelaspectratio>square</pixelaspectratio></samplecharacteristics></format>"
               f"<track>{''.join(v1)}</track><track>{''.join(v2)}</track>{extra}</video>"
               f"<audio><track>{''.join(a1)}</track></audio></media></sequence></xmeml>\n")
        (out / f"{nome}.xml").write_text(xml, encoding="utf-8")

    linhas, t = ["ordem;arquivo;entra_em;sai_em;duracao;tarja_de;tarja_ate;tarja"], 0.0
    hms = lambda s: f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"
    for n, x in enumerate(itens, 1):
        d = x["info"]["dur"]
        a, b = TARJA_SEG
        linhas.append(f"{n};{x['clipe'].name};{hms(t)};{hms(t + d)};{hms(d)};"
                      + (f"{hms(t + a)};{hms(t + min(b, d))};{x['it']['tarja']}" if x["tarja"] else ";;"))
        t += d
    (out / "TEMPOS.csv").write_text("\n".join(linhas) + "\n", encoding="utf-8-sig")

    (out / "LEIA-ME.txt").write_text(f"""Pacote de edição: {nome}
Mantenha esta pasta inteira junta: o XML aponta para os arquivos de clipes/ e tarjas/.
Abriu em outro computador (Mac, Windows ou Linux)? O Premiere/DaVinci vai pedir para religar
a mídia: aponte para o primeiro arquivo de clipes/ e ele acha o resto.

Premiere Pro: Arquivo > Importar > {nome}.xml. Abre a sequência com os clipes em ordem (V1),
  as tarjas por cima (V2, do segundo {TARJA_SEG[0]} ao {TARJA_SEG[1]} de cada clipe), o countdown (V3,
  se houver), o QR (V4, se houver) e o áudio (A1). Cada camada pode ser desligada no olho da trilha.
  Legenda: Arquivo > Importar > {nome}.srt e arraste para a timeline.
DaVinci Resolve: File > Import > Timeline > {nome}.xml (mesmo XML do Premiere).
CapCut: o CapCut não importa projeto de outro programa, então a montagem é manual:
  arraste os arquivos de clipes/ na ordem dos números na trilha principal; as tarjas de tarjas/
  numa camada por cima (do segundo {TARJA_SEG[0]} ao {TARJA_SEG[1]} de cada clipe - os tempos estão em TEMPOS.csv);
  o countdown: camadas/countdown.mov (com transparência) ou, se o CapCut não mostrar o fundo
  transparente, camadas/countdown-chroma.mp4 com Recortar > Chroma key no verde; o QR: camadas/qr.png. Legenda: arquivos .srt de legendas/ (um por clipe) ou {nome}.srt (sequência toda).
Outro editor (Final Cut, iMovie...): mesma lógica do CapCut.

Os clipes são brutos: sem tarja, countdown ou QR, e sem o selo da live no canto superior direito. A legenda vem da legenda automática do
YouTube: revise nomes próprios e números antes de publicar.
""", encoding="utf-8")
    print(f"pronto: {out}")


if __name__ == "__main__":
    fm = set(sys.argv[2].split(",")) if len(sys.argv) > 2 else {"premiere", "capcut", "srt"}
    if fm - {"premiere", "capcut", "srt"}:
        sys.exit(f"formato desconhecido: {', '.join(fm - {'premiere', 'capcut', 'srt'})}")
    main(sys.argv[1], fm)
