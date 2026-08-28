"""
figures.py -- report figures from the sweep.

Palette: categorical slots 1-4 of the validated default theme, checked with
the six-check validator (CVD dE 9.1 protan worst adjacent pair).  Slots 3 and 4
sit below 3:1 against white, so every series is DIRECTLY LABELLED as well as
legended -- identity never rests on hue alone.
"""
import os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gansim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES  = os.path.join(ROOT, "results")

C1, C2, C3, C4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, MUTED, GRID = "#1a1a19", "#5c5c5a", "#dedddb"
DIVERGING = LinearSegmentedColormap.from_list(
    "margin", ["#c0362f", "#e0ded9", "#2a78d6"])       # bad -> neutral -> safe

plt.rcParams.update({
    "figure.dpi": 200, "savefig.dpi": 200, "savefig.bbox": "tight",
    "font.size": 8.5, "axes.labelsize": 8.5, "axes.titlesize": 9,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5,
    "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "lines.linewidth": 1.4,
})


def load():
    import csv
    rows = list(csv.DictReader(open(os.path.join(RES, "sweep_nominal.csv"))))
    for r in rows:
        for k, v in r.items():
            try:
                r[k] = float(v)
            except ValueError:
                pass
        r["DT_ns"] = round(gansim._sec(r["DT"]) * 1e9, 3)
    return rows


# ---------------------------------------------------------------- fig 1
def fig_baseline():
    """The failure and the fix, side by side.  This is the Review-1 figure."""
    cfgs = [("Baseline: fastest driver, no clamp, 0 V off-bias",
             dict(NPU_LS=8, NPD_LS=8, NPD_HS=8, CLKEN=0, VNEG=0, DT="15n")),
            ("Mitigated: Miller clamp on, -2 V off-bias",
             dict(NPU_LS=8, NPD_LS=8, NPD_HS=8, CLKEN=1, VNEG=-2, DT="15n"))]
    fig, axes = plt.subplots(2, 2, figsize=(7.4, 4.6), sharex="col")
    for col, (title, cfg) in enumerate(cfgs):
        d, p = gansim.run_raw(**cfg)
        t = d[:, 0] * 1e6
        sw, vgs_ls, hsg = d[:, 1], d[:, 5], d[:, 7]
        vgs_hs = hsg - sw
        vth = 1.4
        t0, t1 = 2.005, 2.10                      # LS turn-on / crosstalk event
        m = (t > t0) & (t < t1)

        ax = axes[0][col]
        ax.plot(t[m], sw[m], color=C1, label="Switch node")
        ax.set_ylabel("Switch node (V)" if col == 0 else "")
        ax.set_title(title, fontsize=8.5, color=INK, pad=6)
        ax.set_ylim(-25, 135)
        ax.annotate("SW", (t[m][len(t[m]) // 3], sw[m][len(t[m]) // 3]),
                    color=C1, fontsize=8, xytext=(4, 6), textcoords="offset points")

        ax = axes[1][col]
        # Only the OFF device is at risk, so only it carries a series hue.
        # The switching device's gate is context, drawn recessive.
        ax.plot(t[m], vgs_ls[m], color="#b9bec4", lw=1.0, zorder=1)
        ax.annotate("LS gate (switching)", (t[m][int(len(t[m]) * 0.6)], 5.15),
                    color="#8b9299", fontsize=7, ha="center")
        ax.axhline(vth, color="#c0362f", lw=1.0, ls="--", zorder=2)
        ax.plot(t[m], vgs_hs[m], color=C2, lw=1.6, zorder=3,
                label="High-side $V_{GS}$ (off device)")
        pk = vgs_hs[m].max()
        ipk = int(np.argmax(vgs_hs[m]))
        ax.annotate("HS gate \u2014 peak %.2f V" % pk, (t[m][ipk], pk), color=C2,
                    fontsize=7.5, xytext=(16, 14), textcoords="offset points",
                    arrowprops=dict(arrowstyle="-", color=C2, lw=0.7))
        ax.text(t1 - 0.002, vth + 0.25, "$V_{th}$ = 1.4 V", color="#c0362f",
                fontsize=7.5, ha="right")
        ax.set_ylim(-3.2, 5.6)
        ax.set_xlabel("Time (µs)")
        ax.set_ylabel("Gate–source (V)" if col == 0 else "")
        verdict = "FALSE TURN-ON" if pk > vth else "margin %.2f V" % (vth - pk)
        ax.text(0.97, 0.06, verdict, transform=ax.transAxes, ha="right",
                fontsize=8, weight="bold",
                color="#c0362f" if pk > vth else "#1baf7a")
    fig.suptitle("Crosstalk at low-side turn-on, 100 V / 10 A", fontsize=9.5, y=1.0)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "fig1_crosstalk.png"))
    plt.close(fig)
    print("fig1_crosstalk.png")


