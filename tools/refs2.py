import pefile, capstone, sys, struct
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TOS = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\TOS.exe"
pe = pefile.PE(TOS); D = pe.__data__; IMG = 0x400000
def off2va(o):
    for s in pe.sections:
        if s.PointerToRawData <= o < s.PointerToRawData + s.SizeOfRawData:
            return IMG + s.VirtualAddress + (o - s.PointerToRawData)
    return None
def va2off(v):
    r = v - IMG
    for s in pe.sections:
        if s.VirtualAddress <= r < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return s.PointerToRawData + (r - s.VirtualAddress)
    return None
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); md.detail = True
def decode_ref(addr):
    """yield (va, text, access) for instructions referencing addr"""
    t = struct.pack('<I', addr)
    i = 0
    seen = set()
    while True:
        i = D.find(t, i)
        if i < 0: break
        va = off2va(i)
        if va:
            for delta in range(1, 17):
                st = va - delta
                o = va2off(st)
                if o is None: continue
                try:
                    ins = next(md.disasm(D[o:o+16], st))
                except StopIteration:
                    continue
                if len(ins.bytes) < delta + 4: continue
                for op in ins.operands:
                    if op.type == capstone.x86.X86_OP_MEM and op.mem.disp == addr and ins.disp_offset == delta:
                        acc = op.access
                        key = (st, ins.bytes.hex())
                        if key in seen: continue
                        seen.add(key)
                        a = {1: 'R', 2: 'W', 3: 'RW'}.get(acc, '?')
                        yield st, "%s  %s %s" % (a, ins.mnemonic, ins.op_str), acc
        i += 1
for a in sys.argv[1:]:
    addr = int(a, 16)
    print("### refs to %s" % a)
    for st, txt, acc in sorted(decode_ref(addr)):
        print("  %08X  %s" % (st, txt))
