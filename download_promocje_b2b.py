#!/usr/bin/env python3
"""
Pobieranie promocji dnia z B2B GT Poland.
Cena na stronie = Cena BRUTTO z B2B + 100 zl (marza niewidoczna dla klienta).

  set GT_B2B_EMAIL=...
  set GT_B2B_PASSWORD=...
  python download_promocje_b2b.py --headed
  python regenerate_promocje_html.py
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("pip install playwright && python -m playwright install chromium")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "promocje.json"
IMG_DIR = ROOT / "images" / "promocje"
IMG_DIR.mkdir(parents=True, exist_ok=True)
LOGIN_URL = "https://b2bgt.gtpoland.eu/strefa-ofert/promocje-dnia-b2b"
DEFAULT_MARGIN = 100


def parse_price(text: str):
    """Parsuj cene PL: '1 353,00' / '1353 00' / '1353,00' -> 1353."""
    if not text:
        return None
    t = text.replace("\xa0", " ").replace("zl", "").replace("zł", "").replace("PLN", "").strip()
    # '1353 00' lub '1 353 00' (zlote + grosze spacja)
    m = re.search(r"(\d[\d\s]*)[,\s]+(\d{2})\s*$", t)
    if m:
        whole = re.sub(r"\s", "", m.group(1))
        try:
            return int(whole)
        except ValueError:
            pass
    # '1353,00' lub '1.353,00'
    m = re.search(r"(\d[\d\s.]*)[,.](\d{2})", t)
    if m:
        whole = re.sub(r"[\s.]", "", m.group(1))
        try:
            return int(whole)
        except ValueError:
            pass
    digits = re.sub(r"[^\d]", "", t)
    if not digits:
        return None
    try:
        v = int(digits)
        # jesli ktos zlapal grosze bez separatora (135300)
        if v >= 10000 and v % 100 <= 99:
            return v // 100
        return v
    except ValueError:
        return None


def safe_name(text: str) -> str:
    import unicodedata
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^\w\-]+", "_", text)
    return text[:80].strip("_") or "produkt"


def login(page, email: str, password: str) -> bool:
    page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(1500)

    for sel in [
        'button:has-text("Akceptuj wszystko")',
        'button:has-text("Akceptuj")',
        'button:has-text("Zgadzam")',
    ]:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible(timeout=600):
                loc.click(timeout=1500)
                page.wait_for_timeout(400)
        except Exception:
            pass

    if "Moje konto" in page.content() and page.locator('input[type="password"]').count() == 0:
        return True

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
    ]

    filled_e = filled_p = False
    for sel in email_sels:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible(timeout=400):
                loc.fill(email)
                filled_e = True
                break
        except Exception:
            pass
    for sel in pass_sels:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible(timeout=400):
                loc.fill(password)
                filled_p = True
                break
        except Exception:
            pass

    if not (filled_e and filled_p):
        print("Brak pol logowania – zaloguj sie recznie w oknie (--headed).")
        return False

    for sel in btn_sels:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible(timeout=400):
                loc.click(timeout=2000)
                break
        except Exception:
            pass
    else:
        page.keyboard.press("Enter")

    page.wait_for_timeout(3500)
    return True


def scrape_raw(page):
    if "promocje-dnia" not in page.url:
        page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2500)

    for _ in range(8):
        page.mouse.wheel(0, 900)
        page.wait_for_timeout(450)

    data = page.evaluate(
        """() => {
            const out = [];
            const candidates = document.querySelectorAll(
                '.product-item, .product-card, li.product-item, [class*="product-item"], ' +
                '[class*="ProductCard"], .item.product, article.product'
            );
            let cards = Array.from(candidates);

            if (cards.length < 3) {
                const found = new Set();
                document.querySelectorAll('a, button').forEach(b => {
                    const t = (b.innerText || '').trim().toUpperCase();
                    if (t !== 'SPRAWDŹ' && t !== 'SPRAWDZ') return;
                    let el = b.parentElement;
                    for (let i = 0; i < 10 && el; i++) {
                        const tx = el.innerText || '';
                        if (tx.includes('Cena BRUTTO') || tx.includes('Cena NETTO')) {
                            found.add(el);
                            break;
                        }
                        el = el.parentElement;
                    }
                });
                cards = Array.from(found);
            }

            const clean = (s) => (s || '').replace(/\\s+/g, ' ').trim();

            cards.forEach((card, idx) => {
                if (idx > 150) return;
                const text = card.innerText || '';
                if (!text.includes('BRUTTO') && !text.includes('NETTO')) return;

                let name = '';
                const nameEl = card.querySelector(
                    'a.product-item-link, .product-item-name a, .product-name, h2 a, h3 a, h2, h3'
                );
                if (nameEl) name = clean(nameEl.innerText);
                if (!name || /^rabat/i.test(name) || /^cena/i.test(name)) {
                    for (const line of text.split('\\n').map(clean)) {
                        if (line.length < 12) continue;
                        if (/^rabat/i.test(line)) continue;
                        if (/^cena/i.test(line)) continue;
                        if (/^sprawdz/i.test(line) || /^sprawdź/i.test(line)) continue;
                        if (/^nie lacz/i.test(line) || /^nie łącz/i.test(line)) continue;
                        if (/^promocja$/i.test(line)) continue;
                        if (/^core range$/i.test(line)) continue;
                        if (/\\d+[.,]\\d+\\s*z[lł]/i.test(line) && line.length < 35) continue;
                        name = line;
                        break;
                    }
                }

                let brutto = null;
                let netto = null;
                let oldBrutto = null;
                const bruttoM = text.match(/Cena\\s*BRUTTO\\s*([0-9\\s]+[,.]?[0-9]*)/i);
                const nettoM = text.match(/Cena\\s*NETTO\\s*([0-9\\s]+[,.]?[0-9]*)/i);
                if (bruttoM) brutto = bruttoM[1];
                if (nettoM) netto = nettoM[1];

                // kwota SPRZED promocji – przekreslone ceny / old-price
                const oldNodes = card.querySelectorAll('s, del, .old-price, .price-old, [class*="old-price"], [class*="was-price"]');
                const oldCandidates = [];
                oldNodes.forEach(n => {
                    const t = (n.innerText || '').trim();
                    if (/\\d/.test(t)) oldCandidates.push(t);
                });
                // czasem przekreslone ceny sa w tekscie pod BRUTTO (druga liczba po etykiecie)
                // zbierz wszystkie kwoty z karty
                const allPrices = [];
                const rePrice = /(\\d[\\d\\s]*[,.]\\d{2}|\\d[\\d\\s]*\\s\\d{2})\\s*z[lł]/gi;
                let mm;
                const tcopy = text;
                while ((mm = rePrice.exec(tcopy)) !== null) {
                    allPrices.push(mm[1]);
                }
                // typowy uklad GT: NETTO, BRUTTO (aktualne), potem stare NETTO, stare BRUTTO
                // bierzemy najwyzsza kwote jako "sprzed promocji" jesli > aktualne BRUTTO
                if (oldCandidates.length) {
                    oldBrutto = oldCandidates[oldCandidates.length - 1];
                }

                let img = '';
                let bestArea = 0;
                card.querySelectorAll('img').forEach(im => {
                    const src = im.currentSrc || im.src || im.getAttribute('data-src') || '';
                    if (!src || src.startsWith('data:')) return;
                    if (/logo|icon|sprite|badge/i.test(src)) return;
                    const w = im.naturalWidth || im.width || 200;
                    const h = im.naturalHeight || im.height || 200;
                    const area = w * h;
                    if (area >= bestArea) {
                        bestArea = area;
                        img = src;
                    }
                });

                if (name && (brutto || netto || oldBrutto)) {
                    out.push({ name, brutto, netto, oldBrutto, allPrices, img, snippet: text.slice(0, 400) });
                }
            });
            return out;
        }"""
    )
    return data or []


def download_image(page, url: str, dest: Path) -> bool:
    if not url or not url.startswith("http"):
        return False
    try:
        resp = page.request.get(
            url,
            timeout=30000,
            headers={"Referer": "https://b2bgt.gtpoland.eu/"},
        )
        if resp.status != 200:
            return False
        data = resp.body()
        if len(data) < 3000:
            return False
        dest.write_bytes(data)
        return True
    except Exception:
        return False


def build_products(raw, page, margin: int):
    today = str(date.today())
    products = []
    seen = set()

    for it in raw:
        name = (it.get("name") or "").strip()
        if not name or len(name) < 8:
            continue
        if name.lower() in seen:
            continue
        if re.match(r"^(rabat|cena)\b", name, re.I):
            continue

        # aktualna cena promocyjna BRUTTO
        brutto = parse_price(it.get("brutto") or "")
        if brutto is None:
            brutto = parse_price(it.get("netto") or "")

        # kwota SPRZED promocji (przekreslona) – baza do ceny detalicznej
        before = parse_price(it.get("oldBrutto") or "")
        candidates = []
        for ap in (it.get("allPrices") or []):
            v = parse_price(ap)
            if v is not None and v >= 50:
                candidates.append(v)
        # dodatkowo ze snippetu HTML/tekstu karty
        for ap in re.findall(r"(\d[\d\s]{0,6}[,.]\d{2})", it.get("snippet") or ""):
            v = parse_price(ap)
            if v is not None and v >= 50:
                candidates.append(v)
        if before is None:
            if brutto is not None:
                higher = [v for v in candidates if v > brutto + 5]
                if higher:
                    before = max(higher)
            if before is None and candidates:
                # najwyzsza kwota na karcie = zwykle cena regularna
                before = max(candidates)

        # baza: sprzed promocji, fallback: aktualne BRUTTO
        base = before if before is not None else brutto
        if base is None:
            continue

        detal = base + margin
        seen.add(name.lower())

        img_url = it.get("img") or ""
        local_rel = "images/logo.png"
        if img_url:
            ext = ".jpg"
            path = urlparse(img_url).path.lower()
            if path.endswith(".png"):
                ext = ".png"
            elif path.endswith(".webp"):
                ext = ".webp"
            fname = safe_name(name) + ext
            dest = IMG_DIR / fname
            if dest.exists() or download_image(page, img_url, dest):
                local_rel = f"images/promocje/{fname}"
            else:
                local_rel = img_url

        parts = name.split()
        producent = parts[0] if parts else ""
        opis = name if len(name) <= 180 else name[:177] + "…"

        products.append(
            {
                "tytul": name,
                "producent": producent,
                "model": "",
                "kategoria": "",
                "cena_brutto_hurt": brutto,
                "cena_przed_promocja": before,
                "cena": f"{detal} zł",
                "cena_stara": "",
                "opis": opis,
                "zdjecie": local_rel,
                "zdjecie_duze": local_rel,
                "zrodlo": "GT B2B",
                "aktualizacja": today,
            }
        )
    return products


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--headed", action="store_true")
    ap.add_argument("--email", default=os.environ.get("GT_B2B_EMAIL", ""))
    ap.add_argument("--password", default=os.environ.get("GT_B2B_PASSWORD", ""))
    ap.add_argument("--margin", type=int, default=DEFAULT_MARGIN)
    args = ap.parse_args()
    margin = args.margin

    email = args.email.strip()
    password = args.password
    if not email or not password:
        print("Ustaw GT_B2B_EMAIL i GT_B2B_PASSWORD")
        print("  python download_promocje_b2b.py --headed")
        sys.exit(1)

    print(f"Cena klienta = kwota SPRZED promocji + {margin} zl")
    print(f"URL: {LOGIN_URL}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        context = browser.new_context(
            locale="pl-PL",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1500, "height": 900},
        )
        page = context.new_page()

        ok = login(page, email, password)
        if not ok and args.headed:
            print("Zaloguj sie recznie, potem Enter...")
            try:
                input()
            except Exception:
                page.wait_for_timeout(60000)

        try:
            page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(2500)
        except Exception:
            pass

        raw = scrape_raw(page)
        print(f"Surowych kart: {len(raw)}")
        products = build_products(raw, page, margin)
        browser.close()

    if not products:
        print("Brak produktow.")
        sys.exit(3)

    JSON_PATH.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Zapisano {len(products)} promocji -> promocje.json")
    print("Regula: cena = (kwota SPRZED promocji lub BRUTTO) + marza")
    for p in products[:12]:
        before = p.get("cena_przed_promocja")
        hurt = p.get("cena_brutto_hurt")
        print(f"  - {p['tytul'][:48]}")
        print(f"      przed={before}  brutto={hurt}  -> strona {p['cena']}")
    print("\nUruchom: python regenerate_promocje_html.py")


if __name__ == "__main__":
    main()
