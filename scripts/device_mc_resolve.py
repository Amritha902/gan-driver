# -*- coding: utf-8 -*-
"""device_mc_resolve.py -- settle the one device where the ordering failed.

    python3 scripts/device_mc_resolve.py 18

device_mc.py evaluates 36 candidate words per device because 720 x 24 is not
affordable. A subset can only raise the best fixed word's cost, so it deflates
(A) and inflates (B). On device 18 the ordering came out (A) 14.0 % < (B)
21.5 % -- and that device had only 22 of 36 words safe at every corner, which
is precisely the condition where the handicap bites hardest.

So the failure is either real or an artefact of the subset, and one run of the
FULL 720-word grid on that device decides which. 2880 transients, ~75 min.
Checkpointed like device_mc.py.
"""
import csv, itertools, os, re, subprocess, sys, tempfile, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gansim, device_mc as MC

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEV  = int(sys.argv[1]) if len(sys.argv) > 1 else 18
OUT  = os.path.join(ROOT, "results", "device_mc_full_dev%d.csv" % DEV)

GRID = dict(NPU_LS=[1, 2, 3, 4, 6, 8], NPD_LS=[2, 8], NPD_HS=[1, 4, 8],
            DT=["5n", "10n", "15n", "25n", "35n"], CLKEN=[0, 1], VNEG=[0, -2])


def all_words():
    keys = list(GRID)
    return [dict(zip(keys, v)) for v in itertools.product(*(GRID[k] for k in keys))]


def main():
    MC.build_base()
    dev = MC.sample_devices(24)[DEV]
    words = all_words()
    print("device %d: vth=%.3f bh=%.2f cgs=%.0fp CJO=%.0fp"
          % (DEV, dev["vth"], dev["bh"], dev["cgs"], dev["CJO"]), flush=True)
    print("%d words x %d corners = %d transients"
          % (len(words), len(MC.CORNERS), len(words) * len(MC.CORNERS)), flush=True)

    done = set()
    if os.path.exists(OUT):
        with open(OUT) as f:
            for r in csv.DictReader(f):
                done.add((r["NPU_LS"], r["NPD_LS"], r["NPD_HS"], r["DT"],
                          r["CLKEN"], r["VNEG"], r["VBUS"], r["ILOAD"], r["TJ"]))
    jobs = []
    for w in words:
        for c in MC.CORNERS:
            k = tuple(str(w[x]) for x in ("NPU_LS", "NPD_LS", "NPD_HS", "DT",
                                          "CLKEN", "VNEG")) + tuple(str(y) for y in c)
            if k not in done:
                jobs.append((dev, w, c))
    print("%d already done, %d to run" % (len(done), len(jobs)), flush=True)
    if not jobs:
        print("nothing to do"); return

    fields = ["dev", "VBUS", "ILOAD", "TJ", "NPU_LS", "NPD_LS", "NPD_HS",
              "DT", "CLKEN", "VNEG", "E_tot", "ov_pct", "margin", "Vgs_spur_hs"]
    new = not os.path.exists(OUT)
    fh = open(OUT, "a", newline="")
    wr = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
    if new:
        wr.writeheader()
    t0, n, bad = time.time(), 0, 0
    with Pool(4) as pool:
        for r in pool.imap_unordered(MC.job, jobs, chunksize=4):
            n += 1
            if "error" in r:
                bad += 1
            else:
                wr.writerow(r)
            if n % 200 == 0:
                fh.flush()
                el = time.time() - t0
                print("  %5d/%d  %.0fs  eta %.0fs  failed=%d"
                      % (n, len(jobs), el, el / n * (len(jobs) - n), bad), flush=True)
    fh.close()
    print("wrote %s  (%d failed)" % (OUT, bad), flush=True)


if __name__ == "__main__":
    main()
