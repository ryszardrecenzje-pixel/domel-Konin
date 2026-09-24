#!/usr/bin/env python3
"""
Skrypt do automatycznego pobierania zdjęć produktów magazynowych z Allegro / internetu.
Uruchom: python3 download_images.py

Uwaga: Allegro i sklepy często blokują proste scrapery (403 / JS).
Jeśli nie działa, zalecane użycie Playwright (pip install playwright && playwright install).
"""
import json, os, re, time, requests
from urllib.parse import quote

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
}

def get_image_from_allegro(query):
    url = f"https://allegro.pl/listing?string={quote(query)}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        # szukaj URL-i obrazków allegro
        patterns = [
            r'(https://a\.allegroimg\.com/[^"\']+\.(?:jpg|jpeg|png|webp))',
            r'(https://[^"\']*allegroimg[^"\']+\.(?:jpg|jpeg|png|webp))',
            r'src="(https://[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
        ]
        for pat in patterns:
            imgs = re.findall(pat, r.text, re.I)
            for img in imgs:
                if any(x in img.lower() for x in ['placeholder', 'logo', 'icon', 'sprite']):
                    continue
                return img.split('?')[0]
    except Exception as e:
        print("  Allegro error:", e)
    return None

def download(url, path):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        if r.status_code == 200 and len(r.content) > 3000:
            with open(path, "wb") as f:
                f.write(r.content)
            return True
    except Exception as e:
        print("  download error:", e)
    return False

def main():
    with open("magazyn.json", encoding="utf-8") as f:
        products = json.load(f)

    os.makedirs("images/zdjęcia produktów/magazyn", exist_ok=True)
    ok = 0
    for i, p in enumerate(products):
        if p.get("zdjecia"):
            continue
        query = f"{p['producent']} {p['model']}"
        safe = re.sub(r'[^\w\-]', '_', query)[:80]
        path = f"images/zdjęcia produktów/magazyn/{safe}.jpg"
        if os.path.exists(path) and os.path.getsize(path) > 3000:
            p["zdjecia"] = [path]
            ok += 1
            continue
        print(f"[{i+1}/{len(products)}] {query}")
        img = get_image_from_allegro(query)
        if img:
            print(f"  -> {img[:70]}...")
            if download(img, path):
                p["zdjecia"] = [path]
                ok += 1
                print("  OK")
            else:
                print("  fail download")
        else:
            print("  brak zdjęcia")
        time.sleep(2)  # nie spamuj

    with open("magazyn.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print(f"\nGotowe. Zdjęcia dla {ok} produktów. Uruchom ponownie scraper / odśwież magazyn.html jeśli potrzeba.")

if __name__ == "__main__":
    main()
