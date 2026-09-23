import os
import json
import re

def stworz_nazwe_pliku(nazwa):
    zamiany = {
        'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n', 'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
        'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N', 'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'
    }
    for pl, en in zamiany.items():
        nazwa = nazwa.replace(pl, en)
    nazwa = nazwa.lower()
    nazwa = re.sub(r'[^a-z0-9]+', '-', nazwa)
    nazwa = nazwa.strip('-')
    return nazwa + ".html"

CAT_BACK = {
    "lodowki.html": ("lodowki.html", "Lodówki"),
    "pralki.html": ("pralki.html", "Pralki"),
    "zmywarki.html": ("zmywarki.html", "Zmywarki"),
    "piekarniki.html": ("piekarniki.html", "Piekarniki"),
    "male_AGD.html": ("male_AGD.html", "Małe AGD"),
    "kuchenki.html": ("kuchenki.html", "Kuchenki"),
    "suszarki.html": ("suszarki.html", "Suszarki"),
    "zamrazarki.html": ("zamrazarki.html", "Zamrażarki"),
    "plyty_grzewcze.html": ("plyty_grzewcze.html", "Płyty grzewcze"),
}

def detail_html(p, back_href, back_label):
    imgs = p.get("zdjecia", [])
    if not imgs and p.get("zdjecie"):
        imgs = [p["zdjecie"]]
    galeria = ""
    for zdj in imgs:
        galeria += '            <img src="%s" alt="%s" class="product-detail-img">\n' % (zdj, p["tytul"])
    if not galeria:
        galeria = "            <p>Brak zdjęcia</p>\n"
    return """<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>%s - Domel Konin</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: Arial, sans-serif; }
        body { background-color: #f4f4f4; color: #333; line-height: 1.6; }
        .top-bar { background-color: #1a4b84; color: #fff; padding: 0.5rem 2rem; display: flex; justify-content: space-between; font-size: 0.9rem; }
        .top-bar a { color: #fff; text-decoration: none; }
        header { background-color: #fff; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #ddd; }
        .logo-img { max-height: 50px; display: block; }
        .container { max-width: 900px; margin: 2rem auto; padding: 2rem; background: #fff; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .images-container { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; justify-content: center; }
        .product-detail-img { width: calc(50%% - 0.5rem); max-height: 320px; object-fit: contain; border-radius: 8px; background: #f9f9f9; }
        @media (max-width: 600px) { .product-detail-img { width: 100%%; } }
        h1 { color: #1a4b84; margin-bottom: 1rem; }
        .price { font-size: 1.8rem; color: #d9534f; font-weight: bold; margin-bottom: 1.5rem; }
        .desc { font-size: 1.1rem; margin-bottom: 2rem; color: #555; }
        .info-box { background: #f9f9f9; padding: 1rem; border-left: 4px solid #1a4b84; margin-bottom: 2rem; }
        .btn { display: inline-block; background-color: #1a4b84; color: #fff; padding: 0.6rem 1.2rem; border-radius: 4px; text-decoration: none; font-weight: bold; }
        .btn:hover { background-color: #13355f; }
        .btn-back { background-color: #666; }
    </style>
</head>
<body>
    <div class="top-bar">
        <div>Tu jesteśmy: al. 1 Maja 15, Konin | 📞 63 242 17 99</div>
    </div>
    <header>
        <a href="index.html"><img src="images/logo.png" alt="Domel Konin" class="logo-img"></a>
        <a href="%s" class="btn btn-back">← Wróć do %s</a>
    </header>
    <div class="container">
        <div class="images-container">
%s        </div>
        <h1>%s</h1>
        <div class="price">%s</div>
        <div class="desc">
            <h3>Opis produktu:</h3>
            <p>%s</p>
        </div>
        <div class="info-box">
            <p><strong>Dostępność w salonie:</strong> Sprawdź dostępność w naszym sklepie stacjonarnym w Koninie.</p>
            <p>Masz pytania? Zadzwoń: <strong>63 242 17 99</strong> lub odwiedź nas osobiście!</p>
        </div>
        <a href="index.html#kontakt" class="btn">Zapytaj o ten produkt</a>
    </div>
</body>
</html>
""" % (p["tytul"], back_href, back_label, galeria, p["tytul"], p.get("cena", "Cena na zapytanie"), p.get("opis", ""))

def card_html(p, plik_produktu):
    imgs = p.get("zdjecia", [])
    if not imgs and p.get("zdjecie"):
        imgs = [p["zdjecie"]]
    img_src = imgs[0] if imgs else ""
    img_block = ""
    if img_src:
        img_block = '''
                <div class="product-card-image">
                    <img src="%s" alt="%s" onerror="this.style.display='none'">
                </div>''' % (img_src, p["tytul"])
    return '''
            <div class="product-card">
%s
                <h3>%s</h3>
                <p class="opis">%s</p>
                <span class="cena">%s</span>
                <a href="%s" class="btn">Więcej informacji</a>
            </div>
''' % (img_block, p["tytul"], p.get("opis", ""), p.get("cena", "Cena na zapytanie"), plik_produktu)

if not os.path.exists("produkty.json"):
    print("Brak produkty.json")
    raise SystemExit(1)

with open("produkty.json", "r", encoding="utf-8") as f:
    baza = json.load(f)

for plik_html, produkty in baza.items():
    print("Przetwarzanie kategorii:", plik_html)
    back_href, back_label = CAT_BACK.get(plik_html, (plik_html, "kategorii"))
    produkty_html = ""
    for p in produkty:
        plik_produktu = stworz_nazwe_pliku(p["tytul"])
        with open(plik_produktu, "w", encoding="utf-8") as out:
            out.write(detail_html(p, back_href, back_label))
        produkty_html += card_html(p, plik_produktu)
        print("  +", plik_produktu)

    if not os.path.exists(plik_html):
        print("  ! Brak pliku", plik_html)
        continue
    content = open(plik_html, encoding="utf-8").read()
    start_m = "<!-- POCZATEK_PRODUKTOW -->"
    end_m = "<!-- KONIEC_PRODUKTOW -->"
    if start_m in content and end_m in content:
        before = content.split(start_m)[0]
        after = content.split(end_m)[1]
        new_content = before + start_m + "\n" + produkty_html + "\n" + end_m + after
        with open(plik_html, "w", encoding="utf-8") as out:
            out.write(new_content)
        print("  Zaktualizowano", plik_html)
    else:
        print("  ! Brak markerów w", plik_html)

print("Gotowe.")
