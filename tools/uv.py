import struct, os, zlib, sys, pefile, capstone
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ORIG_TL=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN\TLFILE.TLDAT"
PATCH_TL=r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN\TLFILE.TLDAT"
def parse(header):
    d=open(header,"rb").read(); base=40+84385*8; m={}
    for i in range((len(d)-base)//40):
        o=base+40*i
        fs,cs,off,hv=struct.unpack_from("<QQQI", d, o)
        ext=d[o+28:o+36].split(b"\x00")[0].decode("latin1")
        m[hv]=dict(fs=fs,cs=cs,off=off,hv=hv,ext=ext)
    return m
oi=parse(r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN\FILEHEADER.TOFHDB")
pi=parse(r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\patch\P12E\Data\TOS_Server\Archive\Release\R01\WIN\FILEHEADER.TOFHDB")
def get(tl,r):
    with open(tl,"rb") as f: f.seek(r["off"]); d=f.read(r["cs"])
    if r["cs"]==r["fs"]: return d
    return zlib.decompress(d[24:],-15) if d[:4]==b"TLZC" else None
# compare PAL_FONTB0 descriptor (hv=3085532135) and neighbors orig vs patch
for hv,label in [(3085532135,"PAL_FONTB0 desc"),(352725726,"after-atlas desc SAND"),(356323291,"after-atlas pic")]:
    a=get(ORIG_TL,oi[hv]); b=get(PATCH_TL,pi[hv])
    same = (a==b)
    print("%-20s hv=%d same=%s"%(label,hv,same))
    if not same:
        print("   orig :",a.hex())
        print("   patch:",b.hex())
# disasm UV function
TOS=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe=pefile.PE(TOS); D=pe.__data__; IMG=0x400000
def va2off(v):
    r=v-IMG
    for s in pe.sections:
        if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData):
            return s.PointerToRawData+(r-s.VirtualAddress)
print("\n=== slot->UV 0x578737 ===")
md=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
o=va2off(0x578737)
for ins in md.disasm(D[o:o+120], 0x578737):
    print("  %08X  %-8s %s"%(ins.address,ins.mnemonic,ins.op_str))
