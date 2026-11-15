#!/usr/bin/env python3
"""
Wspolne narzedzia do pobierania i walidacji zdjec produktow Domel Konin.

- safe_name()          – bezpieczne nazwy plikow/katalogow
- download_with_retry()– 3 proby, backoff, Content-Type, min. rozmiar, Pillow verify
- placeholder_for()    – images/categories/<kategoria>.jpg gdy brak zdjecia
- PRODUCTS_DIR         – images/products/ (zgodne z CMS media_folder)
- update_json_paths()  – zapis magazyn.json + data/*.json
"""
from __future__ import annotations

import json
import re
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

import requests

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore

ROOT = Path(__file__).resolve().parent
PRODUCTS_DIR = ROOT / "images" / "products"
CATEGORIES_DIR = ROOT / "images" / "categories"
MIN_BYTES = 3 * 1024  # 3 KB
MAX_WORKERS = 4

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
}

_CATEGORY_ALIASES = {
    "lodow": "lodowki",
    "lodów": "lodowki",
    "pralk": "pralki",
    "zmywar": "zmywarki",
    "piekarn": "piekarniki",
    "kuchen": "kuchenki",
    "mikrofal": "kuchenki",
    "płyt": "plyty-grzewcze",
    "plyt": "plyty-grzewcze",
    "grzew": "plyty-grzewcze",
    "male": "male-agd",
    "małe": "male-agd",
    "agd": "male-agd",
    "suszar": "suszarki",
    "zamraż": "zamrazarki",
    "zamraz": "zamrazarki",
    "okap": "male-agd",
}


def safe_name(text: str) -> str:
    """Bezpieczna nazwa: # ? spacje nawiasy polskie znaki → _ / ASCII."""
    pl = str.maketrans({
        "ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n", "ó": "o", "ś": "s", "ź": "z", "ż": "z",
        "Ą": "A", "Ć": "C", "Ę": "E", "Ł": "L", "Ń": "N", "Ó": "O", "Ś": "S", "Ź": "Z", "Ż": "Z",
    })
    text = (text or "").translate(pl)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    for ch in (
        "#", "?", " ", "/", "\\", ":", "*", '"', "<", ">", "|",
        "(", ")", "[", "]", "{", "}", "'", ",", ";", "&", "%", "+", "=", ".",
    ):
        text = text.replace(ch, "_")
    text = re.sub(r"[^\w\-]+", "_", text, flags=re.UNICODE)
    text = re.sub(r"_+", "_", text)
    return text[:90].strip("._") or "produkt"


def category_slug(kategoria: str) -> str:
    k = (kategoria or "").lower()
    for needle, slug in _CATEGORY_ALIASES.items():
        if needle in k:
            return slug
    return "lodowki"


def placeholder_for(kategoria: str = "") -> str:
    """Wzgledna sciezka placeholdera kategorii – nigdy pusty wynik."""
    slug = category_slug(kategoria)
    candidates = [
        CATEGORIES_DIR / f"{slug}.jpg",
        CATEGORIES_DIR / f"{slug}.png",
        CATEGORIES_DIR / "lodowki.jpg",
        ROOT / "images" / "logo.png",
    ]
    for c in candidates:
        if c.is_file() and c.stat().st_size > 100:
            return str(c.relative_to(ROOT)).replace("\\", "/")
    return f"images/categories/{slug}.jpg"


def product_path(stem: str, ext: str = ".jpg") -> Path:
    PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
    if not ext.startswith("."):
        ext = "." + ext
    return PRODUCTS_DIR / f"{safe_name(stem)}{ext.lower()}"


def relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT.resolve())).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def is_image_magic(data: bytes) -> bool:
    if not data or len(data) < 12:
        return False
    if data[:3] == b"\xff\xd8\xff":
        return True
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return True
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return True
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return True
    return False


def ext_from_magic(data: bytes) -> str:
    if data[:3] == b"\xff\xd8\xff":
        return ".jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    return ".jpg"


def verify_image_file(path: Path) -> bool:
    try:
        if not path.is_file() or path.stat().st_size < MIN_BYTES:
            return False
        data = path.read_bytes()[:64]
        if not is_image_magic(data):
            return False
        if Image is not None:
            with Image.open(path) as im:
                im.verify()
        return True
    except Exception:
        return False


