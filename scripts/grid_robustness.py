"""
grid_robustness.py -- how much does the headline decomposition depend on the
choices we made to compute it?

Four questions a reviewer asks, answered off the 36-corner x 720-word grid
that scripts/full_grid.py already produced. No new ngspice runs: this is
re-analysis of results/full_grid.csv.

  1. THE WEIGHT.  The cost function is E_tot + W_OV * ov_pct and W_OV = 0.05
     is our choice. Sweeping it shows the honest answer is TWO-PART: the
     headline 8.9 % IS weight-dependent and roughly triples if overshoot is
     weighted heavily, but the fixed word still captures at least 77 % of
     the gain at every weight tried. The claim that survives is the
     qualitative one, and that is the one to make.
  2. THE MEAN HIDES THE TAIL.  "Adapting is worth 2.6 %" is a mean over 36
     corners. Publish the distribution instead, because the worst corner is
     not 2.6 %.
  3. THE OPTIMUM MOVES BUT THE COST DOES NOT.  Ten distinct best words across
     36 corners, yet freezing one costs little. Draw both curves so the
     distinction is visible rather than asserted.
  4. IS THE GRID TOO COARSE?  We cannot refine it here -- that needs new
     transients -- but we CAN coarsen it: estimate the split on random
     subsets of the 36 corners and see how much the answer wanders. Stability
     under coarsening is evidence, not proof, that the grid is dense enough.

Definitions are taken from scripts/grid_analyse.py unchanged, so the numbers
here reconcile with the published ones:

    cost(r) = E_tot*1e6 + W_OV*ov_pct
    feasible = margin > 0
    common   = words feasible at EVERY corner in the subset
    baseline = MEDIAN mean-cost over `common`   (not the conventional word --
               that one is safe at 9 of 36 corners, and gains measured
               against an unsafe baseline are meaningless)
    A = (median - best_fixed) / baseline
    B = (best_fixed - per_corner_oracle) / baseline
"""
import csv
import os
import random
import statistics as st
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
GRID = os.path.join(RES, "full_grid.csv")

W_OV = 0.05                      # the shipped weight, as in grid_analyse.py
FIELDS = ["NPU_LS", "NPD_LS", "NPD_HS", "DT", "CLKEN", "VNEG"]

# Validated categorical pair. node scripts/validate_palette.js
# "#2a78d6,#b8761a" --mode light -> all six checks PASS on #fcfcfb
# (CVD dE 26.6 protan / 23.1 tritan, normal 29.3).
BLUE, AMBER = "#2a78d6", "#b8761a"
INK, MUTED, RULE, SURF = "#0b0b0b", "#52514e", "#d8d7d2", "#fcfcfb"


def load():
    rows = list(csv.DictReader(open(GRID)))
    by = {}                       # corner -> word -> (E_tot, ov_pct, margin)
    for r in rows:
        w = tuple(r[f] for f in FIELDS)
        by.setdefault(r["corner"], {})[w] = (
            float(r["E_tot"]), float(r["ov_pct"]), float(r["margin"]))
    return by


def split(by, corners, w_ov=W_OV):
    """The A/B decomposition, exactly as grid_analyse.py defines it."""
    cost = lambda t: t[0] * 1e6 + w_ov * t[1]
    feas = {c: {w: t for w, t in by[c].items() if t[2] > 0} for c in corners}
    if any(not feas[c] for c in corners):
        return None
    common = set.intersection(*[set(feas[c]) for c in corners])
    if not common:
        return None
    mean_cost = {w: sum(cost(by[c][w]) for c in corners) / len(corners)
                 for w in common}
    best_fixed = min(mean_cost, key=mean_cost.get)
    c_best = mean_cost[best_fixed]
    base = st.median(mean_cost.values())
    oracle = {c: min(cost(feas[c][w]) for w in feas[c]) for c in corners}
    c_orc = sum(oracle.values()) / len(corners)
    A = (base - c_best) / base * 100
    B = (c_best - c_orc) / base * 100
    return dict(A=A, B=B, share=B / (A + B) * 100 if A + B else 0.0,
                best=best_fixed, n_common=len(common),
                oracle=oracle, c_best_per_corner={
                    c: cost(by[c][best_fixed]) for c in corners})


