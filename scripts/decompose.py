"""
decompose.py -- separate "better settings" from "adaptive settings".

Prior work benchmarks an optimised adaptive driver against a CONVENTIONAL
driver and reports the combined gain.  That conflates two different things:

    conventional  ->  optimised FIXED     "better settings"
    optimised fixed -> per-corner optimum "adaptation"

Only the second requires an FPGA, a LUT, or any operating-point sensing.
This decomposes the total so the two can be priced separately.
"""
import csv, os, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = ["NPU_LS", "NPD_LS", "NPD_HS", "DT", "CLKEN", "VNEG"]

# What a designer picks without optimisation: fastest driver, no clamp,
# no negative rail, a mid-range dead time.
CONVENTIONAL = dict(NPU_LS=8, NPD_LS=8, NPD_HS=8, DT="15n", CLKEN=0, VNEG=0)


def load(fn, tag=None):
    rows = []
    for r in csv.DictReader(open(os.path.join(ROOT, "results", fn))):
        for k, v in list(r.items()):
            if k in ("case", "corner", "DT", "CLKDEL"): continue
            try: r[k] = float(v)
            except (ValueError, TypeError): pass
        if tag and "corner" not in r: r["corner"] = tag
        rows.append(r)
    return rows


def main(w_ov=0.05):
    rows = load("sweep_nominal.csv", "100V_10A_25C") + load("full_corners.csv")
    word = lambda r: tuple(r[f] if f == "DT" else int(float(r[f])) for f in F)
    cost = lambda r: r["E_tot"] * 1e6 + w_ov * r["ov_pct"]
    corners = sorted({r["corner"] for r in rows})
    per = defaultdict(dict)
    for r in rows: per[word(r)][r["corner"]] = r
    conv = tuple(CONVENTIONAL[f] for f in F)

    if conv not in per or len(per[conv]) < len(corners):
        print("conventional word not present at every corner"); return
    c_conv = sum(cost(per[conv][c]) for c in corners) / len(corners)

    univ = [k for k, d in per.items()
            if len(d) == len(corners) and all(x["margin"] > 0 for x in d.values())]
    fixed = min(univ, key=lambda k: sum(cost(per[k][c]) for c in corners))
    c_fix = sum(cost(per[fixed][c]) for c in corners) / len(corners)

    sched = {c: min((r for r in rows if r["corner"] == c and r["margin"] > 0), key=cost)
             for c in corners}
    c_sch = sum(cost(sched[c]) for c in corners) / len(corners)

    print("Decomposition over %d corners, full 720-word search at each.\n" % len(corners))
    print("  %-34s %9s" % ("configuration", "mean cost"))
    print("  %-34s %9.3f   %s" % ("conventional (fastest, no clamp)", c_conv,
          "FALSE TURN-ON" if any(per[conv][c]["margin"] <= 0 for c in corners) else ""))
    print("  %-34s %9.3f" % ("optimised FIXED word", c_fix))
    print("  %-34s %9.3f" % ("per-corner optimum (scheduling)", c_sch))

    tot = 100 * (c_conv - c_sch) / c_conv
    from_fixed = 100 * (c_conv - c_fix) / c_conv
    from_sched = 100 * (c_fix - c_sch) / c_fix
    print("\n  total improvement over conventional ......... %5.1f %%" % tot)
    print("  of which, from better FIXED settings ........ %5.1f %% of conventional" % from_fixed)
    print("  of which, from ADAPTATION ................... %5.1f %% of the optimised fixed" % from_sched)
    if tot > 0:
        share = 100 * (c_conv - c_fix) / (c_conv - c_sch)
        print("\n  -> %.0f%% of the achievable gain needs NO adaptation at all." % share)
        print("     %.0f%% requires operating-point scheduling." % (100 - share))
    print("\n  conventional word : %s" % ("%d/%d/%d/%s/%d/%+g" % conv))
    print("  optimised fixed   : %s" % ("%d/%d/%d/%s/%d/%+g" % fixed))


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 0.05)
