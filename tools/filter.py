import re, sys, os
OUT = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work"
f = sys.argv[1]
path = os.path.join(OUT, f)
rows = []
for line in open(path, encoding="utf-8"):
    line = line.rstrip("\n")
    if not line:
        continue
    kind, addr, s = line.split("\t", 2)
    rows.append((int(addr, 16), kind, s))

# filter interesting
pat = re.compile(r"(\.dll|\.ini|\.log|\.dum|\.fnt|\.dds|\.exe|\\|/|%s|%d|%08|TOS|nvidia|nv|ati|amd|intel|hook|detour|patch|font|glyph|texture|render|present|device|swap|window|dinput|rail|steam|achievement|text|encoding|cp9|949|utf|uni)", re.I)
for addr, kind, s in sorted(rows):
    if pat.search(s):
        print("%08X %s %s" % (addr, kind, s))
