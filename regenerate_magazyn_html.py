#!/usr/bin/env python3
"""Generuje magazyn.html na podstawie magazyn.json (po pobraniu zdjęć)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
with open(ROOT / "magazyn.json", encoding="utf-8") as f:
    products = json.load(f)

cards = []
for p in products:
    img = (p.get("zdjecia") or ["images/logo.png"])[0]
    cards.append(f'''
            <div class="product-card" data-title="{p['tytul'].lower()}" data-keywords="{p['tytul'].lower()} {p.get('kategoria','').lower()} {p.get('producent','').lower()}">
                <div class="availability"><span class="availability-dot dot-warehouse"></span> Dostępny na magazynie</div>
                <div class="product-card-image">
                    <img src="{img}" alt="{p['tytul']}" loading="lazy" onerror="this.onerror=null;this.src='images/logo.png';">
                </div>
                <h3>{p['tytul']}</h3>
                <p class="opis">{p.get('opis','')}</p>
                <span class="cena">{p.get('cena','')}</span>
            </div>''')

html = f'''<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Domel Konin - Produkty na magazynie ({len(products)} szt.)</title>
    <link rel="stylesheet" href="style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        .products-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1.2rem; }}
        .product-card {{ background: #fff; border-radius: 8px; padding: 1.2rem; box-shadow: 0 2px 5px rgba(0,0,0,0.1); text-align: center; position: relative; }}
        .product-card-image {{ width: 100%; height: 180px; display: flex; align-items: center; justify-content: center; margin-bottom: 0.8rem; overflow: hidden; border-radius: 4px; background: #f5f5f5; }}
        .product-card-image img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
        .legend {{ display: flex; gap: 20px; justify-content: center; margin-bottom: 1.5rem; flex-wrap: wrap; }}
        .legend-item {{ display: flex; align-items: center; gap: 6px; font-size: 0.95rem; }}
        .product-count {{ text-align: center; color: #666; margin-bottom: 1rem; }}
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
                    <li><a href="magazyn.html" style="color: #00b4ff;">MAGAZYN</a></li>
                    <li><a href="index.html#contact">KONTAKT</a></li>
                </ul>
            </nav>
        </div>
    </header>
    <section class="section-padding">
        <div class="container">
            <h2 class="page-title">Produkty dostępne na magazynie</h2>
            <p class="section-desc">Pełna lista unikalnych urządzeń dostępnych w magazynie. Złota kropka = dostępny na magazynie.</p>
            <div class="legend">
                <div class="legend-item"><span class="availability-dot dot-local"></span> Dostępny lokalnie (w salonie)</div>
                <div class="legend-item"><span class="availability-dot dot-warehouse"></span> Dostępny na magazynie</div>
            </div>
            <p class="product-count"><strong>{len(products)}</strong> unikalnych produktów</p>
            <div class="category-search">
                <input type="text" id="catSearchInput" placeholder="Szukaj produktu (marka, model, kategoria)..." oninput="filterCatProducts()" autocomplete="off">
                <button onclick="filterCatProducts()"><i class="fa-solid fa-magnifying-glass"></i> Szukaj</button>
            </div>
            <div id="noResults" class="no-results">Brak pasujących produktów</div>
            <div class="products-grid" id="productGrid">
                {"".join(cards)}
            </div>
        </div>
    </section>
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
            document.getElementById('noResults').style.display = visible === 0 ? 'block' : 'none';
        }}
    </script>
    <footer>
        <div class="container footer-content">
            <p>&copy; 2026 DOMEL Konin - Sprzedaż i Serwis AGD. Wszelkie prawa zastrzeżone.</p>
        </div>
    </footer>
</body>
</html>
'''

out = ROOT / "magazyn.html"
out.write_text(html, encoding="utf-8")
print(f"Zapisano {out} ({len(products)} produktów)")
