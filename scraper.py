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

if os.path.exists("produkty.json"):
    with open("produkty.json", "r", encoding="utf-8") as f:
        baza_produktow = json.load(f)
else:
    baza_produktow = {}

for plik_html, produkty in baza_produktow.items():
    print("Przetwarzanie kategorii: " + plik_html)
    produkty_html = ""
    for p in produkty:
        plik_produktu = stworz_nazwe_pliku(p['tytul'])
        
        # Pobieramy zdjęcia z listy (zabezpieczenie, gdyby ktoś podał jedno lub zero)
        lista_zdjec = p.get('zdjecia', [])
        glowne_zdjecie = lista_zdjec[0] if len(lista_zdjec) > 0 else ""
        
        # Generowanie HTML dla dodatkowych zdjęć na podstronie szczegółowej
        galeria_html = ""
        for zdj in lista_zdjec:
            galeria_html += f'<img src="{zdj}" alt="{p["tytul"]}" class="product-detail-img">\n'
        
        szablon_podstrony = f"""<!DOCTYPE html>
<html lang="pl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{p['tytul']} - Domel Konin</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: Arial, sans-serif; }}
        body {{ background-color: #f4f4f4; color: #333; line-height: 1.6; }}
        .top-bar {{ background-color: #1a4b84; color: #fff; padding: 0.5rem 2rem; display: flex; justify-content: space-between; font-size: 0.9rem; }}
        .top-bar a {{ color: #fff; text-decoration: none; }}
        header {{ background-color: #fff; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #ddd; }}
        .logo-img {{ max-height: 50px; display: block; }}
        .container {{ max-width: 900px; margin: 2rem auto; padding: 2rem; background: #fff; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .images-container {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; justify-content: center; }}
        .product-detail-img {{ width: calc(50% - 0.5rem); max-height: 280px; object-fit: contain; border-radius: 6px; background: #fafafa; border: 1px solid #eee; padding: 5px; }}
        h1 {{ color: #1a4b84; margin-bottom: 1rem; font-size: 1.8rem; }}
        .price {{ font-size: 1.8rem; color: #d9534f; font-weight: bold; margin-bottom: 1.5rem; }}
        .desc {{ font-size: 1.1rem; margin-bottom: 2rem; color: #555; }}
        .info-box {{ background: #f9f9f9; padding: 1rem; border-left: 4px solid #1a4b84; margin-bottom: 2rem; }}
        .btn {{ display: inline-block; background-color: #1a4b84; color: #fff; padding: 0.6rem 1.2rem; border-radius: 4px; text-decoration: none; font-weight: bold; }}
        .btn:hover {{ background-color: #13355f; }}
    </style>
</head>
<body>
    <div class="top-bar">
        <div>Tu jesteśmy: al. 1 Maja 15, Konin | 📞 63 242 17 99</div>
    </div>
    <header>
        <a href="index.html"><img src="images/logo.png" alt="Domel Konin" class="logo-img"></a>
        <a href="{plik_html}" class="btn" style="background-color: #666;">← Wróć do kategorii</a>
    </header>
    <div class="container">
        <div class="images-container">
            {galeria_html}
        </div>
        <h1>{p['tytul']}</h1>
        <div class="price">Cena: {p['cena']}</div>
        <div class="desc">
            <h3>Opis produktu:</h3>
            <p>{p['opis']}</p>
        </div>
        <div class="info-box">
            <p><strong>Dostępność w salonie:</strong> Dostępne od ręki w naszym sklepie stacjonarnym w Koninie.</p>
            <p>Masz pytania? Zadzwoń do nas lub odwiedź nas osobiście!</p>
        </div>
        <a href="index.html#kontakt" class="btn">Zapytaj o ten produkt</a>
    </div>
</body>
</html>"""
        
        with open(plik_produktu, "w", encoding="utf-8") as f_prod:
            f_prod.write(szablon_podstrony)
        
        # Kafelek kategorii używa pierwszego zdjęcia jako miniatury
        produkty_html += f"""
            <div class="product-card" style="display: flex; flex-direction: column; justify-content: space-between;">
                <div>
                    <img src="{glowne_zdjecie}" alt="{p['tytul']}" style="width: 100%; height: 180px; object-fit: contain; margin-bottom: 1rem; border-radius: 4px;">
                    <h3>{p['tytul']}</h3>
                    <p class="opis">{p['opis']}</p>
                </div>
                <div>
                    <span class="cena" style="display: block; font-size: 1.3rem; font-weight: bold; color: #d9534f; margin: 0.8rem 0;">{p['cena']}</span>
                    <a href="{plik_produktu}" class="btn">Sprawdź szczegóły</a>
                </div>
            </div>
"""
    
    if os.path.exists(plik_html):
        with open(plik_html, "r", encoding="utf-8") as f:
            zawartosc_strony = f.read()
        start_komentarz = "<!-- POCZATEK_PRODUKTOW -->"
        koniec_komentarz = "<!-- KONIEC_PRODUKTOW -->"
        if start_komentarz in zawartosc_strony and koniec_komentarz in zawartosc_strony:
            czesc_przed = zawartosc_strony.split(start_komentarz)[0]
            czesc_po = zawartosc_strony.split(koniec_komentarz)[1]
            
            nowa_zawartosc = czesc_przed + start_komentarz + "\n" + produkty_html + "\n" + koniec_komentarz + czesc_po
            
            with open(plik_html, "w", encoding="utf-8") as f:
                f.write(nowa_zawartosc)
            print("Zaktualizowano plik kategorii: " + plik_html)

print("Aktualizacja zakończona sukcesem!")