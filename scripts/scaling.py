"""
scaling.py -- does the scheduling ceiling depend on grid density?

Only four corners carry a full 720-word sweep, so 5.2% could be an artefact
of a sparse grid.  This computes the ceiling over EVERY subset of those
corners: if it rises with corner count, 5.2% is a lower bound; if it rises
sub-linearly, a denser grid will not change the conclusion in kind.
"""
import csv, itertools, os, sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = ["NPU_LS", "NPD_LS", "NPD_HS", "DT", "CLKEN", "VNEG"]


def load(fn, tag=None):
    out = []
    for r in csv.DictReader(open(os.path.join(ROOT, "results", fn))):
        for k, v in list(r.items()):
            if k in ("case", "corner", "DT", "CLKDEL"): continue
            try: r[k] = float(v)
            except (ValueError, TypeError): pass
        if tag and "corner" not in r: r["corner"] = tag
        out.append(r)
    return out


def main(w_ov=0.05):
    rows = load("sweep_nominal.csv", "100V_10A_25C") + load("full_corners.csv")
    word = lambda r: tuple(r[f] if f == "DT" else int(float(r[f])) for f in F)
    cost = lambda r: r["E_tot"] * 1e6 + w_ov * r["ov_pct"]
    allc = sorted({r["corner"] for r in rows})
    per = defaultdict(dict)
    for r in rows: per[word(r)][r["corner"]] = r

    def ceiling(cs):
        univ = [k for k, d in per.items()
                if all(c in d and d[c]["margin"] > 0 for c in cs)]
        if not univ: return None
        fx = min(univ, key=lambda k: sum(cost(per[k][c]) for c in cs))
        cf = sum(cost(per[fx][c]) for c in cs) / len(cs)
        co = sum(min(cost(r) for r in rows if r["corner"] == c and r["margin"] > 0)
                 for c in cs) / len(cs)
        return 100 * (cf - co) / cf

    print("Ceiling vs number of corners one fixed word must cover\n")
    print("  corners  subsets     min     mean      max")
    means = []
    for n in range(1, len(allc) + 1):
        v = [ceiling(c) for c in itertools.combinations(allc, n)]
        v = [x for x in v if x is not None]
        means.append(sum(v) / len(v))
        print("     %d       %2d    %6.2f%%  %6.2f%%  %6.2f%%"
              % (n, len(v), min(v), means[-1], max(v)))
    inc = [means[i + 1] - means[i] for i in range(len(means) - 1)]
    print("\n  increments: " + ", ".join("%+.2f" % i for i in inc) + " percentage points")
    print("  -> %s" % ("sub-linear and saturating; a denser grid is unlikely to "
                       "change the conclusion in kind"
                       if len(inc) > 2 and inc[-1] < inc[-2] else
                       "still rising; a denser grid may raise the bound"))
    print("\n  hardest corner pairs to cover with one word:")
    for c in sorted(itertools.combinations(allc, 2),
                    key=lambda c: -(ceiling(c) or 0))[:3]:
        print("    %-36s %6.2f%%" % (" + ".join(c), ceiling(c)))


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 0.05)
