import pefile, capstone, os, sys, re
BASE = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
rel = "korfnt\\korfnt.dll"
pe = pefile.PE(os.path.join(BASE, rel))
img = pe.OPTIONAL_HEADER.ImageBase
IAT = {}
for e in pe.DIRECTORY_ENTRY_IMPORT:
    dll = e.dll.decode()
    for imp in e.imports:
        nm = imp.name.decode() if imp.name else "ord%s"%imp.ordinal
        IAT[imp.address] = "%s!%s" % (dll, nm)
targets = ["EnumProcessModules","GetModuleBaseNameA","ReadProcessMemory","WriteProcessMemory","VirtualProtect","VirtualQueryEx","wglGetProcAddress","glGetIntegerv","D3DXFloat32To16Array"]
# disassemble .text
text = [s for s in pe.sections if s.Name.startswith(b".text")][0]
data = text.get_data()
base = img + text.VirtualAddress
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
hits = []
for ins in md.disasm(data, base):
    for op in ins.operands:
        if op.type == capstone.x86.X86_OP_MEM and op.mem.base == 0 and op.mem.index == 0:
            addr = op.mem.disp
            if addr in IAT and any(t in IAT[addr] for t in targets):
                hits.append((ins.address, IAT[addr], ins.mnemonic, ins.op_str))
last = None
for a, nm, mn, ops in hits:
    print("%08X %-45s %s %s" % (a, nm, mn, ops))
print("total", len(hits))
