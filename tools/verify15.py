"""Replicate logger15.c byte emitters and disassemble to validate branch targets,
register usage and stub sizes (must fit ss=256 bytes)."""
import capstone, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = 0x30000000
GBASE = 0x4000
GCOUNT = 2727
SYMBASE = 2445
MASK = 4095
REG = ["eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi"]


class P:
    def __init__(s): s.b = bytearray()
    def EB(s, v): s.b.append(v & 0xFF); return s
    def EW(s, v): s.b += bytes([v & 0xFF, (v >> 8) & 0xFF]); return s
    def EI(s, v): s.b += (v & 0xFFFFFFFF).to_bytes(4, "little"); return s


def EJMP(p, tgt):
    at = len(p.b) + 1
    p.EB(0xE9); p.EI((tgt - (BASE + at + 4)) & 0xFFFFFFFF); return p


def fixj(p, op, tgt): p.b[op] = (tgt - (op + 1)) & 0xFF
def fixj32(p, op, tgt): p.b[op:op + 4] = ((tgt - (op + 4)) & 0xFFFFFFFF).to_bytes(4, "little")


def KORTEST(p, R):
    p.EB(0x0F); p.EB(0xB7); p.EB(0xC0 | R)
    p.EB(0x8B); p.EB(0xC8)
    p.EB(0x81); p.EB(0xE1); p.EI(0xFF)
    p.EB(0x81); p.EB(0xE9); p.EI(0xA1)
    p.EB(0x83); p.EB(0xF9); p.EB(0x5D)
    p.EB(0x77); ja1 = len(p.b); p.EB(0)
    p.EB(0x8B); p.EB(0xC8)
    p.EB(0xC1); p.EB(0xE9); p.EB(0x08)
    p.EB(0x81); p.EB(0xE9); p.EI(0xA1)
    p.EB(0x83); p.EB(0xF9); p.EB(0x02)
    p.EB(0x76); jb1 = len(p.b); p.EB(0)
    p.EB(0x8B); p.EB(0xC8)
    p.EB(0xC1); p.EB(0xE9); p.EB(0x08)
    p.EB(0x81); p.EB(0xE9); p.EI(0xB0)
    p.EB(0x83); p.EB(0xF9); p.EB(0x18)
    p.EB(0x76); jb2 = len(p.b); p.EB(0)
    p.EB(0xE9); op = len(p.b); p.EI(0)
    Lkr = len(p.b)
    fixj(p, ja1, Lkr - 5); fixj(p, jb1, Lkr); fixj(p, jb2, Lkr)
    return op


def stub_len(R, R3, r_len2, r_resume):
    p = P()
    p.EB(0x50); p.EB(0x51)
    op = KORTEST(p, R)
    p.EB(0x59); p.EB(0x58)
    EJMP(p, BASE + r_len2)
    Lorig = len(p.b); fixj32(p, op, Lorig)
    p.EB(0x59); p.EB(0x58)
    p.EB(0xB8 | R3); p.EI(0xFE)
    EJMP(p, BASE + r_resume)
    return p


def stub_conv(R, R3, r_resume, r_end, isret):
    p = P()
    p.EB(0x50)
    op = KORTEST(p, R)
    p.EB(0x52); p.EB(0x8B); p.EB(0x15); p.EI(0x30010000)
    p.EB(0x89); p.EB(0x04); p.EB(0xD5); p.EI(0x30020000)
    p.EB(0x8B); p.EB(0x4C); p.EB(0x24); p.EB(0x04)
    p.EB(0x89); p.EB(0x0C); p.EB(0xD5); p.EI(0x30020004)
    p.EB(0x83); p.EB(0xC2); p.EB(0x01)
    p.EB(0x81); p.EB(0xE2); p.EI(MASK)
    p.EB(0x89); p.EB(0x15); p.EI(0x30010000)
    p.EB(0x5A)
    p.EB(0x0F); p.EB(0xB7); p.EB(0xC0 | R)
    p.EB(0x8B); p.EB(0xC8)
    p.EB(0xC1); p.EB(0xE9); p.EB(0x08)
    p.EB(0x25); p.EI(0xFF)
    p.EB(0x83); p.EB(0xF9); p.EB(0xB0)
    p.EB(0x73); jh = len(p.b); p.EB(0)
    p.EB(0x81); p.EB(0xE9); p.EI(0xA1)
    p.EB(0x6B); p.EB(0xC9); p.EB(94)
    p.EB(0x2D); p.EI(0xA1)
    p.EB(0x03); p.EB(0xC8)
    p.EB(0x81); p.EB(0xC1); p.EI(SYMBASE)
    p.EB(0xEB); js = len(p.b); p.EB(0)
    Lhan = len(p.b)
    p.EB(0x81); p.EB(0xE9); p.EI(0xB0)
    p.EB(0x6B); p.EB(0xC9); p.EB(94)
    p.EB(0x2D); p.EI(0xA1)
    p.EB(0x03); p.EB(0xC8)
    Ldone = len(p.b); fixj(p, jh, Lhan); fixj(p, js, Ldone)
    p.EB(0x81); p.EB(0xC1); p.EI(GBASE)
    p.EB(0x8B); p.EB(0xC1)
    p.EB(0x83); p.EB(0xC4); p.EB(0x04)
    if isret:
        p.EB(0xC3)
    else:
        EJMP(p, BASE + r_end)
    Lorig = len(p.b); fixj32(p, op, Lorig)
    p.EB(0x58)
    p.EB(0xB8 | R3); p.EI(0x80)
    EJMP(p, BASE + r_resume)
    return p


def stub_width():
    p = P()
    p.EB(0x50)
    op = KORTEST(p, 0)
    p.EB(0x58)
    p.EB(0xB8); p.EI(0x30)
    p.EB(0xC3)
    Lorig = len(p.b); fixj32(p, op, Lorig)
    p.EB(0x58)
    p.EB(0x8B); p.EB(0xC1)
    p.EB(0x81); p.EB(0xE1); p.EI(0xFF00)
    EJMP(p, BASE + 0x17ACD8)
    return p


md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
tests = []
for R, R3 in ((0, 3), (6, 2), (1, 3), (7, 0), (0, 2)):
    tests.append(("len R=%s R3=%s" % (REG[R], REG[R3]), stub_len(R, R3, 0x17A923, 0x17A8E0)))
tests.append(("width", stub_width()))
for R, R3, isret in ((0, 1, 1), (6, 1, 0), (0, 2, 0)):
    tests.append(("conv R=%s R3=%s ret=%d" % (REG[R], REG[R3], isret), stub_conv(R, R3, 0x17A995, 0x17A9E4, isret)))

for name, p in tests:
    print("=== %s len=%d bytes (limit 256) %s ===" % (name, len(p.b), "OK" if len(p.b) <= 256 else "TOO BIG"))
    clob = set()
    for ins in md.disasm(bytes(p.b), BASE):
        print("  %08X %-22s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic + " " + ins.op_str))
        for op in ins.operands:
            if op.type == capstone.x86.X86_OP_REG and ins.mnemonic not in ("mov", "movzx", "push", "pop", "lea", "cmp", "add", "sub", "and", "imul", "shl", "shr", "div", "xor", "test"):
                clob.add(ins.reg_name(op.reg))
    print("  clobbered: %s" % sorted(clob))
    print()
