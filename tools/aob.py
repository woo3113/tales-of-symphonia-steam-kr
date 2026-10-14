import re, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
KOR=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\korfnt\korfnt.dll"
tos=open(TOS,"rb").read()
kor=open(KOR,"rb").read()
# find ASCII hex byte-pattern strings in korfnt.dll
pats=[]
for m in re.finditer(rb"(?:[0-9A-Fa-f]{2}(?:[ \t]|$)){4,}", kor):
    s=m.group().decode("latin1").strip()
    toks=s.split()
    if len(toks)<4: continue
    try: b=bytes(int(t,16) for t in toks)
    except: continue
    pats.append((m.start(), b, s))
print("hex patterns found in korfnt.dll:", len(pats))
# search each in TOS.exe
found=0
for off,b,s in pats:
    idxs=[m.start() for m in re.finditer(re.escape(b), tos)]
    if idxs:
        found+=1
        vas=[hex(0x400000+i) for i in idxs[:4]]
        print("  pat@%06X len=%2d  -> TOS VA %s  : %s"%(off,len(b),vas, s[:70]))
print("patterns that match TOS.exe:", found)
