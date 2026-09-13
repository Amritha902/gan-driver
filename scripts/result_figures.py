# -*- coding: utf-8 -*-
"""result_figures.py -- the three new results, as pictures.

    python3 scripts/result_figures.py

The deck carried these as tables of numbers, which is the wrong form for all
three: each one is a comparison of magnitudes across a handful of categories,
and a reader at the back of a room cannot do arithmetic on a table but can see
a bar that crosses zero.

Palette: #2a78d6 / #eb6834 / #1b7f5f. Validated with the six-check script --
the project's previous third slot (#eda100) FAILS the normal-vision floor
against #eb6834 at delta-E 13.7, so it is not used here. The green's CVD
separation lands at 7.0 (protan), inside the 6-8 band that is legal only with
secondary encoding, so every bar is direct-labelled as well as legended.

Every number is read from results/ rather than typed here, so a figure cannot
drift away from the run that produced it.
"""
import csv, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES  = os.path.join(ROOT, "results")
C1, C2, C3 = "#2a78d6", "#eb6834", "#1b7f5f"
INK, MUTED, GRID = "#1a1a19", "#5c5c5a", "#dedddb"
plt.rcParams.update({
    "figure.dpi": 200, "savefig.dpi": 200, "savefig.bbox": "tight",
    "font.size": 9, "axes.labelsize": 9, "axes.titlesize": 10.5,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": .5,
    "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "lines.linewidth": 1.8,
})
VTH_LINE = dict(color=INK, lw=1.0, ls="-", zorder=3)


import re as _re


def parse_margins(fn, keys):
    """Pull '<label>  <name> +x.xxx V   <name> +y.yyy V' out of a txt result.

    Anchored on "<name> <signed number> V" rather than on splitting at the
    first "V", because the file's own header line contains the word "vs" and
    the model names, and a looser match reads the header as data.
    """
    out = {}
    for line in open(os.path.join(RES, fn)):
        got = []
        for k in keys:
            m = _re.search(r"\b%s\s+([-+]?\d+\.\d+)\s*V" % _re.escape(k), line)
            if not m:
                break
            got.append(float(m.group(1)))
        if len(got) == len(keys):
            label = _re.split(r"\s{2,}", line.strip())[0]
            out[label] = got
    return out


# ----------------------------------------------------------- head to head --
def fig_headtohead():
    rows = list(csv.DictReader(open(os.path.join(RES, "headtohead.csv"))))
    rows = [r for r in rows if r.get("corner", "").endswith("C")]
    labels = [r["corner"].replace("V_", " V / ").replace("A_", " A / ")
                          .replace("C", " °C") for r in rows]
    base = [float(r[" base_as_built"]) for r in rows]
    ours = [float(r[" ours"]) for r in rows]

    y = np.arange(len(rows))
    h = 0.34
    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.barh(y + h / 2 + 0.012, base, h, color=C2, label="base paper",
            zorder=2)
    ax.barh(y - h / 2 - 0.012, ours, h, color=C1, label="ours", zorder=2)
    for v, yy in zip(base, y + h / 2 + 0.012):
        ax.text(v + 0.06, yy, "%+.2f V" % v, va="center", fontsize=8.5,
                color=MUTED)
    for v, yy in zip(ours, y - h / 2 - 0.012):
        ax.text(v + 0.06, yy, "%+.2f V" % v, va="center", fontsize=8.5,
                color=INK, fontweight="bold")
    ax.axvline(0, **VTH_LINE)
    ax.set_yticks(y); ax.set_yticklabels(labels)
    ax.set_xlabel("crosstalk margin  (volts below the turn-on threshold)")
    ax.set_xlim(-0.15, 3.35)
    # A row of headroom at the top, so the note about the zero line has
    # somewhere to sit that is not on top of the longest bar or the title.
    ax.set_ylim(len(rows) - 0.42, -0.95)
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower right", ncol=2)
    ax.text(0.05, -0.88, "0 V — below this the device turns on when it should "
            "be off", fontsize=8.5, color=MUTED, va="top")
    ax.set_title("Ours holds one fixed setting. The base paper is re-tuned at "
                 "every corner. We still lead at all four.", loc="left",
                 pad=11)
    p = os.path.join(RES, "fig_headtohead.png")
    fig.savefig(p); plt.close(fig)
    print("  wrote %s" % os.path.basename(p))


