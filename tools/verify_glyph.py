"""Emit the new custom glyph stub (grid mapping) and disassemble it to verify."""
import capstone, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = 0x30000000
GBASE = 0x4000
GCOUNT = 2445
ASCII_BASE = 2350
GRID_COLS = 5
GRID_ROWS = 7


class P:
    def __init__(s): s.b = bytearray()
    def EB(s, v): s.b.append(v & 0xFF); return s
    def EW(s, v): s.b += bytes([v & 0xFF, (v >> 8) & 0xFF]); return s
    def EI(s, v): s.b += (v & 0xFFFFFFFF).to_bytes(4, "little"); return s


def EJMP(p, tgt):
    at = len(p.b) + 1
    p.EB(0xE9); p.EI((tgt - (BASE + at + 4)) & 0xFFFFFFFF); return p


def fixj(p, op, tgt): p.b[op] = (tgt - (op + 1)) & 0xFF
def fixj32(p, op, tgt): p.b[op:op+4] = ((tgt - (op + 4)) & 0xFFFFFFFF).to_bytes(4, 'little')


def glyph_stub():
    p = P()
    # if ax < GBASE or ax >= GBASE+GCOUNT -> original
    p.EB(0x66); p.EB(0x3D); p.EW(GBASE)
    p.EB(0x0F); p.EB(0x82); j1 = len(p.b); p.EI(0)
    p.EB(0x66); p.EB(0x3D); p.EW(GBASE + GCOUNT)
    p.EB(0x0F); p.EB(0x83); j2 = len(p.b); p.EI(0)
    # our path prologue
    p.EB(0x55); p.EB(0x8B); p.EB(0xEC)          # push ebp; mov ebp,esp
    p.EB(0x51); p.EB(0x56); p.EB(0x53); p.EB(0x57)  # push ecx; push esi; push ebx; push edi
    p.EB(0x8B); p.EB(0xF1)                      # mov esi,ecx
    p.EB(0x85); p.EB(0xF6)                      # test esi,esi
    p.EB(0x75); p.EB(0x05)                      # jne +5
    p.EB(0xBE); p.EI(0xB190A0)                  # mov esi,0xb190a0
    # gi = ax - GBASE
    p.EB(0x0F); p.EB(0xB7); p.EB(0xC0)          # movzx eax,ax
    p.EB(0x2D); p.EI(GBASE)                     # sub eax,GBASE
    p.EB(0x33); p.EB(0xD2)                      # xor edx,edx
    p.EB(0xB9); p.EI(192)                       # mov ecx,192
    p.EB(0xF7); p.EB(0xF1)                      # div ecx   -> eax=page, edx=cell
    p.EB(0x8B); p.EB(0xF8)                      # mov edi,eax (page)
    p.EB(0x8B); p.EB(0xDA)                      # mov ebx,edx (cell)
    p.EB(0x8B); p.EB(0xCB)                      # mov ecx,ebx
    p.EB(0x83); p.EB(0xE1); p.EB(0x0F)          # and ecx,15  (c)
    p.EB(0xC1); p.EB(0xEB); p.EB(0x04)          # shr ebx,4   (r)
    p.EB(0x33); p.EB(0xD2)                      # xor edx,edx
    p.EB(0x8B); p.EB(0xC7)                      # mov eax,edi (page)
    p.EB(0xBF); p.EI(GRID_COLS)                 # mov edi,5
    p.EB(0xF7); p.EB(0xF7)                      # div edi -> eax=gpr, edx=gpc
    p.EB(0xC1); p.EB(0xE2); p.EB(0x04)          # shl edx,4
    p.EB(0x03); p.EB(0xD1)                      # add edx,ecx  (COL)
    p.EB(0x6B); p.EB(0xC0); p.EB(12)            # imul eax,eax,12
    p.EB(0x03); p.EB(0xC3)                      # add eax,ebx  (ROW)
    p.EB(0x50); p.EB(0x52)
    p.EB(0xA1); p.EI(0x30010000)
    p.EB(0x89); p.EB(0x14); p.EB(0xC5); p.EI(0x30020000)
    p.EB(0x8B); p.EB(0x54); p.EB(0x24); p.EB(0x04)
    p.EB(0x89); p.EB(0x14); p.EB(0xC5); p.EI(0x30020004)
    p.EB(0x83); p.EB(0xC0); p.EB(0x01)
    p.EB(0x25); p.EI(4095)
    p.EB(0xA3); p.EI(0x30010000)
    p.EB(0x5A); p.EB(0x58)
    p.EB(0x89); p.EB(0x55); p.EB(0xFC)          # mov [ebp-4],edx
    p.EB(0xDB); p.EB(0x45); p.EB(0xFC)          # fild dword [ebp-4]
    p.EB(0xDC); p.EB(0x0D); p.EI(0x882A30)      # fmul qword [0x882a30]
    p.EB(0xD9); p.EB(0x1E)                      # fstp dword [esi]
    p.EB(0x89); p.EB(0x45); p.EB(0xFC)          # mov [ebp-4],eax
    p.EB(0xDB); p.EB(0x45); p.EB(0xFC)          # fild dword [ebp-4]
    p.EB(0xDC); p.EB(0x0D); p.EI(0x882A30)      # fmul qword [0x882a30]
    p.EB(0xD9); p.EB(0x5E); p.EB(0x04)          # fstp dword [esi+4]
    p.EB(0x8B); p.EB(0x15); p.EI(0xB18F9C)      # mov edx,[0xb18f9c]
    p.EB(0xC7); p.EB(0x46); p.EB(0x08); p.EI(0) # mov dword [esi+8],0
    p.EB(0x89); p.EB(0x56); p.EB(0x0C)          # mov [esi+0xc],edx
    p.EB(0x8B); p.EB(0xC6)                      # mov eax,esi
    p.EB(0x5F); p.EB(0x5B); p.EB(0x5E)          # pop edi; pop ebx; pop esi
    p.EB(0x8B); p.EB(0xE5); p.EB(0x5D); p.EB(0xC3)  # mov esp,ebp; pop ebp; ret
    # original path
    Lorig = len(p.b); fixj32(p, j1, Lorig); fixj32(p, j2, Lorig)
    p.EB(0x55); p.EB(0x8B); p.EB(0xEC); p.EB(0x51); p.EB(0x56)
    EJMP(p, BASE + 0x178685)
    return p


g = glyph_stub()
print("glyph stub len", len(g.b))
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
for ins in md.disasm(bytes(g.b), BASE):
    print("  %08X %-22s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic + " " + ins.op_str))
