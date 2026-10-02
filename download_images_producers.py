#!/usr/bin/env python3
"""
Pobieranie zdjęć produktów ze stron producentów + Bing Images (BEZ Allegro).

Instalacja:
    pip install playwright
    python -m playwright install chromium

Uruchomienie (w folderze projektu):
    python download_images_producers.py --limit 5 --headed
    python download_images_producers.py --start 0 --limit 30 --headed
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

# Preferowane domeny producentów (wyższy priorytet przy wyborze URL)
BRAND_DOMAINS = {
    "samsung": ["samsung.com", "images.samsung.com"],
    "bosch": ["bosch-home.com", "bosch.com", "media3.bosch-home.com"],
    "siemens": ["siemens-home.bsh-group.com", "siemens.com"],
    "candy": ["candy-home.com", "candy.com"],
    "electrolux": ["electrolux.pl", "electrolux.com"],
    "aeg": ["aeg.pl", "aeg.com"],
    "beko": ["beko.com", "beko.pl"],
    "gorenje": ["gorenje.com", "gorenje.pl"],
    "whirlpool": ["whirlpool.pl", "whirlpool.com", "whirlpool.eu"],
    "amica": ["amica.pl", "amica.com"],
    "hisense": ["hisense.com", "hisense-europe.com"],
    "haier": ["haier.com", "haier-europe.com"],
    "teka": ["teka.com"],
    "indesit": ["indesit.pl", "indesit.com"],
    "hoover": ["hoover.com", "hoover.pl"],
    "toshiba": ["toshiba-lifestyle.com"],
    "cecotec": ["cecotec.com", "cecotec.es"],
    "comfee": ["comfee.com", "comfeeglobal.com"],
    "bomann": ["bomann.de", "bomann.pl"],
}


def safe_name(text: str) -> str:
    text = re.sub(r"[^\w\-]+", "_", text, flags=re.UNICODE)
    return text[:90].strip("_")


def is_real_image(data: bytes) -> bool:
    if not data or len(data) < 10000:
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


def score_image_url(url: str, brand: str) -> int:
    low = url.lower()
    bad = (
        "logo", "icon", "sprite", "avatar", "flag", "badge", "placeholder",
        "1x1", "pixel", "tracking", "facebook", "svg", "doubleclick",
        "action-common", "/common/", "favicon", "award", "prize", "medal",
        "winner", "laureat", "odznaka", "nagrody", "nagroda", "trophy",
        "banner", "promo", "campaign", "soundbar", "tv_", "/tv/", "monitor",
        "smartphone", "galaxy-s", "galaxy-z", "neo-qled", "neoqled", "qled",
        "gwarancja", "gwiazda", "dekady", "jakosc", "jakość", "obslugi",
        "obsługi", "matura", "egzamin", "załącznik", "formularz", "pdf",
        "document", "certificate", "diploma",
    )
    if any(b in low for b in bad):
        return -100
    score = 0
    brand_key = (brand or "").lower().split()[0]
    for dom in BRAND_DOMAINS.get(brand_key, []):
        if dom in low:
            score += 30
    # słowa sugerujące AGD
    if any(x in low for x in (
        "oven", "piekarnik", "washer", "pralka", "fridge", "lodow", "dishwasher",
        "zmywark", "dryer", "suszark", "cooker", "kuchenka", "hob", "plyta",
        "microwave", "mikrofala", "built-in", "zabudow",
    )):
        score += 20
    if any(x in low for x in ("samsung", "bosch", "electrolux", "whirlpool", "gorenje", "beko", "candy", "amica")):
        score += 6
    if any(x in low for x in ("_large", "large", "zoom", "master", "original", "1200", "1000", "800", "high")):
        score += 6
    if any(x in low for x in ("thumb", "small", "tiny", "50x", "100x", "icon", "star")):
        score -= 15
    if low.startswith("http"):
        score += 1
    return score


def fetch_bytes(page, img_url: str) -> bytes | None:
    try:
        b64 = page.evaluate(
            """async (url) => {
                try {
                    const r = await fetch(url, {credentials:'omit', mode:'cors', cache:'force-cache'});
                    if (!r.ok) return null;
                    const buf = await r.arrayBuffer();
                    if (buf.byteLength < 10000) return null;
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


def collect_bing_urls(page, query: str) -> list[str]:
    url = f"https://www.bing.com/images/search?q={quote(query)}&form=HDRSC2&first=1"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
    except Exception as e:
        print(f"  bing goto fail: {e}")
        return []
    try:
        page.wait_for_timeout(2000)
    except Exception:
        return []
    # cookies bing
    for sel in [
        '#bnp_btn_accept',
        'button[id*="accept"]',
        'button:has-text("Accept")',
        'button:has-text("Akceptuj")',
    ]:
        try:
            loc = page.locator(sel).first
            if loc.count() and loc.is_visible(timeout=500):
                loc.click(timeout=1000)
                page.wait_for_timeout(500)
        except Exception:
            pass
    try:
        page.wait_for_selector("img.mimg, .imgpt img, a.iusc", timeout=10000)
    except Exception:
        page.wait_for_timeout(2000)
    page.mouse.wheel(0, 900)
    page.wait_for_timeout(600)

    urls = page.evaluate(
        """() => {
            const out = [];
            const add = (u) => {
                if (!u || typeof u !== 'string') return;
                u = u.trim();
                if (!u.startsWith('http')) return;
                if (u.includes('data:')) return;
                if (u.includes('th?id=OIP')) { /* bing thumb */ }
                out.push(u.split('?')[0] === u ? u : u);
            };
            // metadane pełnego obrazu w a.iusc
            document.querySelectorAll('a.iusc').forEach(a => {
                try {
                    const m = JSON.parse(a.getAttribute('m') || '{}');
                    if (m.murl) add(m.murl);
                    if (m.turl) add(m.turl);
                } catch(e) {}
                const href = a.getAttribute('href') || '';
                const mm = href.match(/mediaurl=([^&]+)/);
                if (mm) add(decodeURIComponent(mm[1]));
            });
            document.querySelectorAll('img.mimg, .imgpt img').forEach(img => {
                add(img.src);
                add(img.getAttribute('data-src'));
            });
            return [...new Set(out)];
        }"""
    )
    return urls or []


def manufacturer_search_urls(brand: str, model: str) -> list[str]:
    b = (brand or "").lower().strip()
    m = quote(f"{brand} {model}".strip())
    model_q = quote(model or "")
    urls = []
    if "samsung" in b:
        urls.append(f"https://www.samsung.com/pl/search/?searchvalue={model_q}")
        urls.append(f"https://www.samsung.com/us/search/searchResults/?searchValue={model_q}")
    if "bosch" in b:
        urls.append(f"https://www.bosch-home.com/pl/search?SearchTerm={model_q}&q={model_q}")
    if "siemens" in b:
        urls.append(f"https://www.siemens-home.bsh-group.com/pl/search?SearchTerm={model_q}")
    if "electrolux" in b:
        urls.append(f"https://www.electrolux.pl/search/?q={model_q}")
    if "beko" in b:
        urls.append(f"https://www.beko.com/pl-pl/search?text={model_q}")
    if "gorenje" in b:
        urls.append(f"https://www.gorenje.com/search?q={model_q}")
    if "whirlpool" in b:
        urls.append(f"https://www.whirlpool.pl/search/?text={model_q}")
    if "amica" in b:
        urls.append(f"https://www.amica.pl/szukaj?q={model_q}")
    if "candy" in b:
        urls.append(f"https://www.candy-home.com/pl_PL/search/?text={model_q}")
    if "hisense" in b:
        urls.append(f"https://www.hisense-europe.com/pl/search?q={model_q}")
    if "cecotec" in b:
        urls.append(f"https://www.cecotec.es/en/search?s={model_q}")
    return urls


def collect_site_urls(page, page_url: str) -> list[str]:
    try:
        page.goto(page_url, wait_until="domcontentloaded", timeout=35000)
        page.wait_for_timeout(1500)
        page.mouse.wheel(0, 600)
        page.wait_for_timeout(400)
        urls = page.evaluate(
            """() => {
                const out = [];
                document.querySelectorAll('img').forEach(img => {
                    const s = img.currentSrc || img.src || img.getAttribute('data-src') || '';
                    if (s.startsWith('http') && (img.naturalWidth||0) >= 100) out.push(s);
                    else if (s.startsWith('http')) out.push(s);
                });
                const og = document.querySelector('meta[property="og:image"]');
                if (og) out.push(og.getAttribute('content'));
                return [...new Set(out.filter(Boolean))];
            }"""
        )
        return urls or []
    except Exception:
        return []


def category_keyword(kategoria: str) -> str:
    k = (kategoria or "").lower()
    mapping = [
        ("piekarn", "piekarnik oven"),
        ("pralk", "pralka washing machine"),
        ("zmywar", "zmywarka dishwasher"),
        ("suszar", "suszarka dryer"),
        ("lodów", "lodówka refrigerator"),
        ("lodow", "lodówka refrigerator"),
        ("zamraż", "zamrażarka freezer"),
        ("zamraz", "zamrażarka freezer"),
        ("płyt", "płyta grzewcza hob"),
        ("plyt", "płyta grzewcza hob"),
        ("kuchen", "kuchenka cooker"),
        ("mikrof", "mikrofalówka microwave"),
        ("okap", "okap hood"),
    ]
    for key, val in mapping:
        if key in k:
            return val
    return "AGD appliance"


def find_image(page, brand: str, model: str, title: str, kategoria: str = "") -> bytes | None:
    cat = category_keyword(kategoria)
    candidates: list[str] = []

    # 1) strony producenta
    for mu in manufacturer_search_urls(brand, model)[:2]:
        print(f"  site: {mu[:75]}...")
        candidates.extend(collect_site_urls(page, mu))
        time.sleep(0.5)

    # 2) Bing – zapytanie z kategorią (żeby nie brać odznak / TV)
    bing_q = f"{brand} {model} {cat}"
    print(f"  bing: {bing_q}")
    candidates.extend(collect_bing_urls(page, bing_q))

    # 3) drugi wariant zapytania
    bing_q2 = f'"{model}" {brand} {cat.split()[0]}'
    print(f"  bing2: {bing_q2}")
    candidates.extend(collect_bing_urls(page, bing_q2))

    ranked = sorted(
        ((score_image_url(u, brand), u) for u in set(candidates)),
        key=lambda x: -x[0],
    )
    for sc, u in ranked[:15]:
        if sc < 5:
            continue
        print(f"  try ({sc}): {u[:80]}...")
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
    print("Źródła: strony producentów + Bing Images (bez Allegro)\n")

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
                data = find_image(page, brand, model, title, prod.get("kategoria") or "")
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
            time.sleep(1.8)

        browser.close()

    JSON_PATH.write_text(json.dumps(products, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n=== PODSUMOWANIE ===")
    print(f"Pobrane:   {ok}")
    print(f"Pominięte: {skip}")
    print(f"Błędy:     {fail}")
    print("Sprawdź images/magazyn – różne rozmiary, otwieralne w Paint.")
    print("Potem: python regenerate_magazyn_html.py")


if __name__ == "__main__":
    main()
