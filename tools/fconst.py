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
def off2va(o):
    for s in pe.sections:
        if s.PointerToRawData <= o < s.PointerToRawData + s.SizeOfRawData:
            return IMG + s.VirtualAddress + (o - s.PointerToRawData)
    return None
def find_f32(val):
    t = struct.pack('<f', val); res=[]; i=0
    while True:
        i = D.find(t, i)
        if i < 0: break
        res.append(off2va(i)); i += 1
    return res
def find_f64(val):
    t = struct.pack('<d', val); res=[]; i=0
    while True:
        i = D.find(t, i)
        if i < 0: break
        res.append(off2va(i)); i += 1
    return res
def find_u32(val):
    t = struct.pack('<I', val); res=[]; i=0
    while True:
        i = D.find(t, i)
        if i < 0: break
        res.append(off2va(i)); i += 1
    return res
for v in sys.argv[1:]:
    val = float(v)
    print("f32 %s -> %s" % (v, [hex(x) for x in find_f32(val)]))
    print("f64 %s -> %s" % (v, [hex(x) for x in find_f64(val)]))
