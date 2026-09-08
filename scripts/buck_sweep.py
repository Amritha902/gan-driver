"""
buck_sweep.py -- the drive-strength trade-off, measured on the CONVERTER.

The 720-word search was run on the double-pulse bench, because 2,880 converter
runs is not affordable. This is the check that the bench was measuring the
right thing: the same knob, swept on the real converter, and the same
trade-off appearing in converter-level quantities (efficiency, output
voltage, device stress) rather than in per-edge ones.
"""
import os, sys, csv, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bucksim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "results", "buck_sweep.csv")

POINTS = []
for n in (1, 2, 3, 4, 6, 8):
    POINTS.append(("clamp on, -2 V", n, 1, -2))
for n in (1, 8):
    POINTS.append(("no clamp, 0 V", n, 0, 0))

rows, t0 = [], time.time()
print("%-18s %6s %8s %8s %8s %8s %8s %9s" %
      ("configuration", "slices", "Vout V", "Pout W", "eff %", "loss W",
       "SW pk V", "crosstalk"))
print("-" * 84)
for lab, n, clken, vneg in POINTS:
    r = bucksim.run(NPU_LS=n, NPU_HS=n, CLKEN=clken, VNEG=vneg)
    if r is None:
        print("%-18s %6d   FAILED" % (lab, n)); continue
    r["config"], r["slices"] = lab, n
    rows.append(r)
    print("%-18s %6d %8.2f %8.2f %8.2f %8.3f %8.1f %9s" %
          (lab, n, r["Vout"], r["Pout"], r["eff"], r["loss"], r["sw_pk"],
           "safe" if clken else "-"))

keys = sorted(rows[0].keys())
with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys); w.writeheader()
    for r in rows: w.writerow(r)
print("\n%d converter runs in %.0f s -> %s" % (len(rows), time.time() - t0, OUT))