def download_with_retry(
    url: str,
    dest: Path,
    *,
    retries: int = 3,
    min_bytes: int = MIN_BYTES,
    timeout: int = 25,
    session: Optional[requests.Session] = None,
) -> bool:
    if not url or not url.startswith("http"):
        return False
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    sess = session or requests.Session()

    for attempt in range(1, retries + 1):
        try:
            r = sess.get(url, headers=HEADERS, timeout=timeout, stream=True)
            if r.status_code != 200:
                raise RuntimeError(f"HTTP {r.status_code}")
            ctype = (r.headers.get("Content-Type") or "").lower()
            if ctype and not any(
                x in ctype for x in ("image/", "octet-stream", "binary", "application/webp")
            ):
                if "text/" in ctype or "json" in ctype or "html" in ctype:
                    raise RuntimeError(f"zly Content-Type: {ctype}")
            data = r.content
            if len(data) < min_bytes:
                raise RuntimeError(f"za maly plik ({len(data)} B)")
            if not is_image_magic(data):
                raise RuntimeError("brak naglowka obrazu (magic)")
            ext = ext_from_magic(data)
            if dest.suffix.lower() != ext:
                dest = dest.with_suffix(ext)
            dest.write_bytes(data)
            if not verify_image_file(dest):
                dest.unlink(missing_ok=True)
                raise RuntimeError("Pillow verify() nie przeszlo")
            return True
        except Exception as e:
            if dest.exists():
                try:
                    dest.unlink()
                except OSError:
                    pass
            if attempt >= retries:
                print(f"  download FAIL {url[:70]}… ({e})")
                return False
            time.sleep(0.8 * attempt)
    return False


def ensure_zdjecia(product: dict, local_path: Optional[Path] = None) -> list[str]:
    if local_path and verify_image_file(local_path):
        rel = relative_path(local_path)
        product["zdjecia"] = [rel]
        return product["zdjecia"]
    ph = placeholder_for(product.get("kategoria") or product.get("category") or "")
    product["zdjecia"] = [ph]
    return product["zdjecia"]


def already_have_product_image(stem: str) -> Optional[Path]:
    base = safe_name(stem)
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        cand = PRODUCTS_DIR / f"{base}{ext}"
        if verify_image_file(cand):
            return cand
    return None


def update_json_files(products: list[dict], *, magazyn_path: Optional[Path] = None) -> None:
    magazyn_path = magazyn_path or (ROOT / "magazyn.json")
    magazyn_path.write_text(
        json.dumps(products, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    data_dir = ROOT / "data"
    if not data_dir.is_dir():
        return
    by_key: dict[str, dict] = {}
    for p in products:
        k1 = f"{(p.get('producent') or '').lower()}|{(p.get('model') or '').lower()}"
        k2 = (p.get("tytul") or "").lower()
        by_key[k1] = p
        if k2:
            by_key[k2] = p

    for fp in data_dir.glob("*.json"):
        try:
            item = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(item, dict):
            continue
        k1 = f"{(item.get('producent') or '').lower()}|{(item.get('model') or '').lower()}"
        k2 = (item.get("tytul") or "").lower()
        src = by_key.get(k1) or by_key.get(k2)
        if not src:
            if not item.get("zdjecia"):
                item["zdjecia"] = [placeholder_for(item.get("kategoria") or item.get("category") or "")]
                fp.write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            continue
        if src.get("zdjecia"):
            item["zdjecia"] = list(src["zdjecia"])
            fp.write_text(json.dumps(item, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def map_parallel(
    tasks: Iterable[Any],
    worker: Callable[[Any], Any],
    *,
    max_workers: int = MAX_WORKERS,
) -> list[Any]:
    results: list[Any] = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(worker, t): t for t in tasks}
        for fut in as_completed(futs):
            try:
                results.append(fut.result())
            except Exception as e:
                results.append(e)
    return results


def download_url_to_products(
    url: str,
    stem: str,
    *,
    retries: int = 3,
) -> Optional[Path]:
    PRODUCTS_DIR.mkdir(parents=True, exist_ok=True)
    dest = product_path(stem, ".jpg")
    if download_with_retry(url, dest, retries=retries):
        for ext in (".jpg", ".png", ".webp", ".gif"):
            cand = PRODUCTS_DIR / f"{safe_name(stem)}{ext}"
            if verify_image_file(cand):
                return cand
        if verify_image_file(dest):
            return dest
    return None
