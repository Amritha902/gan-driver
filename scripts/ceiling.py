"""
ceiling.py -- the definitive test of how much operating-point scheduling can
possibly buy.

Uses FULL 720-word sweeps at four corners (nominal + three extremes), so the
per-corner optimum is the true optimum, not the best of a pre-selected
candidate list.  If scheduling still buys little here, the negative result in
FINDINGS section 14 is established rather than merely suggested.
"""
import csv, os, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELDS = ["NPU_LS", "NPD_LS", "NPD_HS", "DT", "CLKEN", "VNEG"]
NOMINAL = "100V_10A_25C"


def numify(r):
    for k, v in list(r.items()):
        if k in ("corner", "DT", "CLKDEL"): continue
        try: r[k] = float(v)
        except (ValueError, TypeError): pass
    return r


def load():
    rows = []
    for r in csv.DictReader(open(os.path.join(ROOT, "results", "sweep_nominal.csv"))):
        r = numify(r); r["corner"] = NOMINAL; rows.append(r)
    p = os.path.join(ROOT, "results", "full_corners.csv")
    if os.path.exists(p):
        rows += [numify(r) for r in csv.DictReader(open(p))]
    return rows


word = lambda r: tuple(r[f] if f == "DT" else int(r[f]) for f in FIELDS)


def main(w_ov=0.05):
    rows = load()
    by = defaultdict(dict)
    for r in rows:
        by[word(r)][r["corner"]] = r
    corners = sorted({r["corner"] for r in rows})
    cost = lambda r: r["E_tot"] * 1e6 + w_ov * r["ov_pct"]
    print("Full 720-word sweeps at %d corners: %s\n" % (len(corners), ", ".join(corners)))

    print("Per-corner TRUE optimum (searched all 720 words):")
    sched = {}
    for c in corners:
        feas = [r for r in rows if r["corner"] == c and r["margin"] > 0]
        if not feas:
            print("  %-16s NO FEASIBLE WORD in the entire 720" % c); continue
        b = min(feas, key=cost); sched[c] = b
        print("  %-16s %-26s cost %7.3f  margin %+.2f"
              % (c, "%d/%d/%d/%s/%d/%+g" % word(b), cost(b), b["margin"]))

    univ = [k for k, d in by.items()
            if len(d) == len(corners) and all(x["margin"] > 0 for x in d.values())]
    print("\nWords feasible at ALL %d corners: %d of %d" % (len(corners), len(univ), len(by)))
    if not univ:
        print("-> no universal word: scheduling is REQUIRED."); return
    fixed = min(univ, key=lambda k: sum(cost(by[k][c]) for c in corners))
    cf = sum(cost(by[fixed][c]) for c in corners) / len(corners)
    cs = sum(cost(sched[c]) for c in corners) / len(corners)
    print("Best fixed word  : %-26s mean cost %7.3f"
          % ("%d/%d/%d/%s/%d/%+g" % fixed, cf))
    print("Per-corner optimum:                            mean cost %7.3f" % cs)
    print("\nCEILING on scheduling at w_ov=%.2f : %.1f%%" % (w_ov, 100 * (cf - cs) / cf))
    print("\nPer-corner breakdown (how much the fixed word loses at each):")
    for c in corners:
        print("  %-16s fixed %7.3f   optimum %7.3f   penalty %5.1f%%"
              % (c, cost(by[fixed][c]), cost(sched[c]),
                 100 * (cost(by[fixed][c]) - cost(sched[c])) / cost(by[fixed][c])))


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 0.05)
