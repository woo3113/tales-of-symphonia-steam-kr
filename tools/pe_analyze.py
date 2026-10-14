import pefile, sys, os, re, struct

BASE = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"

def analyze(rel):
    path = os.path.join(BASE, rel)
    print("="*100)
    print("FILE:", rel, " size=", os.path.getsize(path))
    pe = pefile.PE(path, fast_load=False)
    print("Machine:", hex(pe.FILE_HEADER.Machine), "TimeDateStamp:", pe.FILE_HEADER.TimeDateStamp,
          "Characteristics:", hex(pe.FILE_HEADER.Characteristics))
    print("Subsystem:", pe.OPTIONAL_HEADER.Subsystem, "DllChars:", hex(pe.OPTIONAL_HEADER.DllCharacteristics),
          "ImageBase:", hex(pe.OPTIONAL_HEADER.ImageBase), "EP:", hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint))
    print("-- Sections --")
    for s in pe.sections:
        name = s.Name.rstrip(b"\x00").decode("latin1")
        print("  %-10s VA=%08X VS=%08X RAW=%08X RS=%08X ch=%08X" % (name, s.VirtualAddress, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData, s.Characteristics))
    print("-- Exports --")
    if hasattr(pe, "DIRECTORY_ENTRY_EXPORT"):
        d = pe.DIRECTORY_ENTRY_EXPORT
        print("  DLL name:", d.name.decode("latin1") if d.name else None, " numfuncs:", len(d.symbols))
        for e in d.symbols:
            print("   ", e.ordinal, e.name.decode("latin1") if e.name else None, "->", hex(e.address))
    else:
        print("  (none)")
    print("-- Imports --")
    if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            print("  ", entry.dll.decode("latin1"))
            for imp in entry.imports[:40]:
                print("      ", hex(imp.address), imp.name.decode("latin1") if imp.name else ("ord %s"%imp.ordinal))
            if len(entry.imports) > 40:
                print("      ... (%d more)" % (len(entry.imports)-40))
    else:
        print("  (none)")
    pe.close()

for f in sys.argv[1:]:
    analyze(f)
