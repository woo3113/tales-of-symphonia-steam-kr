import pefile, sys, os
BASE = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
path = os.path.join(BASE, sys.argv[1])
pe = pefile.PE(path)
print("Imported DLLs:")
for e in pe.DIRECTORY_ENTRY_IMPORT:
    dll = e.dll.decode("latin1")
    names = [ (i.name.decode("latin1") if i.name else "ord%s"%i.ordinal) for i in e.imports ]
    print("  %-30s (%d) %s" % (dll, len(names), ", ".join(names[:12]) + (" ..." if len(names)>12 else "")))
print()
print("Delay-import DLLs:")
if hasattr(pe,"DIRECTORY_ENTRY_DELAY_IMPORT"):
    for e in pe.DIRECTORY_ENTRY_DELAY_IMPORT:
        dll = e.dll.decode("latin1")
        names = [ (i.name.decode("latin1") if i.name else "ord%s"%i.ordinal) for i in e.imports ]
        print("  %-30s (%d) %s" % (dll, len(names), ", ".join(names[:12])))
