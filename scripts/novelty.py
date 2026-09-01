"""
novelty.py -- decompose the gain into the two things the literature conflates.

An active-gate-driver paper reports one number: the improvement over a
conventional driver. That number bundles two separable effects:

    (A) choosing a better FIXED control word        -- needs no sensing
    (B) ADAPTING the word to the operating point    -- needs sensing, a LUT,
                                                       and a controller

Only (B) justifies the adaptive hardware, and no published work separates
them. This script measures both on the same data, which is the contribution.

The conventional word (fastest drive, no clamp) false-turns-on, so its cost is
not comparable -- a driver that destroys the device is not a cheaper driver.
So (A) is measured inside the FEASIBLE set instead: from a badly-chosen but
safe word to the best fixed word. That is a conservative floor for (A),
because it excludes the unsafe configurations entirely.
"""
import csv, os, sys
from collections import defaultdict
from statistics import median

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = ["NPU_LS", "NPD_LS", "NPD_HS", "DT", "CLKEN", "VNEG"]
W_OV = 0.05


def load():
    rows = []
    for fn, tag in (("sweep_nominal.csv", "100V_10A_25C"), ("full_corners.csv", None)):
        for r in csv.DictReader(open(os.path.join(ROOT, "results", fn))):
            for k, v in list(r.items()):
                if k in ("corner", "DT", "CLKDEL"): continue
                try: r[k] = float(v)
                except (ValueError, TypeError): pass
            if tag and "corner" not in r: r["corner"] = tag
            rows.append(r)
    return rows


def main(w_ov=W_OV):
    rows = load()
    cost = lambda r: r["E_tot"] * 1e6 + w_ov * r["ov_pct"]
    word = lambda r: tuple(r[f] if f == "DT" else int(r[f]) for f in F)
    corners = sorted({r["corner"] for r in rows})

    by = defaultdict(dict)
    for r in rows: by[word(r)][r["corner"]] = r

    # words that are SAFE at every corner -- the only ones a real design may use
    univ = [k for k, d in by.items()
            if len(d) == len(corners) and all(x["margin"] > 0 for x in d.values())]
    mean_cost = {k: sum(cost(by[k][c]) for c in corners) / len(corners) for k in univ}

    best_fixed  = min(univ, key=lambda k: mean_cost[k])
    worst_fixed = max(univ, key=lambda k: mean_cost[k])
    med_cost    = median(mean_cost.values())

    # per-corner scheduling: the true optimum at each corner
    sched = {}
    for c in corners:
        feas = [r for r in rows if r["corner"] == c and r["margin"] > 0]
        sched[c] = min(feas, key=cost)
    c_sched = sum(cost(sched[c]) for c in corners) / len(corners)
    c_best  = mean_cost[best_fixed]
    c_worst = mean_cost[worst_fixed]
    c_med   = med_cost

    fmt = lambda k: "%d/%d/%d/%s/%d/%+g" % k
    print("Decomposing the gain, %d corners, %d words safe at all of them.\n"
          % (len(corners), len(univ)))
    print("  %-42s %9s" % ("configuration", "mean cost"))
    print("  %-42s %9.3f   %s" % ("worst safe fixed word", c_worst, fmt(worst_fixed)))
    print("  %-42s %9.3f" % ("median safe fixed word", c_med))
    print("  %-42s %9.3f   %s" % ("BEST fixed word (no sensing needed)", c_best, fmt(best_fixed)))
    print("  %-42s %9.3f   (per-corner)" % ("per-corner optimum (needs sensing)", c_sched))

    # ONE baseline for every percentage. An earlier version expressed (B) as a
    # fraction of the best fixed word and the total as a fraction of the WORST,
    # then divided one by the other and called the answer a share. It is not a
    # share of anything: the numerator and denominator had different bases.
    # Everything below is relative to the median safe fixed word.
    base = c_med
    A, B, T = base - c_best, c_best - c_sched, base - c_sched

    print("\n  All percentages below share ONE baseline: the median safe fixed")
    print("  word, cost %.3f. Mixing baselines is how a share stops meaning" % base)
    print("  anything, so it is done once here and not again.\n")
    print("  %-46s %8s %9s" % ("", "cost", "of base"))
    print("  %-46s %8.3f %8.1f%%" % ("(A) choosing a better FIXED word", A, 100*A/base))
    print("  %-46s %8.3f %8.1f%%" % ("(B) ADAPTING it per operating point", B, 100*B/base))
    print("  %-46s %8.3f %8.1f%%" % ("total available", T, 100*T/base))
    print("\n  -> adaptation is %.1f %% of the total gain." % (100*B/T))
    print("     The other %.1f %% needs no sensing, no lookup table, no controller."
          % (100 - 100*B/T))

    # How much of (B) survives if the controller may pick between only TWO
    # words on a single threshold? Exhaustive over the 7 two-way splits.
    def best_for(group):
        cand = [k for k, d in by.items()
                if all(c in d and d[c]["margin"] > 0 for c in group)]
        if not cand: return None
        k = min(cand, key=lambda k: sum(cost(by[k][c]) for c in group))
        return sum(cost(by[k][c]) for c in group)

    out = {"A_pct": 100*A/base, "B_pct": 100*B/base, "T_pct": 100*T/base,
           "share": 100*B/T, "closed": None, "residual": None}

    best2 = None
    for mask in range(1, 2 ** len(corners) - 1):
        g1 = [c for i, c in enumerate(corners) if mask >> i & 1]
        g2 = [c for c in corners if c not in g1]
        t1, t2 = best_for(g1), best_for(g2)
        if t1 is None or t2 is None: continue
        tot = (t1 + t2) / len(corners)
        if best2 is None or tot < best2[0]: best2 = (tot, g1, g2)

    if best2 and B > 0:
        c2, g1, g2 = best2
        closed = (c_best - c2) / B
        print("\n  With only TWO words, chosen by a single comparator:")
        print("    mean cost %.3f  -> closes %.0f %% of the adaptive gap" % (c2, 100*closed))
        print("    split: {%s} vs the rest" % ", ".join(g1 if len(g1) < len(g2) else g2))
        print("\n  So a full sense + ADC + lookup table delivers %.1f %% x %.1f %% ="
              % (100*B/T, 100*(1-closed)))
        print("  %.1f %% of the total achievable gain over a fixed word plus one"
              % (100 * (B/T) * (1-closed)))
        print("  comparator. That is the number the adaptive hardware has to justify.")
        out["closed"] = 100 * closed
        out["residual"] = 100 * (B / T) * (1 - closed)

    print("\n  Robustness of the split to the overshoot weight:")
    print("    %6s %10s %10s %9s" % ("w_ov", "(A)", "(B)", "B share"))
    for w in (0.0, 0.05, 0.1, 0.2, 0.5, 1.0):
        c2f = lambda r: r["E_tot"] * 1e6 + w * r["ov_pct"]
        mc = {k: sum(c2f(by[k][c]) for c in corners) / len(corners) for k in univ}
        bf, md = min(univ, key=lambda k: mc[k]), median(mc.values())
        sc = sum(c2f(min((r for r in rows if r["corner"] == c and r["margin"] > 0), key=c2f))
                 for c in corners) / len(corners)
        a, b, t = md - mc[bf], mc[bf] - sc, md - sc
        print("    %6.2f %9.1f%% %9.1f%% %8.1f%%"
              % (w, 100*a/md, 100*b/md, 100*b/t if t else float("nan")))

    # returned so that figures which quote these numbers can import them
    # rather than hardcode them - the architecture diagram did the latter and
    # was still showing 10.7 % after the baseline fix moved it to 13.4 %
    return out


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else W_OV)
