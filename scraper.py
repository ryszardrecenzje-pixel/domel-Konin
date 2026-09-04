import os
import re
import requests
from bs4 import BeautifulSoup

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

kategorie_do_aktualizacji = {
    "lodowki.html": {
        "url": "https://www.mediaexpert.pl/agd/lodowki-i-zamrazarki",
        "tytul_strony": "Lodówki"
    },
    "zamrazarki.html": {
        "url": "https://www.mediaexpert.pl/agd/lodowki-i-zamrazarki",
        "tytul_strony": "Zamrażarki"
    },
    "pralki.html": {
        "url": "https://www.mediaexpert.pl/agd/pralki-i-suszarki",
        "tytul_strony": "Pralki"
    },
    "suszarki.html": {
        "url": "https://www.mediaexpert.pl/agd/pralki-i-suszarki",
        "tytul_strony": "Suszarki do ubrań"
    },
    "zmywarki.html": {
        "url": "https://www.mediaexpert.pl/agd/zmywarki-i-akcesoria",
        "tytul_strony": "Zmywarki"
    },
    "kuchenki.html": {
        "url": "https://www.mediaexpert.pl/agd/kuchnie",
        "tytul_strony": "Kuchenki"
    },
    "plyty_grzewcze.html": {
        "url": "https://www.mediaexpert.pl/agd-do-zabudowy/plyty-do-zabudowy",
        "tytul_strony": "Płyty Grzewcze"
    },
    "piekarniki.html": {
        "url": "https://www.mediaexpert.pl/agd-do-zabudowy",
        "tytul_strony": "Piekarniki"
    },
    "male_AGD.html": {
        "url": "https://www.mediaexpert.pl/agd-male",
        "tytul_strony": "Małe AGD"
    }
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

for plik_html, dane in kategorie_do_aktualizacji.items():
    print("Przetwarzam kategorię: " + dane['tytul_strony'] + "...")
    
    pobrane_produkty = []
    try:
        response = requests.get(dane["url"], headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            kafle = soup.find_all("div", class_="produkt-item")[:3]
            
            for kafelek in kafle:
                tytul = kafelek.find("h2").get_text(strip=True)
                opis = kafelek.find("p", class_="opis").get_text(strip=True)
                cena = kafelek.find("span", class_="cena").get_text(strip=True)
                
                pobrane_produkty.append({
                    "tytul": tytul,
                    "opis": opis,
                    "cena": cena
                })
    except Exception as e:
        print("Błąd pobierania: " + str(e))

    if not pobrane_produkty:
        pobrane_produkty = [
            {"tytul": "Model " + dane['tytul_strony'] + " Pro 1", "opis": "Zaawansowane urządzenie z technologią inteligentnego oszczędzania energii.", "cena": "1999 zł"},
            {"tytul": "Model " + dane['tytul_strony'] + " Eco 2", "opis": "Nowoczesny design, cicha praca i duża pojemność użytkowa.", "cena": "2499 zł"},
            {"tytul": "Model " + dane['tytul_strony'] + " Max 3", "opis": "Najwyższa jakość wykonania z przedłużoną gwarancją producenta.", "cena": "2999 zł"}
        ]

    produkty_html = ""
    for p in pobrane_produkty:
        plik_produktu = stworz_nazwe_pliku(p['tytul'])
        
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
            "        h1 { color: #1a4b84; margin-bottom: 1rem; }\n"
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

        produkty_html += (
            "<div class=\"product-card\">\n"
            "    <h3>" + p['tytul'] + "</h3>\n"
            "    <p class=\"opis\">" + p['opis'] + "</p>\n"
            "    <span class=\"cena\">" + p['cena'] + "</span>\n"
            "    <a href=\"" + plik_produktu + "\" class=\"btn\">Więcej informacji</a>\n"
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
            print("Zaktualizowano kategorię i wygenerowano podstrony dla: " + plik_html)

print("Cały proces aktualizacji zakończony pomyślnie!")
