#!/usr/bin/env python3
"""
Pobieranie promocji dnia z B2B GT Poland + marża +200 zł.

Wymaga konta B2B: https://b2bgt.gtpoland.eu/

Instalacja:
    pip install playwright
    python -m playwright install chromium

Uruchomienie (NIE wklejaj hasła do chatu – tylko lokalnie):

    set GT_B2B_EMAIL=twoj@email.pl
    set GT_B2B_PASSWORD=twoje_haslo
    python download_promocje_b2b.py --headed

    python regenerate_promocje_html.py

Marża detaliczna: +200 zł do ceny hurtowej z B2B.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import date
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("pip install playwright && python -m playwright install chromium")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "promocje.json"
LOGIN_URL = "https://b2bgt.gtpoland.eu/strefa-ofert/promocje-dnia-b2b"
MARGIN = 200  # zł marży detalicznej


def parse_price(text: str) -> int | None:
    if not text:
        return None
    # 1 299,00 zł / 1299.00 / 1299
    t = text.replace("\xa0", " ").replace("zł", "").replace("PLN", "")
    t = t.replace(" ", "").replace(",", ".")
    m = re.search(r"(\d+(?:\.\d+)?)", t)
    if not m:
        return None
    try:
        return int(round(float(m.group(1))))
    except ValueError:
        return None


def retail_price(hurt: int) -> str:
    return f"{hurt + MARGIN} zł"


def login(page, email: str, password: str) -> bool:
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(1500)

    # cookies
    for sel in [
        'button:has-text("Akceptuj wszystko")',
        'button:has-text("Akceptuj")',
        'button:has-text("Zgadzam")',
    ]:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible(timeout=800):
                loc.click(timeout=1500)
                page.wait_for_timeout(400)
        except Exception:
            pass

    # pola logowania – różne warianty formularza Magento/custom
    email_sels = [
        'input[name="login[username]"]',
        'input[name="username"]',
        'input[type="email"]',
        'input[id*="email"]',
        'input[name="email"]',
    ]
    pass_sels = [
        'input[name="login[password]"]',
        'input[name="password"]',
        'input[type="password"]',
    ]
    btn_sels = [
        'button:has-text("ZALOGUJ")',
        'button:has-text("Zaloguj")',
        'button[type="submit"]',
        'input[type="submit"]',
    ]

    filled_e = filled_p = False
    for sel in email_sels:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible(timeout=500):
                loc.fill(email)
                filled_e = True
                break
        except Exception:
            pass
    for sel in pass_sels:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible(timeout=500):
                loc.fill(password)
                filled_p = True
                break
        except Exception:
            pass

    if not (filled_e and filled_p):
        print("Nie znaleziono pól logowania – użyj --headed i sprawdź formularz.")
        return False

    clicked = False
    for sel in btn_sels:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible(timeout=500):
                loc.click(timeout=2000)
                clicked = True
                break
        except Exception:
            pass
    if not clicked:
        page.keyboard.press("Enter")

    page.wait_for_timeout(3500)
    # czy nadal ekran logowania?
    content = page.content().lower()
    if "zaloguj się" in content and "hasło" in content and "promocje dnia" not in content:
        # może już jesteśmy w środku – sprawdź URL
        if "login" in page.url.lower() or "customer/account" in page.url.lower():
            print("Logowanie prawdopodobnie nieudane (sprawdź email/hasło).")
            return False
    return True


def scrape_products(page) -> list[dict]:
    """Elastyczny zrzut kart produktów ze strony promocji."""
    # upewnij się że jesteśmy na promocjach
    if "promocje-dnia" not in page.url:
        try:
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2000)
        except Exception as e:
            print(f"goto promocje: {e}")

    page.mouse.wheel(0, 1200)
    page.wait_for_timeout(800)
    page.mouse.wheel(0, 1200)
    page.wait_for_timeout(800)

    # dump struktury do debug (pomaga dopasować selektory)
    raw = page.evaluate(
        """() => {
            const items = [];
            // typowe selektory sklepów B2B / Magento
            const cards = document.querySelectorAll(
                '.product-item, .product-card, .item.product, li.product-item, ' +
                '[data-product-id], .product-info, .product.details, .grid .product'
            );
            const pickText = (el, sels) => {
                for (const s of sels) {
                    const n = el.querySelector(s);
                    if (n && n.innerText.trim()) return n.innerText.trim();
                }
                return '';
            };
            const pickImg = (el) => {
                const img = el.querySelector('img');
                if (!img) return '';
                return img.currentSrc || img.src || img.getAttribute('data-src') || '';
            };
            cards.forEach((el, i) => {
                if (i > 200) return;
                const name = pickText(el, [
                    '.product-item-name a', '.product-name', 'h2', 'h3', 'a.product-item-link',
                    '.name', '[itemprop="name"]'
                ]);
                const price = pickText(el, [
                    '.price', '.special-price .price', '.price-wrapper',
                    '[data-price-type="finalPrice"]', '.final-price', '.price-box'
                ]);
                const oldPrice = pickText(el, [
                    '.old-price .price', '.price-old', 's.price', '.was-price'
                ]);
                const img = pickImg(el);
                if (name || price) {
                    items.push({ name, price, oldPrice, img, htmlSnippet: el.innerText.slice(0, 300) });
                }
            });
            // fallback: jeśli brak kart – zbierz wszystkie bloki z ceną
            if (items.length === 0) {
                document.querySelectorAll('div, li, article').forEach((el) => {
                    if (items.length > 150) return;
                    const t = (el.innerText || '').trim();
                    if (t.length < 20 || t.length > 500) return;
                    if (!/\\d+[\\s,.]?\\d*\\s*zł/i.test(t)) return;
                    if (el.querySelectorAll('div, li, article').length > 8) return;
                    const img = el.querySelector('img');
                    items.push({
                        name: t.split('\\n')[0].slice(0, 120),
                        price: (t.match(/(\\d[\\d\\s]*[,.]?\\d*)\\s*zł/i) || ['',''])[0],
                        oldPrice: '',
                        img: img ? (img.currentSrc || img.src || '') : '',
                        htmlSnippet: t.slice(0, 300)
                    });
                });
            }
            return items;
        }"""
    )

    products = []
    today = str(date.today())
    seen = set()
    for it in raw or []:
        name = (it.get("name") or "").strip()
        if not name or len(name) < 3:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)

        hurt = parse_price(it.get("price") or "")
        if hurt is None:
            # spróbuj ze snippetu
            hurt = parse_price(it.get("htmlSnippet") or "")
        if hurt is None:
            continue

        old = parse_price(it.get("oldPrice") or "")
        img = it.get("img") or "images/logo.png"
        # nie zapisuj zewnętrznych URL na stałe bez pobrania – zostaw URL lub placeholder
        if img.startswith("http"):
            zdjecie = img  # zewnętrzny – przeglądarka załaduje; opcjonalnie można dociągnąć lokalnie
        else:
            zdjecie = img if img else "images/logo.png"

        # spróbuj wyciągnąć producenta/model z nazwy
        parts = name.split()
        producent = parts[0] if parts else ""
        model = " ".join(parts[1:3]) if len(parts) > 1 else ""

        products.append(
            {
                "tytul": name,
                "producent": producent,
                "model": model,
                "kategoria": "",
                "cena_hurt": hurt,
                "cena": retail_price(hurt),
                "cena_stara": f"{old} zł" if old and old > hurt else "",
                "opis": f"Promocja dnia GT B2B. Cena detaliczna = {hurt} zł (hurt) + {MARGIN} zł marży.",
                "zdjecie": zdjecie,
                "zrodlo": "GT B2B – promocje dnia",
                "aktualizacja": today,
            }
        )
    return products


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--email", default=os.environ.get("GT_B2B_EMAIL", ""))
    ap.add_argument("--password", default=os.environ.get("GT_B2B_PASSWORD", ""))
    ap.add_argument("--margin", type=int, default=MARGIN)
    args = ap.parse_args()

    global MARGIN
    MARGIN = args.margin

    email = args.email.strip()
    password = args.password
    if not email or not password:
        print("Podaj dane logowania B2B:")
        print("  set GT_B2B_EMAIL=twoj@email.pl")
        print("  set GT_B2B_PASSWORD=haslo")
        print("  python download_promocje_b2b.py --headed")
        print("albo:")
        print("  python download_promocje_b2b.py --email ... --password ... --headed")
        sys.exit(1)

    print(f"Marża detaliczna: +{MARGIN} zł")
    print(f"URL: {LOGIN_URL}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        context = browser.new_context(
            locale="pl-PL",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1400, "height": 900},
        )
        page = context.new_page()

        ok = login(page, email, password)
        if not ok:
            print("Logowanie nie powiodło się.")
            if args.headed:
                print("Okno zostaje otwarte 60 s – zaloguj się ręcznie, potem Enter w konsoli…")
                try:
                    input()
                except Exception:
                    page.wait_for_timeout(60000)
            else:
                browser.close()
                sys.exit(2)

        # po ręcznym logowaniu wejdź ponownie na promocje
        try:
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2500)
        except Exception:
            pass

        products = scrape_products(page)
        browser.close()

    if not products:
        print("Nie znaleziono produktów. Uruchom z --headed i sprawdź selektory na stronie.")
        print("Możesz też ręcznie uzupełnić promocje.json.")
        sys.exit(3)

    JSON_PATH.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Zapisano {len(products)} promocji → {JSON_PATH}")
    for p in products[:5]:
        print(f"  - {p['tytul']}: hurt {p['cena_hurt']} → detal {p['cena']}")
    print("\nNastępnie:")
    print("  python regenerate_promocje_html.py")


if __name__ == "__main__":
    main()
