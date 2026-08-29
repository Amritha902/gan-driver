"""
emi_analyse.py -- does the conclusion survive an objective that prices EMI?

Two claims in the paper are scoped to a loss-and-overshoot cost:

    (a) scheduling the control word across operating points is worth <= 5.2 %
    (b) of the six fields, pull-up drive strength is worth 0.00 %

Claim (b) is the one that contradicts the active-gate-driver literature, and
Section III.E concedes the reason: that literature schedules drive strength
for EMI, which our cost never prices.  This re-runs both the ceiling and the
freeze test under a family of objectives that DOES price it:

    cost(r; a) = (1-a) * [E_tot*1e6 + w_ov*ov_pct] / L0  +  a * EMI(r) / D0

a = 0 recovers the paper's objective exactly; a = 1 optimises for EMI alone.
At a = 0 the ceiling printed here must equal ceiling.py's 5.2 % on the same
corners; that is the check that this script is measuring the same thing.
L0 and D0 are medians over the feasible set, computed once so that costs stay
comparable across corners.

Two EMI measures are run separately, because they disagree in sign:

    dvdt_1090   10-90 % switch-node slew   -- faster pull-up is WORSE
    E_osc_on    turn-on ringing energy     -- faster pull-up is BETTER

An objective built on either one is defensible, and if they give opposite
answers about scheduling that is itself the result.
"""
import csv, os, sys
from collections import defaultdict
from statistics import median

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F    = ["NPU_LS", "NPD_LS", "NPD_HS", "DT", "CLKEN", "VNEG"]
NICE = {"NPU_LS": "pull-up strength", "NPD_LS": "pull-down strength",
        "NPD_HS": "high-side pull-down", "DT": "dead time",
        "CLKEN": "Miller clamp", "VNEG": "gate off-bias"}
W_OV   = 0.05
ALPHAS = [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9, 1.0]


def load():
    p = os.path.join(ROOT, "results", "emi_sweep.csv")
    if not os.path.exists(p):
        sys.exit("results/emi_sweep.csv not found -- run scripts/emi_sweep.py first")
    rows = []
    for r in csv.DictReader(open(p)):
        for k, v in list(r.items()):
            if k in ("corner", "DT", "CLKDEL"): continue
            try: r[k] = float(v)
            except (ValueError, TypeError): pass
        rows.append(r)
    return rows


def mkcost(a, L0, D0, emi_key, sign):
    def cost(r):
        loss = (r["E_tot"] * 1e6 + W_OV * r["ov_pct"]) / L0
        return (1 - a) * loss + a * (sign * r[emi_key]) / D0
    return cost


def freeze_cost(feas, corners, cost, field, value):
    """Mean cost when `field` is pinned to `value` and everything else adapts.
    None if that value is infeasible at some corner."""
    sub = [r for r in feas if r[field] == value]
    tot = 0.0
    for c in corners:
        cand = [r for r in sub if r["corner"] == c]
        if not cand:
            return None
        tot += cost(min(cand, key=cost))
    return tot / len(corners)


def analyse(rows, emi_key, sign):
    """sign = +1 if larger is worse (dV/dt), so the term is used as-is."""
    feas = [r for r in rows if r["margin"] > 0
            and r.get(emi_key) == r.get(emi_key)]          # drop NaN
    if not feas:
        print("  no feasible rows with a valid %s" % emi_key); return
    corners = sorted({r["corner"] for r in feas})
    L0 = median(r["E_tot"] * 1e6 + W_OV * r["ov_pct"] for r in feas) or 1.0
    D0 = median(sign * r[emi_key] for r in feas) or 1.0
    word = lambda r: tuple(r[f] if f == "DT" else int(float(r[f])) for f in F)

    print("\n  EMI measure: %s   (normalisers L0=%.4g  D0=%.4g, %d feasible rows)"
          % (emi_key, L0, D0, len(feas)))
    print("  %5s %10s  %-22s %s" % ("alpha", "ceiling", "best fixed word", "freeze penalty per field"))

    for a in ALPHAS:
        cost = mkcost(a, L0, D0, emi_key, sign)

        # ---- ceiling: per-corner optimum vs best single universal word ----
        per = defaultdict(dict)
        for r in feas: per[word(r)][r["corner"]] = r
        sched = {c: min((r for r in feas if r["corner"] == c), key=cost)
                 for c in corners}
        c_sched = sum(cost(sched[c]) for c in corners) / len(corners)
        univ = [k for k, d in per.items() if len(d) == len(corners)]
        if not univ:
            print("  %5.1f   no universal word" % a); continue
        bw = min(univ, key=lambda k: sum(cost(per[k][c]) for c in corners))
        c_fix = sum(cost(per[bw][c]) for c in corners) / len(corners)
        # denominator is the FIXED cost, matching ceiling.py, scaling.py and
        # robust_analyse.py -- "scheduling would save this fraction of what a
        # fixed word costs you". Dividing by c_sched instead inflates every
        # number (5.2 % becomes 5.5 %) and would not be comparable to the
        # paper's headline.
        ceiling = 100 * (c_fix - c_sched) / abs(c_fix) if c_fix else float("nan")

        # ---- freeze test under the same objective -------------------------
        pens = []
        for f in F:
            best = None
            for v in sorted({r[f] for r in feas}, key=str):
                cc = freeze_cost(feas, corners, cost, f, v)
                if cc is None: continue
                pen = 100 * (cc - c_sched) / abs(c_sched)
                if best is None or pen < best: best = pen
            pens.append((f, best if best is not None else float("nan")))
        pens.sort(key=lambda x: -(x[1] if x[1] == x[1] else -1))
        tag = "  ".join("%s %.2f%%" % (f, p) for f, p in pens[:3])
        wstr = "%d/%d/%d/%s/%d/%+d" % (bw[0], bw[1], bw[2], bw[3], bw[4], bw[5])
        print("  %5.1f %9.2f%%  %-22s %s" % (a, ceiling, wstr, tag))

    # ---- the specific question: when does pull-up start to matter? --------
    print("\n  pull-up freeze penalty vs alpha:")
    for a in ALPHAS:
        cost = mkcost(a, L0, D0, emi_key, sign)
        c_free = sum(cost(min((r for r in feas if r["corner"] == c), key=cost))
                     for c in corners) / len(corners)
        got = None
        for v in sorted({r["NPU_LS"] for r in feas}):
            pen = freeze_cost(feas, corners, cost, "NPU_LS", v)
            if pen is None: continue
            pen = 100 * (pen - c_free) / abs(c_free)
            if got is None or pen < got[0]: got = (pen, v)
        if got:
            print("    alpha=%.1f   penalty %.2f%%   best frozen N_PU = %d"
                  % (a, got[0], int(got[1])))


def main():
    rows = load()
    print("Scheduling ceiling and freeze test under EMI-aware objectives.")
    print("%d rows, %d corners.\n" % (rows and len(rows), len({r["corner"] for r in rows})))
    analyse(rows, "dvdt_1090", +1.0)      # faster slew = worse EMI
    analyse(rows, "E_osc_on",  +1.0)      # more ringing energy = worse EMI


if __name__ == "__main__":
    main()
