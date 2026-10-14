import re, sys, os

BASE = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"

def strings(data, minlen=4, wide=True):
    out = []
    if wide:
        for m in re.finditer(rb"(?:[\x20-\x7e]\x00){%d,}" % minlen, data):
            out.append(("W", m.group().decode("utf-16-le", "replace")))
    for m in re.finditer(rb"[\x20-\x7e]{%d,}" % minlen, data):
        out.append(("A", m.group().decode("latin1")))
    return out

rel = sys.argv[1]
path = os.path.join(BASE, rel)
data = open(path, "rb").read()
filters = sys.argv[2:]
print("###", rel, "size", len(data))
seen = set()
for kind, s in strings(data):
    if kind == "A":
        continue  # ascii substring of wide too; keep wide+ascii dedup
    key = s
    if key in seen:
        continue
    seen.add(key)
    if filters and not any(f.lower() in s.lower() for f in filters):
        continue
    print(kind, s)
# also ascii-only uniques not in wide
seen2 = set()
for kind, s in strings(data):
    if kind != "A":
        continue
    if s in seen or s in seen2:
        continue
    seen2.add(s)
    if filters and not any(f.lower() in s.lower() for f in filters):
        continue
    print("A", s)
