import re, os, collections, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
base = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release"
for r in ["R01","R02","R03","R04","R05"]:
    p = os.path.join(base, r, "WIN", "FILEHEADER.TOFHDB.debug")
    if not os.path.exists(p): continue
    xml = open(p,"rb").read().decode("shift_jis","replace")
    exts = collections.Counter(re.findall(r'<Extension>\s*"([^"]*)"', xml))
    files = re.findall(r"<File>\s*<FileSize>\s*(\d+)\s*</FileSize>\s*<CompressSize>\s*(\d+)\s*</CompressSize>\s*<Offset>\s*(\d+)\s*</Offset>\s*<HashValue>\s*(\d+)\s*</HashValue>\s*<Extension>\s*\"([^\"]*)\"\s*</Extension>", xml)
    print("==", r, "entries", len(files))
    for e,c in exts.most_common(40):
        print("   %-10s %d" % (e,c))
