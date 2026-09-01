"""
lloop_analyse.py -- the scheduling ceiling as a function of loop inductance.

Combines the dedicated sweep (lloop_sweep.csv, or the committed
lloop_sweep.csv.gz so a fresh clone need not re-run 76 minutes of ngspice)
with the three points the robustness study already produced (robust_all.csv:
1.5, 3.0 and 4.5 nH) and reports the ceiling at each inductance.

The threshold is stated explicitly rather than eyeballed. A design is taken to
justify the adaptive path when scheduling returns more than DECIDE per cent of
the blended cost; DECIDE defaults to 10 %, which is roughly where the benefit
stops being inside the spread of the cost function itself.

NOTE on the crossover figures below: with eight points the curve turns out
NOT to be monotonic - it peaks at 13.5 % at 1.5 nH and falls back to 8.1 % at
1.0 nH, because only 165 of 720 words are still feasible that tight
(FINDINGS.md section 30). A single crossover therefore does not describe it.
The crossovers are still printed, but the deliverable is the band: adaptive
control pays from roughly 2.5 nH down. Read them with that caveat.
"""
import csv, gzip, os, sys
from collections import defaultdict

ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F      = ["NPU_LS", "NPD_LS", "NPD_HS", "DT", "CLKEN", "VNEG"]
W_OV   = 0.05
DECIDE = 10.0
# A drain overshoot above this is the Miller-clamp switch chattering, not
# physics (FINDINGS.md section 27). Its incidence rises steeply as the loop
# tightens - 43 % of words at 1.0 nH against 0 % at 3.5 nH - so on THIS sweep,
# unlike the robustness study, it is not self-quarantining and has to be
# excluded before the curve means anything.
CHATTER_OV = 50.0


def numify(r):
    for k, v in list(r.items()):
        if k in ("case", "corner", "DT", "CLKDEL", "lloop"): continue
        try: r[k] = float(v)
        except (ValueError, TypeError): pass
    return r


def nh(s):
    """'1.5n' -> 1.5"""
    return float(str(s).strip().rstrip("nN"))


def load():
    """{inductance_nH: [rows]} from both sources."""
    out = defaultdict(list)
    # the sweep costs 76 minutes, so the gzipped copy is committed and stands
    # in when a fresh clone has not re-run it
    p = os.path.join(ROOT, "results", "lloop_sweep.csv")
    fh = None
    if os.path.exists(p):
        fh = open(p)
    elif os.path.exists(p + ".gz"):
        fh = gzip.open(p + ".gz", "rt")
    if fh is not None:
        with fh:
            for r in csv.DictReader(fh):
                out[nh(numify(r)["lloop"])].append(r)
    p = os.path.join(ROOT, "results", "robust_all.csv")
    if os.path.exists(p):
        m = {"LLOOP_lo": 1.5, "nominal": 3.0, "LLOOP_hi": 4.5}
        for r in csv.DictReader(open(p)):
            if r["case"] in m:
                out[m[r["case"]]].append(numify(r))
    return out


def ceiling(rows, w_ov=W_OV, drop_chatter=False):
    if drop_chatter:
        rows = [r for r in rows if r["ov_pct"] <= CHATTER_OV]
    cost = lambda r: r["E_tot"] * 1e6 + w_ov * r["ov_pct"]
    word = lambda r: tuple(r[f] if f == "DT" else int(float(r[f])) for f in F)
    corners = sorted({r["corner"] for r in rows})
    if len(corners) < 2: return None, None, None
    by = defaultdict(dict)
    for r in rows: by[word(r)][r["corner"]] = r
    sched = {}
    for c in corners:
        feas = [r for r in rows if r["corner"] == c and r["margin"] > 0]
        if not feas: return None, None, None
        sched[c] = min(feas, key=cost)
    univ = [k for k, d in by.items()
            if len(d) == len(corners) and all(x["margin"] > 0 for x in d.values())]
    if not univ: return None, None, len(univ)
    fx = min(univ, key=lambda k: sum(cost(by[k][c]) for c in corners))
    cf = sum(cost(by[fx][c]) for c in corners) / len(corners)
    cs = sum(cost(sched[c]) for c in corners) / len(corners)
    return 100 * (cf - cs) / cf, fx, len(univ)


def main():
    data = load()
    if not data:
        sys.exit("no lloop data yet -- run scripts/lloop_sweep.py")
    drop = "--drop-chatter" in sys.argv
    print("Scheduling ceiling vs power-loop inductance%s\n"
          % ("   (clamp-chatter points excluded)" if drop else ""))
    print("  %8s %10s %10s   %s" % ("L (nH)", "ceiling", "feasible", "best fixed word"))
    pts = []
    for L in sorted(data):
        c, fx, n = ceiling(data[L], drop_chatter=drop)
        if c is None:
            print("  %8.1f   no universal word (%s feasible)" % (L, n)); continue
        pts.append((L, c))
        print("  %8.1f %9.2f%% %10d   %d/%d/%d/%s/%d/%+g" % ((L, c, n) + fx))

    if len(pts) < 2:
        return
    print("\n  Crossover — the loop inductance below which scheduling returns")
    print("  more than the stated threshold:\n")
    print("    %-12s %s" % ("threshold", "crossover"))
    for thr in (5.0, 7.5, 10.0, 12.5):
        cross = None
        for (l1, c1), (l2, c2) in zip(pts, pts[1:]):
            if (c1 - thr) * (c2 - thr) < 0:                 # sign change
                cross = l1 + (thr - c1) * (l2 - l1) / (c2 - c1)
                break
        print("    %-12s %s" % ("%.1f %%" % thr,
              ("%.2f nH" % cross) if cross else "outside the swept range"))

    lo, hi = pts[0], pts[-1]
    print("\n  Over %.1f-%.1f nH the ceiling moves %.2f%% -> %.2f%%." %
          (lo[0], hi[0], lo[1], hi[1]))
    print("  Loop inductance is board layout, not the transistor, so this is a")
    print("  LAYOUT decision that determines whether adaptive gate control is")
    print("  worth building — which is not a trade-off the literature states.")


if __name__ == "__main__":
    main()
