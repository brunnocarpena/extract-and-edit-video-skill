"""Monta o vídeo final a partir de um roteiro JSON. Rodar DE DENTRO da pasta do projeto.

Uso: <python da skill> -I <pasta da skill>/scripts/montar.py roteiros/<nome>.json [--cru]
     --cru: versão bruta para editor - sem countdown, tarja e QR, e com o selo gravado no canto
     superior direito da fonte do YouTube apagado (delogo). Grava brutos/<nome>.mp4.

Roteiro (formato completo em references/roteiro.md):
{
  "saida": "finais/almoco-dia1.mp4",     # com "separados": true, é uma PASTA (um mp4 por corte)
  "perfil": "perfil.json",               # opcional; sem ele, perfis/mari.json da skill
  "countdown": "Voltamos em",            # opcional; null = sem relógio (cortes avulsos)
  "qr": {"url": "...", "legenda": "Ficha de interesse"},   # opcional
  "separados": false,                    # true = não junta; solta cada corte como arquivo
  "delogo": [1112, 4, 164, 152],         # opcional; caixa x,y,w,h (em 1280x720) apagada no --cru
  "itens": [{"id": "BX-3C2OX7FU", "ini": "53:01", "fim": "60:25", "tarja": "...", "rotulo": "...", "nome": "..."},
            {"arquivo": "novos/DEP-0001.mp4", "tarja": "...", "nome": "Aline"}]   # vídeo local (inteiro)
}
Vídeo vertical entra centralizado sobre um fundo desfocado dele mesmo.

Etapas: baixa cada trecho (cache em trechos/), mede a duração real, gera o countdown do total
e codifica cada trecho UMA vez já com tarja + fatia do countdown + QR; no fim junta sem recodificar.
"""
import json, os, re, shutil, subprocess, sys, time, unicodedata
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
RAIZ = Path.cwd()
PY = sys.executable
SOBRE = SKILL / "scripts/sobreposicoes.py"
TARJA_SEG = (2, 14)  # tarja aparece do segundo 2 ao 14 de cada trecho
DELOGO = (1112, 4, 164, 152)  # selo "COMU | RT"/StreamYard das lives da Mari, em 1280x720


def achar_ytdlp():
    exe = "yt-dlp.exe" if os.name == "nt" else "yt-dlp"  # no Windows o venv usa Scripts/, não bin/
    for c in (os.environ.get("YTDLP"), Path(PY).parent / exe,
              RAIZ / "tools/venv/bin" / exe, RAIZ / "tools/venv/Scripts" / exe):
        if c and Path(c).exists():
            return str(c)
    c = shutil.which("yt-dlp")
    if not c:
        sys.exit("yt-dlp não encontrado: rode scripts/preparar.py ou defina YTDLP=")
    return c


def encoder():
    """h264_videotoolbox (Mac) é ~5x mais rápido que libx264; no Windows/Linux, libx264."""
    enc = subprocess.run(["ffmpeg", "-hide_banner", "-encoders"], capture_output=True, text=True).stdout
    if "h264_videotoolbox" in enc:
        return ["-c:v", "h264_videotoolbox", "-b:v", "4500k", "-maxrate", "6M", "-bufsize", "9M"]
    return ["-c:v", "libx264", "-preset", "veryfast", "-crf", "21"]


def slug(t):
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:50]


def rodar(cmd):
    subprocess.run([str(c) for c in cmd], check=True)


def duracao(arq):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(arq)],
                         capture_output=True, text=True, check=True).stdout
    return float(out)


def validar(itens):
    for it in itens:
        if it.get("arquivo"):
            arq = (RAIZ / it["arquivo"]).resolve()
            if not arq.is_relative_to(RAIZ.resolve()) or not arq.is_file():
                sys.exit(f"arquivo local inválido ou fora da pasta do projeto: {it['arquivo']!r}")
        elif not re.fullmatch(r"[A-Za-z0-9_-]{11}", it.get("id", "")):
            sys.exit(f"id do YouTube inválido: {it.get('id')!r}")


def dimensoes(arq):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "csv=p=0", str(arq)], capture_output=True, text=True, check=True).stdout
    w, h = out.strip().split(",")[:2]
    return int(w), int(h)


def filtro_base(arq, delogo=None):
    """Leva qualquer fonte para 1280x720/30fps. Vertical: centralizado sobre fundo desfocado."""
    w, h = dimensoes(arq)
    if h > w:
        f = ("[0:v]split[fg0][bg0];[bg0]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
             "gblur=sigma=40,eq=brightness=-0.12[bg];[fg0]scale=-2:720[fg];[bg][fg]overlay=(W-w)/2:0")
    else:
        f = "[0:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2"
    if delogo:
        f += ",delogo=x={}:y={}:w={}:h={}".format(*delogo)
    return f + ",setsar=1,fps=30,format=yuv420p[v1]"


def baixar(item, ytdlp=None):
    if item.get("arquivo"):
        return RAIZ / item["arquivo"]
    ini, fim = item["ini"].replace(":", ""), item["fim"].replace(":", "")
    arq = RAIZ / "trechos" / f"{item['id']}_{ini}-{fim}.mp4"
    if not arq.exists():
        arq.parent.mkdir(exist_ok=True)
        ytdlp = ytdlp or achar_ytdlp()
        for tentativa in range(3):  # o YouTube falha de vez em quando sem motivo; tenta de novo
            try:
                rodar([ytdlp, "--quiet", "--no-warnings", "-f", "bv*[height<=720][vcodec^=avc1]+ba[ext=m4a]/b[height<=720]",
                       "--download-sections", f"*{item['ini']}-{item['fim']}", "--force-keyframes-at-cuts",
                       "--merge-output-format", "mp4", "-o", str(arq), f"https://www.youtube.com/watch?v={item['id']}"])
                break
            except subprocess.CalledProcessError:
                if tentativa == 2:
                    raise
                time.sleep(10)
    return arq


