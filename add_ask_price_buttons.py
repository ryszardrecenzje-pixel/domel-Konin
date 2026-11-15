#!/usr/bin/env python3
"""Dodaje przycisk 'Zapytaj o cene' pod span.cena w kartach produktow."""
from __future__ import annotations
import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
CATEGORY_FILES = [
    "lodowki.html", "pralki.html", "zmywarki.html", "piekarniki.html",
    "male_agd.html", "male_AGD.html", "male_agd_1.html",
    "kuchenki.html", "plyty_grzewcze.html", "suszarki.html", "zamrazarki.html",
]
BTN_CSS = """
        .btn-ask {
            display: inline-block;
            margin-top: 0.6rem;
            padding: 0.45rem 0.9rem;
            background-color: #ff6600;
            color: #fff !important;
            border-radius: 4px;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
            transition: background 0.2s;
        }
        .btn-ask:hover { background-color: #e55a00; }
"""

def add_buttons(html: str) -> tuple[str, int]:
    count = 0
    parts = []
    last_h3 = ""
    for line in html.splitlines(keepends=True):
        hm = re.search(r"<h3[^>]*>(.*?)</h3>", line)
        if hm:
            last_h3 = re.sub(r"<[^>]+>", "", hm.group(1)).strip()
        if 'class="cena"' in line and "btn-ask" not in line and last_h3:
            if "</span>" in line:
                href = f"index.html?produkt={quote(last_h3)}#repair"
                line = line.replace(
                    "</span>",
                    f'</span>\n                <a class="btn btn-ask" href="{href}">Zapytaj o cenę</a>',
                    1,
                )
                count += 1
        parts.append(line)
    new_html = "".join(parts)
    if count and ".btn-ask" not in new_html:
        new_html = re.sub(r"(</style>)", BTN_CSS + r"\1", new_html, count=1)
    return new_html, count

def main() -> None:
    total = 0
    for fn in CATEGORY_FILES:
        p = ROOT / fn
        if not p.exists():
            print("SKIP missing", fn)
            continue
        text = p.read_text(encoding="utf-8")
        if 'class="cena"' not in text:
            print("SKIP no cena", fn)
            continue
        if "btn-ask" in text and text.count("btn-ask") >= text.count('class="cena"'):
            print("OK already", fn)
            continue
        new_text, n = add_buttons(text)
        p.write_text(new_text, encoding="utf-8")
        total += n
        print(f"{fn}: +{n}")
    print("TOTAL", total)

if __name__ == "__main__":
    main()
