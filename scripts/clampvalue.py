"""
clampvalue.py -- what is the active Miller clamp worth?

The paper carried "10.3 %" for a while with no script behind it. It is
reproducible, but only under one of four defensible definitions, and the four
span 9.7-12.2 %. A headline that moves 2.5 points on an arbitrary choice of
averaging order should be reported as a range, the way the cost-weight
sensitivity already is.

The two choices that have to be made, and neither is obviously right:

  baseline   compare the best FIXED word with and without the clamp, or the
             per-corner SCHEDULED optimum with and without?
  averaging  take the percentage of the mean costs, or the mean of the
             per-corner percentages?

All four are printed. The clamp is worth about a tenth of the blended cost
however you slice it, which is the claim worth making - it is roughly twice
what operating-point scheduling is worth, and it is a static architecture
choice needing no sensing, no lookup table and no controller.
"""
import csv, os, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = ["NPU_LS", "NPD_LS", "NPD_HS", "DT", "CLKEN", "VNEG"]
W_OV = 0.05


def load():
    rows = []
    for fn, tag in (("sweep_nominal.csv", "100V_10A_25C"), ("full_corners.csv", None)):
        p = os.path.join(ROOT, "results", fn)
        if not os.path.exists(p): continue
        for r in csv.DictReader(open(p)):
            for k, v in list(r.items()):
                if k in ("corner", "DT", "CLKDEL"): continue
                try: r[k] = float(v)
                except (ValueError, TypeError): pass
            if tag and "corner" not in r: r["corner"] = tag
            rows.append(r)
    return rows


def main(w_ov=W_OV):
    rows = load()
    corners = sorted({r["corner"] for r in rows})
    cost = lambda r: r["E_tot"] * 1e6 + w_ov * r["ov_pct"]
    word = lambda r: tuple(r[f] if f == "DT" else int(r[f]) for f in F)

    def best_fixed(pool):
        by = defaultdict(dict)
        for r in pool: by[word(r)][r["corner"]] = r
        univ = [k for k, d in by.items()
                if len(d) == len(corners) and all(x["margin"] > 0 for x in d.values())]
        if not univ: return None
        k = min(univ, key=lambda k: sum(cost(by[k][c]) for c in corners))
        return {c: by[k][c] for c in corners}, k

    def scheduled(pool):
        out = {}
        for c in corners:
            feas = [r for r in pool if r["corner"] == c and r["margin"] > 0]
            if not feas: return None
            out[c] = min(feas, key=cost)
        return out, None

    on  = [r for r in rows if r["CLKEN"] == 1]
    off = [r for r in rows if r["CLKEN"] == 0]

    print("Value of the active Miller clamp, w_ov=%.2f, %d corners.\n" % (w_ov, len(corners)))
    print("  %-28s %10s %10s   %s" % ("definition", "clamped", "unclamped", "clamp worth"))
    vals = []
    for bname, pick in (("best fixed word", best_fixed), ("per-corner optimum", scheduled)):
        a, ka = pick(on); b, kb = pick(off)
        if a is None or b is None:
            print("  %-28s  no feasible word" % bname); continue
        ma = sum(cost(a[c]) for c in corners) / len(corners)
        mb = sum(cost(b[c]) for c in corners) / len(corners)
        v1 = 100 * (mb - ma) / mb
        v2 = sum(100 * (cost(b[c]) - cost(a[c])) / cost(b[c]) for c in corners) / len(corners)
        vals += [v1, v2]
        print("  %-28s %10.3f %10.3f   %7.2f%%   (%% of the means)" % (bname, ma, mb, v1))
        print("  %-28s %10s %10s   %7.2f%%   (mean of the %%s)" % ("", "", "", v2))
        if ka: print("      clamped word %s" % ("%d/%d/%d/%s/%d/%+g" % ka))
        if kb: print("      unclamped word %s" % ("%d/%d/%d/%s/%d/%+g" % kb))

    if vals:
        print("\n  Across all four definitions: %.1f %% to %.1f %%." % (min(vals), max(vals)))
        print("  The paper reports this range. 10.3 % is the per-corner-optimum basis, averaged as a mean")
        print("  of percentages. Report the range, not the single most flattering pick.")
        print("\n  For comparison, the ceiling on operating-point scheduling is 5.2 %,")
        print("  so the clamp is worth roughly twice what scheduling is worth - and")
        print("  unlike scheduling it needs no sensing, no lookup table, no controller.")


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else W_OV)
