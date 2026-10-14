import os, re, sys
base = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\P12E\Data\TOS_Server\Archive\Release"
for rel in [r"R01\WIN\TLFILE.TLDAT"]:
    p = os.path.join(base, rel)
    size = os.path.getsize(p)
    print("==", rel, size)
    f = open(p, "rb")
    off = 0
    CH = 64*1024*1024
    tot16 = tot8 = 0
    samp16 = []; samp8 = []
    read = 0
    while read < 600*1024*1024:
        b = f.read(CH)
        if not b: break
        read += len(b)
        # UTF-16LE Hangeul: high byte 0xAC-0xD7
        for m in re.finditer(rb"[\x00-\xff][\xac-\xd7]", b):
            tot16 += 1
            if len(samp16) < 20:
                s = b[max(0,m.start()-40):m.start()+40]
                try: samp16.append(s.decode("utf-16-le","replace"))
                except: pass
        # UTF-8 Hangeul: EA-ED xx xx
        for m in re.finditer(rb"[\xea-\xed][\x80-\xbf][\x80-\xbf]", b):
            tot8 += 1
            if len(samp8) < 20:
                s = b[max(0,m.start()-40):m.start()+40]
                samp8.append(s.decode("utf-8","replace"))
    f.close()
    print("scanned", read, "utf16 hangeul-ish", tot16, "utf8 hangeul-ish", tot8)
    print("-- utf16 samples --")
    for s in samp16: print("   ", repr(s))
    print("-- utf8 samples --")
    for s in samp8: print("   ", repr(s))
