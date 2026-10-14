import re, os, sys, zlib, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REG = {  # region -> (debug xml path, tldat path)
}
def parse(region_dir, out_json):
    xmlp = os.path.join(region_dir, "FILEHEADER.TOFHDB.debug")
    tlp = os.path.join(region_dir, "TLFILE.TLDAT")
    xml = open(xmlp, "rb").read().decode("shift_jis", "replace")
    entries = []
    for i, m in enumerate(re.finditer(r"<File>\s*<FileSize>\s*(\d+)\s*</FileSize>\s*<CompressSize>\s*(\d+)\s*</CompressSize>\s*<Offset>\s*(\d+)\s*</Offset>\s*<HashValue>\s*(\d+)\s*</HashValue>\s*<Extension>\s*\"([^\"]*)\"\s*</Extension>", xml)):
        fs, cs, off, hv, ext = m.groups()
        entries.append(dict(idx=i, fs=int(fs), cs=int(cs), off=int(off), hv=int(hv), ext=ext))
    json.dump(entries, open(out_json, "w", encoding="utf-8"), ensure_ascii=False)
    print("parsed", len(entries), "->", out_json)
    return entries, xmlp, tlp

def dec(tlp, off, cs, fs):
    with open(tlp, "rb") as f:
        f.seek(off); d = f.read(cs)
    if cs == fs: return d
    if d[:4] == b"TLZC":
        try: return zlib.decompress(d[24:], -15)
        except Exception: return None
    return None

if __name__ == "__main__":
    region_dir = sys.argv[1]
    out_json = sys.argv[2]
    entries, xmlp, tlp = parse(region_dir, out_json)
    # summary by ext
    from collections import Counter
    print(Counter(e["ext"] for e in entries).most_common(40))
    # extract named-ish key entries into files
    outdir = os.path.join(os.path.dirname(out_json), "entries")
    os.makedirs(outdir, exist_ok=True)
    for e in entries:
        if e["ext"] in ("TLFNTB_D","TLCLRB","TLPICB_D","TXB","CSV","TXT","PAK"):
            d = dec(tlp, e["off"], e["cs"], e["fs"])
            if d is None:
                print("  (fail decomp)", e["ext"], e["hv"]); continue
            fn = os.path.join(outdir, "%s_%d_%d.bin" % (e["ext"], e["hv"], e["fs"]))
            open(fn, "wb").write(d)
            print("  saved", fn)
