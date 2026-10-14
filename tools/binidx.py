import re, os, sys, struct, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
reg = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
hdr = open(os.path.join(reg,"FILEHEADER.TOFHDB"),"rb").read()
xml = open(os.path.join(reg,"FILEHEADER.TOFHDB.debug"),"rb").read().decode("shift_jis","replace")
files=[]
for m in re.finditer(r"<File>\s*<FileSize>\s*(\d+)\s*</FileSize>\s*<CompressSize>\s*(\d+)\s*</CompressSize>\s*<Offset>\s*(\d+)\s*</Offset>\s*<HashValue>\s*(\d+)\s*</HashValue>\s*<Extension>\s*\"([^\"]*)\"\s*</Extension>", xml):
    fs,cs,off,hv,ext=m.groups(); files.append((int(fs),int(cs),int(off),int(hv),ext))
print("files", len(files))
HDR=40; FH=84385*8; FA=len(hdr)-HDR-FH
print("header",HDR,"filehash",FH,"filearray",FA,"rec",FA/len(files))
# header dump
print("header bytes:", hdr[:40].hex())
base=HDR+FH
for i in range(3):
    rec=hdr[base+40*i:base+40*(i+1)]
    fs,cs,off,hv,ext=files[i]
    print("--- rec %d expect fs=%d cs=%d off=%d hv=%d ext=%s"%(i,fs,cs,off,hv,ext))
    print("   bytes:", rec.hex())
    # u32 fields
    print("   u32s:", ["%d(0x%X)"%(struct.unpack_from('<I',rec,j)[0],struct.unpack_from('<I',rec,j)[0]) for j in range(0,40,4)])
    print("   ascii:", ''.join(chr(b) if 32<=b<127 else '.' for b in rec))