# ---------------------------------------------------------------- fig 2
def fig_actuator():
    """
    Which control field moves which objective.  One factor at a time.

    The pairing is not arbitrary and getting it wrong is easy: the drain
    overshoot happens at turn-OFF, so it answers to the PULL-DOWN code and is
    almost completely deaf to the pull-up code (0.0004 points across the whole
    pull-up range).  Crosstalk on the opposite device is driven by the dV/dt of
    this device's turn-ON, so it answers to the PULL-UP code.  That asymmetry
    is the reason pull-up and pull-down are separately programmable instead of
    being one "drive strength" number.
    """
    from multiprocessing import Pool
    base = dict(NPU_HS=8, NPD_HS=8, DT="15n", CLKEN=0, VNEG=0)
    n = [1, 2, 3, 4, 5, 6, 7, 8]
    jobs = ([dict(base, NPU_LS=k, NPD_LS=8) for k in n] +
            [dict(base, NPU_LS=8, NPD_LS=k) for k in n])
    with Pool(4) as pool:
        res = pool.map(_one, jobs)
    pu, pd = res[:len(n)], res[len(n):]

    fig, ax = plt.subplots(2, 2, figsize=(7.2, 5.0))
    panels = [
        (ax[0][0], pu, "E_on",     C1, "Turn-on energy $E_{on}$ (µJ)", 1e6),
        (ax[0][1], pu, "margin",   C2, "Crosstalk margin (V)",          1.0),
        (ax[1][0], pd, "E_off",    C1, "Turn-off energy $E_{off}$ (µJ)", 1e6),
        (ax[1][1], pd, "ov_pct",   C2, "Drain overshoot (% of $V_{bus}$)", 1.0),
    ]
    for a, data, key, col, lab, sc in panels:
        y = [r[key] * sc for r in data]
        a.plot(n, y, "o-", color=col, ms=5)
        a.set_ylabel(lab, fontsize=8)
        a.set_xticks(n)
        span = max(y) - min(y)
        a.set_title("range %.3g" % span, fontsize=7.5, color=MUTED, loc="right")
        if key == "margin":
            a.axhline(0, color="#c0362f", lw=1.0, ls="--")
    ax[0][0].set_title("Pull-up code $N_{PU}$  (turn-on)", fontsize=9, loc="left")
    ax[0][1].set_title("", loc="left")
    ax[1][0].set_title("Pull-down code $N_{PD}$  (turn-off)", fontsize=9, loc="left")
    for a in (ax[1][0], ax[1][1]):
        a.set_xlabel("Slices enabled")
    fig.suptitle("Actuator characterisation: each code moves its own objective",
                 fontsize=9.5, y=1.0)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "fig2_actuator.png"))
    plt.close(fig)
    print("fig2_actuator.png")


def _one(cfg):
    return gansim.run(**cfg)


