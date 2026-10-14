import pefile, sys, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe = pefile.PE(TOS); D = pe.__data__; IMG = 0x400000
def off2va(o):
    for s in pe.sections:
        if s.PointerToRawData <= o < s.PointerToRawData + s.SizeOfRawData:
            return IMG + s.VirtualAddress + (o - s.PointerToRawData)
    return None
# restrict to executable section
exec_lo = exec_hi = None
for s in pe.sections:
    if s.Characteristics & 0x20000000:
        exec_lo = s.PointerToRawData; exec_hi = s.PointerToRawData + s.SizeOfRawData
        print("# exec section", s.Name, hex(exec_lo), hex(exec_hi))
def scan(pat, label):
    i = exec_lo
    hits = []
    while True:
        i = D.find(pat, i, exec_hi)
        if i < 0: break
        hits.append(off2va(i)); i += 1
    print("%s (%s): %s" % (label, pat.hex(), [hex(h) for h in hits[:60]]))
vals = [int(x, 0) for x in sys.argv[1:]]
for v in vals:
    scan(struct.pack('<I', v), "imm32 %d" % v)
    if v < 0x10000:
        scan(struct.pack('<H', v), "imm16 %d" % v)
