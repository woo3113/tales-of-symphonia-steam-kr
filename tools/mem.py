import pefile, sys, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe = pefile.PE(TOS); D = pe.__data__; IMG = 0x400000
def va2off(v):
    r = v - IMG
    for s in pe.sections:
        if s.VirtualAddress <= r < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (r - s.VirtualAddress)
    return None
def show(v, n=64, label=""):
    o = va2off(v)
    print("=== %s 0x%X (off %s) ===" % (label, v, hex(o) if o else None))
    if o is None: return
    b = D[o:o+n]
    for i in range(0, n, 16):
        chunk = b[i:i+16]
        hexs = ' '.join('%02X' % c for c in chunk)
        fs = ' '.join('%+.3f' % struct.unpack_from('<f', chunk, j)[0] for j in range(0, len(chunk), 4) if len(chunk) >= j+4)
        print("  %08X  %-48s | %s" % (v+i, hexs, fs))
if __name__ == "__main__":
    for a in sys.argv[1:]:
        show(int(a, 16))
