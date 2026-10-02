#!/usr/bin/env python3
"""Generuje promocje.html z promocje.json (zdjecia + lightbox, bez ujawniania marzy)."""
import json
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent
products = json.loads((ROOT / "promocje.json").read_text(encoding="utf-8"))

cards = []
for p in products:
    img = p.get("zdjecie") or "images/logo.png"
    big = p.get("zdjecie_duze") or img
    stara = p.get("cena_stara") or ""
    stara_html = f'<span class="cena-stara">{stara}</span> ' if stara else ""
    title = p.get("tytul") or ""
    opis = p.get("opis") or title
    cards.append(
        f"""
            <div class="product-card" data-title="{title.lower()}" data-keywords="{title.lower()} {(p.get('producent') or '').lower()}">
                <div class="availability"><span class="availability-dot dot-promo"></span> Promocja dnia</div>
                <div class="product-card-image">
                    <a href="{big}" class="zoom-link" data-full="{big}" data-caption="{title}" title="Kliknij aby powiekszyc">
                        <img src="{img}" alt="{title}" loading="lazy" onerror="this.onerror=null;this.src='images/logo.png';">
                    </a>
                </div>
                <h3>{title}</h3>
                <p class="opis">{opis}</p>
                <div class="cena-wrap">{stara_html}<span class="cena">{p.get('cena') or ''}</span></div>
            </div>"""
    )

upd = products[0].get("aktualizacja") if products else str(date.today())
cards_html = "".join(cards) if cards else '<p style="text-align:center">Brak promocji – uruchom skrypt B2B.</p>'

