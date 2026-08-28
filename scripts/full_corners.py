"""
full_corners.py -- the FULL 720-word sweep at a few extreme corners.

Purpose: establish the CEILING on operating-point scheduling.  The 36-corner
study used 42 candidate words chosen at the nominal corner, so it could only
show that scheduling is worth little FOR THAT CANDIDATE SET.  Sweeping all
720 words at corners far from nominal removes that objection: if a
corner-specific word existed that beat the fixed word substantially, a full
sweep at that corner would find it.

Corners chosen at the extremes of the grid, where the optimum has the best
chance of moving:
    50 V / 2 A / 25 C     lightest, coldest
    200 V / 10 A / 125 C  heaviest, hottest
    200 V / 2 A / 125 C   high voltage, light load, hot
The nominal corner (100 V / 10 A / 25 C) already has a full sweep in
sweep_nominal.csv and is reused rather than recomputed.
"""
import csv, itertools, os, sys, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gansim
from sweep import GRID

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "results", "full_corners.csv")

CORNERS = [(50, 2, 25), (200, 10, 125), (200, 2, 125)]


def job(a):
    cfg, vb, il, tj = a
    r = gansim.run(VBUS=vb, ILOAD=il, TJ=tj, **cfg)
    if r is None:
        return None
    r["corner"] = "%dV_%dA_%dC" % (vb, il, tj)
    return r


def main():
    keys = list(GRID)
    words = [dict(zip(keys, v)) for v in itertools.product(*(GRID[k] for k in keys))]
    jobs = [(w, vb, il, tj) for (vb, il, tj) in CORNERS for w in words]
    print("words: %d   corners: %d   -> %d transients"
          % (len(words), len(CORNERS), len(jobs)), flush=True)
    t0, rows, bad = time.time(), [], 0
    with Pool(4) as pool:
        for n, r in enumerate(pool.imap_unordered(job, jobs, chunksize=4), 1):
            if r is None: bad += 1
            else: rows.append(r)
            if n % 200 == 0:
                el = time.time() - t0
                print("  %4d/%d  %.0fs  eta %.0fs  failed=%d"
                      % (n, len(jobs), el, el * (len(jobs) - n) / n, bad), flush=True)
    cols = list(rows[0])
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print("wrote %s : %d rows, %d failed, %.0fs"
          % (OUT, len(rows), bad, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
