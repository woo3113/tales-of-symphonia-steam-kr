import re, os, zlib, collections, sys

BASE = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release\R01\WIN"
xml = open(os.path.join(BASE,"FILEHEADER.TOFHDB.debug"),"rb").read().decode("shift_jis","replace")
tldat = os.path.join(BASE,"TLFILE.TLDAT")

files = []
for m in re.finditer(r"<File>\s*<FileSize>\s*(\d+)\s*</FileSize>\s*<CompressSize>\s*(\d+)\s*</CompressSize>\s*<Offset>\s*(\d+)\s*</Offset>\s*<HashValue>\s*(\d+)\s*</HashValue>\s*<Extension>\s*\"([^\"]*)\"\s*</Extension>", xml):
    fs, cs, off, hv, ext = m.groups()
    files.append((int(fs), int(cs), int(off), int(hv), ext))
print("parsed files:", len(files))
exts = collections.Counter(f[4] for f in files)
for e,c in exts.most_common(40):
    print("  %-8s %d" % (e, c))

def get_entry(off, cs):
    with open(tldat,"rb") as fh:
        fh.seek(off); return fh.read(cs)

def decompress(data, outsize):
    # try raw deflate, zlib, gzip
    for wbits in (-15, 15, 31):
        try:
            return zlib.decompress(data, wbits)
        except Exception:
            pass
    # some entries may be stored with a small header
    try:
        return zlib.decompressobj(-15).decompress(data)
    except Exception:
        return None

# find CSV entries and check headers
csvs = [f for f in files if f[4].upper()=="CSV"]
print("CSV count:", len(csvs))
kr = 0; samples=[]
for fs, cs, off, hv, ext in csvs[:400]:
    raw = get_entry(off, cs)
    if cs != fs:
        d = decompress(raw, fs)
        if d is None: continue
    else:
        d = raw
    try:
        s = d[:400].decode("shift_jis","replace")
    except Exception:
        continue
    if "KR" in s.split("\n")[2] if len(s.split("\n"))>2 else False:
        kr += 1
    if "ID,JP" in s or "Language" in s:
        if len(samples)<5:
            samples.append(s[:300])
print("csv with KR-ish header:", kr)
for s in samples:
    print("-----")
    print(s)
