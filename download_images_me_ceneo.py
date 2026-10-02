#!/usr/bin/env python3
"""
Pobieranie zdjęć z Media Expert + Ceneo (bez Allegro / Bing).

  pip install playwright
  python -m playwright install chromium

  python download_images_me_ceneo.py --limit 5 --headed
  python download_images_me_ceneo.py --start 0 --limit 30 --headed
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
    if not data or len(data) < 12000:
        return False
    if data[:3] == b"\xff\xd8\xff":
        return True
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
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


def already_ok(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        return is_real_image(path.read_bytes())
    except Exception:
        return False


def accept_cookies(page) -> None:
    for sel in [
        'button:has-text("Akceptuj")',
        'button:has-text("Zgadzam")',
        'button:has-text("accept")',
        '#onetrust-accept-btn-handler',
        'button[id*="accept"]',
        '[data-testid="accept-cookies"]',
        'button.cookie-accept',
    ]:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible(timeout=600):
                loc.click(timeout=1200)
                page.wait_for_timeout(400)
                return
        except Exception:
            pass


def score_url(url: str, model: str = "") -> int:
    low = (url or "").lower()
    bad = (
        "logo", "icon", "sprite", "avatar", "badge", "placeholder", "1x1",
        "favicon", "banner", "promo", "award", "medal", "gwarancja",
        "facebook", "svg", "pixel", "tracking", "doubleclick",
        "poradnik", "ranking", "garnek", "garnk", "odkurzacz", "kinghoff",
        "kobieta", "stock", "shutterstock", "getty",
    )
    if any(b in low for b in bad):
        return -100
    score = 0
    if "mediaexpert" in low or "cdn.mediaexpert" in low:
        score += 20
    if "ceneo" in low or "static.ceneo" in low:
        score += 18
    if any(x in low for x in ("gallery", "large", "zoom", "original", "filemanager")):
        score += 6
    if any(x in low for x in ("thumb", "small", "mini", "50x", "100x")):
        score -= 12
    if any(ext in low for ext in (".jpg", ".jpeg", ".png", ".webp")):
        score += 3
    # model w URL = mocny sygnał
    m = (model or "").lower().replace("/", "").replace(" ", "")
    if m and len(m) >= 4 and m.lower() in low.replace("-", "").replace("_", ""):
        score += 40
    return score


def fetch_bytes(page, img_url: str) -> bytes | None:
    try:
        b64 = page.evaluate(
            """async (url) => {
                try {
                    const r = await fetch(url, {credentials:'omit', mode:'cors'});
                    if (!r.ok) return null;
                    const buf = await r.arrayBuffer();
                    if (buf.byteLength < 12000) return null;
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
    try:
        resp = page.request.get(
            img_url,
            timeout=25000,
            headers={"Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"},
        )
        if resp.status == 200:
            data = resp.body()
            if is_real_image(data):
                return data
    except Exception:
        pass
    return None


def collect_imgs_from_page(page) -> list[str]:
    try:
        urls = page.evaluate(
            """() => {
                const out = [];
                const add = (u) => {
                    if (!u || typeof u !== 'string') return;
                    u = u.trim();
                    if (!u.startsWith('http')) return;
                    out.push(u);
                };
                document.querySelectorAll('img').forEach(img => {
                    add(img.currentSrc || img.src);
                    add(img.getAttribute('data-src'));
                    add(img.getAttribute('data-lazy-src'));
                    const ss = img.getAttribute('srcset') || '';
                    ss.split(',').forEach(p => add(p.trim().split(' ')[0]));
                });
                const og = document.querySelector('meta[property="og:image"]');
                if (og) add(og.getAttribute('content'));
                return [...new Set(out)];
            }"""
        )
        return urls or []
    except Exception:
        return []


def search_mediaexpert(page, query: str) -> list[str]:
    url = f"https://www.mediaexpert.pl/search?query={quote(query)}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
    except Exception as e:
        print(f"  ME goto fail: {e}")
        return []
    page.wait_for_timeout(1500)
    accept_cookies(page)
    try:
        page.wait_for_selector("img", timeout=8000)
    except Exception:
        pass
    page.mouse.wheel(0, 700)
    page.wait_for_timeout(500)

    # wejdź w pierwszy produkt
    try:
        links = page.eval_on_selector_all(
            'a[href]',
            """els => {
                const out=[], seen=new Set();
                const bad = ['poradnik','ranking','blog','aktualnosc','promocj','search','konto','koszyk','regulamin'];
                for (const a of els) {
                    let h = a.href || '';
                    if (!h.includes('mediaexpert.pl')) continue;
                    const low = h.toLowerCase();
                    if (bad.some(b => low.includes(b))) continue;
                    const c = h.split('?')[0];
                    if (seen.has(c)) continue;
                    if (c.split('/').filter(Boolean).length < 5) continue;
                    seen.add(c);
                    out.push(c);
                    if (out.length >= 6) break;
                }
                return out;
            }""",
        )
    except Exception:
        links = []

    urls: list[str] = []
    urls.extend(collect_imgs_from_page(page))

    for href in (links or [])[:3]:
        try:
            print(f"  ME produkt: {href[:70]}...")
            page.goto(href, wait_until="domcontentloaded", timeout=40000)
            page.wait_for_timeout(1200)
            accept_cookies(page)
            urls.extend(collect_imgs_from_page(page))
        except Exception as e:
            print(f"  ME produkt fail: {e}")
    return urls


def search_ceneo(page, query: str) -> list[str]:
    url = f"https://www.ceneo.pl/;szukaj-{quote(query)}"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
    except Exception as e:
        print(f"  Ceneo goto fail: {e}")
        return []
    page.wait_for_timeout(1500)
    accept_cookies(page)
    try:
        page.wait_for_selector("img", timeout=8000)
    except Exception:
        pass
    page.mouse.wheel(0, 600)
    page.wait_for_timeout(400)

    urls = collect_imgs_from_page(page)

    # pierwsza karta produktu
    try:
        links = page.eval_on_selector_all(
            'a[href*="ceneo.pl/"]',
            """els => {
                const out=[], seen=new Set();
                for (const a of els) {
                    let h = a.href || '';
                    // produkty ceneo: /12345678 lub /Nazwa-produktu-123
                    if (!/ceneo\\.pl\\/\\d+/.test(h) && !/ceneo\\.pl\\/[^/]+-\\d+/.test(h)) continue;
                    const c = h.split('?')[0];
                    if (seen.has(c)) continue;
                    seen.add(c);
                    out.push(c);
                    if (out.length >= 3) break;
                }
                return out;
            }""",
        )
    except Exception:
        links = []

    for href in (links or [])[:2]:
        try:
            print(f"  Ceneo produkt: {href[:70]}...")
            page.goto(href, wait_until="domcontentloaded", timeout=40000)
            page.wait_for_timeout(1200)
            accept_cookies(page)
            urls.extend(collect_imgs_from_page(page))
        except Exception as e:
            print(f"  Ceneo produkt fail: {e}")
    return urls


def find_image(page, brand: str, model: str, title: str) -> bytes | None:
    query = f"{brand} {model}".strip() or title
    candidates: list[str] = []

    print(f"  MediaExpert: {query}")
    candidates.extend(search_mediaexpert(page, query))
    time.sleep(0.8)

    print(f"  Ceneo: {query}")
    candidates.extend(search_ceneo(page, query))

    ranked = sorted(((score_url(u, model), u) for u in set(candidates)), key=lambda x: -x[0])
    for sc, u in ranked[:12]:
        if sc < 5:
            continue
        print(f"  try ({sc}): {u[:85]}...")
        data = fetch_bytes(page, u)
        if data:
            return data
    return None


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
    print("Źródła: Media Expert + Ceneo\n")

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

        for n, (idx, prod) in enumerate(items, start=1):
            brand = (prod.get("producent") or "").strip()
            model = (prod.get("model") or "").strip()
            title = prod.get("tytul") or f"{brand} {model}".strip()
            base = safe_name(f"{brand}_{model}" if model else title)

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

            print(f"[{idx+1}/147] {brand} {model}")
            try:
                data = find_image(page, brand, model, title)
            except Exception as e:
                print(f"  ERROR: {e}")
                data = None

            if data:
                ext = ext_for(data)
                dest = OUT_DIR / f"{base}{ext}"
                dest.write_bytes(data)
                prod["zdjecia"] = [f"images/magazyn/{dest.name}"]
                ok += 1
                print(f"  OK {dest.name} ({len(data)} B)")
            else:
                fail += 1
                print("  FAIL")

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
    print("Sprawdź images/magazyn, potem: python regenerate_magazyn_html.py")


if __name__ == "__main__":
    main()
