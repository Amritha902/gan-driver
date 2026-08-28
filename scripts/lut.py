"""
lut.py -- extract the schedule LUT from the corner sweep and, more
importantly, test whether operating-point scheduling is worth doing at all.

The headline number is not the LUT.  It is the comparison between:
    (a) per-corner scheduling  -- the best word chosen at each corner
    (b) one fixed word everywhere -- the best single compromise
If (a) barely beats (b), the FPGA is not earning its place and the honest
thing is to say so.
"""
import csv, os, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC  = os.path.join(ROOT, "results", "corners.csv")
W_OV = 0.05                       # uJ per point of overshoot -- stated cost
FIELDS = ["NPU_LS", "NPD_LS", "NPD_HS", "DT", "CLKEN", "VNEG"]


def load():
    rows = list(csv.DictReader(open(SRC)))
    for r in rows:
        for k, v in r.items():
            if k in ("corner", "DT", "CLKDEL"): continue
            try: r[k] = float(v)
            except (ValueError, TypeError): pass
    return rows


def word(r):
    return tuple(r[f] if f == "DT" else int(r[f]) for f in FIELDS)


def cost(r):
    return r["E_tot"] * 1e6 + W_OV * r["ov_pct"]


def main():
    rows = load()
    by_corner = defaultdict(list)
    for r in rows:
        by_corner[r["corner"]].append(r)
    corners = sorted(by_corner, key=lambda c: (int(c.split("V")[0]),
                                               int(c.split("_")[1][:-1]),
                                               int(c.split("_")[2][:-1])))
    print("=== Schedule LUT, cost = E_tot + %.2f x overshoot ===\n" % W_OV)
    print("%-16s %-28s %8s %8s %8s" % ("corner", "word (PU/PD/PDHS/DT/CLK/VNEG)",
                                       "E_tot", "ov%", "margin"))
    lut, infeasible = {}, []
    for c in corners:
        feas = [r for r in by_corner[c] if r["margin"] > 0]
        if not feas:
            infeasible.append(c)
            print("%-16s %-28s %8s" % (c, "NO FEASIBLE WORD", "--"))
            continue
        best = min(feas, key=cost)
        lut[c] = best
        w = word(best)
        print("%-16s %-28s %8.2f %8.1f %+8.2f"
              % (c, "%d/%d/%d/%s/%d/%+g" % w, best["E_tot"] * 1e6,
                 best["ov_pct"], best["margin"]))

    print("\n=== Does the optimal word actually move? ===")
    uniq = {word(b) for b in lut.values()}
    print("distinct words across %d solved corners: %d" % (len(lut), len(uniq)))
    for w in sorted(uniq, key=str):
        n = sum(1 for b in lut.values() if word(b) == w)
        print("   %-28s used at %2d corner(s)" % ("%d/%d/%d/%s/%d/%+g" % w, n))

    print("\n=== Is scheduling worth it? ===")
    #  best single fixed word: the one with the lowest total cost across all
    #  corners where it is feasible everywhere
    per_word = defaultdict(dict)
    for r in rows:
        per_word[word(r)][r["corner"]] = r
    universal = [w for w, d in per_word.items()
                 if len(d) == len(corners) and all(x["margin"] > 0 for x in d.values())]
    if not universal:
        print("No single word is feasible at every corner.")
        print("-> scheduling is REQUIRED, not merely an optimisation.")
        for w, d in per_word.items():
            ok = sum(1 for x in d.values() if x["margin"] > 0)
            per_word[w]["_ok"] = ok
        bestcov = max(per_word, key=lambda w: per_word[w]["_ok"])
        print("   best fixed word covers %d of %d corners: %s"
              % (per_word[bestcov]["_ok"], len(corners),
                 "%d/%d/%d/%s/%d/%+g" % bestcov))
    else:
        fixed = min(universal,
                    key=lambda w: sum(cost(per_word[w][c]) for c in corners))
        c_fixed = sum(cost(per_word[fixed][c]) for c in corners) / len(corners)
        c_sched = sum(cost(lut[c]) for c in lut) / len(lut)
        print("best fixed word : %s   mean cost %.3f"
              % ("%d/%d/%d/%s/%d/%+g" % fixed, c_fixed))
        print("per-corner sched: mean cost %.3f" % c_sched)
        gain = 100 * (c_fixed - c_sched) / c_fixed
        print("scheduling buys %.1f%%" % gain)
        print("-> %s" % ("worth the FPGA" if gain > 5 else
                         "MARGINAL: report this honestly, the fixed word is nearly as good"))
    if infeasible:
        print("\nCorners with no feasible candidate word: %s" % ", ".join(infeasible))
        print("(the candidate set came from the nominal corner; these need their own sweep)")


if __name__ == "__main__":
    main()