def main(roteiro_path, cru=False):
    r = json.loads(Path(roteiro_path).read_text(encoding="utf-8"))
    if cru:  # versão para editor: sem nenhuma camada nossa
        r = {**r, "countdown": None, "qr": None, "separados": False,
             "saida": str(Path("brutos") / (Path(r["saida"]).stem + ".mp4")),
             "itens": [{k: v for k, v in it.items() if k != "tarja"} for it in r["itens"]]}
    perfil_arq = Path(r["perfil"]) if r.get("perfil") else SKILL / "perfis/mari.json"
    perfil = json.loads(perfil_arq.read_text(encoding="utf-8"))
    sobre = [PY, "-I", SOBRE, "--perfil", perfil_arq]
    validar(r["itens"])
    nome = Path(r["saida"]).stem
    tmp = RAIZ / "montagem" / (nome + ("-cru" if cru else ""))
    tmp.mkdir(parents=True, exist_ok=True)

    ytdlp = achar_ytdlp() if any(not it.get("arquivo") for it in r["itens"]) else None
    arquivos = [baixar(it, ytdlp) for it in r["itens"]]
    durs = [duracao(a) for a in arquivos]
    total = int(round(sum(durs)))
    print(f"{len(arquivos)} trechos, {total // 60} min {total % 60} s")

    cd = None
    if r.get("countdown"):
        cd = tmp / "countdown"
        if not (cd / f"{total:06d}.png").exists():
            rodar(sobre + ["countdown", total, r["countdown"], cd])
    qr = None
    if r.get("qr"):
        qr = tmp / "qr.png"
        rodar(sobre + ["qr", r["qr"]["url"], r["qr"].get("legenda", "Ficha de interesse"), qr])

    venc = encoder()
    partes, desloc = [], 0.0
    for n, (it, arq, d) in enumerate(zip(r["itens"], arquivos, durs)):
        parte = tmp / f"{n:03d}.mp4"
        partes.append(parte)
        inicio_cd = int(desloc)
        desloc += d
        if parte.exists():
            continue
        entradas = ["-i", arq]
        dl = None
        if cru and not it.get("arquivo") and it.get("delogo", True):
            dl = it["delogo"] if isinstance(it.get("delogo"), list) else r.get("delogo", DELOGO)
        filtro = filtro_base(arq, dl)
        ultimo, k = "v1", 1
        if cd:
            entradas += ["-framerate", "1", "-start_number", inicio_cd, "-i", cd / "%06d.png"]
            filtro += f";[{k}:v]fps=30[cd];[{ultimo}][cd]overlay=(W-w)/2:24:eof_action=repeat[v{k + 1}]"
            ultimo, k = f"v{k + 1}", k + 1
        if it.get("tarja"):
            tj = tmp / f"tarja_{n:03d}.png"
            rodar(sobre + ["tarja", it.get("rotulo", perfil.get("rotulo_tarja", "Depoimento")), it["tarja"], tj])
            entradas += ["-loop", "1", "-i", tj]
            a, b = TARJA_SEG
            filtro += f";[{ultimo}][{k}:v]overlay=40:H-h-92:shortest=1:enable='between(t,{a},{b})'[t{k}]"
            ultimo, k = f"t{k}", k + 1
        if qr:
            entradas += ["-loop", "1", "-i", qr]
            filtro += f";[{ultimo}][{k}:v]overlay=W-w-32:H-h-92:shortest=1[q{k}]"
            ultimo, k = f"q{k}", k + 1
        fim_fade = max(d - 0.6, 0)
        filtro += (f";[{ultimo}]fade=t=in:d=0.5,fade=t=out:st={fim_fade:.2f}:d=0.6[vout]"
                   f";[0:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000,"
                   f"afade=t=in:d=0.5,afade=t=out:st={fim_fade:.2f}:d=0.6[aout]")
        rodar(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *entradas, "-filter_complex", filtro,
               "-map", "[vout]", "-map", "[aout]", "-t", f"{d:.3f}", *venc, "-r", "30",
               "-c:a", "aac", "-b:a", "160k", "-ac", "2", "-movflags", "+faststart", parte])
        print(f"  {n + 1}/{len(arquivos)} ok")

    saida = (RAIZ / r["saida"]).resolve()
    if not saida.is_relative_to(RAIZ.resolve()):
        sys.exit(f"saida fora da pasta do projeto: {r['saida']}")
    if r.get("separados"):
        saida.mkdir(parents=True, exist_ok=True)
        for n, (it, p) in enumerate(zip(r["itens"], partes), 1):
            rotulo = it.get("nome") or it.get("tarja") or it.get("id") or Path(it["arquivo"]).stem
            destino = saida / f"{n:02d}_{slug(rotulo)}_{it.get('ini', '0').replace(':', 'm')}s.mp4"
            shutil.copyfile(p, destino)
            print(f"pronto: {destino}")
        return

    lista = tmp / "lista.txt"
    # aspas simples no caminho quebrariam a lista do concat; escape do próprio ffmpeg
    lista.write_text("".join("file '" + p.as_posix().replace("'", "'\\''") + "'\n" for p in partes), encoding="utf-8")
    saida.parent.mkdir(parents=True, exist_ok=True)
    rodar(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", lista,
           "-c", "copy", "-movflags", "+faststart", saida])
    print(f"pronto: {saida} ({duracao(saida) / 60:.1f} min)")


if __name__ == "__main__":
    main(sys.argv[1], cru="--cru" in sys.argv[2:])
