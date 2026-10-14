import json, sys, os, zlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

orig = json.load(open(sys.argv[1], encoding="utf-8"))
patch = json.load(open(sys.argv[2], encoding="utf-8"))
o = {e["hv"]: e for e in orig}
p = {e["hv"]: e for e in patch}
print("orig entries", len(orig), "patch entries", len(patch))
only_o = set(o) - set(p)
only_p = set(p) - set(o)
print("only in orig:", len(only_o), " only in patch:", len(only_p))

from collections import Counter
print("only-patch exts:", Counter(p[h]["ext"] for h in only_p).most_common(20))
print("only-orig exts:", Counter(o[h]["ext"] for h in only_o).most_common(20))

changed = []
for h in set(o) & set(p):
    a, b = o[h], p[h]
    if a["fs"] != b["fs"] or a["ext"] != b["ext"]:
        changed.append((h, a, b))
print("changed (same hv, diff size/ext):", len(changed))
cext = Counter(a["ext"] for _, a, _ in changed)
print("changed exts:", cext.most_common(30))

# details for key exts
for h, a, b in changed:
    if a["ext"] in ("TLFNTB_D","TLCLRB","TXB","CSV","TXT","TOTEXB_D","PAC","TOSBIN","TOSHDB","PAK"):
        print("  CHG %-10s hv=%-12d fs %d -> %d  cs %d -> %d" % (a["ext"], h, a["fs"], b["fs"], a["cs"], b["cs"]))
