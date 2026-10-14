"""Run TOS.exe with our logger DLL installed as korfnt\\korfnt.dll, collect krcodes.bin, restore.

Usage:  py -3.12 run_logger8.py [seconds]
"""
import subprocess, time, struct, os, sys, shutil, collections, ctypes
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GAME = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
WORK = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work"
OUT = os.path.join(GAME, "krcodes.bin")
RING = 1024
WAIT = int(sys.argv[1]) if len(sys.argv) > 1 else 120

KORFNT = os.path.join(GAME, "korfnt", "korfnt.dll")
REAL = os.path.join(GAME, "korfnt", "korfnt.dll.real")
LOGGER = os.path.join(WORK, "korfnt_logger5c.dll")

k32 = ctypes.WinDLL("kernel32", use_last_error=True)


def install():
    if not os.path.exists(REAL):
        shutil.copy2(KORFNT, REAL)
        print("backed up korfnt.dll -> korfnt.dll.real")
    shutil.copy2(LOGGER, KORFNT)
    print("installed logger as korfnt\\korfnt.dll")


def restore():
    if os.path.exists(REAL):
        shutil.copy2(REAL, KORFNT)
        print("restored original korfnt.dll")


def rd(h, a, n):
    b = (ctypes.c_char * n)(); c = ctypes.c_size_t(0)
    return b.raw if k32.ReadProcessMemory(h, ctypes.c_void_p(a), b, n, ctypes.byref(c)) else None


def main():
    if os.path.exists(OUT):
        os.remove(OUT)
    install()
    p = subprocess.Popen([os.path.join(GAME, "TOS.exe")], cwd=GAME)
    print("pid", p.pid)
    h = k32.OpenProcess(0x410, False, p.pid)
    best = None
    try:
        for t in range(WAIT // 4):
            time.sleep(4)
            if p.poll() is not None:
                print("process exited early, code", p.returncode); break
            if os.path.exists(OUT) and os.path.getsize(OUT) >= 12 + RING * 24:
                d = open(OUT, "rb").read()
                i0, i1, i2 = struct.unpack_from("<III", d, 0)
                hx = rd(h, 0x57A8DA, 6)
                print("t=%ds idx(conv,glyph,width)=%s 57A8DA=%s" % (4 * (t + 1), (i0, i1, i2), hx.hex() if hx else None))
                if i0 > 0:
                    best = d; break
    finally:
        try: p.terminate()
        except Exception: pass
        restore()
    if best is None and os.path.exists(OUT):
        best = open(OUT, "rb").read()
    if not best:
        print("NO LOG"); return
    d = best; i0, i1, i2 = struct.unpack_from("<III", d, 0); off = 12
    conv = [struct.unpack_from("<II", d, off + 8 * k) for k in range(RING)]; off += RING * 8
    wid = [struct.unpack_from("<II", d, off + 8 * k) for k in range(RING)]; off += RING * 8
    gly = [struct.unpack_from("<II", d, off + 8 * k) for k in range(RING)]
    cc = collections.Counter(c for c, _ in conv if c)
    print("CONV idx", i0, "distinct", len(cc), "2byte(>0xFF):", sum(1 for k in cc if k > 0xFF))
    print("  top:", [(hex(k), v) for k, v in cc.most_common(25)])
    print("  conv callers:", [(hex(k), v) for k, v in collections.Counter(b for _, b in conv if b).most_common(10)])
    wc = collections.Counter(a for a, _ in wid if a)
    print("WIDTH idx", i2, "distinct", len(wc), "2byte:", sum(1 for k in wc if k > 0xFF))
    print("  width inputs:", [(hex(k), v) for k, v in wc.most_common(12)])
    print("  width callers:", [(hex(k), v) for k, v in collections.Counter(b for _, b in wid if b).most_common(12)])
    gc = collections.Counter(a for a, _ in gly if a)
    print("GLYPH idx", i1, "distinct", len(gc), "top:", [(hex(k), v) for k, v in gc.most_common(15)])


if __name__ == "__main__":
    main()
