"""
lloop_sweep.py -- where does per-operating-point scheduling START to pay?

The robustness study (section 28) found the scheduling ceiling is robust to
every DEVICE parameter and conditional on ONE thing: the power-loop
inductance, which is board layout. Three points:

    1.5 nH -> 13.54 %      3.0 nH -> 5.95 %      4.5 nH -> 0.55 %

Three points is a trend, not a design rule. This sweeps the loop inductance
finely enough to locate the CROSSOVER: the loop inductance below which
adaptive control earns its hardware, and above which a single fixed word is
as good. That number is actionable - a designer measures their loop and reads
off whether to build the adaptive path at all - and nobody has published it.

Full 720-word search at both corners for every inductance, because the
ceiling is a difference of two optima and a shortlist would bias both.
"""
import csv, itertools, os, re, subprocess, sys, tempfile, shutil, time
from collections import defaultdict
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gansim
from flatten import inline
from sweep import GRID

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "results", "lloop_sweep.csv")
CORNERS = [(100, 10, 25), (200, 2, 125)]        # same pair as robust.py
# 3.0 nH is nominal and already measured; the new points bracket the crossover
LLOOPS = ["1.0n", "2.0n", "2.5n", "3.5n", "6.0n"]

BASE = None
def build_base():
    global BASE
    BASE = inline(os.path.join(ROOT, "sim", "dpt.cir"))


def job(a):
    lloop, cfg, vb, il, tj = a
    src = BASE.replace("LLOOP = 3n", "LLOOP = %s" % lloop)
    if "LLOOP = %s" % lloop not in src:
        return {"error": "substitution failed for %s" % lloop}
    p = dict(gansim.DEFAULTS); p.update(cfg); p.update(VBUS=vb, ILOAD=il, TJ=tj)
    block = "\n".join(".param %s=%s" % (k, v) for k, v in p.items())
    src = re.sub(r"(?s)(==== PARAM BLOCK.*?====\n).*?(\* ====+ END PARAM BLOCK)",
                 lambda m: m.group(1) + block + "\n" + m.group(2), src)
    d = tempfile.mkdtemp(prefix="ll_")
    try:
        open(os.path.join(d, "dpt.cir"), "w").write(src)
        subprocess.run(["ngspice", "-b", "dpt.cir"], cwd=d,
                       capture_output=True, text=True, timeout=300)
        f = os.path.join(d, "out.dat")
        if not os.path.exists(f) or os.path.getsize(f) < 1000:
            return None
        import numpy as np
        m = gansim.metrics(np.loadtxt(f), p)
        m.update(lloop=lloop, corner="%dV_%dA_%dC" % (vb, il, tj),
                 **{k: v for k, v in cfg.items()})
        return m
    except Exception:
        return None
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _write(rows, path):
    cols = list(rows[0])
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)


def main():
    build_base()
    keys = list(GRID)
    words = [dict(zip(keys, v)) for v in itertools.product(*(GRID[k] for k in keys))]
    jobs = [(L, w, vb, il, tj) for L in LLOOPS for (vb, il, tj) in CORNERS for w in words]
    print("inductances: %d   corners: %d   words: %d   -> %d transients"
          % (len(LLOOPS), len(CORNERS), len(words), len(jobs)), flush=True)
    t0, rows, bad = time.time(), [], 0
    with Pool(4) as pool:
        for n, r in enumerate(pool.imap_unordered(job, jobs, chunksize=8), 1):
            if r is None or "error" in r:
                bad += 1
                if r and bad < 3: print("  ERROR:", r["error"], flush=True)
            else:
                rows.append(r)
            if n % 250 == 0:
                el = time.time() - t0
                print("  %5d/%d  %.0fs  eta %.0fs  failed=%d"
                      % (n, len(jobs), el, el * (len(jobs) - n) / n, bad), flush=True)
            if n % 500 == 0 and rows:
                _write(rows, OUT + ".part")
    if not rows:
        print("no rows"); return
    _write(rows, OUT)
    if os.path.exists(OUT + ".part"): os.remove(OUT + ".part")
    print("wrote %s : %d rows, %d failed, %.0fs"
          % (OUT, len(rows), bad, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
