import pefile, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe = pefile.PE(TOS); D = pe.__data__; IMG = 0x400000
def va2off(v):
    r = v - IMG
    for s in pe.sections:
        if s.VirtualAddress <= r < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (r - s.VirtualAddress)
    return None
def cstr(v):
    o = va2off(v)
    e = D.find(b'\x00', o)
    return D[o:e]
for a in sys.argv[1:]:
    v = int(a, 16); b = cstr(v)
    try: s = b.decode('shift_jis')
    except: s = b.decode('latin1')
    print("%s -> %r" % (a, s))
