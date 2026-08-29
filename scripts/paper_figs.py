"""
paper_figs.py -- figures for the manuscript.

Palette: categorical slots 1/2/4 of the validated default theme, checked
with the six-check validator.  Every series is direct-labelled as well as
legended, so identity never rests on hue alone.
"""
import csv, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES  = os.path.join(ROOT, "results")
C1, C2, C3 = "#2a78d6", "#eb6834", "#eda100"
INK, MUTED, GRID, FAIL = "#1a1a19", "#5c5c5a", "#dedddb", "#c0362f"
plt.rcParams.update({
    "figure.dpi": 200, "savefig.dpi": 200, "savefig.bbox": "tight",
    "font.size": 8.5, "axes.labelsize": 8.5, "axes.titlesize": 9,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": .5,
    "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "lines.linewidth": 1.4,
})

F = ["NPU_LS", "NPD_LS", "NPD_HS", "DT", "CLKEN", "VNEG"]


def load(fn, tag=None):
    out = []
    for r in csv.DictReader(open(os.path.join(RES, fn))):
        for k, v in list(r.items()):
            if k in ("case", "corner", "DT", "CLKDEL"): continue
            try: r[k] = float(v)
            except (ValueError, TypeError): pass
        if tag and "corner" not in r: r["corner"] = tag
        out.append(r)
    return out


rows = load("sweep_nominal.csv", "100V_10A_25C") + load("full_corners.csv")
esw = lambda r: (r["E_on"] + r["E_off"]) * 1e6
cost = lambda r: r["E_tot"] * 1e6 + .05 * r["ov_pct"]


def fig1():
    """Safety is free: the energy-optimal word is already feasible."""
    g = [r for r in rows if r["corner"] == "100V_10A_25C"]
    e = np.array([esw(r) for r in g]); m = np.array([r["margin"] for r in g])
    ok = m > 0
    fig, ax = plt.subplots(figsize=(5.4, 3.6))
    ax.scatter(e[~ok], m[~ok], s=13, color=FAIL, alpha=.45, linewidths=0,
               label="false turn-on (%d)" % (~ok).sum())
    ax.scatter(e[ok], m[ok], s=13, color=C1, alpha=.55, linewidths=0,
               label="feasible (%d)" % ok.sum())
    ax.axhline(0, color=FAIL, lw=1.1, ls="--")
    # Two distinct optima: the globally cheapest word, and the cheapest
    # FEASIBLE one.  At this corner they are NOT the same word -- the
    # global optimum sits below the threshold.  The gap between them is
    # the price of crosstalk safety.
    i = int(np.argmin(e))
    fi = int(np.arange(len(e))[ok][np.argmin(e[ok])])
    ax.scatter([e[i]], [m[i]], s=90, marker="X", color=FAIL, zorder=5,
               label="lowest energy (infeasible)")
    ax.scatter([e[fi]], [m[fi]], s=110, marker="*", color="#0E6B45", zorder=6,
               label="lowest energy that is feasible")
    ax.annotate("price of safety here:\n%.2f -> %.2f µJ  (+%.2f %%)"
                % (e[i], e[fi], 100 * (e[fi] - e[i]) / e[i]),
                (e[fi], m[fi]), fontsize=7.5, color="#0E6B45",
                xytext=(30, 20), textcoords="offset points",
                arrowprops=dict(arrowstyle="-", color="#0E6B45", lw=.7))
    ax.text(e.max() * .97, .12, "$V_{th}$ threshold", color=FAIL, fontsize=7.5, ha="right")
    ax.set_xlabel("Switching energy $E_{on}+E_{off}$ (µJ)")
    ax.set_ylabel("Crosstalk margin $V_{th}-V_{GS,spur}$ (V)")
    ax.set_title("All 720 control words, 100 V / 10 A / 25 °C", fontsize=9)
    ax.legend(loc="lower right", fontsize=7.5)
    fig.tight_layout(); fig.savefig(os.path.join(RES, "paper_fig1_safety_free.png"))
    plt.close(fig); print("paper_fig1_safety_free.png")


