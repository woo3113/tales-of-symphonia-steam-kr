import struct, sys, zlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ORIG_TL = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN\TLFILE.TLDAT"
ORIG_H = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN\FILEHEADER.TOFHDB"
def parse(header):
    d = open(header, "rb").read(); base = 40 + 84385*8; recs = []
    for i in range((len(d)-base)//40):
        o = base + 40*i
        fs, cs, off, hv = struct.unpack_from("<QQQI", d, o)
        ext = d[o+28:o+36].split(b"\x00")[0].decode("latin1")
        recs.append(dict(i=i, fs=fs, cs=cs, off=off, hv=hv, ext=ext))
    return recs
def get(tl, r):
    with open(tl, "rb") as f:
        f.seek(r["off"]); d = f.read(r["cs"])
    if r["cs"] == r["fs"]: return d
    return zlib.decompress(d[24:], -15) if d[:4] == b"TLZC" else None
recs = parse(ORIG_H)
for r in recs:
    if 83355 <= r["i"] <= 83370:
        data = get(ORIG_TL, r)
        n = len(data) if data else -1
        hx = data[:64].hex() if data else ""
        print("idx %5d %-9s fs %-9d cs %-8d off %d  n=%d" % (r["i"], r["ext"], r["fs"], r["cs"], r["off"], n))
        if r["ext"] == "TOTEXB_D":
            print("     hex:", hx)
            # try to interpret as u16/u32
            if data:
                print("     u32:", [hex(x) for x in struct.unpack_from("<%dI" % (len(data)//4), data, 0)])
