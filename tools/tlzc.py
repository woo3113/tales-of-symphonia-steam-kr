import re, os, sys, zlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
R = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
xml = open(os.path.join(R,"FILEHEADER.TOFHDB.debug"),"rb").read().decode("shift_jis","replace")
entries=[]
for m in re.finditer(r"<File>\s*<FileSize>\s*(\d+)\s*</FileSize>\s*<CompressSize>\s*(\d+)\s*</CompressSize>\s*<Offset>\s*(\d+)\s*</Offset>\s*<HashValue>\s*(\d+)\s*</HashValue>\s*<Extension>\s*\"([^\"]*)\"\s*</Extension>", xml):
    fs,cs,off,hv,ext = m.groups()
    entries.append(dict(fs=int(fs),cs=int(cs),off=int(off),hv=int(hv),ext=ext))
def raw(off, cs):
    with open(os.path.join(R,"TLFILE.TLDAT"),"rb") as f:
        f.seek(off); return f.read(cs)

e = [x for x in entries if x["ext"]=="TLFNTB_D"][0]
d = raw(e["off"], e["cs"])
print("TLFNTB_D hdr:", d[:24].hex())
for start in [20,22,24,28,32]:
    for wb in (-15,15,31):
        try:
            out = zlib.decompress(d[start:], wb)
            if len(out)==e["fs"]:
                print("OK start=%d wb=%d len=%d (expected %d)" % (start,wb,len(out),e["fs"]))
                print("  head:", out[:64].hex())
                print("  ascii:", ''.join(chr(b) if 32<=b<127 else '.' for b in out[:120]))
                break
        except Exception as ex:
            pass
    else:
        continue
    break
else:
    print("no deflate variant matched; trying lz4")
    try:
        import lz4.block
        for start in [16,20,24]:
            try:
                out = lz4.block.decompress(d[start:], uncompressed_size=e["fs"])
                print("LZ4 OK start",start,len(out))
                break
            except Exception as ex: print("lz4",start,ex)
    except Exception as ex:
        print("lz4 fail", ex)
