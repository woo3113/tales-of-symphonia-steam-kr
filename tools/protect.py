import pefile, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe=pefile.PE(TOS)
print("sections:")
for s in pe.sections:
    print("  %-10s VA=%08X VS=%08X RAW=%08X"%(s.Name.rstrip(b'\x00').decode('latin1'), s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData))
D=pe.__data__
for kw in ["VMProtect","vmp","Denuvo","denuvo","SteamStub","SecuROM","Themida","Enigma","\\sec\\",".tmp","AntiDebug","IsDebuggerPresent","NtQueryInformationProcess","VirtualProtect","WriteProcessMemory","CheckRemoteDebugger"]:
    b=kw.encode('latin1'); c=len(re.findall(re.escape(b), D))
    if c: print("  string %-24s count=%d"%(kw,c))
print("imports (notable):")
for e in pe.DIRECTORY_ENTRY_IMPORT:
    for i in e.imports:
        n=i.name.decode('latin1') if i.name else 'ord%d'%i.ordinal
        if n in ("VirtualProtect","WriteProcessMemory","ReadProcessMemory","NtQueryInformationProcess","CheckRemoteDebuggerPresent","IsDebuggerPresent","OutputDebugStringA","GetTickCount","QueryPerformanceCounter","VirtualProtectEx"):
            print("  %s!%s"%(e.dll.decode('latin1'),n))
