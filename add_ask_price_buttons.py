#!/usr/bin/env python3
"""
Zamiast linku do formularza – przycisk „Dodaj do koszyka” (cart.js / data-add-to-cart).
Usuwa stare linki .btn-ask jeśli są.
"""
from __future__ import annotations
import re
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parent
CATEGORY_FILES = [
    "lodowki.html", "pralki.html", "zmywarki.html", "piekarniki.html",
    "male_agd.html", "male_AGD.html", "male_agd_1.html",
    "kuchenki.html", "plyty_grzewcze.html", "suszarki.html", "zamrazarki.html",
]


def make_button(title: str, price: str = "Cena na zapytanie") -> str:
    t = escape(title, quote=True)
    p = escape(price, quote=True)
    return (
        f'<button type="button" class="btn-add-cart" data-add-to-cart '
        f'data-title="{t}" data-price="{p}">'
        f'\n                    <i class="fa-solid fa-cart-plus"></i> Dodaj do koszyka'
        f'\n                </button>'
    )


def process(html: str) -> tuple[str, int]:
    html = re.sub(
        r'\s*<a\s+class="btn btn-ask"[^>]*>.*?</a>',
        "",
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )

    count = 0
    parts = []
    last_h3 = ""
    last_price = "Cena na zapytanie"

    for line in html.splitlines(keepends=True):
        hm = re.search(r"<h3[^>]*>(.*?)</h3>", line)
        if hm:
            last_h3 = re.sub(r"<[^>]+>", "", hm.group(1)).strip()

        cm = re.search(r'<span class="cena">([^<]*)</span>', line)
        if cm:
            last_price = cm.group(1).strip() or "Cena na zapytanie"
            if "data-add-to-cart" not in line and last_h3:
                if "</span>" in line:
                    line = line.replace(
                        "</span>",
                        "</span>\n                " + make_button(last_h3, last_price),
                        1,
                    )
                    count += 1
        parts.append(line)

    new_html = "".join(parts)

    if "cart.js" not in new_html and "</body>" in new_html:
        new_html = new_html.replace(
            "</body>",
            '    <script src="cart.js"></script>\n</body>',
            1,
        )

    if 'href="koszyk.html"' not in new_html and "</nav>" in new_html:
        nav_item = (
            '                <li><a href="koszyk.html" class="cart-link">'
            'KOSZYK <span class="cart-badge" data-cart-count>0</span></a></li>\n'
        )
        if "</ul>\n        </nav>" in new_html:
            new_html = new_html.replace(
                "</ul>\n        </nav>",
                nav_item + "            </ul>\n        </nav>",
                1,
            )
        elif 'href="koszyk.html"' not in new_html:
            new_html = new_html.replace("</nav>", nav_item + "        </nav>", 1)

    return new_html, count


def main() -> None:
    total = 0
    for fn in CATEGORY_FILES:
        p = ROOT / fn
        if not p.exists():
            print("SKIP missing", fn)
            continue
        text = p.read_text(encoding="utf-8")
        if 'class="cena"' not in text and "btn-ask" not in text:
            print("SKIP no products", fn)
            continue
        new_text, n = process(text)
        if new_text != text:
            p.write_text(new_text, encoding="utf-8")
            total += n
            print(f"{fn}: +{n} cart buttons")
        else:
            print(f"{fn}: no change")
    print("TOTAL", total)


if __name__ == "__main__":
    main()
