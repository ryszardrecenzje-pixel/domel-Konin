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
            galeria_html += f"<img src=\"{zdj}\" alt=\"{p['tytul']}\" class=\"product-detail-img\">\n"

        szablon_podstrony = (
            "<!DOCTYPE html>\n"
            "<html lang=\"pl\">\n"
            "<head>\n"
            "    <meta charset=\"UTF-8\">\n"
            "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
            "    <title>" + p['tytul'] + " - Domel Konin</title>\n"
            "    <style>\n"
            "        * { box-sizing: border-box; margin: 0; padding: 0; font-family: Arial, sans-serif; }\n"
            "        body { background-color: #f4f4f4; color: #333; line-height: 1.6; }\n"
            "        .top-bar { background-color: #1a4b84; color: #fff; padding: 0.5rem 2rem; display: flex; justify-content: space-between; font-size: 0.9rem; }\n"
            "        .top-bar a { color: #fff; text-decoration: none; }\n"
            "        header { background-color: #fff; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #ddd; }\n"
            "        .logo-img { max-height: 50px; display: block; }\n"
            "        .container { max-width: 900px; margin: 2rem auto; padding: 2rem; background: #fff; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }\n"
            "        .images-container { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; justify-content: center; }\n"
            "        .product-detail-img { width: calc(50% - 0.5rem); max-height: 280px; object-fit: contain; border-radius: 6px; background: #fafafa; border: 1px solid #eee; padding: 5px; }\n"
            "        h1 { color: #1a4b84; margin-bottom: 1rem; font-size: 1.8rem; }\n"
            "        .price { font-size: 1.8rem; color: #d9534f; font-weight: bold; margin-bottom: 1.5rem; }\n"
            "        .desc { font-size: 1.1rem; margin-bottom: 2rem; color: #555; }\n"
            "        .info-box { background: #f9f9f9; padding: 1rem; border-left: 4px solid #1a4b84; margin-bottom: 2rem; }\n"
            "        .btn { display: inline-block; background-color: #1a4b84; color: #fff; padding: 0.6rem 1.2rem; border-radius: 4px; text-decoration: none; font-weight: bold; }\n"
            "        .btn:hover { background-color: #13355f; }\n"
            "    </style>\n"
            "</head>\n"
            "<body>\n"
            "    <div class=\"top-bar\">\n"
            "        <div>Tu jesteśmy: al. 1 Maja 15, Konin | 📞 63 242 17 99</div>\n"
            "    </div>\n"
            "    <header>\n"
            "        <a href=\"index.html\"><img src=\"images/logo.png\" alt=\"Domel Konin\" class=\"logo-img\"></a>\n"
            "        <a href=\"" + plik_html + "\" class=\"btn\" style=\"background-color: #666;\">← Wróć do kategorii</a>\n"
            "    </header>\n"
            "    <div class=\"container\">\n"
            "        <div class=\"images-container\">\n"
            "            " + galeria_html + "\n"
            "        </div>\n"
            "        <h1>" + p['tytul'] + "</h1>\n"
            "        <div class=\"price\">Cena: " + p['cena'] + "</div>\n"
            "        <div class=\"desc\">\n"
            "            <h3>Opis produktu:</h3>\n"
            "            <p>" + p['opis'] + "</p>\n"
            "        </div>\n"
            "        <div class=\"info-box\">\n"
            "            <p><strong>Dostępność w salonie:</strong> Dostępne od ręki w naszym sklepie stacjonarnym w Koninie.</p>\n"
            "            <p>Masz pytania? Zadzwoń do nas lub odwiedź nas osobiście!</p>\n"
            "        </div>\n"
            "        <a href=\"index.html#kontakt\" class=\"btn\">Zapytaj o ten produkt</a>\n"
            "    </div>\n"
            "</body>\n"
            "</html>"
        )

        with open(plik_produktu, "w", encoding="utf-8") as f_prod:
            f_prod.write(szablon_podstrony)

        # Kafelek kategorii używa pierwszego zdjęcia jako miniatury
        produkty_html += (
            "<div class=\"product-card\" style=\"display: flex; flex-direction: column; justify-content: space-between;\">\n"
            "    <div>\n"
            "        <img src=\"" + glowne_zdjecie + "\" alt=\"" + p['tytul'] + "\" style=\"width: 100%; height: 180px; object-fit: contain; margin-bottom: 1rem; border-radius: 4px;\">\n"
            "        <h3>" + p['tytul'] + "</h3>\n"
            "        <p class=\"opis\">" + p['opis'] + "</p>\n"
            "    </div>\n"
            "    <div>\n"
            "        <span class=\"cena\" style=\"display: block; font-size: 1.3rem; font-weight: bold; color: #d9534f; margin: 0.8rem 0;\">" + p['cena'] + "</span>\n"
            "        <a href=\"" + plik_produktu + "\" class=\"btn\">Sprawdź szczegóły</a>\n"
            "    </div>\n"
            "</div>\n"
        )

    if os.path.exists(plik_html):
        with open(plik_html, "r", encoding="utf-8") as f:
            zawartosc_strony = f.read()

        start_komentarz = "<!-- POCZATEK_PRODUKTOW -->"
        koniec_komentarz = "<!-- KONIEC_PRODUKTOW -->"

        if start_komentarz in zawartosc_strony and koniec_komentarz in zawartosc_strony:
            czesc_przed = zawartosc_strony.split(start_komentarz)[0]
            czesc_po = zawartosc_strony.split(koniec_komentarz)[1]
            
            nowa_zawartosc = czesc_przed + start_komentarz + "\n" + produkty_html + "\n" + czesc_po + koniec_komentarz
            
            with open(plik_html, "w", encoding="utf-8") as f:
                f.write(nowa_zawartosc)
            print("Zaktualizowano plik kategorii: " + plik_html)

print("Aktualizacja zakończona sukcesem!")