def style(ax):
    ax.set_facecolor(SURF)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(RULE)
    ax.tick_params(colors=MUTED, labelsize=9, length=3)
    ax.grid(True, color=RULE, lw=0.6, alpha=0.7)
    ax.set_axisbelow(True)


def fig_weight(by, corners, out):
    """1. Does the answer depend on the overshoot weight we chose?"""
    ws = [0.0, 0.01, 0.02, 0.05, 0.10, 0.20, 0.50, 1.0]
    A, B, S = [], [], []
    for w in ws:
        s = split(by, corners, w)
        A.append(s["A"]); B.append(s["B"]); S.append(s["share"])

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.2, 6.4), sharex=True,
                                   facecolor=SURF,
                                   gridspec_kw=dict(height_ratios=[1, 1], hspace=0.18))
    for ax in (ax1, ax2):
        style(ax)
        ax.set_xscale("symlog", linthresh=0.01)

    ax1.plot(ws, A, color=BLUE, lw=2, marker="o", ms=5,
             label="(A) choosing the fixed word well")
    ax1.plot(ws, B, color=AMBER, lw=2, marker="s", ms=5,
             label="(B) adapting per operating point")
    ax1.set_ylabel("share of baseline  [%]", color=MUTED, fontsize=10)
    ax1.legend(frameon=False, fontsize=9.5, labelcolor=MUTED, loc="center left")
    ax1.set_ylim(0, max(A) * 1.18)
    # direct labels at the shipped weight, not on every point
    i = ws.index(W_OV)
    ax1.annotate("%.1f %%" % A[i], (ws[i], A[i]), textcoords="offset points",
                 xytext=(0, 9), ha="center", color=BLUE, fontsize=9.5, weight="bold")
    ax1.annotate("%.1f %%" % B[i], (ws[i], B[i]), textcoords="offset points",
                 xytext=(0, 9), ha="center", color=AMBER, fontsize=9.5, weight="bold")

    ax2.plot(ws, S, color=AMBER, lw=2, marker="s", ms=5)
    ax2.set_ylabel("(B) as a share of\nthe total gain  [%]", color=MUTED, fontsize=10)
    ax2.set_xlabel("overshoot weight W_OV in cost = E_tot + W_OV · ov_pct   "
                   "(shipped: 0.05)", color=MUTED, fontsize=10, labelpad=8)
    ax2.set_ylim(0, max(S) * 1.30)
    ax2.annotate("%.1f %%" % S[i], (ws[i], S[i]), textcoords="offset points",
                 xytext=(0, 9), ha="center", color=AMBER, fontsize=9.5, weight="bold")
    for ax in (ax1, ax2):
        ax.axvline(W_OV, color=MUTED, lw=1, ls=(0, (4, 3)), alpha=0.8)

    ax1.set_title("Adaptation is worth more the harder you punish overshoot "
                  "\u2014 and the fixed word still wins",
                  color=INK, fontsize=13, weight="bold", loc="left", pad=12)
    ax2.annotate("(B) ranges %.1f\u2013%.1f %% of the gain across two orders of "
                 "magnitude of W_OV,\nso the 8.9 %% headline is weight-dependent. "
                 "What does NOT move:\nthe fixed word takes at least %.0f %% of the "
                 "gain at every weight."
                 % (min(S), max(S), 100 - max(S)),
                 (0.0, -0.46), xycoords="axes fraction", color=MUTED, fontsize=9.5)
    fig.savefig(out, dpi=170, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)
    return ws, A, B, S


def fig_penalty(by, corners, out):
    """2. The distribution behind the mean."""
    s = split(by, corners)
    pens = sorted((100.0 * (s["c_best_per_corner"][c] - s["oracle"][c])
                   / s["oracle"][c], c) for c in corners)
    vals = [p for p, _ in pens]
    fig, ax = plt.subplots(figsize=(9.6, 5.0), facecolor=SURF)
    style(ax)
    x = range(len(vals))
    ax.bar(x, vals, color=BLUE, width=0.72, linewidth=0)
    med = st.median(vals)
    ax.axhline(med, color=MUTED, lw=1.2, ls=(0, (4, 3)))
    ax.annotate("median %.1f %%" % med, (0.4, med), textcoords="offset points",
                xytext=(0, 6), color=MUTED, fontsize=9.5)
    ax.annotate("worst corner %s, %.1f %%" % (pens[-1][1], vals[-1]),
                (len(vals) - 1, vals[-1]), textcoords="offset points",
                xytext=(-6, 4), ha="right", color=INK, fontsize=9.5, weight="bold")
    ax.set_ylabel("cost of using the one fixed word\nat that corner  [%]",
                  color=MUTED, fontsize=10)
    ax.set_xlabel("the 36 operating corners, sorted", color=MUTED, fontsize=10)
    ax.set_xticks([])
    ax.set_title("What one fixed word costs, corner by corner",
                 color=INK, fontsize=13, weight="bold", loc="left", pad=12)
    ax.annotate("the headline 2.6 %% is a mean over these 36 bars; "
                "%d of 36 cost more than 5 %%" % sum(1 for v in vals if v > 5),
                (0.0, -0.17), xycoords="axes fraction", color=MUTED, fontsize=9.5)
    fig.savefig(out, dpi=170, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)
    return vals, pens


