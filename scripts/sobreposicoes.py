"""Gera as sobreposições em PNG (não depende de drawtext/libass no ffmpeg).

  [--perfil perfil.json] countdown <segundos> <rotulo> <pasta>   -> 1 PNG por segundo (000000.png = tempo cheio)
  [--perfil perfil.json] tarja <rotulo> <frase> <saida.png>       -> tarja inferior do depoimento
  [--perfil perfil.json] qr <url> <legenda> <saida.png>           -> QR com legenda, canto inferior direito

Perfil (JSON): {"fonte": "/caminho.ttc", "fonte_index_bold": 2, "fonte_index_normal": 0,
                "fundo": [45,23,58], "texto": [244,231,214], "destaque": [125,211,206]}
Sem perfil, usa o perfil da Mari (perfis/mari.json).
"""
import json, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PERFIL_PADRAO = Path(__file__).resolve().parent.parent / "perfis/mari.json"
P = {}


def carregar_perfil(caminho):
    global P
    P = json.loads(Path(caminho).read_text(encoding="utf-8"))
    for k in ("fundo", "texto", "destaque"):
        P[k] = tuple(P[k])


def fonte(tam, bold=True):
    idx = P.get("fonte_index_bold", 0) if bold else P.get("fonte_index_normal", 0)
    return ImageFont.truetype(P["fonte"], tam, index=idx)


def hms(s):
    h, m, s = s // 3600, s % 3600 // 60, s % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def countdown(total, rotulo, pasta):
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    f_rot, f_num = fonte(20), fonte(54)
    largura = 300 if total >= 3600 else 230
    for i in range(total + 1):
        img = Image.new("RGBA", (largura, 118), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((0, 0, largura - 1, 117), 18, fill=P["fundo"] + (225,), outline=P["destaque"] + (255,), width=2)
        d.text((largura / 2, 30), rotulo.upper(), font=f_rot, fill=P["destaque"], anchor="mm")
        d.text((largura / 2, 78), hms(total - i), font=f_num, fill=P["texto"], anchor="mm")
        img.save(pasta / f"{i:06d}.png")


def tarja(rotulo, frase, saida):
    """O nome do convidado já aparece no vídeo; a tarja traz só a transformação."""
    f_rot, f_frase = fonte(20), fonte(34)
    larg = int(max(f_rot.getlength(rotulo), f_frase.getlength(frase))) + 64
    img = Image.new("RGBA", (min(larg, 1180), 100), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, img.width - 1, 99), 14, fill=P["fundo"] + (230,))
    d.rectangle((0, 14, 7, 85), fill=P["destaque"])
    d.text((32, 30), rotulo.upper(), font=f_rot, fill=P["destaque"], anchor="lm")
    d.text((32, 66), frase, font=f_frase, fill=P["texto"], anchor="lm")
    img.save(saida)


def qr(url, legenda, saida):
    import segno
    tmp = Path(saida).with_suffix(".tmp.png")
    escuro = "#%02x%02x%02x" % P["fundo"]
    segno.make(url, error="m").save(tmp, scale=8, border=2, dark=escuro, light="#ffffff")
    code = Image.open(tmp).convert("RGBA")
    tmp.unlink()
    code = code.resize((220, 220), Image.NEAREST)
    img = Image.new("RGBA", (252, 290), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, 251, 289), 18, fill=P["texto"] + (245,))
    img.alpha_composite(code, (16, 16))
    d.text((126, 262), legenda, font=fonte(20), fill=P["fundo"], anchor="mm")
    img.save(saida)


if __name__ == "__main__":
    args = sys.argv[1:]
    perfil = PERFIL_PADRAO
    if args[:1] == ["--perfil"]:
        perfil, args = args[1], args[2:]
    carregar_perfil(perfil)
    cmd, *a = args
    if cmd == "countdown":
        countdown(int(a[0]), a[1], a[2])
    elif cmd == "tarja":
        tarja(a[0], a[1], a[2])
    elif cmd == "qr":
        qr(a[0], a[1], a[2])
