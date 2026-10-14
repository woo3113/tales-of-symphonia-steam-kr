import re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
D=open(r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe","rb").read()
def va(o): return 0x400000+o
# 1) converter copies: "B9 80 00 00 00 66 3B"
conv=bytes.fromhex("B980000000663B")
print("converter copies (B9 80 00 00 00 66 3B):")
for m in re.finditer(re.escape(conv), D): print("   0x%08X"%va(m.start()))
# 2) length rule: lea reg,[eax+0x7EFF] then cmp ... 0xFE  -> pattern "8D ?? FF 7E 00 00"
rule=re.compile(rb"\x8D[\x80-\xBF]\xFF\x7E\x00\x00")
print("length-rule candidates (lea reg,[eax+0x7EFF]):")
for m in rule.finditer(D):
    seg=D[m.start():m.start()+20]
    print("   0x%08X  %s"%(va(m.start()), seg.hex()))
# 3) width-table pattern (lea +0x7EC0, 0x19F)
wt=re.compile(rb"\x8D[\x80-\xBF]\xC0\x7E\x00\x00")
print("width-table candidates (+0x7EC0):")
for m in wt.finditer(D): print("   0x%08X"%va(m.start()))
