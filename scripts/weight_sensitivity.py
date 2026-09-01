# -*- coding: utf-8 -*-
"""Is the decomposition weight-dependent?

novelty.py reports (A) and (B) at one overshoot weight and shows six sample
weights. The B share swings 5.5-20.1 % across those six, which makes "13.4 %"
look fragile. This sweeps a dense grid to find what actually survives.
"""
import os, sys
from collections import defaultdict
from statistics import median
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import novelty

F = novelty.F
rows = novelty.load()
word = lambda r: tuple(r[f] if f == "DT" else int(r[f]) for f in F)
corners = sorted({r["corner"] for r in rows})
by = defaultdict(dict)
for r in rows:
    by[word(r)][r["corner"]] = r
univ = [k for k, d in by.items()
        if len(d) == len(corners) and all(x["margin"] > 0 for x in d.values())]

def decompose(w):
    c = lambda r: r["E_tot"] * 1e6 + w * r["ov_pct"]
    mc = {k: sum(c(by[k][x]) for x in corners) / len(corners) for k in univ}
    md = median(mc.values())
    bf = min(mc, key=mc.get)
    sched = sum(c(min((r for r in rows if r["corner"] == x and r["margin"] > 0), key=c))
                for x in corners) / len(corners)
    A, B, T = md - mc[bf], mc[bf] - sched, md - sched
    return 100*A/md, 100*B/md, (100*B/T if T else float("nan"))

grid = [i/100.0 for i in range(0, 101)] + [1.25, 1.5, 2.0, 3.0, 5.0]
res = [(w,) + decompose(w) for w in grid]

def band(lo, hi, label):
    sub = [r for r in res if lo <= r[0] <= hi]
    A = [r[1] for r in sub]; B = [r[2] for r in sub]; S = [r[3] for r in sub]
    print("  %-26s A %4.1f-%4.1f %%   B %4.1f-%4.1f %%   B share %4.1f-%4.1f %%"
          % (label, min(A), max(A), min(B), max(B), min(S), max(S)))
    return A, B, S

print("  BY WEIGHT RANGE")
print("  (w_ov prices one percentage point of overshoot against one uJ of energy,")
print("   so a weight of 5 means 1 %% overshoot costs 5 uJ -- physically extreme.)\n")
band(0.0, 1.0, "0.00 - 1.00  (studied)")
band(0.0, 2.0, "0.00 - 2.00")
band(0.0, 5.0, "0.00 - 5.00  (extreme)")
print()
As = [r[1] for r in res]; Bs = [r[2] for r in res]; Sh = [r[3] for r in res]
print("  overshoot weight swept over %d values, 0.00 to %.2f\n" % (len(grid), grid[-1]))
print("  %-34s %6s %6s" % ("", "min", "max"))
print("  %-34s %5.1f%% %5.1f%%" % ("(A) better FIXED word, of baseline", min(As), max(As)))
print("  %-34s %5.1f%% %5.1f%%" % ("(B) ADAPTING per operating point", min(Bs), max(Bs)))
print("  %-34s %5.1f%% %5.1f%%" % ("    B as share of total gain", min(Sh), max(Sh)))
print("\n  A/B ratio at worst case for the fixed word: %.1fx" % (min(As)/max(Bs)))
print("\n  The weight-INDEPENDENT statement:")
print("    across every weight tested, a better fixed word is worth")
print("    %.0f-%.0f %% of baseline, while adaptation never exceeds %.1f %%." % (min(As), max(As), max(Bs)))
print("    A exceeds B at every single weight: %s" % all(a > b for _, a, b, _ in res))

try:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ws = [r[0] for r in res]
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.plot(ws, As, lw=2.0, color="#1b5e9c", label="(A) better fixed word")
    ax.plot(ws, Bs, lw=2.0, color="#c1462f", label="(B) adaptation on top")
    ax.fill_between(ws, Bs, As, color="#1b5e9c", alpha=0.07)
    ax.set_xlabel("overshoot weight $w_{ov}$ in the cost function")
    ax.set_ylabel("% of baseline switching energy")
    ax.set_title("The split does not depend on the weighting", fontsize=11)
    ax.set_xlim(0, 2.0); ax.set_ylim(0, max(As)*1.15)
    ax.legend(frameon=False, fontsize=9); ax.grid(alpha=0.25, lw=0.6)
    ax.annotate("a fixed word is worth %.0f-%.0f %% at every weight" % (min(As), max(As)),
                xy=(1.0, max(As)*0.80), fontsize=8.5, color="#1b5e9c")
    ax.annotate("adaptation never exceeds %.1f %%" % max(Bs),
                xy=(1.0, max(Bs)*1.6), fontsize=8.5, color="#c1462f")
    fig.tight_layout()
    p = os.path.join(novelty.ROOT, "results", "fig_weight_sensitivity.png")
    fig.savefig(p, dpi=170)
    print("\n  wrote %s" % p)
except ImportError:
    print("\n  (matplotlib unavailable; table only)")
