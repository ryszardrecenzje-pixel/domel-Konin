#!/usr/bin/env python3
"""
Pobieranie zdjec produktow magazynowych (Allegro listing → images/products/).
Uzywa image_utils: safe_name, download_with_retry, placeholder, ThreadPoolExecutor.

  python download_images.py
  python download_images.py --limit 20
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import quote

import requests

from image_utils import (
    HEADERS,
    PRODUCTS_DIR,
    ROOT,
    already_have_product_image,
    download_url_to_products,
    ensure_zdjecia,
    map_parallel,
    placeholder_for,
    safe_name,
    update_json_files,
    verify_image_file,
)

JSON_PATH = ROOT / "magazyn.json"


def get_image_from_allegro(query: str, session: requests.Session) -> str | None:
    url = f"https://allegro.pl/listing?string={quote(query)}"
    try:
        r = session.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return None
        patterns = [
            r'(https://a\.allegroimg\.com/[^"\']+\.(?:jpg|jpeg|png|webp))',
            r'(https://[^"\']*allegroimg[^"\']+\.(?:jpg|jpeg|png|webp))',
            r'src="(https://[^"]+\.(?:jpg|jpeg|png|webp)[^"]*)"',
        ]
        for pat in patterns:
            for img in re.findall(pat, r.text, re.I):
                low = img.lower()
                if any(x in low for x in ("placeholder", "logo", "icon", "sprite")):
                    continue
                return img.split("?")[0]
    except Exception as e:
        print("  Allegro error:", e)
    return None


def process_one(args: tuple) -> tuple[int, dict, str]:
    idx, prod = args
    brand = (prod.get("producent") or "").strip()
    model = (prod.get("model") or "").strip()
    title = prod.get("tytul") or f"{brand} {model}".strip() or f"produkt_{idx}"
    stem = f"{brand}_{model}" if model else title
    stem = safe_name(stem)

    existing = already_have_product_image(stem)
    if existing:
        ensure_zdjecia(prod, existing)
        return idx, prod, f"SKIP {existing.name}"

    session = requests.Session()
    query = f"{brand} {model}".strip() or title
    img_url = get_image_from_allegro(query, session)
    if img_url:
        path = download_url_to_products(img_url, stem)
        if path and verify_image_file(path):
            ensure_zdjecia(prod, path)
            return idx, prod, f"OK {path.name}"

    ensure_zdjecia(prod, None)
    return idx, prod, f"PLACEHOLDER {prod['zdjecia'][0]}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    products = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    items = list(enumerate(products))[args.start :]
    if args.limit > 0:
        items = items[: args.limit]

    PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Pobieranie {len(items)} produktow → {PRODUCTS_DIR} (workers={args.workers})")

    results = map_parallel(items, process_one, max_workers=max(1, args.workers))
    ok = skip = fail = 0
    for res in results:
        if isinstance(res, Exception):
            fail += 1
            print("  ERROR", res)
            continue
        idx, prod, status = res
        products[idx] = prod
        print(f"[{idx+1}] {status}")
        if status.startswith("OK"):
            ok += 1
        elif status.startswith("SKIP"):
            skip += 1
        else:
            fail += 1

    for p in products:
        if not p.get("zdjecia"):
            ensure_zdjecia(p, None)

    update_json_files(products, magazyn_path=JSON_PATH)
    print(f"\nOK={ok} SKIP={skip} FAIL/placeholder={fail}")
    print(f"Zapisano {JSON_PATH} + data/*.json")


if __name__ == "__main__":
    main()
