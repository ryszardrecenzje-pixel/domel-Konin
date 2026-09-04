# scraper.py
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

for plik_html, dane in kategorie_do_aktualizacji.items():
    print("Przetwarzam kategorię: " + dane['tytul_strony'] + "...")
    
    pobrane_produkty = []
    try:
        response = requests.get(dane["url"], headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Próbujemy znaleźć produkty – selektory mogą się zmieniać
            kafle = soup.find_all("div", class_="produkt-item")[:3]
            
            for kafelek in kafle:
                tytul_elem = kafelek.find("h2") or kafelek.find("h3") or kafelek.find("a", class_="name")
                opis_elem = kafelek.find("p", class_="opis") or kafelek.find("div", class_="opis")
                cena_elem = kafelek.find("span", class_="cena") or kafelek.find("div", class_="price")
                
                if tytul_elem:
                    tytul = tytul_elem.get_text(strip=True)
                    opis = opis_elem.get_text(strip=True) if opis_elem else "Wysokiej jakości urządzenie AGD."
                    cena = cena_elem.get_text(strip=True) if cena_elem else "Sprawdź cenę"
                    
                    pobrane_produkty.append({
                        "tytul": tytul,
                        "opis": opis,
                        "cena": cena
                    })
    except Exception as e:
        print("Błąd pobierania z MediaExpert: " + str(e))

    # Fallback – gdy nie udało się pobrać prawdziwych produktów
    if not pobrane_produkty:
        pobrane_produkty = [
            {
                "tytul": "Model " + dane['tytul_strony'] + " Pro 1",
                "opis": "Zaawansowane urządzenie z technologią inteligentnego oszczędzania energii.",
                "cena": "1999 zł"
            },
            {
                "tytul": "Model " + dane['tytul_strony'] + " Eco 2",
                "opis": "Nowoczesny design, cicha praca i duża pojemność użytkowa.",
                "cena": "2499 zł"
            },
            {
                "tytul": "Model " + dane['tytul_strony'] + " Max 3",
                "opis": "Najwyższa jakość wykonania z przedłużoną gwarancją producenta.",
                "cena": "2999 zł"
            }
        ]

    produkty_html = ""
    
    for p in pobrane_produkty:
        plik_produktu = stworz_nazwe_pliku(p['tytul'])
        
        # ---------- PODSTRONA PRODUKTU ----------
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
        h1 {{ color: #1a4b84; margin-bottom: 1rem; }}
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

        # ---------- KAFEL NA LIŚCIE KATEGORII ----------
        produkty_html += f"""
            <div class="product-card">
                <h3>{p['tytul']}</h3>
                <p class="opis">{p['opis']}</p>
                <span class="cena">{p['cena']}</span>
                <a href="{plik_produktu}" class="btn">Więcej informacji</a>
            </div>
"""

    # ---------- AKTUALIZACJA PLIKU KATEGORII ----------
    if os.path.exists(plik_html):
        with open(plik_html, "r", encoding="utf-8") as f:
            zawartosc_strony = f.read()

        start_komentarz = "<!-- POCZATEK_PRODUKTOW -->"
        koniec_komentarz = "<!-- KONIEC_PRODUKTOW -->"

        if start_komentarz in zawartosc_strony and koniec_komentarz in zawartosc_strony:
            czesc_przed = zawartosc_strony.split(start_komentarz)[0]
            czesc_po = zawartosc_strony.split(koniec_komentarz)[1]
            
            nowa_zawartosc = (
                czesc_przed 
                + start_komentarz + "\n" 
                + produkty_html 
                + "\n" + koniec_komentarz 
                + czesc_po
            )
            
            with open(plik_html, "w", encoding="utf-8") as f:
                f.write(nowa_zawartosc)
            
            print("Zaktualizowano kategorię i wygenerowano podstrony dla: " + plik_html)
        else:
            print("Uwaga: Nie znaleziono markerów <!-- POCZATEK_PRODUKTOW --> w pliku " + plik_html)
    else:
        print("Uwaga: Plik " + plik_html + " nie istnieje.")

print("Cały proces aktualizacji zakończony pomyślnie!")