def fig_fixed_vs_optimum(by, corners, out):
    """3. The optimum moves; the cost of ignoring it does not."""
    s = split(by, corners)
    order = sorted(corners, key=lambda c: s["oracle"][c])
    orc = [s["oracle"][c] for c in order]
    fix = [s["c_best_per_corner"][c] for c in order]
    fig, ax = plt.subplots(figsize=(9.6, 5.0), facecolor=SURF)
    style(ax)
    x = list(range(len(order)))
    ax.plot(x, orc, color=BLUE, lw=2, marker="o", ms=4,
            label="best word chosen for that corner (the oracle)")
    ax.plot(x, fix, color=AMBER, lw=2, marker="s", ms=4,
            label="the one fixed word, used everywhere")
    ax.fill_between(x, orc, fix, color=AMBER, alpha=0.10, linewidth=0)
    ax.set_ylabel("cost  [µJ-equivalent]", color=MUTED, fontsize=10)
    ax.set_xlabel("the 36 operating corners, sorted by oracle cost",
                  color=MUTED, fontsize=10)
    ax.set_xticks([])
    ax.legend(frameon=False, fontsize=9.5, labelcolor=MUTED, loc="upper left")
    ax.set_title("The best word changes with the corner. The cost of ignoring "
                 "that barely does.", color=INK, fontsize=13, weight="bold",
                 loc="left", pad=12)
    ax.annotate("the shaded gap IS the adaptive gain (B). It is %.1f %% of the "
                "baseline." % s["B"], (0.0, -0.17), xycoords="axes fraction",
                color=MUTED, fontsize=9.5)
    fig.savefig(out, dpi=170, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)
    return s


def fig_subsample(by, corners, out, trials=250, seed=20260926):
    """4. How much does the answer wander if the grid is coarser?"""
    rng = random.Random(seed)
    full = split(by, corners)["share"]
    ks = [4, 9, 18, 27]
    data = []
    for k in ks:
        got = []
        for _ in range(trials):
            sub = rng.sample(list(corners), k)
            s = split(by, sub)
            if s:
                got.append(s["share"])
        data.append(got)

    fig, ax = plt.subplots(figsize=(9.2, 5.0), facecolor=SURF)
    style(ax)
    for i, (k, got) in enumerate(zip(ks, data)):
        xs = [i + rng.uniform(-0.16, 0.16) for _ in got]
        ax.scatter(xs, got, s=13, color=BLUE, alpha=0.30, linewidths=0)
        ax.plot([i - 0.28, i + 0.28], [st.median(got)] * 2,
                color=INK, lw=2.2, solid_capstyle="butt")
        ax.annotate("median %.1f %%" % st.median(got), (i, st.median(got)),
                    textcoords="offset points", xytext=(0, 10), ha="center",
                    color=INK, fontsize=9.5, weight="bold")
    ax.axhline(full, color=AMBER, lw=2, ls=(0, (5, 3)))
    ax.annotate("all 36 corners: %.1f %%" % full, (len(ks) - 0.5, full),
                textcoords="offset points", xytext=(0, 7), ha="right",
                color=AMBER, fontsize=10, weight="bold")
    ax.set_xticks(range(len(ks)))
    ax.set_xticklabels(["%d corners" % k for k in ks], color=MUTED)
    ax.set_ylabel("(B) as a share of the total gain  [%]", color=MUTED, fontsize=10)
    ax.set_title("The estimate settles as corners are added \u2014 four is not "
                 "enough, twenty-seven is",
                 color=INK, fontsize=13, weight="bold", loc="left", pad=12)
    ax.annotate("%d random corner subsets at each size. Four corners scatter "
                "over 0\u201323 %%, which is why the\nn = 4 study reported a "
                "different number. This tests stability under COARSENING; it "
                "cannot\nprove a finer grid would agree."
                % trials, (0.0, -0.20), xycoords="axes fraction",
                color=MUTED, fontsize=9.5)
    fig.savefig(out, dpi=170, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)
    return full, ks, data