# ---------------------------------------------------------------- fig 3
def fig_pareto(rows):
    """
    Left : the whole sweep, coloured by crosstalk margin.
    Right: only the FEASIBLE points (margin > 0, i.e. no false turn-on) with
           the true 2-D Pareto staircase.  A 3-objective front cannot be drawn
           as a line in 2-D -- projecting it implies an ordering that does not
           exist -- so the third objective becomes a feasibility constraint
           instead.  That is also the way the result is actually used: you are
           not allowed to false-turn-on, so trade loss against overshoot
           inside the region where you do not.
    """
    x  = np.array([r["E_tot"] * 1e6 for r in rows])
    y  = np.array([r["ov_pct"] for r in rows])
    m  = np.array([r["margin"] for r in rows])
    dt = np.array([r["DT_ns"] for r in rows])

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.6, 3.9))

    lim = max(abs(m.min()), abs(m.max()))
    sc = a1.scatter(x, y, c=m, cmap=DIVERGING,
                    norm=TwoSlopeNorm(vcenter=0, vmin=-lim, vmax=lim),
                    s=20, alpha=0.85, linewidths=0.3, edgecolors="white")
    a1.set_xlabel("Total loss per cycle  $E_{on}+E_{off}+E_{dt}$  (µJ)")
    a1.set_ylabel("Drain overshoot (% of $V_{bus}$)")
    a1.set_title("All 720 control words", fontsize=9)
    hi = y > 40
    if hi.any():
        a1.annotate("5 ns dead time AND weak pull-down\n"
                    "($N_{PD}$=2): turn-off unfinished\nwhen the other device turns on",
                    (x[hi].min(), y[hi].max()), fontsize=7, color=MUTED,
                    xytext=(30, -30), textcoords="offset points",
                    arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))
    cb = fig.colorbar(sc, ax=a1, pad=0.02)
    cb.set_label("Crosstalk margin (V)", fontsize=8)
    cb.ax.axhline(0, color=INK, lw=1.0)

    ok = m > 0
    xf, yf = x[ok], y[ok]
    idx = [i for i in range(len(xf))
           if not np.any((xf <= xf[i]) & (yf <= yf[i]) &
                         ((xf < xf[i]) | (yf < yf[i])))]
    idx.sort(key=lambda i: xf[i])
    a2.scatter(xf, yf, s=20, color="#c8ccd1", linewidths=0, zorder=1,
               label="feasible (margin > 0)")
    a2.step(xf[idx], yf[idx], where="post", color=C1, lw=1.6, zorder=2)
    a2.scatter(xf[idx], yf[idx], s=34, color=C1, zorder=3, label="Pareto front")
    a2.set_xlabel("Total loss per cycle (µJ)")
    a2.set_ylabel("Drain overshoot (% of $V_{bus}$)")
    a2.set_title("Feasible region only, %d of 720 words" % ok.sum(), fontsize=9)
    a2.legend(loc="upper right", fontsize=7.5)

    # exchange rate along the front: uJ of loss per point of overshoot removed
    rate = None
    if len(idx) > 1:
        dE = xf[idx[-1]] - xf[idx[0]]
        dV = yf[idx[0]] - yf[idx[-1]]
        if dV > 0:
            rate = dE / dV
            a2.annotate("%.2f µJ per point of\novershoot removed" % rate,
                        (xf[idx[len(idx) // 2]], yf[idx[len(idx) // 2]]),
                        fontsize=7.5, color=C1, xytext=(14, 16),
                        textcoords="offset points",
                        arrowprops=dict(arrowstyle="-", color=C1, lw=0.7))
    fig.suptitle("Pareto surface over the control word, 100 V / 10 A / 25 °C",
                 fontsize=9.5, y=1.02)
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "fig3_pareto.png"))
    plt.close(fig)
    print("fig3_pareto.png  feasible=%d  front=%d  rate=%s"
          % (ok.sum(), len(idx),
             ("%.3f uJ/pt" % rate) if rate else "n/a"))
    return rate


# ---------------------------------------------------------------- fig 4
def fig_gan_trade(rows):
    """The GaN-specific knot: negative off-bias buys margin, costs dead-time loss."""
    fig, ax = plt.subplots(figsize=(6.2, 3.8))
    for vneg, col, lab in ((0.0, C1, "$V_{GS,off}$ = 0 V"),
                           (-2.0, C2, "$V_{GS,off}$ = −2 V")):
        s = [r for r in rows if r["VNEG"] == vneg and r["CLKEN"] == 0]
        by = {}
        for r in s:
            by.setdefault(r["DT_ns"], []).append(r)
        dts = sorted(by)
        e = [np.mean([r["E_dt"] * 1e6 for r in by[d]]) for d in dts]
        g = [np.mean([r["margin"] for r in by[d]]) for d in dts]
        ax.plot(e, g, "o-", color=col, ms=5, label=lab)
        ax.annotate(lab, (e[-1], g[-1]), color=col, fontsize=8,
                    xytext=(6, -2), textcoords="offset points")
        for d, ee, gg in zip(dts, e, g):
            if d in (5, 35):
                ax.annotate("%.0f ns" % d, (ee, gg), fontsize=7, color=MUTED,
                            xytext=(0, -11), textcoords="offset points", ha="center")
    ax.axhline(0, color="#c0362f", lw=1.0, ls="--")
    ax.text(0.02, 0.02, "below: false turn-on", transform=ax.transAxes,
            fontsize=7.5, color="#c0362f")
    ax.set_xlabel("Dead-time conduction loss  $E_{dt}$  (µJ)\n"
                  "mean over all driver-strength codes at each dead time", labelpad=2)
    ax.set_ylabel("Crosstalk margin (V)")
    ax.set_title("The GaN-specific trade: negative off-bias buys crosstalk\n"
                 "margin and pays for it in third-quadrant conduction", fontsize=9)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(os.path.join(RES, "fig4_gan_trade.png"))
    plt.close(fig)
    print("fig4_gan_trade.png")


if __name__ == "__main__":
    fig_baseline()
    rows = load()
    fig_actuator()
    fig_pareto(rows)
    fig_gan_trade(rows)
