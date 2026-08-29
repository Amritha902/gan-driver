"""
robust_analyse.py -- ceiling on operating-point scheduling, per model case.

For each device-model perturbation, recompute from the FULL 720-word search:
    per-corner optimum   vs   best single fixed word across both corners
If the ceiling stays in single digits under every perturbation, the result is
a property of the circuit rather than of our parameter choices.
"""
import csv, os, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = ["NPU_LS", "NPD_LS", "NPD_HS", "DT", "CLKEN", "VNEG"]
W_OV = 0.05


def main(w_ov=W_OV):
    rows = []
    for r in csv.DictReader(open(os.path.join(ROOT, "results", "robust.csv"))):
        for k, v in list(r.items()):
            if k in ("case", "corner", "DT", "CLKDEL"): continue
            try: r[k] = float(v)
            except (ValueError, TypeError): pass
        rows.append(r)
    word = lambda r: tuple(r[f] if f == "DT" else int(float(r[f])) for f in F)
    cost = lambda r: r["E_tot"] * 1e6 + w_ov * r["ov_pct"]

    by_case = defaultdict(list)
    for r in rows: by_case[r["case"]].append(r)

    print("Ceiling on operating-point scheduling, per device-model case.")
    print("Full 720-word search at each of 2 corners.\n")
    print("  %-12s %7s %8s %10s   %s" % ("case", "corners", "feasible", "ceiling", "best fixed word"))
    ceilings = {}
    for case in sorted(by_case):
        rs = by_case[case]
        corners = sorted({r["corner"] for r in rs})
        per = defaultdict(dict)
        for r in rs: per[word(r)][r["corner"]] = r
        sched, ok = {}, True
        for c in corners:
            feas = [r for r in rs if r["corner"] == c and r["margin"] > 0]
            if not feas: ok = False; break
            sched[c] = min(feas, key=cost)
        if not ok:
            print("  %-12s  no feasible word at some corner" % case); continue
        univ = [k for k, d in per.items()
                if len(d) == len(corners) and all(x["margin"] > 0 for x in d.values())]
        if not univ:
            print("  %-12s  no universal word -> scheduling REQUIRED" % case); continue
        fixed = min(univ, key=lambda k: sum(cost(per[k][c]) for c in corners))
        cf = sum(cost(per[fixed][c]) for c in corners) / len(corners)
        cs = sum(cost(sched[c]) for c in corners) / len(corners)
        ceil = 100 * (cf - cs) / cf
        ceilings[case] = ceil
        nfeas = sum(1 for r in rs if r["margin"] > 0)
        print("  %-12s %7d %8d %9.1f%%   %s"
              % (case, len(corners), nfeas, ceil, "%d/%d/%d/%s/%d/%+g" % fixed))
    if not ceilings:
        return
    v = list(ceilings.values())
    nom = ceilings.get("nominal")
    print("\n  ceiling across %d model perturbations: %.1f%% .. %.1f%%  (median %.1f%%)"
          % (len(v), min(v), max(v), sorted(v)[len(v) // 2]))

    # The 5.2 % headline is a FOUR-corner result. This study runs two corners,
    # so its own nominal case is the baseline -- comparing a perturbed
    # two-corner ceiling against the four-corner 5.2 % would be meaningless.
    if nom is None:
        print("  (no nominal case in the data -- shifts below cannot be computed)")
        return
    print("\n  Baseline: this study's own NOMINAL case is %.1f%% on these two corners." % nom)
    print("  It is not the 5.2% headline, which is a four-corner result. Each")
    print("  perturbation is judged against %.1f%%, not against 5.2%%.\n" % nom)
    print("  %-12s %9s %11s   %s" % ("case", "ceiling", "vs nominal", "direction"))
    for case in sorted(ceilings, key=lambda c: -abs(ceilings[c] - nom)):
        d = ceilings[case] - nom
        arrow = "--" if case == "nominal" else ("higher" if d > 0 else "lower")
        print("  %-12s %8.2f%% %+10.2f pp   %s" % (case, ceilings[case], d, arrow))

    worst = max(v)
    spread = max(v) - min(v)
    print("\n  Largest excursion from nominal: %+.2f pp. Full spread: %.2f pp."
          % (max((ceilings[c] - nom for c in ceilings), key=abs), spread))
    # "nominal" is the baseline, not a perturbation: if IT is already double
    # digits that is a statement about the corner pair, not about robustness.
    hi = sorted(c for c in ceilings if c != "nominal" and ceilings[c] >= 10)
    if nom >= 10:
        print("  -> NOTE: the nominal case is itself %.1f%% on this corner pair." % nom)
        print("     That is a property of the two corners chosen, not of the model.")
    if worst < 10:
        print("  -> ROBUST: single digits under every perturbation tested. The")
        print("     ceiling is a property of the circuit, not of the model parameters.")
    elif not hi:
        print("  -> ROBUST: no perturbation reaches double digits.")
    else:
        print("  -> NOT robust: %s push the ceiling into double digits." % ", ".join(hi))
        print("     The central claim must be restated as conditional on the device")
        print("     parameters, naming these perturbations.")


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else W_OV)
