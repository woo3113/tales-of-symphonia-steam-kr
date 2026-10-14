import re, os, zlib, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
xml = open(os.path.join(R,"FILEHEADER.TOFHDB.debug"),"rb").read().decode("shift_jis","replace")
entries=[]
for m in re.finditer(r"<File>\s*<FileSize>\s*(\d+)\s*</FileSize>\s*<CompressSize>\s*(\d+)\s*</CompressSize>\s*<Offset>\s*(\d+)\s*</Offset>\s*<HashValue>\s*(\d+)\s*</HashValue>\s*<Extension>\s*\"([^\"]*)\"\s*</Extension>", xml):
    fs,cs,off,hv,ext = m.groups()
    entries.append(dict(fs=int(fs),cs=int(cs),off=int(off),hv=int(hv),ext=ext))

def read(off, cs):
    with open(os.path.join(R,"TLFILE.TLDAT"),"rb") as f:
        f.seek(off); return f.read(cs)

def dec(data, outsize):
    for wb in (-15,15,31,-14):
        try: return zlib.decompress(data, wb)
        except Exception: pass
    try:
        d=zlib.decompressobj(-15)
        out=d.decompress(data)
        return out
    except Exception: return None

for ext in ["TLFNTB_D","TLCLRB","TLPICB_D","TOSHDB","PAK","TOSBIN"]:
    for e in entries:
        if e["ext"]==ext:
            raw = read(e["off"], e["cs"])
            if e["cs"] == e["fs"]:
                data = raw; comp="none"
            else:
                data = dec(raw, e["fs"]); comp="defl"
            print("=== %s fs=%d cs=%d off=%d hv=%d comp=%s declen=%s" % (ext,e["fs"],e["cs"],e["off"],e["hv"],comp, len(data) if data else None))
            if data:
                d = data
                # hex + ascii head
                for i in range(0,min(160,len(d)),16):
                    print("   %06X  %s  %s" % (i, " ".join("%02x"%b for b in d[i:i+16]), "".join(chr(b) if 32<=b<127 else "." for b in d[i:i+16])))
                # ascii strings
                ss=[s.decode('latin1') for s in re.findall(rb"[\x20-\x7e]{4,}", d[:2000])]
                print("   strings:", ss[:30])
            break
