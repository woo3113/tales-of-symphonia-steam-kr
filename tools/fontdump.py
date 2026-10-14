import re, os, sys, zlib, binascii
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
def raw(off, cs):
    with open(os.path.join(R,"TLFILE.TLDAT"),"rb") as f:
        f.seek(off); return f.read(cs)
xml = open(os.path.join(R,"FILEHEADER.TOFHDB.debug"),"rb").read().decode("shift_jis","replace")
entries=[]
for m in re.finditer(r"<File>\s*<FileSize>\s*(\d+)\s*</FileSize>\s*<CompressSize>\s*(\d+)\s*</CompressSize>\s*<Offset>\s*(\d+)\s*</Offset>\s*<HashValue>\s*(\d+)\s*</HashValue>\s*<Extension>\s*\"([^\"]*)\"\s*</Extension>", xml):
    fs,cs,off,hv,ext = m.groups()
    entries.append(dict(fs=int(fs),cs=int(cs),off=int(off),hv=int(hv),ext=ext))
e=[x for x in entries if x["ext"]=="TLFNTB_D"][0]
d=raw(e["off"],e["cs"])
out=zlib.decompress(d[24:],-15)
open(os.path.join(r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work","TLFNTB_D.bin"),"wb").write(out)
print("font bank size", len(out))
for i in range(0,320,16):
    print("  %06X  %s  %s" % (i," ".join("%02x"%b for b in out[i:i+16]),"".join(chr(b) if 32<=b<127 else "." for b in out[i:i+16])))
print("strings:", [s.decode('latin1') for s in re.findall(rb"[\x20-\x7e]{3,}", out)][:60])
# search pattern in TOS.exe
pat = bytes.fromhex("B98000000066 3BC1 732F 83E07F 83F820 7705".replace(" ",""))
tos = open(r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe","rb").read()
i = tos.find(pat)
print("AOB pattern in TOS.exe:", i, hex(i) if i>=0 else "")
# also search korfnt pattern bytes
