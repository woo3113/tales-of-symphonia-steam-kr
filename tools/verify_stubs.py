"""Replicate logger8.c stub emitters and disassemble to verify branch targets."""
import capstone, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = 0x30000000
GBASE = 0x4000
MASK = 4095


class P:
    def __init__(s): s.b = bytearray()
    def EB(s, v): s.b.append(v & 0xFF); return s
    def EW(s, v): s.b += bytes([v & 0xFF, (v >> 8) & 0xFF]); return s
    def EI(s, v): s.b += (v & 0xFFFFFFFF).to_bytes(4, "little"); return s


def EJMP(p, tgt):
    at = len(p.b) + 1
    p.EB(0xE9); p.EI((tgt - (BASE + at + 4)) & 0xFFFFFFFF); return p


def fixj(p, op, tgt):
    p.b[op] = (tgt - (op + 1)) & 0xFF


def KORTEST(p, R):
    p.EB(0x0F); p.EB(0xB7); p.EB(0xC0 | R)
    p.EB(0x8B); p.EB(0xC8)
    p.EB(0xC1); p.EB(0xE9); p.EB(0x08)
    p.EB(0x81); p.EB(0xE9); p.EI(0xB0)
    p.EB(0x83); p.EB(0xF9); p.EB(0x18)
    p.EB(0x77); ja = len(p.b); p.EB(0x00)
    p.EB(0x0F); p.EB(0xB6); p.EB(0xC8)
    p.EB(0x81); p.EB(0xE9); p.EI(0xA1)
    p.EB(0x83); p.EB(0xF9); p.EB(0x5D)
    p.EB(0x77); jb = len(p.b); p.EB(0x00)
    return ja, jb


def emit_conv(R, R3, isret):
    p = P()
    p.EB(0x50)
    ja, jb = KORTEST(p, R)
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
    p.EB(0x81); p.EB(0xE9); p.EI(0xB0)
    p.EB(0x6B); p.EB(0xC9); p.EB(94)
    p.EB(0x25); p.EI(0xFF)
    p.EB(0x2D); p.EI(0xA1)
    p.EB(0x03); p.EB(0xC8)
    p.EB(0x81); p.EB(0xC1); p.EI(GBASE)
    p.EB(0x8B); p.EB(0xC1)
    p.EB(0x83); p.EB(0xC4); p.EB(0x04)
    if isret:
        p.EB(0xC3)
    else:
        EJMP(p, BASE + 0x17A9E4)
    Lorig = len(p.b)
    fixj(p, ja, Lorig); fixj(p, jb, Lorig)
    p.EB(0x58)
    p.EB(0xB8 | R3); p.EI(0x80)
    EJMP(p, BASE + 0x17A995)
    return p


REG = ["eax", "ecx", "edx", "ebx", "esp", "ebp", "esi", "edi"]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for R, R3, isret in ((0, 1, 1), (6, 1, 0)):
    p = emit_conv(R, R3, isret)
    print("=== conv R=%s R3=%s len=%d ===" % (REG[R], REG[R3], len(p.b)))
    for ins in md.disasm(bytes(p.b), BASE):
        print("  %08X %-20s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic + " " + ins.op_str))
    print()
