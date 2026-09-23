import os
import json
import re

CAT_BACK = {
    "lodowki.html": "Lodówki",
    "pralki.html": "Pralki",
    "zmywarki.html": "Zmywarki",
    "piekarniki.html": "Piekarniki",
    "male_agd.html": "Małe AGD",
    "kuchenki.html": "Kuchenki",
    "suszarki.html": "Suszarki",
    "zamrazarki.html": "Zamrażarki",
    "plyty_grzewcze.html": "Płyty grzewcze",
}

LIGHTBOX_CSS = """
        .lightbox {
            display: none; position: fixed; z-index: 9999;
            left: 0; top: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.9);
            align-items: center; justify-content: center; cursor: zoom-out;
        }
        .lightbox.active { display: flex; }
        .lightbox img {
            max-width: 95%; max-height: 95%; object-fit: contain;
            border-radius: 4px; box-shadow: 0 4px 30px rgba(0,0,0,0.5);
        }
        .lightbox-close {
            position: absolute; top: 20px; right: 30px;
            color: #fff; font-size: 2.5rem; font-weight: bold; cursor: pointer; line-height: 1;
        }
        .product-card-image img { cursor: zoom-in; transition: opacity 0.2s; }
        .product-card-image img:hover { opacity: 0.85; }
"""

LIGHTBOX_HTML = """
    <div class="lightbox" id="lightbox" onclick="closeLightbox()">
        <span class="lightbox-close">&times;</span>
        <img id="lightbox-img" src="" alt="Powiększone zdjęcie">
    </div>
    <script>
        function openLightbox(src) {
            document.getElementById('lightbox-img').src = src;
            document.getElementById('lightbox').classList.add('active');
            document.body.style.overflow = 'hidden';
        }
        function closeLightbox() {
            document.getElementById('lightbox').classList.remove('active');
            document.body.style.overflow = '';
        }
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') closeLightbox();
        });
    </script>
"""

def card_html(p):
    imgs = p.get("zdjecia", [])
    if not imgs and p.get("zdjecie"):
        imgs = [p["zdjecie"]]
    img_src = imgs[0] if imgs else ""
    img_block = ""
    if img_src:
        img_block = '''
                <div class="product-card-image">
                    <img src="%s" alt="%s" onclick="openLightbox(this.src)" onerror="this.style.display='none'">
                </div>''' % (img_src, p["tytul"])
    return '''
            <div class="product-card">
%s
                <h3>%s</h3>
                <p class="opis">%s</p>
                <span class="cena">%s</span>
            </div>
''' % (img_block, p["tytul"], p.get("opis", ""), p.get("cena", "Cena na zapytanie"))

if not os.path.exists("produkty.json"):
    print("Brak produkty.json")
    raise SystemExit(1)

with open("produkty.json", "r", encoding="utf-8") as f:
    baza = json.load(f)

for plik_html, produkty in baza.items():
    print("Przetwarzanie:", plik_html)
    produkty_html = "".join(card_html(p) for p in produkty)

    if not os.path.exists(plik_html):
        print("  ! Brak pliku", plik_html)
        continue
    content = open(plik_html, encoding="utf-8").read()
    start_m = "<!-- POCZATEK_PRODUKTOW -->"
    end_m = "<!-- KONIEC_PRODUKTOW -->"
    if start_m in content and end_m in content:
        before = content.split(start_m)[0]
        after = content.split(end_m)[1]
        content = before + start_m + "\n" + produkty_html + "\n" + end_m + after
        if "lightbox" not in content and "</style>" in content:
            content = content.replace("</style>", LIGHTBOX_CSS + "\n    </style>", 1)
        if 'id="lightbox"' not in content and "</body>" in content:
            content = content.replace("</body>", LIGHTBOX_HTML + "\n</body>", 1)
        with open(plik_html, "w", encoding="utf-8") as out:
            out.write(content)
        print("  OK,", len(produkty), "produktów")
    else:
        print("  ! Brak markerów")

print("Gotowe. (bez osobnych podstron produktów)")
