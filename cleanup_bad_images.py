#!/usr/bin/env python3
"""Usuwa oczywiste złe zdjęcia z images/magazyn (odznaki, TV, dokumenty)."""
from pathlib import Path

OUT = Path("images/magazyn")
# proste heurystyki po nazwie / rozmiarze + lista znanych złych wzorców w nazwie nie działa
# więc: użytkownik może też ręcznie usunąć – tu usuwamy bardzo małe i podejrzane rozszerzenia dokumentów

removed = []
for p in OUT.iterdir():
    if not p.is_file():
        continue
    try:
        data = p.read_bytes()
    except Exception:
        continue
    low = p.name.lower()
    # za małe
    if len(data) < 15000:
        p.unlink()
        removed.append(p.name + " (mały)")
        continue
    # webp będące skanem / dokumentem – trudno wykryć; zostawiamy decyzję wizualną
print("Usunięto:", len(removed))
for r in removed:
    print(" ", r)
print("Przejrzyj ręcznie images/magazyn i usuń odznaki / TV / dokumenty.")
print("Potem: python download_images_producers.py --headed")
print("(skrypt pominie już dobre pliki)")
