import pefile, capstone, struct, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
pe=pefile.PE(r"D:\SteamLibrary\steamapps\common\Tales of Symphonia\korfnt\korfnt.dll"); D=pe.__data__; IMG=0x10000000
def va2off(v):
    r=v-IMG
    for s in pe.sections:
        if s.VirtualAddress<=r<s.VirtualAddress+max(s.Misc_VirtualSize,s.SizeOfRawData): return s.PointerToRawData+(r-s.VirtualAddress)
o=va2off(0x100022B0); end=va2off(0x1000289C)
region=D[o:end]
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.detail=True
handlers=set()
for ins in md.disasm(region, 0x100022B0):
    # detect mov eax,imm / push imm / mov edx,imm etc with imm in code range
    if ins.mnemonic in ("mov","push"):
        for op in ins.operands:
            if op.type==capstone.x86.X86_OP_IMM:
                v=op.imm
                if 0x10001000<=v<0x1002D000:
                    handlers.add(v)
print("handler function pointers referenced:", sorted(hex(h) for h in handlers))
# also strings referenced
strs=set()
for ins in md.disasm(region, 0x100022B0):
    if ins.mnemonic=="push":
        for op in ins.operands:
            if op.type==capstone.x86.X86_OP_IMM and 0x10035000<=op.imm<0x10036000:
                strs.add(op.imm)
print("string pointers:", [hex(s) for s in sorted(strs)])
