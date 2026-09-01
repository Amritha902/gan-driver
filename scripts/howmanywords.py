"""
howmanywords.py -- how much adaptive machinery does the benefit actually need?

The field frames this as a binary: one fixed word, or per-operating-point
adaptation with sensing, an ADC and a lookup table. That is a false choice,
and the data can settle it.

If K control words are allowed, and the controller picks between them, how
much of the full adaptive benefit is captured?

    K = 1   a strapped configuration            no sensing at all
    K = 2   ONE comparator (e.g. light-load detect)
    K = 3   two thresholds
    K = 4   full per-corner scheduling          sense + ADC + LUT

K = 2 is the interesting case: a single comparator is perhaps two orders of
magnitude cheaper than an ADC and a lookup table. If two words capture most of
the benefit, the correct engineering answer is neither "fix it" nor "build the
LUT" - it is "build a comparator", and nobody has reported that because nobody
has separated the fixed and adaptive halves in the first place.

Exhaustive over all partitions of the corners: 4 corners give 15 non-empty
subsets and 7 two-way splits, so nothing here is a heuristic.
"""
import csv, itertools, os, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = ["NPU_LS", "NPD_LS", "NPD_HS", "DT", "CLKEN", "VNEG"]


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


def main(w_ov=0.05, guard=0.0):
    rows = load()
    cost = lambda r: r["E_tot"] * 1e6 + w_ov * r["ov_pct"]
    word = lambda r: tuple(r[f] if f == "DT" else int(r[f]) for f in F)
    corners = sorted({r["corner"] for r in rows})
    by = defaultdict(dict)
    for r in rows: by[word(r)][r["corner"]] = r

    def best_for(group):
        """cheapest single word that is feasible at every corner in `group`"""
        cand = [k for k, d in by.items()
                if all(c in d and d[c]["margin"] > guard for c in group)]
        if not cand: return None, None
        k = min(cand, key=lambda k: sum(cost(by[k][c]) for c in group))
        return k, sum(cost(by[k][c]) for c in group)

    n = len(corners)
    _, tot1 = best_for(corners)
    c1 = tot1 / n
    cN = sum(cost(min((r for r in rows if r["corner"] == c and r["margin"] > guard),
                      key=cost)) for c in corners) / n

    print("How many control words does the benefit actually need?")
    print("guard band %.1f V, %d corners, cost = E_tot + %.2f*overshoot\n"
          % (guard, n, w_ov))

    # exhaustive over every partition of the corners into exactly K groups
    def partitions(items, k):
        if k == 1:
            yield [list(items)]; return
        if len(items) < k: return
        first, rest = items[0], items[1:]
        for smaller in partitions(rest, k - 1):
            yield [[first]] + smaller
        for smaller in partitions(rest, k):
            for i in range(len(smaller)):
                yield smaller[:i] + [[first] + smaller[i]] + smaller[i+1:]

    print("  %-3s %10s %12s %14s   %s" % ("K", "mean cost", "gain vs K=1",
                                          "of full benefit", "split"))
    results = {}
    for K in range(1, n + 1):
        bestcost, bestsplit = None, None
        for part in partitions(corners, K):
            tot, ok = 0.0, True
            for g in part:
                _, t = best_for(g)
                if t is None: ok = False; break
                tot += t
            if ok and (bestcost is None or tot < bestcost):
                bestcost, bestsplit = tot, part
        if bestcost is None: continue
        c = bestcost / n
        results[K] = c
        gain = 100 * (c1 - c) / c1
        full = 100 * (c1 - c) / (c1 - cN) if c1 > cN else float("nan")
        desc = " | ".join("+".join(x.replace("_", "/") for x in g) for g in bestsplit)
        print("  %-3d %10.3f %11.2f%% %13.0f%%   %s" % (K, c, gain, full, desc[:48]))

    if 2 in results:
        share = 100 * (c1 - results[2]) / (c1 - cN) if c1 > cN else float("nan")
        print("\n  ONE comparator (K=2) captures %.0f%% of everything full" % share)
        print("  per-corner scheduling can deliver. The remaining %.0f%% is what"
              % (100 - share))
        print("  a sense + ADC + lookup table buys over a single threshold.")


if __name__ == "__main__":
    a = sys.argv[1:]
    main(float(a[0]) if a else 0.05, float(a[1]) if len(a) > 1 else 0.0)