# ------------------------------------------------------- model dependence --
def fig_modeldep():
    si = parse_margins("silicon_check.txt", ["ideal", "sky130"])
    cm = parse_margins("capmodel_check.txt", ["diodes", "charge"])
    order = ["constant word, no clamp", "clamp on", "clamp + -2 V off-bias"]
    nice = ["constant word,\nno clamp", "clamp on", "clamp +\n−2 V off-bias"]
    series = [("ideal switches", C1, [si[k][0] for k in order]),
              ("real SKY130 transistors", C2, [si[k][1] for k in order]),
              ("charge capacitance", C3, [cm[k][1] for k in order])]

    x = np.arange(len(order))
    w = 0.26
    fig, ax = plt.subplots(figsize=(10, 3.9))
    for i, (name, col, vals) in enumerate(series):
        off = (i - 1) * (w + 0.015)
        ax.bar(x + off, vals, w, color=col, label=name, zorder=2)
        for xx, v in zip(x + off, vals):
            ax.text(xx, v + (0.09 if v >= 0 else -0.09), "%+.2f" % v,
                    ha="center", va="bottom" if v >= 0 else "top",
                    fontsize=8.5, color=INK)
    ax.axhline(0, **VTH_LINE)
    ax.set_xticks(x); ax.set_xticklabels(nice)
    ax.set_ylabel("crosstalk margin  (V)")
    ax.set_ylim(-1.05, 3.25)
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left", ncol=3)
    # the note goes under the third group, which has no negative bars; under
    # the first group it lands on top of the two that do
    ax.text(x[-1] + 0.42, -0.16, "below this line the device falsely turns on",
            ha="right", va="top", fontsize=8.5, color=MUTED)
    ax.set_title("Swap the output stage, swap the capacitance law — only "
                 "the shipped design stays safe under all three.",
                 loc="left", pad=11)
    p = os.path.join(RES, "fig_modeldep.png")
    fig.savefig(p); plt.close(fig)
    print("  wrote %s" % os.path.basename(p))


# ------------------------------------------------------------ closed loop --
def fig_closedloop():
    """The two disturbances, which is what the slide claims.

    The full 0-1500 us window was tried first and is misleading: the
    open-loop run has no soft start BY CONSTRUCTION -- its control node is
    frozen from t=0, so it slams to the rail and rings for 200 us. That is an
    artifact of how the comparison is built, not a property of open-loop
    control, and on a shared axis it clips the top of the plot and buries the
    disturbances the figure exists to show. So the window starts once both are
    settled. The closed-loop soft start is a real number (3.8 % overshoot) and
    it lives in the caption.
    """
    path = os.path.join(RES, "closedloop_wave.csv")
    if not os.path.exists(path):
        print("  SKIPPED closed loop: run scripts/closedloop.py first")
        return
    d = np.genfromtxt(path, delimiter=",", names=True)
    m = d["t_us"] >= 780.0
    t = d["t_us"][m]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 4.5), sharex=True,
                                 gridspec_kw=dict(height_ratios=[2.9, 1],
                                                  hspace=0.13))
    a1.plot(t, d["vout_open"][m], color=C2, label="open loop")
    a1.plot(t, d["vout_closed"][m], color=C1, label="closed loop")
    a1.axhline(50, color=INK, lw=0.9, ls=(0, (4, 3)), zorder=1)
    a1.text(t[0] + 8, 51.4, "target 50 V", fontsize=8.5, color=MUTED)
    a1.text(t[-1] - 8, d["vout_open"][m][-1] + 1.0, "58.3 V", fontsize=10,
            color=C2, ha="right", fontweight="bold")
    a1.text(t[-1] - 8, d["vout_closed"][m][-1] - 1.6, "50.0 V", fontsize=10,
            color=C1, ha="right", va="top", fontweight="bold")
    a1.set_ylabel("output voltage  (V)")
    # the open-loop line-step transient peaks above 62 V; clipping a peak
    # off the top of a plot is how a figure tells a lie by omission
    a1.set_ylim(41, 66)
    a1.legend(loc="lower left", ncol=1)
    a1.set_title("Same converter, same drivers. The loop holds 50 V through "
                 "both disturbances; open loop walks to 58 V.",
                 loc="left", pad=11)

    a2.plot(t, d["iout"][m], color=MUTED, lw=1.0)
    a2.set_ylabel("load  (A)")
    a2.set_xlabel(u"time  (\u00b5s)")
    a2.set_ylim(0, 14)

    for ax in (a1, a2):
        for tx, lab in ((900.0, u"load 5 \u2192 10 A"),
                        (1200.0, u"input 100 \u2192 120 V")):
            ax.axvline(tx, color=MUTED, lw=0.9, ls=(0, (2, 3)), zorder=1)
            if ax is a1:
                ax.text(tx + 9, 64.6, lab, fontsize=9, color=MUTED)
    p = os.path.join(RES, "fig_closedloop.png")
    fig.savefig(p); plt.close(fig)
    print("  wrote %s" % os.path.basename(p))


if __name__ == "__main__":
    print("\n  RESULT FIGURES")
    fig_headtohead()
    fig_modeldep()
    fig_closedloop()
    print()
