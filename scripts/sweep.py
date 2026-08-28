"""
sweep.py -- walk the control word at the nominal corner, write results.csv

Sweep budget is deliberate, not exhaustive.  A full 16-bit sweep is 65536
transients; this is 720, which is what one evening buys you.
"""
import csv, itertools, os, sys, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gansim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "results", "sweep_nominal.csv")

GRID = dict(
    NPU_LS = [1, 2, 3, 4, 6, 8],     # LS pull-up  -> turn-on speed
    NPD_LS = [2, 8],                 # LS pull-down-> turn-off speed
    NPD_HS = [1, 4, 8],              # HS pull-down-> crosstalk holding
    DT     = ["5n", "10n", "15n", "25n", "35n"],
    CLKEN  = [0, 1],                 # active Miller clamp
    VNEG   = [0, -2],                # negative off-bias
)


def job(c):
    return gansim.run(**c)


def main():
    keys  = list(GRID)
    combos = [dict(zip(keys, v)) for v in itertools.product(*(GRID[k] for k in keys))]
    print("points: %d" % len(combos), flush=True)
    t0, rows, bad = time.time(), [], 0
    with Pool(4) as pool:
        for n, r in enumerate(pool.imap_unordered(job, combos, chunksize=4), 1):
            if r is None:
                bad += 1
            else:
                rows.append(r)
            if n % 40 == 0:
                print("  %4d/%d  %.0fs  failed=%d"
                      % (n, len(combos), time.time() - t0, bad), flush=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cols = list(rows[0])
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print("wrote %s : %d rows, %d failed, %.0fs"
          % (OUT, len(rows), bad, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
