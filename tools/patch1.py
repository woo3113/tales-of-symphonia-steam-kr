import pefile, sys, shutil, hashlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
GAME=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
WORK=r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work"
pe=pefile.PE(GAME); D=bytearray(pe.__data__)
t=[s for s in pe.sections if s.Name.startswith(b".text")][0]
lo=t.PointerToRawData; hi=lo+t.SizeOfRawData
# find a long run of 0xCC padding in .text
best=None
i=lo
while i<hi:
    if D[i]==0xCC:
        j=i
        while j<hi and D[j]==0xCC: j+=1
        if best is None or (j-i)>(best[1]-best[0]): best=(i,j)
        i=j
    else:
        i+=1
a,b=best
print("longest int3 padding run: file 0x%X..0x%X len=%d"%(a,b,b-a))
# choose a byte in the middle of the run (definitely not executed)
target=a+(b-a)//2
old=D[target]
D[target]=0x90  # int3 -> nop (harmless change to the file)
va=0x400000+ (target - (lo - t.VirtualAddress))
print("patching file offset 0x%X (VA %08X): 0x%02X -> 0x90"%(target, va, old))
pe.close()
tmp=GAME+".new"
with open(tmp,"wb") as f: f.write(bytes(D))
import os
os.replace(tmp, GAME)
with open(GAME,"rb") as f: chk=hashlib.sha256(f.read()).hexdigest()
print("new sha256:", chk)
print("backup exists:", os.path.exists(WORK+r"\TOS.exe.bak"))
