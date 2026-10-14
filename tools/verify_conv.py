"""Verify logger9's converter stub (ASCII + Korean + original) by replicating and disassembling."""
import capstone, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = 0x30000000
GBASE = 0x4000
ASCII_BASE = 2350
MASK = 4095


class P:
    def __init__(s): s.b = bytearray()
    def EB(s, v): s.b.append(v & 0xFF); return s
    def EI(s, v): s.b += (v & 0xFFFFFFFF).to_bytes(4, "little"); return s


def EJMP(p, tgt):
    at = len(p.b) + 1
    p.EB(0xE9); p.EI((tgt - (BASE + at + 4)) & 0xFFFFFFFF); return p


def fixj32(p, op, tgt):
    p.b[op:op + 4] = ((tgt - (op + 4)) & 0xFFFFFFFF).to_bytes(4, "little")


def KORTEST(p, R):
    p.EB(0x0F); p.EB(0xB7); p.EB(0xC0 | R)
    p.EB(0x8B); p.EB(0xC8)
    p.EB(0xC1); p.EB(0xE9); p.EB(0x08)
    p.EB(0x81); p.EB(0xE9); p.EI(0xB0)
    p.EB(0x83); p.EB(0xF9); p.EB(0x18)
    p.EB(0x0F); p.EB(0x82); ja = len(p.b); p.EI(0)
    p.EB(0x0F); p.EB(0xB6); p.EB(0xC8)
    p.EB(0x81); p.EB(0xE9); p.EI(0xA1)
    p.EB(0x83); p.EB(0xF9); p.EB(0x5D)
    p.EB(0x0F); p.EB(0x82); jb = len(p.b); p.EI(0)
    return ja, jb


def emit_conv(R, R3, isret):
    p = P()
    p.EB(0x50)
    p.EB(0x0F); p.EB(0xB7); p.EB(0xC0 | R)
    p.EB(0x3D); p.EI(0x20)
    p.EB(0x0F); p.EB(0x82); jA = len(p.b); p.EI(0)
    p.EB(0x3D); p.EI(0x7E)
    p.EB(0x0F); p.EB(0x87); jB = len(p.b); p.EI(0)
    p.EB(0x2D); p.EI(0x20)
    p.EB(0x05); p.EI(GBASE + ASCII_BASE)
    p.EB(0x83); p.EB(0xC4); p.EB(0x04)
    if isret:
        p.EB(0xC3)
    else:
        EJMP(p, BASE + 0x17A9E4)
    Lnota = len(p.b); fixj32(p, jA, Lnota); fixj32(p, jB, Lnota)
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
    Lorig = len(p.b); fixj32(p, ja, Lorig); fixj32(p, jb, Lorig)
    p.EB(0x58)
    p.EB(0xB8 | R3); p.EI(0x80)
    EJMP(p, BASE + 0x17A995)
    return p


md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for R, R3, isret in ((0, 1, 1), (6, 1, 0)):
    p = emit_conv(R, R3, isret)
    print("=== conv R=%d R3=%d ret=%d len=%d ===" % (R, R3, isret, len(p.b)))
    for ins in md.disasm(bytes(p.b), BASE):
        print("  %08X %-20s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic + " " + ins.op_str))
    print()