def main():
    if not os.path.exists(GRID):
        raise SystemExit("no %s -- run scripts/full_grid.py first" % GRID)
    by = load()
    corners = sorted(by)
    out = []
    P = lambda s="": (print(s), out.append(s))

    P("\n  GRID ROBUSTNESS -- re-analysis of results/full_grid.csv")
    P("  %d corners x %d words. No new transients.\n"
      % (len(corners), len(by[corners[0]])))

    ws, A, B, S = fig_weight(by, corners, os.path.join(RES, "fig_wov_sensitivity.png"))
    P("  1. THE OVERSHOOT WEIGHT")
    P("     %-8s %9s %9s %9s" % ("W_OV", "(A) %", "(B) %", "B share %"))
    for w, a, b, s in zip(ws, A, B, S):
        P("     %-8.2f %9.2f %9.2f %9.2f%s"
          % (w, a, b, s, "   <- shipped" if w == W_OV else ""))
    P("     -> (B) ranges %.1f-%.1f %%, so the 8.9 %% headline IS weight-"
      % (min(S), max(S)))
    P("        dependent: weight overshoot heavily and adaptation matters more,")
    P("        which is physical -- overshoot is what varies most across corners.")
    P("        What survives every weight: the fixed word takes at least %.0f %% of"
      % (100 - max(S)))
    P("        the gain. Claim that, not the 8.9 %.\n")

    vals, pens = fig_penalty(by, corners, os.path.join(RES, "fig_corner_penalty.png"))
    P("  2. THE DISTRIBUTION BEHIND THE MEAN")
    q = lambda p: sorted(vals)[int(p * (len(vals) - 1))]
    P("     per-corner cost of the fixed word, n = %d" % len(vals))
    P("     min %.2f | 25%% %.2f | median %.2f | 75%% %.2f | max %.2f  [%%]"
      % (min(vals), q(.25), st.median(vals), q(.75), max(vals)))
    P("     corners above 5 %%: %d of %d   worst: %s"
      % (sum(1 for v in vals if v > 5), len(vals), pens[-1][1]))
    P("     -> quote the distribution, not the mean. The mean is honest; the")
    P("        mean ALONE is not.\n")

    s = fig_fixed_vs_optimum(by, corners, os.path.join(RES, "fig_fixed_vs_optimum.png"))
    P("  3. THE OPTIMUM MOVES, THE COST DOES NOT")
    P("     words feasible at every corner : %d of %d" % (s["n_common"], len(by[corners[0]])))
    P("     best fixed word                : %s" % ", ".join(s["best"]))
    P("     (A) %.2f %%   (B) %.2f %%   B share %.2f %%" % (s["A"], s["B"], s["share"]))
    P("     -> the gap between the two curves IS B. Drawing it stops the")
    P("        'but the optimum moves' objection from landing.\n")

    full, ks, data = fig_subsample(by, corners, os.path.join(RES, "fig_grid_subsample.png"))
    P("  4. DOES THE ANSWER DEPEND ON WHICH CORNERS?")
    P("     all 36 corners: B share = %.2f %%" % full)
    for k, got in zip(ks, data):
        P("     %2d corners, %3d subsets: median %.2f %%  (%.2f - %.2f)"
          % (k, len(got), st.median(got), min(got), max(got)))
    P("     -> the estimate settles: 4 corners scatter over 0-23 %, 27 corners")
    P("        sit on the full-grid answer. This is why the n = 4 study reported")
    P("        a different share, and why 36 is the one to quote. Evidence the")
    P("        grid is dense enough, NOT proof a finer one would agree.\n")

    with open(os.path.join(RES, "grid_robustness.txt"), "w") as f:
        f.write("\n".join(out) + "\n")
    P("  wrote results/grid_robustness.txt and four figures.")


if __name__ == "__main__":
    main()
