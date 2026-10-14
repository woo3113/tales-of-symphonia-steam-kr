import pefile, os, math, sys
BASE = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
def ent(b):
    if not b: return 0
    from collections import Counter
    c = Counter(b); n=len(b)
    return -sum((v/n)*math.log2(v/n) for v in c.values())
for rel in sys.argv[1:]:
    p = os.path.join(BASE, rel)
    pe = pefile.PE(p)
    print("###", rel)
    for s in pe.sections:
        name = s.Name.rstrip(b"\x00").decode("latin1")
        d = s.get_data()
        print("  %-10s VS=%08X RS=%08X entropy=%.2f" % (name, s.Misc_VirtualSize, s.SizeOfRawData, ent(d[:200000])))
