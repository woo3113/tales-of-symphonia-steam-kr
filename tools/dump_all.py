import re, sys, os

BASE = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
OUT = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work"

def dump(rel):
    path = os.path.join(BASE, rel)
    data = open(path, "rb").read()
    name = rel.replace("\\", "_").replace("/", "_")
    outpath = os.path.join(OUT, name + ".strings.txt")
    lines = []
    # wide
    for m in re.finditer(rb"(?:[\x20-\x7e]\x00){4,}", data):
        s = m.group().decode("utf-16-le", "replace")
        lines.append("W\t%08X\t%s" % (m.start(), s))
    # ascii
    for m in re.finditer(rb"[\x20-\x7e]{5,}", data):
        s = m.group().decode("latin1")
        lines.append("A\t%08X\t%s" % (m.start(), s))
    open(outpath, "w", encoding="utf-8").write("\n".join(lines))
    print(outpath, len(lines))

for f in sys.argv[1:]:
    dump(f)
