"""
cases.py -- specific cases, run one at a time, with what came out.

"We searched 720 settings" describes a procedure. It is not something anyone
can check, picture, or disagree with. These are named cases -- each one a
decision somebody actually has to make when building this converter -- run
separately in ngspice, each printing its own result.

PART 1 builds the crosstalk fix one change at a time, so the effect of each
change is visible on its own line rather than bundled into a claim.

PART 2 is the case for adapting at all: the same driver at two operating
points, where the dead time that costs least is not the same number.

The 720-point search is still what found case 5. This is what it found, put
where it can be read one line at a time.

    python3 scripts/cases.py
"""
import os, sys, csv, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gansim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "results", "cases.csv")
VTH  = 1.4

FULL = dict(VBUS=100, ILOAD=10)

BUILD = [
    ("1. Fastest drive, nothing else",
     "8 pull-up slices, no clamp, off gate at 0 V",
     dict(NPU_LS=8, NPU_HS=8, NPD_LS=8, NPD_HS=8, DT="15n", CLKEN=0, VNEG=0)),
    ("2. Turn the Miller clamp on",
     "same drive; the clamp shorts the off gate down",
     dict(NPU_LS=8, NPU_HS=8, NPD_LS=8, NPD_HS=8, DT="15n", CLKEN=1, VNEG=0)),
    ("3. Add the -2 V off-bias rail",
     "same again; the off gate now sits at -2 V, not 0 V",
     dict(NPU_LS=8, NPU_HS=8, NPD_LS=8, NPD_HS=8, DT="15n", CLKEN=1, VNEG=-2)),
    ("4. Slow the drive right down",
     "1 pull-up slice instead of 8 -- the safe-but-wasteful extreme",
     dict(NPU_LS=1, NPU_HS=1, NPD_LS=8, NPD_HS=8, DT="15n", CLKEN=1, VNEG=-2)),
    ("5. The setting the search chose",
     "8/8/1 slices, 25 ns dead time, clamp on, 0 V rail",
     dict(NPU_LS=8, NPU_HS=8, NPD_LS=8, NPD_HS=1, DT="25n", CLKEN=1, VNEG=0)),
]

CHOSEN = dict(NPU_LS=8, NPU_HS=8, NPD_LS=8, NPD_HS=1, CLKEN=1, VNEG=0)
POINTS = [("full load   100 V, 10 A", dict(VBUS=100, ILOAD=10)),
          ("light load   50 V,  2 A", dict(VBUS=50,  ILOAD=2))]
DEADTIMES = ["5n", "10n", "15n", "25n"]


def main():
    rows, t0 = [], time.time()

    print()
    print("  PART 1  --  building the fix, one change at a time")
    print("  Full load, 100 V and 10 A. The device switches on at %.1f V, so the" % VTH)
    print("  gate of the device that is meant to be OFF has to stay under that.")
    print()
    print("  %-33s %10s %10s %10s   %s"
          % ("case", "peak gate", "margin", "loss", "verdict"))
    print("  " + "-" * 84)
    for label, detail, kw in BUILD:
        p = dict(FULL); p.update(kw)
        r = gansim.run(**p)
        safe = r["margin"] > 0
        print("  %-33s %+9.3f V %+9.3f V %8.3f uJ   %s"
              % (label, r["Vgs_spur"], r["margin"], r["E_tot"] * 1e6,
                 "safe" if safe else "FALSE TURN-ON"))
        print("      %s" % detail)
        rows.append(dict(part=1, case=label, detail=detail, VBUS=100, ILOAD=10,
                         dead_time="", peak_V=round(r["Vgs_spur"], 4),
                         margin_V=round(r["margin"], 4),
                         loss_uJ=round(r["E_tot"] * 1e6, 4), safe=int(safe)))

    print()
    print("  PART 2  --  does one fixed setting fit every operating point?")
    print("  Case 5's driver, unchanged, at two operating points, sweeping only")
    print("  the dead time. If the cheapest dead time were the same number at")
    print("  both, there would be nothing to adapt.")
    print()
    for plabel, pt in POINTS:
        print("  %s" % plabel)
        best_l, best_dt = None, None
        for dt in DEADTIMES:
            p = dict(CHOSEN); p.update(pt); p["DT"] = dt
            r = gansim.run(**p)
            loss = r["E_tot"] * 1e6
            flag = "   <-- thin margin" if 0 < r["margin"] < 0.2 else ""
            print("      dead time %-4s   loss %7.3f uJ   margin %+7.3f V%s"
                  % (dt, loss, r["margin"], flag))
            rows.append(dict(part=2, case=plabel.strip(), detail="dead-time sweep",
                             VBUS=pt["VBUS"], ILOAD=pt["ILOAD"], dead_time=dt,
                             peak_V=round(r["Vgs_spur"], 4),
                             margin_V=round(r["margin"], 4),
                             loss_uJ=round(loss, 4), safe=int(r["margin"] > 0)))
            if best_l is None or loss < best_l:
                best_l, best_dt = loss, dt
        print("      cheapest: %s" % best_dt)
        print()

    print("  " + "-" * 84)
    print("  %d ngspice runs, %.0f s. Written to results/cases.csv"
          % (len(rows), time.time() - t0))
    print()

    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(r)


if __name__ == "__main__":
    main()
