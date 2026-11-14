#!/usr/bin/env python3
"""
Zmienia niebezpieczne nazwy plikow (#, ?, spacje, nawiasy, polskie znaki) na bezpieczne (_).
Aktualizuje sciezki w produkty.json oraz plikach HTML/JS/JSON.
Uruchom w katalogu repozytorium: python fix_safe_filenames.py
"""
from __future__ import annotations

import json
import re
import shutil
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent

PL = str.maketrans({
    "ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n", "ó": "o", "ś": "s", "ź": "z", "ż": "z",
    "Ą": "A", "Ć": "C", "Ę": "E", "Ł": "L", "Ń": "N", "Ó": "O", "Ś": "S", "Ź": "Z", "Ż": "Z",
})


def safe_name(text: str) -> str:
    """Bezpieczna nazwa: #, ?, spacje, nawiasy, polskie znaki -> _ / ASCII."""
    text = (text or "").translate(PL)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    for ch in (
        "#", "?", " ", "/", "\\", ":", "*", '"', "<", ">", "|",
        "(", ")", "[", "]", "{", "}", "'", ",", ";", "&", "%", "+", "=", ".",
    ):
        text = text.replace(ch, "_")
    text = re.sub(r"[^\w\-]+", "_", text, flags=re.UNICODE)
    text = re.sub(r"_+", "_", text)
    return text[:90].strip("._") or "plik"


def convert_image_path(old: str) -> str:
    old = old.replace("\\", "/")
    markers = (
        "images/zdjęcia produktów/",
        "images/zdjecia produktow/",
        "images/zdjecia_produktow/",
    )
    rest = None
    for m in markers:
        if old.startswith(m):
            rest = old[len(m):]
            break
    if rest is None:
        if re.search(r"images/[^/]*zdj", old):
            m = re.search(r"images/[^/]+/(.+)$", old)
            if m:
                rest = m.group(1)
            else:
                return old
        else:
            return old
    parts = []
    segs = rest.split("/")
    for i, part in enumerate(segs):
        if i == len(segs) - 1 and "." in part:
            stem, suf = part.rsplit(".", 1)
            parts.append(safe_name(stem) + "." + suf.lower())
        else:
            parts.append(safe_name(part))
    return "images/zdjecia_produktow/" + "/".join(parts)


def rename_tree() -> dict:
    mapping = {}

    src = ROOT / "male_agd (1).html"
    if src.exists():
        dst = ROOT / "male_agd_1.html"
        src.rename(dst)
        mapping["male_agd (1).html"] = "male_agd_1.html"
        print("HTML:", src.name, "->", dst.name)

    old_root = ROOT / "images" / "zdjęcia produktów"
    new_root = ROOT / "images" / "zdjecia_produktow"

    if old_root.exists():
        for f in sorted(old_root.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(old_root)
            safe_parts = []
            for i, part in enumerate(rel.parts):
                if i == len(rel.parts) - 1 and "." in part:
                    stem, suf = part.rsplit(".", 1)
                    safe_parts.append(safe_name(stem) + "." + suf.lower())
                else:
                    safe_parts.append(safe_name(part))
            dest = new_root.joinpath(*safe_parts)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dest)
            old_rel = str(Path("images") / "zdjęcia produktów" / rel).replace("\\", "/")
            new_rel = str(Path("images") / "zdjecia_produktow" / Path(*safe_parts)).replace("\\", "/")
            mapping[old_rel] = new_rel
            print("IMG:", old_rel, "->", new_rel)
        shutil.rmtree(old_root)
        print("Usunieto images/zdjecia produktow (stare)")

    promo = ROOT / "images" / "promocje"
    if promo.exists():
        for f in list(promo.iterdir()):
            if not f.is_file():
                continue
            sn = safe_name(f.stem) + f.suffix.lower()
            if sn != f.name:
                dest = f.with_name(sn)
                if not dest.exists():
                    f.rename(dest)
                    mapping[f"images/promocje/{f.name}"] = f"images/promocje/{sn}"
                    print("PROMO:", f.name, "->", sn)

    return mapping


def update_text_refs() -> int:
    count = 0
    text_exts = {".html", ".js", ".json", ".css", ".md", ".yml", ".bat", ".txt"}
    for f in ROOT.rglob("*"):
        if not f.is_file() or f.suffix.lower() not in text_exts:
            continue
        if ".git" in f.parts:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        orig = text
        text = text.replace("images/zdjęcia produktów/", "images/zdjecia_produktow/")
        text = text.replace("male_agd (1).html", "male_agd_1.html")

        def repl(m):
            path = m.group(1)
            if " " in path or "(" in path or "zdjęcia" in path:
                return m.group(0).replace(path, convert_image_path(path))
            return m.group(0)

        text = re.sub(r"(?:src|href)=[\"']([^\"']+)[\"']", repl, text)

        if f.name == "produkty.json":
            try:
                data = json.loads(text)
                for _cat, items in data.items():
                    for item in items:
                        if "zdjecia" in item:
                            item["zdjecia"] = [convert_image_path(z) for z in item["zdjecia"]]
                text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
            except Exception as e:
                print("produkty.json parse error:", e)

        if text != orig:
            f.write_text(text, encoding="utf-8")
            count += 1
            print("REF:", f.relative_to(ROOT))
    return count


def main() -> None:
    print("=== fix_safe_filenames ===")
    mapping = rename_tree()
    n = update_text_refs()
    (ROOT / "rename_mapping.json").write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Gotowe. Renames={len(mapping)}, pliki tekstowe={n}")


if __name__ == "__main__":
    main()
