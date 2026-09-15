"""Paylasim karti (og:image, 1200x630): python build/og_gorsel.py -> static/og.png
Site renkleri + ad + slogan; yazi tipi fontlar/Archivo (degisken, wght=700)."""
from pathlib import Path
import json

from PIL import Image, ImageDraw, ImageFont

KOK = Path(__file__).resolve().parent.parent
site = json.loads((KOK / "data" / "site.json").read_text("utf-8"))
KAGIT, MUREKKEP, VURGU, SOLUK = "#F5F8F6", "#101A19", "#0E5A5E", "#5D6F6C"


def yazi(boyut: int, agirlik: float) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(str(KOK / "fontlar" / "Archivo[wdth,wght].ttf"), boyut)
    try:
        f.set_variation_by_axes([100, agirlik])
    except Exception:
        pass
    return f


im = Image.new("RGB", (1200, 630), KAGIT)
d = ImageDraw.Draw(im)
d.rectangle([0, 0, 1200, 14], fill=VURGU)
d.rounded_rectangle([80, 90, 168, 178], radius=22, fill=VURGU)
d.text((124, 134), "İK", font=yazi(44, 700), fill="#FFFFFF", anchor="mm")
d.text((196, 134), site["ad"], font=yazi(58, 700), fill=MUREKKEP, anchor="lm")
d.text((80, 300), site.get("slogan", ""), font=yazi(64, 700), fill=MUREKKEP, anchor="lm")
aciklama = site.get("aciklama", "")
satirlar, satir = [], ""
for kelime in aciklama.split():
    if d.textlength(satir + " " + kelime, font=yazi(30, 500)) > 1040:
        satirlar.append(satir.strip()); satir = kelime
    else:
        satir += " " + kelime
satirlar.append(satir.strip())
y = 380
for s in satirlar[:3]:
    d.text((80, y), s, font=yazi(30, 500), fill=SOLUK)
    y += 44
d.text((80, 560), "iskilavuzu.com", font=yazi(30, 700), fill=VURGU)
(KOK / "static" / "og.png").parent.mkdir(exist_ok=True)
im.save(KOK / "static" / "og.png", optimize=True)
print("static/og.png", im.size)
