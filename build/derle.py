"""iskilavuzu.com statik site üreteci.

Kullanım:  python build/derle.py      -> dist/ klasörüne siteyi yazar

Girdi:
  data/site.json      site adı, alan adı, analitik kimlikleri
  data/alanlar.json   konu başlıkları (her biri bir hub sayfası olur)
  data/rehberler.json rehber içerikleri

Kural: uydurma veri yok. Bir rehberdeki her sayı, oran ve tarih
`kaynaklar` listesindeki bir kaynağa dayanır ve sayfanın altında görünür.
Kaynağı olmayan sayı yazılmaz.
"""
from __future__ import annotations

import html
import json
import re
import shutil
import sys
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

sys.stdout.reconfigure(encoding="utf-8")

KOK = Path(__file__).resolve().parent.parent
DATA = KOK / "data"
DIST = KOK / "dist"
TEMPLATES = KOK / "templates"
STATIC = KOK / "static"

TR_MAP = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
AYLAR = ["", "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
         "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


def slugify(metin: str) -> str:
    metin = metin.translate(TR_MAP)
    metin = unicodedata.normalize("NFKD", metin).encode("ascii", "ignore").decode()
    metin = re.sub(r"[^a-zA-Z0-9]+", "-", metin).strip("-").lower()
    return re.sub(r"-{2,}", "-", metin)


def oku(ad: str, varsayilan):
    yol = DATA / ad
    return json.loads(yol.read_text(encoding="utf-8")) if yol.exists() else varsayilan


def yaz(yol: Path, icerik: str) -> None:
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(icerik, encoding="utf-8")


def tarih_yaz(iso: str) -> str:
    try:
        g = date.fromisoformat(iso)
        return f"{g.day} {AYLAR[g.month]} {g.year}"
    except Exception:
        return iso


def duz_metin(rehber: dict) -> str:
    parcalar = [rehber.get("ozet", ""), rehber.get("cevap", "")]
    for b in rehber.get("bolumler", []):
        parcalar.append(b.get("metin", ""))
        parcalar += b.get("maddeler", [])
        for a in b.get("adimlar", []):
            parcalar += [a.get("baslik", ""), a.get("metin", "")]
        for satir in b.get("satirlar", []):
            parcalar += [str(h) for h in satir]
    for s in rehber.get("sss", []):
        parcalar += [s.get("s", ""), s.get("c", "")]
    return " ".join(p for p in parcalar if p)


def icindekiler(rehber: dict) -> list:
    """Rehberdeki h2 basliklarindan gezinme listesi."""
    cikti = []
    for b in rehber.get("bolumler", []):
        if b.get("tur") == "baslik":
            cikti.append({"ad": b["metin"], "id": slugify(b["metin"])})
    return cikti


def main() -> int:
    site = oku("site.json", {})
    alanlar = oku("alanlar.json", [])
    rehberler = oku("rehberler.json", [])

    alan_haritasi = {a["slug"]: a for a in alanlar}

    for r in rehberler:
        r.setdefault("slug", slugify(r["baslik"]))
        r["yol"] = f"/rehber/{r['slug']}/"
        r["kelime"] = len(duz_metin(r).split())
        r["okuma"] = max(1, round(r["kelime"] / 200))
        r["icindekiler"] = icindekiler(r)
        r["alan_adi"] = alan_haritasi.get(r.get("alan"), {}).get("ad", "")
        for b in r.get("bolumler", []):
            if b.get("tur") == "baslik":
                b["id"] = slugify(b["metin"])

    for a in alanlar:
        a["yol"] = f"/{a['slug']}/"
        a["rehberler"] = [r for r in rehberler if r.get("alan") == a["slug"]]

    # ilgili rehberler: once ayni alandan, sonra diger alanlardan
    for r in rehberler:
        ayni = [x for x in rehberler if x.get("alan") == r.get("alan") and x is not r]
        diger = [x for x in rehberler if x.get("alan") != r.get("alan")]
        r["ilgili"] = (ayni + diger)[:3]

    site["derleme_zamani"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    site["rehber_sayisi"] = len(rehberler)
    # Icerik yayimlanana kadar arama motorlarina kapali: ince sayfa indekslenmesin.
    site["noindex"] = not rehberler

    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["tarih"] = tarih_yaz

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    shutil.copytree(STATIC, DIST / "static")

    kok = site["alan_adi"].rstrip("/")
    ortak = {"site": site, "alanlar": alanlar, "rehberler": rehberler, "kok": kok}

    yaz(DIST / "index.html", env.get_template("home.html").render(**ortak))
    yaz(DIST / "404.html", env.get_template("404.html").render(**ortak))

    for a in alanlar:
        yaz(DIST / a["slug"] / "index.html",
            env.get_template("alan.html").render(alan=a, **ortak))

    for r in rehberler:
        yaz(DIST / "rehber" / r["slug"] / "index.html",
            env.get_template("rehber.html").render(
                rehber=r, alan=alan_haritasi.get(r.get("alan"), {}), **ortak))

    # site haritasi
    yollar = ["/"] + [a["yol"] for a in alanlar] + [r["yol"] for r in rehberler]
    girdiler = "\n".join(
        f"  <url><loc>{kok}{y}</loc></url>" for y in yollar)
    yaz(DIST / "sitemap.xml",
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{girdiler}\n</urlset>\n")

    yaz(DIST / "robots.txt",
        ("User-agent: *\nDisallow: /\n" if site["noindex"] else "User-agent: *\nAllow: /\n")
        + f"Sitemap: {kok}/sitemap.xml\n")

    # llms.txt: yapay zeka motorlarina sitenin haritasi
    satirlar = [f"# {site['ad']}", "", f"> {site['aciklama']}", ""]
    for a in alanlar:
        satirlar.append(f"## {a['ad']}")
        satirlar.append(a["aciklama"])
        for r in a["rehberler"]:
            satirlar.append(f"- [{r['baslik']}]({kok}{r['yol']}): {r['ozet']}")
        satirlar.append("")
    yaz(DIST / "llms.txt", "\n".join(satirlar))

    sayfa = len(list(DIST.rglob("*.html")))
    kelime = sum(r["kelime"] for r in rehberler)
    print(f"Derlendi: {sayfa} sayfa | {len(alanlar)} alan | {len(rehberler)} rehber | {kelime} kelime")
    print(f"Arama motoruna kapalı: {site['noindex']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
