#!/usr/bin/env python3
"""
Pobieranie zdjęć produktów z Allegro (Playwright).
Wejście w ofertę → główne zdjęcie galerii → walidacja magicznych bajtów.

  pip install playwright
  python -m playwright install chromium

  python download_images_playwright.py --limit 5 --headed
  python download_images_playwright.py --start 0 --limit 30 --headed
  python regenerate_magazyn_html.py
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("pip install playwright && python -m playwright install chromium")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent
JSON_PATH = ROOT / "magazyn.json"
OUT_DIR = ROOT / "images" / "magazyn"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_name(text: str) -> str:
    text = re.sub(r"[^\w\-]+", "_", text, flags=re.UNICODE)
    return text[:90].strip("_")


def is_real_image(data: bytes) -> bool:
    if not data or len(data) < 8000:
        return False
    # JPEG
    if data[:3] == b"\xff\xd8\xff":
        return True
    # PNG
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    # WEBP
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return True
    # GIF
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return True
    return False


def ext_for(data: bytes) -> str:
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return ".jpg"


def accept_cookies(page) -> None:
    for sel in [
        'button:has-text("zgadzam")',
        'button:has-text("Zgadzam")',
        'button:has-text("Akceptuję")',
        '[data-role="accept-consent"]',
        'button[data-testid="accept-button"]',
        '#onetrust-accept-btn-handler',
    ]:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible(timeout=600):
                loc.click(timeout=1500)
                page.wait_for_timeout(500)
                return
        except Exception:
            pass


def blocked(page) -> bool:
    try:
        t = page.content()
        return "Zostałeś zablokowany" in t or "zostałeś zablokowany" in t.lower()
    except Exception:
        return False


def listing_offer_links(page, query: str) -> list[str]:
    url = f"https://allegro.pl/listing?string={quote(query)}"
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(1200)
    if blocked(page):
        return []
    accept_cookies(page)
    try:
        page.wait_for_selector('a[href*="/oferta/"]', timeout=10000)
    except Exception:
        page.wait_for_timeout(2000)
    page.mouse.wheel(0, 500)
    page.wait_for_timeout(400)

    links = page.eval_on_selector_all(
        'a[href*="/oferta/"]',
        """els => {
            const out = [], seen = new Set();
            for (const a of els) {
                let h = a.href || a.getAttribute('href') || '';
                if (!h.includes('/oferta/')) continue;
                // pomiń kotwice / parametry śledzące jako unikalność
                const clean = h.split('?')[0];
                if (seen.has(clean)) continue;
                seen.add(clean);
                out.push(clean);
                if (out.length >= 8) break;
            }
            return out;
        }""",
    )
    return links or []


def gallery_image_urls(page) -> list[str]:
    """URL-e z galerii produktu na stronie oferty."""
    urls = page.evaluate(
        """() => {
            const out = [];
            const add = (u) => {
                if (!u || typeof u !== 'string') return;
                u = u.trim();
                if (!u.startsWith('http')) return;
                if (u.includes('action-common')) return;
                if (u.includes('logo') || u.includes('avatar')) return;
                out.push(u.split('?')[0]);
            };
            // główne img w galerii
            document.querySelectorAll(
                '[data-testid="gallery"] img, [class*="gallery"] img, [class*="Gallery"] img, ' +
                'div[data-box-name*="gallery"] img, img[src*="allegroimg"]'
            ).forEach(img => {
                add(img.currentSrc || img.src);
                const ss = img.getAttribute('srcset') || '';
                ss.split(',').forEach(p => add(p.trim().split(' ')[0]));
            });
            // przyciski miniatur często mają data-src / background
            document.querySelectorAll('[data-testid="gallery"] button img, [class*="thumbnail"] img').forEach(img => {
                add(img.currentSrc || img.src);
            });
            // meta og:image
            const og = document.querySelector('meta[property="og:image"]');
            if (og) add(og.getAttribute('content'));
            return [...new Set(out)];
        }"""
    )
    return urls or []


def score_url(u: str) -> int:
    low = u.lower()
    if "action-common" in low or "/common/" in low:
        return -100
    score = 0
    if "allegroimg" in low:
        score += 5
    if "/original/" in low:
        score += 15
    for s, pts in (("s1280", 10), ("s1024", 8), ("s720", 6), ("s600", 4), ("s512", 2)):
        if s in low:
            score += pts
    for s in ("s64", "s128", "s32", "thumbnail"):
        if s in low:
            score -= 12
    return score


def pick_best(urls: list[str]) -> str | None:
    ranked = sorted(((score_url(u), u) for u in urls), key=lambda x: -x[0])
    for sc, u in ranked:
        if sc > 0:
            return u
    return None


def fetch_bytes(page, img_url: str) -> bytes | None:
    # 1) fetch w stronie
    try:
        b64 = page.evaluate(
            """async (url) => {
                try {
                    const r = await fetch(url, {credentials:'include', mode:'cors', cache:'force-cache'});
                    if (!r.ok) return null;
                    const buf = await r.arrayBuffer();
                    if (buf.byteLength < 8000) return null;
                    const bytes = new Uint8Array(buf);
                    let bin = '';
                    const chunk = 0x8000;
                    for (let i = 0; i < bytes.length; i += chunk)
                        bin += String.fromCharCode.apply(null, bytes.subarray(i, i+chunk));
                    return btoa(bin);
                } catch(e) { return null; }
            }""",
            img_url,
        )
        if b64:
            data = base64.b64decode(b64)
            if is_real_image(data):
                return data
    except Exception:
        pass

    # 2) API request
    try:
        resp = page.request.get(
            img_url,
            timeout=30000,
            headers={
                "Referer": "https://allegro.pl/",
                "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            },
        )
        if resp.status == 200:
            data = resp.body()
            if is_real_image(data):
                return data
    except Exception:
        pass
    return None


def download_from_offer(page, offer_url: str) -> bytes | None:
    page.goto(offer_url, wait_until="domcontentloaded", timeout=50000)
    page.wait_for_timeout(1500)
    if blocked(page):
        print("  BLOKADA Allegro")
        return None
    try:
        page.wait_for_selector('img[src*="allegroimg"]', timeout=8000)
    except Exception:
        pass
    page.mouse.wheel(0, 300)
    page.wait_for_timeout(400)

    urls = gallery_image_urls(page)
    # sortuj od najlepszych
    urls = sorted(urls, key=score_url, reverse=True)
    for u in urls[:6]:
        if score_url(u) <= 0:
            continue
        data = fetch_bytes(page, u)
        if data:
            return data
    return None


def already_ok(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        data = path.read_bytes()
        return is_real_image(data)
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--headed", action="store_true")
    args = ap.parse_args()

    products = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    items = list(enumerate(products))[args.start :]
    if args.limit > 0:
        items = items[: args.limit]

    print(f"Do pobrania: {len(items)} (start={args.start})")
    print("Usuń stare złe pliki przed startem, jeśli jeszcze są.\n")

    ok = skip = fail = 0

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
        first = True

        for n, (idx, prod) in enumerate(items, start=1):
            title = prod.get("tytul") or f"{prod.get('producent','')} {prod.get('model','')}".strip()
            query = f"{prod.get('producent','')} {prod.get('model','')}".strip() or title
            base = safe_name(query)

            # sprawdź istniejący dobry plik
            existing = None
            for ext in (".jpg", ".png", ".webp"):
                cand = OUT_DIR / f"{base}{ext}"
                if already_ok(cand):
                    existing = cand
                    break
            if existing:
                prod["zdjecia"] = [f"images/magazyn/{existing.name}"]
                skip += 1
                print(f"[{idx+1}/147] SKIP {title}")
                continue

            print(f"[{idx+1}/147] {query}")
            if first:
                # rozgrzewka listing + cookies
                listing_offer_links(page, query)
                first = False

            links = listing_offer_links(page, query)
            if not links:
                print("  brak ofert / blokada")
                fail += 1
                continue

            data = None
            used = None
            for href in links[:4]:
                print(f"  oferta: {href[:70]}...")
                data = download_from_offer(page, href)
                if data:
                    used = href
                    break
                time.sleep(0.8)

            if data:
                ext = ext_for(data)
                dest = OUT_DIR / f"{base}{ext}"
                dest.write_bytes(data)
                prod["zdjecia"] = [f"images/magazyn/{dest.name}"]
                ok += 1
                print(f"  OK {dest.name} ({len(data)} B) magic=OK")
            else:
                fail += 1
                print("  FAIL – brak poprawnego zdjęcia")

            if n % 3 == 0:
                JSON_PATH.write_text(
                    json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            time.sleep(2.0)

        browser.close()

    JSON_PATH.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n=== PODSUMOWANIE ===")
    print(f"Pobrane:   {ok}")
    print(f"Pominięte: {skip}")
    print(f"Błędy:     {fail}")
    print("Sprawdź pliki w images/magazyn – powinny otwierać się w Paint / przeglądarce.")
    print("Potem: python regenerate_magazyn_html.py")


if __name__ == "__main__":
    main()
