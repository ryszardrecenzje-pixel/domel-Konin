import os
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

# Baza konkretnych modeli AGD z prawdziwymi zdjęciami i opisami
baza_produktow = {
    "lodowki.html": {
        "tytul_strony": "Lodówki",
        "produkty": [
            {
                "tytul": "Lodówka WHIRLPOOL WHK26363XBR5E No frost",
                "opis": "Pojemność 316 l, pełny Dual NoFrost, cicha praca 35 dB, kompresor inwerterowy.",
                "cena": "2 099,99 zł",
                "zdjecie": "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?auto=format&fit=crop&w=500&q=80"
            },
            {
                "tytul": "Lodówka SAMSUNG Brrr Inverter NoFrost",
                "opis": "Technologia SpaceMax, szuflada Chef Zone, elegancki panel wykończenia inox.",
                "cena": "2 499,00 zł",
                "zdjecie": "https://images.unsplash.com/photo-1571175336579-bc4a54c44d5a?auto=format&fit=crop&w=500&q=80"
            },
            {
                "tytul": "Lodówka BOSCH EcoFresh Duo",
                "opis": "System VitaFresh utrzymuje świeżość produktów do dwóch razy dłużej.",
                "cena": "2 899,00 zł",
                "zdjecie": "https://images.unsplash.com/photo-1536353284636-d245963493e8?auto=format&fit=crop&w=500&q=80"
            }
        ]
    },
    "pralki.html": {
        "tytul_strony": "Pralki",
        "produkty": [
            {
                "tytul": "Pralka BOSCH Serie 6 WGG2440SPL",
                "opis": "Pojemność 9 kg, 1400 obr/min, silnik EcoSilence Drive z 10-letnią gwarancją.",
                "cena": "2 199,00 zł",
                "zdjecie": "https://images.unsplash.com/photo-1626806787461-102c1bfaaea1?auto=format&fit=crop&w=500&q=80"
            },
            {
                "tytul": "Pralka SAMSUNG WW90T534DAE AI Control",
                "opis": "Technologia EcoBubble - pranie w niskich temperaturach, sterowanie smartfonem.",
                "cena": "2 399,00 zł",
                "zdjecie": "https://images.unsplash.com/photo-1517646287270-a5a9ca602e5c?auto=format&fit=crop&w=500&q=80"
            },
            {
                "tytul": "Pralka BEKO SteamCure Slim",
                "opis": "Głębokość tylko 45 cm, funkcja parowa usuwająca zagniecenia i alergeny.",
                "cena": "1 699,00 zł",
                "zdjecie": "https://images.unsplash.com/photo-1582735689369-4fe89db7114c?auto=format&fit=crop&w=500&q=80"
            }
        ]
    },
    "zmywarki.html": {
        "tytul_strony": "Zmywarki",
        "produkty": [
            {
                "tytul": "Zmywarka BOSCH SMV4HVX31E Do zabudowy",
                "opis": "Szerokość 60 cm, Home Connect, Extra Dry - dokładne suszenie trudnych naczyń.",
                "cena": "2 299,00 zł",
                "zdjecie": "https://images.unsplash.com/photo-1585670149060-873d6d56d22a?auto=format&fit=crop&w=500&q=80"
            },
            {
                "tytul": "Zmywarka BEKO DIN28435",
                "opis": "Technologia CornerIntense dla idealnego dotarcia wody w każdy kąt komory.",
                "cena": "1 899,00 zł",
                "zdjecie": "https://images.unsplash.com/photo-1581622558663-b2e33377dfb2?auto=format&fit=crop&w=500&q=80"
            },
            {
                "tytul": "Zmywarka WHIRLPOOL WSIC 3M17 C",
                "opis": "Szerokość 45 cm, technologia 6. Zmysł automatycznie dobiera parametry zmywania.",
                "cena": "1 599,00 zł",
                "zdjecie": "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=500&q=80"
            }
        ]
    }
}

for plik_html, dane in baza_produktow.items():
    print("Generowanie kategorii: " + dane['tytul_strony'] + "...")
    pobrane_produkty = dane['produkty']

    produkty_html = ""
    for p in pobrane_produkty:
        plik_produktu = stworz_nazwe_pliku(p['tytul'])
        
        # Szablon podstrony szczegółów produktu
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
            "        .product-detail-img { width: 100%; max-height: 350px; object-fit: contain; margin-bottom: 1.5rem; border-radius: 6px; }\n"
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
            "        <img src=\"" + p['zdjecie'] + "\" alt=\"" + p['tytul'] + "\" class=\"product-detail-img\">\n"
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

        # Kafel na stronie kategorii ze zdjęciem
        produkty_html += (
            "<div class=\"product-card\" style=\"display: flex; flex-direction: column; justify-content: space-between;\">\n"
            "    <div>\n"
            "        <img src=\"" + p['zdjecie'] + "\" alt=\"" + p['tytul'] + "\" style=\"width: 100%; height: 180px; object-fit: contain; margin-bottom: 1rem; border-radius: 4px;\">\n"
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
            print("Zaktualizowano plik: " + plik_html)

print("Wszystko gotowe i zaktualizowane!")
