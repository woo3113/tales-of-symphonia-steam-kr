import pefile, struct, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS=r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe=pefile.PE(TOS)
oh=pe.OPTIONAL_HEADER
print("ImageBase", hex(oh.ImageBase))
print("SectionAlignment", hex(oh.SectionAlignment), "FileAlignment", hex(oh.FileAlignment))
print("SizeOfHeaders", hex(oh.SizeOfHeaders))
print("NumberOfSections", pe.FILE_HEADER.NumberOfSections)
print("SizeOfOptionalHeader", hex(pe.FILE_HEADER.SizeOfOptionalHeader))
sec_table_off = 0x18 + pe.FILE_HEADER.SizeOfOptionalHeader
print("section table off", hex(sec_table_off), "ends at", hex(sec_table_off+40*pe.FILE_HEADER.NumberOfSections))
print("first section header VA:", hex(pe.sections[0].VirtualAddress), "RAW:", hex(pe.sections[0].PointerToRawData))
print("SizeOfImage", hex(oh.SizeOfImage))
last=pe.sections[-1]
print("last section:", last.Name, "VA", hex(last.VirtualAddress), "VS", hex(last.Misc_VirtualSize), "RAW", hex(last.PointerToRawData), "RS", hex(last.SizeOfRawData))
print("DllCharacteristics", hex(oh.DllCharacteristics))
print("file size", len(pe.__data__))
# room for one more section header?
room = pe.sections[0].PointerToRawData - (sec_table_off+40*pe.FILE_HEADER.NumberOfSections)
print("bytes free after section table before first RAW:", room)
