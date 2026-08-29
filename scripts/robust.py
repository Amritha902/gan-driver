"""
robust.py -- is the scheduling-ceiling result robust to the device model?

The ceiling result (scheduling buys <=5.2%) is the project's strongest claim,
and its most obvious vulnerability is that the GaN model is behavioural and
hand-built.  A reviewer will ask whether the conclusion is a property of the
power stage or of our model parameters.

This perturbs the parameters that plausibly drive the answer and recomputes
the ceiling from a FULL 720-word search at each of two corners:

    CGD0   Miller capacitance   +-50%   (drives crosstalk directly)
    CGS    input capacitance    +-30%
    VTH    threshold            +-20%   (drives the false-turn-on limit)
    LLOOP  power-loop inductance+-50%   (drives overshoot and ringing)
    BETA   transconductance     +-30%   (drives R_on and switching speed)

If the ceiling stays in single digits across all of these, the conclusion is
about the circuit, not about our parameter choices.
"""
import csv, itertools, os, re, subprocess, sys, tempfile, shutil, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gansim
from flatten import inline
from sweep import GRID

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "results", "robust.csv")
CORNERS = [(100, 10, 25), (200, 2, 125)]      # nominal + the divergent corner

CASES = {
    "nominal":    {},
    "CGD0_hi":    {"CJO=150p": "CJO=225p"},
    "CGD0_lo":    {"CJO=150p": "CJO=75p"},
    "CGS_hi":     {"cgs=350p": "cgs=455p"},
    "CGS_lo":     {"cgs=350p": "cgs=245p"},
    "VTH_hi":     {"vth=1.4":  "vth=1.68"},
    "VTH_lo":     {"vth=1.4":  "vth=1.12"},
    "LLOOP_hi":   {"LLOOP = 3n": "LLOOP = 4.5n"},
    "LLOOP_lo":   {"LLOOP = 3n": "LLOOP = 1.5n"},
    "BETA_hi":    {"bh=5.55":  "bh=7.2"},
    "BETA_lo":    {"bh=5.55":  "bh=3.9"},
}

BASE = None


def build_base():
    global BASE
    BASE = inline(os.path.join(ROOT, "sim", "dpt.cir"))


def job(a):
    case, subs, cfg, vb, il, tj = a
    src = BASE
    for old, new in subs.items():
        if old not in src:
            return {"case": case, "error": "substitution %r not found" % old}
        src = src.replace(old, new)
    p = dict(gansim.DEFAULTS)
    p.update(cfg); p.update(VBUS=vb, ILOAD=il, TJ=tj)
    block = "\n".join(".param %s=%s" % (k, v) for k, v in p.items())
    src = re.sub(r"(?s)(==== PARAM BLOCK.*?====\n).*?(\* ====+ END PARAM BLOCK)",
                 lambda m: m.group(1) + block + "\n" + m.group(2), src)
    d = tempfile.mkdtemp(prefix="rob_")
    try:
        open(os.path.join(d, "dpt.cir"), "w").write(src)
        subprocess.run(["ngspice", "-b", "dpt.cir"], cwd=d,
                       capture_output=True, text=True, timeout=300)
        f = os.path.join(d, "out.dat")
        if not os.path.exists(f) or os.path.getsize(f) < 1000:
            return None
        import numpy as np
        m = gansim.metrics(np.loadtxt(f), p)
        m.update(case=case, corner="%dV_%dA_%dC" % (vb, il, tj), **{k: v for k, v in cfg.items()})
        return m
    except Exception:
        return None
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main():
    build_base()
    keys = list(GRID)
    words = [dict(zip(keys, v)) for v in itertools.product(*(GRID[k] for k in keys))]
    jobs = [(c, s, w, vb, il, tj)
            for c, s in CASES.items()
            for (vb, il, tj) in CORNERS
            for w in words]
    print("cases: %d   corners: %d   words: %d   -> %d transients"
          % (len(CASES), len(CORNERS), len(words), len(jobs)), flush=True)
    t0, rows, bad = time.time(), [], 0
    with Pool(4) as pool:
        for n, r in enumerate(pool.imap_unordered(job, jobs, chunksize=8), 1):
            if r is None or "error" in r:
                bad += 1
                if r and "error" in r and bad < 3:
                    print("  ERROR: %s" % r["error"], flush=True)
            else:
                rows.append(r)
            if n % 500 == 0:
                el = time.time() - t0
                print("  %5d/%d  %.0fs  eta %.0fs  failed=%d"
                      % (n, len(jobs), el, el * (len(jobs) - n) / n, bad), flush=True)
    cols = list(rows[0])
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    print("wrote %s : %d rows, %d failed, %.0fs" % (OUT, len(rows), bad, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
