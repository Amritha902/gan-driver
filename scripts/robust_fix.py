"""
robust_fix.py -- re-run the four cases robust.py silently no-opped.

robust.py perturbed the threshold and the transconductance by substituting
into the EGAN subcircuit's DEFAULT parameter line:

    .subckt EGAN d g s params: vth=1.4 bh=5.55 ...

but both devices are instantiated with those parameters passed explicitly:

    Xhs hsd hsg sw EGAN params: vth={VTH_T} bh={BH_T}
    Xls lsd lsg 0  EGAN params: vth={VTH_T} bh={BH_T}

so the defaults are overridden and the substitution changed nothing. It did
not error - the target string was present, it was just the wrong string. The
tell was in the output: VTH_hi, VTH_lo, BETA_hi and BETA_lo returned a ceiling
of 5.95 %, 978 feasible words and the same best fixed word as nominal, to the
digit. Four of eleven cases were measuring the unperturbed circuit.

The real targets are the .param lines that feed the instantiations:

    .param BH_T  = {5.55/KT}
    .param VTH_T = {1.4 - 0.0015*(TJ-25)}

Threshold needs one further thing that a string substitution cannot do. The
crosstalk margin is Vth - Vgs_spur, and gansim.metrics() computes Vth from its
own VTH_NOM constant. Perturbing the device threshold without moving that
constant would judge feasibility against the old threshold and quietly
invalidate every margin in the case. VTH_NOM is therefore set to match inside
each worker, before metrics() is called.
"""
import csv, itertools, os, re, subprocess, sys, tempfile, shutil, time
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gansim
from flatten import inline
from sweep import GRID

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "results", "robust_fix.csv")
CORNERS = [(100, 10, 25), (200, 2, 125)]        # same pair as robust.py

# case -> (substitution, new nominal threshold for the margin metric)
CASES = {
    "VTH_hi":  ({"1.4 - 0.0015*(TJ-25)": "1.68 - 0.0015*(TJ-25)"}, 1.68),
    "VTH_lo":  ({"1.4 - 0.0015*(TJ-25)": "1.12 - 0.0015*(TJ-25)"}, 1.12),
    "BETA_hi": ({"5.55/KT": "7.2/KT"},  None),
    "BETA_lo": ({"5.55/KT": "3.9/KT"},  None),
}

BASE = None


def build_base():
    global BASE
    BASE = inline(os.path.join(ROOT, "sim", "dpt.cir"))


def job(a):
    case, subs, vth_nom, cfg, vb, il, tj = a
    src = BASE
    for old, new in subs.items():
        if old not in src:
            return {"case": case, "error": "substitution %r not found" % old}
        if src.count(old) != 1:
            return {"case": case, "error": "%r is not unique (%d)" % (old, src.count(old))}
        src = src.replace(old, new)
    p = dict(gansim.DEFAULTS)
    p.update(cfg); p.update(VBUS=vb, ILOAD=il, TJ=tj)
    block = "\n".join(".param %s=%s" % (k, v) for k, v in p.items())
    src = re.sub(r"(?s)(==== PARAM BLOCK.*?====\n).*?(\* ====+ END PARAM BLOCK)",
                 lambda m: m.group(1) + block + "\n" + m.group(2), src)
    d = tempfile.mkdtemp(prefix="robfix_")
    try:
        open(os.path.join(d, "dpt.cir"), "w").write(src)
        subprocess.run(["ngspice", "-b", "dpt.cir"], cwd=d,
                       capture_output=True, text=True, timeout=300)
        f = os.path.join(d, "out.dat")
        if not os.path.exists(f) or os.path.getsize(f) < 1000:
            return None
        import numpy as np
        # the margin metric must judge against the PERTURBED threshold
        saved = gansim.VTH_NOM
        if vth_nom is not None:
            gansim.VTH_NOM = vth_nom
        try:
            m = gansim.metrics(np.loadtxt(f), p)
        finally:
            gansim.VTH_NOM = saved
        m.update(case=case, corner="%dV_%dA_%dC" % (vb, il, tj),
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
    jobs = [(c, s, vt, w, vb, il, tj)
            for c, (s, vt) in CASES.items()
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
            if n % 250 == 0:
                el = time.time() - t0
                print("  %5d/%d  %.0fs  eta %.0fs  failed=%d"
                      % (n, len(jobs), el, el * (len(jobs) - n) / n, bad), flush=True)
            if n % 500 == 0 and rows:          # checkpoint; robust.py did not
                _write(rows, OUT + ".part")
    if not rows:
        print("no rows -- aborting"); return
    _write(rows, OUT)
    if os.path.exists(OUT + ".part"):
        os.remove(OUT + ".part")
    print("wrote %s : %d rows, %d failed, %.0fs"
          % (OUT, len(rows), bad, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