def fig2():
    """The ceiling, and how unevenly it is distributed."""
    corners = sorted({r["corner"] for r in rows})
    per = {}
    for r in rows:
        per.setdefault(tuple(r[f] if f == "DT" else int(float(r[f])) for f in F), {})[r["corner"]] = r
    univ = [k for k, d in per.items()
            if len(d) == len(corners) and all(x["margin"] > 0 for x in d.values())]
    fixed = min(univ, key=lambda k: sum(cost(per[k][c]) for c in corners))
    pen, labs = [], []
    for c in corners:
        best = min([r for r in rows if r["corner"] == c and r["margin"] > 0], key=cost)
        pen.append(100 * (cost(per[fixed][c]) - cost(best)) / cost(per[fixed][c]))
        labs.append(c.replace("_", " / ").replace("V", " V").replace("A", " A").replace("C", " °C"))
    order = np.argsort(pen)
    pen = [pen[i] for i in order]; labs = [labs[i] for i in order]
    fig, ax = plt.subplots(figsize=(5.4, 2.9))
    cols = [C2 if p == max(pen) else C1 for p in pen]
    b = ax.barh(range(len(pen)), pen, color=cols, height=.62)
    ax.set_yticks(range(len(pen))); ax.set_yticklabels(labs, fontsize=8)
    for i, p in enumerate(pen):
        ax.text(p + .25, i, "%.1f %%" % p, va="center", fontsize=8,
                color=cols[i], fontweight="bold" if p == max(pen) else "normal")
    ax.axvline(np.mean(pen), color=INK, lw=1.1, ls="--")
    ax.text(np.mean(pen) + .25, -.72, "mean = ceiling, %.1f %%" % np.mean(pen),
            fontsize=7.5, color=INK)
    ax.set_xlabel("Cost penalty for using one fixed control word (%)")
    ax.set_title("Scheduling pays at one corner type, not generally", fontsize=9)
    ax.set_xlim(0, max(pen) * 1.25); ax.grid(axis="y", visible=False)
    fig.tight_layout(); fig.savefig(os.path.join(RES, "paper_fig2_ceiling.png"))
    plt.close(fig); print("paper_fig2_ceiling.png")


def fig3():
    """At the divergent corner the optimum switches off-bias rail.

    NOTE: an earlier title read "where the one bit that matters shows up".
    Section III.D's freeze test corrected that - DEAD TIME carries the
    benefit (5.45 %), not off-bias (2.55 %, and 0.00 % at a 1 V guard band).
    This figure still shows something true and worth showing, that the rail
    choice separates the two corners, but it is not the one bit.
    """
    fig, axes = plt.subplots(1, 2, figsize=(6.6, 2.9), sharey=True)
    for ax, c, t in zip(axes, ["100V_10A_25C", "200V_2A_125C"],
                        ["100 V / 10 A / 25 °C\n(fixed word is fine)",
                         "200 V / 2 A / 125 °C\n(off-bias earns its place)"]):
        g = [r for r in rows if r["corner"] == c and r["margin"] > 0]
        for vn, col, lab in ((0.0, C1, "0 V off-bias"), (-2.0, C2, "−2 V off-bias")):
            s = sorted([cost(r) for r in g if r["VNEG"] == vn])
            if not s: continue
            ax.plot(np.linspace(0, 100, len(s)), s, color=col, lw=1.6, label=lab)
            ax.scatter([0], [s[0]], color=col, s=30, zorder=5)
            ax.annotate("%.2f" % s[0], (0, s[0]), color=col, fontsize=7.5,
                        xytext=(5, -9), textcoords="offset points")
        ax.set_title(t, fontsize=8.5); ax.set_xlabel("feasible words, sorted (%)")
    axes[0].set_ylabel("Blended cost (lower is better)")
    axes[1].legend(loc="upper left", fontsize=7.5)
    fig.suptitle("The off-bias rail changes the answer at one corner, not both",
             fontsize=9.5, y=1.02)
    fig.tight_layout(); fig.savefig(os.path.join(RES, "paper_fig3_offbias.png"))
    plt.close(fig); print("paper_fig3_offbias.png")


if __name__ == "__main__":
    fig1(); fig2(); fig3()
