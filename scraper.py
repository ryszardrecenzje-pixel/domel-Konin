import os
import requests
from bs4 import BeautifulSoup

# Słownik definiujący kategorie oraz linki źródłowe (podmień linki na realne strony ze źródłami)
kategorie_do_aktualizacji = {
    "lodowki.html": {
        "url": "https://example.com/kategoria/lodowki",
        "tytul_strony": "Lodówki"
    },
    "zamrazarki.html": {
        "url": "https://example.com/kategoria/zamrazarki",
        "tytul_strony": "Zamrażarki"
    },
    "pralki.html": {
        "url": "https://example.com/kategoria/pralki",
        "tytul_strony": "Pralki"
    },
    "suszarki.html": {
        "url": "https://example.com/kategoria/suszarki",
        "tytul_strony": "Suszarki do ubrań"
    },
    "zmywarki.html": {
        "url": "https://example.com/kategoria/zmywarki",
        "tytul_strony": "Zmywarki"
    },
    "kuchenki.html": {
        "url": "https://example.com/kategoria/kuchenki",
        "tytul_strony": "Kuchenki"
    },
    "plyty_grzewcze.html": {
        "url": "https://example.com/kategoria/plyty-grzewcze",
        "tytul_strony": "Płyty Grzewcze"
    },
    "piekarniki.html": {
        "url": "https://example.com/kategoria/piekarniki",
        "tytul_strony": "Piekarniki"
    },
    "male_AGD.html": {
        "url": "https://example.com/kategoria/male-agd",
        "tytul_strony": "Małe AGD"
    }
}

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Pętla aktualizująca każdą kategorię po kolei
for plik_html, dane in kategorie_do_aktualizacji.items():
    print(f"Aktualizuję kategorię: {dane['tytul_strony']} ({plik_html})...")
    
    # Próba pobrania danych ze źródła
    pobrane_produkty = []
    try:
        response = requests.get(dane["url"], headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            
            # W tym miejscu dopasowujesz selektory do struktury strony źródłowej
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
        print(f"Błąd podczas pobierania {plik_html}: {e}")

    # Jeśli scraper nie pobrał danych (np. blokada), generujemy bezpieczne dane domyślne
    if not pobrane_produkty:
        pobrane_produkty = [
            {"tytul": f"Model {dane['tytul_strony']} 1", "opis": "Automatyczny opis testowy wysokiej jakości.", "cena": "1999 zł"},
            {"tytul": f"Model {dane['tytul_strony']} 2", "opis": "Nowoczesny design i zaawansowane funkcje.", "cena": "2499 zł"},
            {"tytul": f"Model {dane['tytul_strony']} 3", "opis": "Energooszczędne urządzenie do Twojego domu.", "cena": "2999 zł"}
        ]

    # Generowanie kodu HTML dla produktów
    produkty_html = ""
    for p in pobrane_produkty:
        produkty_html += f"""
            <div class="product-card">
                <h3>{p['tytul']}</h3>
                <p>{p['opis']}</p>
                <p style="font-weight: bold; color: #1a4b84; margin-bottom: 1rem;">Cena: {p['cena']}</p>
                <a href="#" class="btn">Sprawdź szczegóły</a>
            </div>"""

    # Wstrzykiwanie danych do odpowiedniego pliku HTML
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
            print(f"Sukces! Plik {plik_html} został zaktualizowany.")
        else:
            print(f"Brak znaczników komentarza w pliku {plik_html}.")
    else:
        print(f"Nie znaleziono pliku {plik_html} w katalogu.")

print("Wszystkie pliki kategorii zostały przetworzone!")
