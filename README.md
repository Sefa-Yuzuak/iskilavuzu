# iskilavuzu.com

İş kurma, evden çalışma, ek gelir, part-time iş, yasal mevzuat, yurtdışından ürün getirme,
3D baskı işi ve kamuda işe girme konularında Türkçe rehberler. Statik site.

## Çalıştırma

```
pip install jinja2
python build/derle.py          # dist/ klasörüne siteyi üretir
```

Yerelde bakmak için:

```
python -m http.server 8000 --directory dist
```

## Yapı

| Yol | Ne işe yarar |
|---|---|
| `build/derle.py` | Statik üreteç. Tek giriş noktası. |
| `data/site.json` | Site adı, alan adı, GA4 ve Search Console kimlikleri. |
| `data/alanlar.json` | On konu başlığı. Ana sayfadaki kartları besler. |
| `data/rehberler.json` | Rehber içerikleri. Boş olduğu sürece site arama motorlarına kapalı kalır. |
| `templates/` | Jinja2 şablonları. |
| `static/` | CSS, logo, favicon. Olduğu gibi `dist/static/` altına kopyalanır. |
| `nginx.conf` | Yayın sunucusu ayarları. |
| `Dockerfile` | İki aşamalı: Python ile derler, nginx ile yayınlar. |

## İçerik kuralı

Uydurma veri yok. Bir maliyet, ücret, oran veya tarih yazılıyorsa kaynağı
`rehberler.json` içindeki `kaynaklar` listesinde durur ve sayfanın altında görünür.
Bilinmeyen bir sayı tahminle doldurulmaz, boş bırakılır.

## Arama motoruna kapalılık

`data/rehberler.json` boşken üreteç `robots.txt` dosyasını `Disallow: /` olarak yazar
ve her sayfaya `noindex` etiketi koyar. İlk gerçek rehber eklendiğinde bu kendiliğinden
kalkar. Amaç, içeriksiz bir sitenin Google'da ince içerik olarak kaydedilmemesi.

## Yayın

Coolify (`coolify.polyazilim.com`), sunucu `70.40.138.238`.
`main` dalına push, `.github/workflows/deploy.yml` üzerinden Coolify deploy API'sini
`force=true` ile çağırır. Gerekli secret'lar: `COOLIFY_DEPLOY_URL`, `COOLIFY_TOKEN`.

Deploy'un gerçekten indiğini doğrulamak için her sayfanın sonundaki derleme damgasına bak:

```
curl -s https://iskilavuzu.com/ | grep derleme
```

## Alan adı

`iskilavuzu.com` — Atak Domain üzerinden kayıtlı, ad sunucuları Güzel Hosting'de.
Kök A kaydı `70.40.138.238`, `www` kök alan adına CNAME.
AAAA kaydı **bilerek yok**: eski IPv6 adresi Let's Encrypt doğrulamasını yanlış sunucuya
yönlendirip sertifika alınmasını engelliyordu.
