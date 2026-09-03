"""iskilavuzu.com statik site üreteci.

Kullanım:  python build/derle.py      -> dist/ klasörüne siteyi yazar
Girdi:     data/site.json, data/alanlar.json, data/rehberler.json

Kural: uydurma veri yok. Bir rehberin her olgusu data/rehberler.json içinde
kaynağıyla birlikte durur; kaynağı olmayan cümle yazılmaz.
"""
from __future__ import annotations

import json
import re
import shutil
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

sys.stdout.reconfigure(encoding="utf-8")

KOK = Path(__file__).resolve().parent.parent
DATA = KOK / "data"
DIST = KOK / "dist"
TEMPLATES = KOK / "templates"
STATIC = KOK / "static"

TR_MAP = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")


def slugify(metin: str) -> str:
    metin = metin.translate(TR_MAP)
    metin = unicodedata.normalize("NFKD", metin).encode("ascii", "ignore").decode()
    metin = re.sub(r"[^a-zA-Z0-9]+", "-", metin).strip("-").lower()
    return re.sub(r"-{2,}", "-", metin)


def oku(ad: str, varsayilan):
    yol = DATA / ad
    if not yol.exists():
        return varsayilan
    return json.loads(yol.read_text(encoding="utf-8"))


def yaz(yol: Path, icerik: str) -> None:
    yol.parent.mkdir(parents=True, exist_ok=True)
    yol.write_text(icerik, encoding="utf-8")


def main() -> int:
    site = oku("site.json", {})
    alanlar = oku("alanlar.json", [])
    rehberler = oku("rehberler.json", [])

    for r in rehberler:
        r.setdefault("slug", slugify(r["baslik"]))

    # Her alana, o alana ait rehberleri bağla.
    for a in alanlar:
        a["rehberler"] = [r for r in rehberler if r.get("alan") == a["slug"]]

    site["derleme_zamani"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    site["rehber_sayisi"] = len(rehberler)
    # İçerik yayımlanana kadar arama motorlarına kapalı: ince sayfa indekslenmesin.
    site["noindex"] = bool(site.get("noindex", True)) and not rehberler

    env = Environment(
        loader=FileSystemLoader(TEMPLATES),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    shutil.copytree(STATIC, DIST / "static")

    ortak = {"site": site, "alanlar": alanlar, "rehberler": rehberler}

    yaz(DIST / "index.html", env.get_template("home.html").render(**ortak))
    yaz(DIST / "404.html", env.get_template("404.html").render(**ortak))

    for r in rehberler:
        yaz(
            DIST / "rehber" / r["slug"] / "index.html",
            env.get_template("rehber.html").render(rehber=r, **ortak),
        )

    kok = site["alan_adi"].rstrip("/")
    yollar = ["/"] + [f"/rehber/{r['slug']}/" for r in rehberler]
    girdiler = "\n".join(
        f"  <url><loc>{kok}{y}</loc></url>" for y in yollar
    )
    yaz(
        DIST / "sitemap.xml",
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{girdiler}\n</urlset>\n",
    )
    yaz(
        DIST / "robots.txt",
        ("User-agent: *\nDisallow: /\n" if site["noindex"] else "User-agent: *\nAllow: /\n")
        + f"Sitemap: {kok}/sitemap.xml\n",
    )

    sayfa = len(list(DIST.rglob("*.html")))
    print(f"Derlendi: {sayfa} sayfa, {len(rehberler)} rehber, {len(alanlar)} alan.")
    print(f"Arama motoruna kapalı: {site['noindex']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
