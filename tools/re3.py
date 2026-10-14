import pefile, struct, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe = pefile.PE(TOS)
D = pe.__data__
IMG = pe.OPTIONAL_HEADER.ImageBase
print("ImageBase", hex(IMG))
for s in pe.sections:
    print("  %-8s VA=%08X VS=%08X RAW=%08X" % (s.Name.rstrip(b'\x00').decode('latin1'), s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData))

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

# dump table 0x8AD868 as big-endian u16 for ASCII range
print("=== table 0x8AD868 (BE u16) for c=0x20..0x7F ===")
o = va2off(0x8AD868)
print("file offset", hex(o) if o else None)
if o:
    vals=[]
    for c in range(0x20,0x80):
        b0,b1 = D[o+2*c], D[o+2*c+1]
        vals.append((c,(b0<<8)|b1))
    for i in range(0,96,8):
        print("  ", " ".join("'%s'=%04X"%(chr(c),v) for c,v in vals[i:i+8]))

# xrefs to strings
def str_va(s):
    b=s.encode('latin1'); i=D.find(b)
    return off2va(i) if i>=0 else None
for nm in ["TLFNTB_D","fontb0.dat","FontData.pac","PAL_FONTB0.TOTEXB_D","NUMERALFONTTEX_PIC000"]:
    v=str_va(nm)
    print("string %-24s VA=%s"%(nm, hex(v) if v else None))
    if v:
        # search code for immediate (E8-free) push imm32 referencing full VA, and lea
        tgt=(IMG+v).to_bytes(4,'little')
        hits=[off2va(i) for i in range(0,len(D)-4) if D[i:i+4]==tgt]
        print("     xrefs:", [hex(h) for h in hits[:10]], "count", len(hits))
