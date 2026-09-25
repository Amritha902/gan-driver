"""converter_numbers.py -- the converter's own headline, read from the sweep.

Slides 6, 7, 14 and 31 all quote "the converter". They disagreed: slide 14
was corrected on 24 Sep when an audit found the headline had been taken at
the wrong off rail, and the other three kept the 8 Sep text -- 236.9 W and
97.7 % against 236.3 W and 97.5 %. Nothing re-derived either, so nothing
caught it.

This reads the shipped row out of results/buck_sweep.csv instead: clamp on,
-2 V off rail, all eight slices, which is the word the project ships. Every
slide that quotes the converter now quotes the same run.
"""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(ROOT, "results", "buck_sweep.csv")


def shipped():
    """The shipped operating point: CLKEN=1, VNEG=-2, all eight slices."""
    with open(CSV) as fh:
        rows = list(csv.DictReader(fh))
    want = [r for r in rows
            if r["CLKEN"] == "1" and float(r["VNEG"]) == -2.0
            and float(r["slices"]) == 8.0]
    if len(want) != 1:
        raise SystemExit("buck_sweep.csv: expected exactly one shipped row "
                         "(CLKEN=1, VNEG=-2, 8 slices), found %d" % len(want))
    r = want[0]
    return {k: float(r[k]) for k in
            ("Vin", "Iin", "Vout", "Iout", "Pin", "Pout", "eff", "loss",
             "sw_pk", "ov_pct")}


V = shipped()

# Pre-rendered strings, so every slide spells the same number the same way.
VIN   = "%.0f V"   % V["Vin"]
VOUT  = "%.2f V"   % V["Vout"]
IOUT  = "%.3f A"   % V["Iout"]
PIN   = "%.2f W"   % V["Pin"]
POUT  = "%.2f W"   % V["Pout"]
EFF   = "%.2f %%"  % V["eff"]
SWPK  = "%.1f V"   % V["sw_pk"]
OV    = "%.1f %%"  % V["ov_pct"]

if __name__ == "__main__":
    for k in sorted(V):
        print("  %-8s %12.4f" % (k, V[k]))
    print("\n  %s in -> %s at %s: %s drawn, %s delivered, %s efficient"
          % (VIN, VOUT, IOUT, PIN, POUT, EFF))
