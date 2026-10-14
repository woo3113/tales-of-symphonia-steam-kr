"""Run TOS.exe with a logger DLL installed as korfnt\\korfnt.dll, collect krcodes.bin, restore.
Usage: py -3.12 run_logger9.py [dll basename] [seconds]"""
import subprocess, time, struct, os, sys, shutil, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GAME = r"D:\SteamLibrary\steamapps\common\Tales of Symphonia"
WORK = r"C:\Users\woo31\AppData\Local\Temp\opencode\tos_kr\work"
OUT = os.path.join(GAME, "krcodes.bin")
RING = 4096
DLL = sys.argv[1] if len(sys.argv) > 1 else "korfnt_logger7.dll"
WAIT = int(sys.argv[2]) if len(sys.argv) > 2 else 120
HDR = 20
KORFNT = os.path.join(GAME, "korfnt", "korfnt.dll")
REAL = os.path.join(GAME, "korfnt", "korfnt.dll.real")


def install():
    if not os.path.exists(REAL):
        shutil.copy2(KORFNT, REAL)
    for _ in range(40):
        try:
            shutil.copy2(os.path.join(WORK, DLL), KORFNT); return True
        except PermissionError:
            time.sleep(0.5)
    return False


def restore():
    for _ in range(40):
        try:
            shutil.copy2(REAL, KORFNT); return True
        except PermissionError:
            time.sleep(0.5)
    return False


def main():
    if os.path.exists(OUT):
        os.remove(OUT)
    print("install:", install())
    p = subprocess.Popen([os.path.join(GAME, "TOS.exe")], cwd=GAME)
    print("pid", p.pid)
    best = None
    try:
        for t in range(WAIT // 4):
            time.sleep(4)
            if p.poll() is not None:
                print("EXITED early code", p.returncode, hex(p.returncode & 0xffffffff)); break
            if os.path.exists(OUT) and os.path.getsize(OUT) >= HDR + RING * 32:
                d = open(OUT, "rb").read()
                i = struct.unpack_from("<IIIII", d, 0)
                print("t=%ds idx(loop,width,glyph,conv)=%s npatched=%d" % (4 * (t + 1), i[:4], i[4]))
                if i[0] > 0 and i[4] > 0:
                    best = d
                if i[0] > 0:
                    break
    finally:
        try: p.terminate()
        except Exception: pass
        time.sleep(1.5)
        print("restore:", restore())
    if best is None and os.path.exists(OUT):
        best = open(OUT, "rb").read()
    if not best:
        print("NO LOG"); return
    open(os.path.join(WORK, "krcodes7.bin"), "wb").write(best)
    i0, i1, i2, i3, np = struct.unpack_from("<IIIII", best, 0)
    off = HDR
    bufs = {}
    for name in ("loop", "width", "glyph", "conv"):
        bufs[name] = [struct.unpack_from("<II", best, off + 8 * k) for k in range(RING)]
        off += RING * 8
    print("indices:", i0, i1, i2, i3, "npatched:", np)
    lp = bufs["loop"][:min(i0, RING)]
    print("LOOP samples (%d):" % len(lp))
    for a, b in lp[:30]:
        by = struct.pack("<I", b)
        print("   ptr=%08X bytes=%s %s" % (a, by.hex(), "".join(chr(c) if 32 <= c < 127 else "." for c in by)))
    cc = collections.Counter(a for a, _ in bufs["conv"] if a)
    print("CONV distinct", len(cc), "top", [(hex(k), v) for k, v in cc.most_common(20)])
    wc = collections.Counter(a for a, _ in bufs["width"] if a)
    print("WIDTH distinct", len(wc), "top", [(hex(k), v) for k, v in wc.most_common(15)])
    print("  width 2byte(>0xFF):", [(hex(k), v) for k, v in wc.items() if k > 0xFF][:15])
    gc = collections.Counter(a for a, _ in bufs["glyph"] if a)
    print("GLYPH distinct", len(gc), "top", [(hex(k), v) for k, v in gc.most_common(15)])


if __name__ == "__main__":
    main()
