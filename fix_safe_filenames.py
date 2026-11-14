#!/usr/bin/env python3
"""
Zmienia niebezpieczne nazwy PLIKOW i KATALOGOW (#, ?, spacje, nawiasy, polskie znaki) na bezpieczne (_).
Aktualizuje sciezki w produkty.json oraz plikach HTML/JS/JSON.
Usuwa stare, uszkodzone katalogi-duplikaty (zle kodowanie UTF-8).
Uruchom: python fix_safe_filenames.py
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

SAFE_RE = re.compile(r"^[A-Za-z0-9_\-]+$")
SAFE_FILE_RE = re.compile(r"^[A-Za-z0-9_\-.]+$")


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


def is_safe_dir_name(name: str) -> bool:
    return bool(SAFE_RE.match(name))


def is_safe_file_name(name: str) -> bool:
    return bool(SAFE_FILE_RE.match(name))


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


def remove_corrupt_image_trees() -> int:
    """Usuwa stare katalogi z uszkodzonym kodowaniem (duplikaty)."""
    images = ROOT / "images"
    if not images.exists():
        return 0
    removed = 0
    keep = {"categories", "magazyn", "promocje", "zdjecia_produktow"}
    for child in list(images.iterdir()):
        if not child.is_dir():
            continue
        name = child.name
        if name in keep:
            continue
        if not is_safe_dir_name(name) or name.startswith("zdj"):
            print("USUWAM uszkodzony katalog:", child.relative_to(ROOT))
            shutil.rmtree(child, ignore_errors=True)
            removed += 1
    return removed


def rename_unsafe_under(base: Path) -> dict:
    """Rekurencyjnie zmienia niebezpieczne nazwy katalogow i plikow."""
    mapping = {}
    if not base.exists():
        return mapping

    dirs = sorted(
        [p for p in base.rglob("*") if p.is_dir()],
        key=lambda p: len(p.parts),
        reverse=True,
    )
    for d in dirs:
        if is_safe_dir_name(d.name):
            continue
        new_name = safe_name(d.name)
        dest = d.parent / new_name
        if dest.exists() and dest != d:
            for item in d.iterdir():
                target = dest / item.name
                if not target.exists():
                    shutil.move(str(item), str(target))
            shutil.rmtree(d, ignore_errors=True)
            print("MERGE dir:", d.relative_to(ROOT), "->", dest.relative_to(ROOT))
        else:
            old_rel = str(d.relative_to(ROOT)).replace("\\", "/")
            d.rename(dest)
            new_rel = str(dest.relative_to(ROOT)).replace("\\", "/")
            mapping[old_rel] = new_rel
            print("DIR:", old_rel, "->", new_rel)

    for f in list(base.rglob("*")):
        if not f.is_file():
            continue
        if is_safe_file_name(f.name):
            continue
        if f.name in {".a", "a."} or f.name.startswith("."):
            try:
                f.unlink()
                print("DEL junk:", f.relative_to(ROOT))
            except Exception:
                pass
            continue
        stem, suf = f.stem, f.suffix
        new_name = safe_name(stem) + (suf.lower() if suf else "")
        dest = f.with_name(new_name)
        if dest.exists() and dest != f:
            f.unlink()
            print("DEL dup:", f.relative_to(ROOT))
            continue
        old_rel = str(f.relative_to(ROOT)).replace("\\", "/")
        f.rename(dest)
        new_rel = str(dest.relative_to(ROOT)).replace("\\", "/")
        mapping[old_rel] = new_rel
        print("FILE:", old_rel, "->", new_rel)

    return mapping


def rename_tree() -> dict:
    mapping = {}

    src = ROOT / "male_agd (1).html"
    if src.exists():
        dst = ROOT / "male_agd_1.html"
        src.rename(dst)
        mapping["male_agd (1).html"] = "male_agd_1.html"
        print("HTML:", src.name, "->", dst.name)

    n = remove_corrupt_image_trees()
    print(f"Usunieto {n} uszkodzonych katalogow")

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
        shutil.rmtree(old_root, ignore_errors=True)
        print("Usunieto images/zdjecia produktow (stare)")

    images = ROOT / "images"
    if images.exists():
        mapping.update(rename_unsafe_under(images))

    for f in list(ROOT.iterdir()):
        if f.is_file() and not is_safe_file_name(f.name) and f.suffix.lower() in {".html", ".htm", ".json", ".js", ".css"}:
            if f.name.startswith("."):
                continue
            new_name = safe_name(f.stem) + f.suffix.lower()
            dest = f.with_name(new_name)
            if not dest.exists():
                f.rename(dest)
                mapping[f.name] = new_name
                print("ROOT FILE:", f.name, "->", new_name)

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
            if " " in path or "(" in path or "zdjęcia" in path or "#" in path:
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

        if f.name in {"promocje.json", "magazyn.json"}:
            try:
                def fix_path_in_json(s: str) -> str:
                    def sub(m):
                        p = m.group(1)
                        if any(ord(c) > 127 for c in p) or " " in p or "(" in p:
                            parts = p.replace("\\", "/").split("/")
                            out = []
                            for i, part in enumerate(parts):
                                if i == len(parts) - 1 and "." in part:
                                    stem, suf = part.rsplit(".", 1)
                                    out.append(safe_name(stem) + "." + suf.lower())
                                elif i == 0 and part == "images":
                                    out.append(part)
                                elif i == 1 and is_safe_dir_name(part):
                                    out.append(part)
                                else:
                                    out.append(safe_name(part))
                            return '"' + "/".join(out) + '"'
                        return m.group(0)
                    return re.sub(r'"((?:images/)[^"]+)"', sub, s)

                text = fix_path_in_json(text)
                try:
                    text = json.dumps(json.loads(text), ensure_ascii=False, indent=2) + "\n"
                except Exception:
                    pass
            except Exception as e:
                print(f.name, "error:", e)

        if text != orig:
            f.write_text(text, encoding="utf-8")
            count += 1
            print("REF:", f.relative_to(ROOT))
    return count


def main() -> None:
    print("=== fix_safe_filenames (pliki + katalogi) ===")
    mapping = rename_tree()
    n = update_text_refs()
    (ROOT / "rename_mapping.json").write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    bad = []
    images = ROOT / "images"
    if images.exists():
        for p in images.rglob("*"):
            if p.is_dir() and not is_safe_dir_name(p.name):
                bad.append(str(p.relative_to(ROOT)))
            if p.is_file() and not is_safe_file_name(p.name) and p.name not in {".gitkeep"}:
                bad.append(str(p.relative_to(ROOT)))
    if bad:
        print("UWAGA - nadal niebezpieczne:")
        for b in bad:
            print(" ", b)
    else:
        print("OK: wszystkie katalogi i pliki pod images/ sa bezpieczne")
    print(f"Gotowe. Renames={len(mapping)}, pliki tekstowe={n}")


if __name__ == "__main__":
    main()
