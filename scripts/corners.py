"""
corners.py -- sweep the 36-point operating grid and extract the schedule LUT.

A full control-word sweep at every corner is 720 x 36 = 25,920 transients.
Instead: take a candidate set from the nominal-corner analysis (the feasible
Pareto front plus a spread of good words plus the fixed-strength baseline),
and evaluate only those at each corner.  That is the sweep budget the plan
allowed for, and it is what makes the LUT affordable.

Uses the ideal-switch netlist: it is the one verified converged (122.5 V flat
across a 25x range of maxstep).  The SKY130 transistor-level netlist is NOT
used here -- its transient does not converge.  See FINDINGS.md 10-12.
"""
import csv, itertools, os, sys, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gansim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOM  = os.path.join(ROOT, "results", "sweep_nominal.csv")
OUT  = os.path.join(ROOT, "results", "corners.csv")

VBUS = [50, 100, 150, 200]
ILOAD = [2, 5, 10]
TJ    = [25, 75, 125]
W_OV  = 0.05                      # uJ per point of overshoot, stated cost

FIELDS = ["NPU_LS", "NPD_LS", "NPD_HS", "DT", "CLKEN", "VNEG"]


def candidates(n_extra=32):
    rows = list(csv.DictReader(open(NOM)))
    for r in rows:
        for k, v in r.items():
            try: r[k] = float(v)
            except ValueError: pass
    feas = [r for r in rows if r["margin"] > 0]
    x = [r["E_tot"] for r in feas]; y = [r["ov_pct"] for r in feas]
    front = [feas[i] for i in range(len(feas))
             if not any(x[j] <= x[i] and y[j] <= y[i] and
                        (x[j] < x[i] or y[j] < y[i]) for j in range(len(feas)))]
    rest = sorted((r for r in feas if r not in front),
                  key=lambda r: r["E_tot"] + W_OV * r["ov_pct"])[:n_extra]
    base = [r for r in rows if r["NPU_LS"] == 8 and r["NPD_LS"] == 8
            and r["CLKEN"] == 0 and r["VNEG"] == 0 and r["DT"] == "15n"]
    words, seen = [], set()
    for r in front + rest + base:
        w = tuple(r[f] for f in FIELDS)
        if w in seen: continue
        seen.add(w)
        words.append({f: (r[f] if f == "DT" else int(r[f])) for f in FIELDS})
    return words, len(front)


def job(a):
    word, vb, il, tj = a
    r = gansim.run(VBUS=vb, ILOAD=il, TJ=tj, **word)
    if r is None: return None
    r["corner"] = "%dV_%dA_%dC" % (vb, il, tj)
    return r


def main():
    words, nfront = candidates()
    corners = list(itertools.product(VBUS, ILOAD, TJ))
    jobs = [(w, vb, il, tj) for (vb, il, tj) in corners for w in words]
    print("candidate words: %d (%d on the nominal front)" % (len(words), nfront))
    print("corners: %d   -> %d transients" % (len(corners), len(jobs)), flush=True)
    t0, rows, bad = time.time(), [], 0
    with Pool(4) as pool:
        for n, r in enumerate(pool.imap_unordered(job, jobs, chunksize=4), 1):
            if r is None: bad += 1
            else: rows.append(r)
            if n % 100 == 0:
                print("  %4d/%d  %.0fs  failed=%d"
                      % (n, len(jobs), time.time() - t0, bad), flush=True)
    cols = list(rows[0])
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print("wrote %s : %d rows, %d failed, %.0fs"
          % (OUT, len(rows), bad, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
