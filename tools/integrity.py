import pefile, re, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe=pefile.PE(TOS); D=pe.__data__; IMG=0x400000
# look for self-integrity patterns: GetModuleFileNameA followed by CreateFile, checksum APIs
print("imports of interest:")
for e in pe.DIRECTORY_ENTRY_IMPORT:
    for i in e.imports:
        n=i.name.decode('latin1') if i.name else 'ord%d'%i.ordinal
        if n in ("GetModuleFileNameA","GetModuleFileNameW","CreateFileA","CreateFileW","MapFileAndCheckSumA","MapFileAndCheckSumW","CheckSumMappedFile","GetFileSize","ReadFile","CryptAcquireContextW","GetModuleHandleA","GetModuleHandleW","MapViewOfFile","CreateFileMappingA"):
            print("  %s!%s"%(e.dll.decode('latin1'),n))
# strings that suggest integrity check
for kw in ["check","Check","integrity","CRC","crc32","signature","tamper","self","GetModuleFileName","IsDebuggerPresent","NtQuery","OutputDebug"]:
    hits=[m.start() for m in re.finditer(re.escape(kw.encode()), D)]
    if hits: print("string '%s' count=%d"%(kw,len(hits)))
# Try to see if the exe's own path string appears (self-reference)
print("exe filename refs:", len(re.findall(rb"TOS\.exe", D)))