html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Domel Konin - Promocje dnia ({len(products)} szt.)</title>
    <link rel="stylesheet" href="style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .products-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.2rem; }}
        .product-card {{ background: #fff; border-radius: 8px; padding: 1.2rem; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; position: relative; }}
        .product-card-image {{ width: 100%; height: 200px; display: flex; align-items: center; justify-content: center; margin-bottom: 0.8rem; overflow: hidden; border-radius: 4px; background: #f5f5f5; }}
        .product-card-image img {{ max-width: 100%; max-height: 100%; object-fit: contain; cursor: zoom-in; transition: transform .2s; }}
        .product-card-image a:hover img {{ transform: scale(1.04); }}
        .product-card h3 {{ font-size: 0.98rem; line-height: 1.35; min-height: 2.7em; }}
        .opis {{ font-size: 0.88rem; color: #555; margin: 0.3rem 0 0.5rem; }}
        .legend {{ display: flex; gap: 20px; justify-content: center; margin-bottom: 1.5rem; flex-wrap: wrap; }}
        .legend-item {{ display: flex; align-items: center; gap: 6px; font-size: 0.95rem; }}
        .availability-dot.dot-promo {{ background: #e11d48; box-shadow: 0 0 0 2px rgba(225,29,72,0.25); }}
        .cena-stara {{ text-decoration: line-through; color: #999; font-size: 0.95rem; margin-right: 0.4rem; }}
        .cena-wrap {{ margin-top: 0.4rem; }}
        .promo-note {{ max-width: 720px; margin: 0 auto 1.5rem; text-align: center; color: #555; font-size: 0.95rem; }}
        /* lightbox */
        #lightbox {{ display: none; position: fixed; z-index: 9999; inset: 0; background: rgba(0,0,0,.85); align-items: center; justify-content: center; padding: 1rem; }}
        #lightbox.open {{ display: flex; }}
        #lightbox img {{ max-width: min(96vw, 1000px); max-height: 90vh; object-fit: contain; border-radius: 6px; box-shadow: 0 8px 40px rgba(0,0,0,.5); }}
        #lightbox .lb-close {{ position: absolute; top: 16px; right: 22px; color: #fff; font-size: 2rem; cursor: pointer; line-height: 1; }}
        #lightbox .lb-caption {{ position: absolute; bottom: 18px; left: 50%; transform: translateX(-50%); color: #fff; background: rgba(0,0,0,.55); padding: 0.4rem 0.9rem; border-radius: 6px; max-width: 90vw; text-align: center; font-size: 0.95rem; }}
    </style>
</head>
<body>
    <div id="top">
        <div class="container top-container">
            <div class="top-info">
                <a href="https://www.google.com/maps/place/Aleje+1+Maja+15,+62-510+Konin" target="_blank" class="top-link">
                    <i class="fa-solid fa-location-dot"></i> al. 1 Maja 15 | 62-510 Konin
                </a>
                <a href="tel:696085262" class="top-link phone-link"><i class="fa-solid fa-phone"></i> 696 085 262</a>
            </div>
            <div class="top-social">
                <a href="https://www.facebook.com/profile.php?id=61594405195116" target="_blank" title="Facebook"><i class="fa-brands fa-facebook-f"></i></a>
                <a href="https://www.instagram.com/outletdomel/" target="_blank" title="Instagram"><i class="fa-brands fa-instagram"></i></a>
            </div>
        </div>
    </div>
    <header id="border">
        <div class="container header-container">
            <div class="logo-wrapper">
                <a href="index.html">
                    <img src="images/logo.png" alt="Domel Konin Logo" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                    <div class="fallback-logo" style="display:none;"><span class="domel-text">DOMEL</span><span class="sub-text">KONIN</span></div>
                </a>
            </div>
            <nav id="menu">
                <ul>
                    <li><a href="index.html">STRONA GŁÓWNA</a></li>
                    <li><a href="sprzedaz.html">SPRZEDAŻ AGD</a></li>
                    <li><a href="magazyn.html">MAGAZYN</a></li>
                    <li><a href="promocje.html" style="color: #e11d48;">PROMOCJE DNIA</a></li>
                    <li><a href="index.html#contact">KONTAKT</a></li>
                </ul>
            </nav>
        </div>
    </header>
    <section class="section-padding">
        <div class="container">
            <h2 class="page-title">Promocje dnia</h2>
            <p class="section-desc">Aktualne promocje AGD. Kliknij zdjęcie, aby powiększyć.</p>
            <p class="promo-note">Aktualizacja: <strong>{upd}</strong> · Pozycji: <strong>{len(products)}</strong><br>
            Dostępność potwierdź telefonicznie: <a href="tel:696085262">696 085 262</a></p>
            <div class="legend">
                <div class="legend-item"><span class="availability-dot dot-promo"></span> Promocja dnia</div>
            </div>
            <div class="category-search">
                <input type="text" id="catSearchInput" placeholder="Szukaj promocji (marka, model)..." oninput="filterCatProducts()" autocomplete="off">
                <button onclick="filterCatProducts()"><i class="fa-solid fa-magnifying-glass"></i> Szukaj</button>
            </div>
            <div id="noResults" class="no-results">Brak pasujących promocji</div>
            <div class="products-grid" id="productGrid">
                {cards_html}
            </div>
        </div>
    </section>

    <div id="lightbox" onclick="closeLightbox(event)">
        <span class="lb-close" onclick="closeLightbox(event)">&times;</span>
        <img id="lightbox-img" src="" alt="">
        <div class="lb-caption" id="lightbox-caption"></div>
    </div>

    <script>
        function filterCatProducts() {{
            const val = document.getElementById('catSearchInput').value.toLowerCase().trim();
            const cards = document.querySelectorAll('.product-card');
            let visible = 0;
            cards.forEach(card => {{
                const title = (card.getAttribute('data-title') || '').toLowerCase();
                const keywords = (card.getAttribute('data-keywords') || '').toLowerCase();
                if (!val || title.includes(val) || keywords.includes(val)) {{
                    card.style.display = '';
                    visible++;
                }} else {{
                    card.style.display = 'none';
                }}
            }});
            const noRes = document.getElementById('noResults');
            if (noRes) noRes.style.display = (visible === 0 && val) ? 'block' : 'none';
        }}
        document.querySelectorAll('.zoom-link').forEach(a => {{
            a.addEventListener('click', function(e) {{
                e.preventDefault();
                const lb = document.getElementById('lightbox');
                document.getElementById('lightbox-img').src = this.getAttribute('data-full') || this.href;
                document.getElementById('lightbox-caption').textContent = this.getAttribute('data-caption') || '';
                lb.classList.add('open');
            }});
        }});
        function closeLightbox(e) {{
            if (e.target.id === 'lightbox' || e.target.classList.contains('lb-close')) {{
                document.getElementById('lightbox').classList.remove('open');
                document.getElementById('lightbox-img').src = '';
            }}
        }}
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape') document.getElementById('lightbox').classList.remove('open');
        }});
    </script>
    <footer>
        <div class="container footer-content">
            <p>&copy; 2026 DOMEL Konin - Sprzedaż i Serwis AGD. Wszelkie prawa zastrzeżone.</p>
        </div>
    </footer>
</body>
</html>
"""

(ROOT / "promocje.html").write_text(html, encoding="utf-8")
print(f"Zapisano promocje.html ({len(products)} pozycji)")
