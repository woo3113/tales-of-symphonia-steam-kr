import pefile, sys, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe = pefile.PE(TOS); D = pe.__data__; IMG = 0x400000
def off2va(o):
    for s in pe.sections:
        if s.PointerToRawData <= o < s.PointerToRawData + s.SizeOfRawData:
            return IMG + s.VirtualAddress + (o - s.PointerToRawData)
    return None
def va2off(v):
    r = v - IMG
    for s in pe.sections:
        if s.VirtualAddress <= r < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (r - s.VirtualAddress)
    return None
# find any occurrence of the 4-byte address followed by anything -> list instruction bytes
for a in sys.argv[1:]:
    t = struct.pack('<I', int(a, 16))
    print("### refs to %s" % a)
    i = 0
    while True:
        i = D.find(t, i)
        if i < 0: break
        va = off2va(i)
        # dump a few bytes before to see instruction
        pre = D[max(0,i-8):i+7]
        print("  at fileoff %X va %s  pre=%s" % (i, hex(va) if va else None, pre.hex()))
        i += 1
