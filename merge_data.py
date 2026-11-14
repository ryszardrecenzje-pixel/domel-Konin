import json, glob, os
items = []
for f in sorted(glob.glob('data/*.json')):
    with open(f, encoding='utf-8') as fh:
        items.append(json.load(fh))
with open('magazyn.json', 'w', encoding='utf-8') as fh:
    json.dump(items, fh, ensure_ascii=False, indent=2)
print('merged', len(items))
