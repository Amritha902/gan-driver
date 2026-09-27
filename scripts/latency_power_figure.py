"""
latency_power_figure.py -- the two parameters the panel asked about, alone.

The Review-1 comment named latency and device power specifically. Both are in
the six-parameter tables (slides 4 and 24) and in the three-way small
multiples (slide 26), but in each of those they are one row among six, and a
row among six is not an answer to a question that was asked about two.

This is those two, at full size, for all three configurations, with the ratio
on each bar. Nothing here is new data: it is results/panel_metrics.csv, the
same file the tables read.
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUT = os.path.join(RES, "fig_latency_power.png")

# node scripts/validate_palette.js "#1b7f5f,#b8761a,#2a78d6" --mode light
# -> ALL CHECKS PASS on #fcfcfb
SI, BASE, OURS = "#1b7f5f", "#b8761a", "#2a78d6"
INK, MUTED, RULE, SURF = "#0b0b0b", "#52514e", "#d8d7d2", "#fcfcfb"

CONFIGS = [("si_ours",  u"Silicon MOSFET",        SI),
           ("gan_base", u"GaN, base paper [10]",  BASE),
           ("gan_ours", u"GaN, our driver",       OURS)]

PANELS = [("latency_ns", u"Latency", u"PWM edge → switch node at 50 %",
           u"ns", "%.2f"),
          ("p_dev_W",    u"Power lost in the devices", u"averaged over 20 whole "
           u"switching cycles", u"W", "%.2f")]


def main():
    pm = {r["config"]: r for r in csv.DictReader(
        open(os.path.join(RES, "panel_metrics.csv")))}

    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.2), facecolor=SURF)
    fig.subplots_adjust(wspace=0.30, top=0.74, bottom=0.14, left=0.03, right=0.985)

    for ax, (key, title, sub, unit, fmt) in zip(axes, PANELS):
        vals = [float(pm[c][key]) for c, _, _ in CONFIGS]
        cols = [c for _, _, c in CONFIGS]
        y = list(range(len(vals)))[::-1]

        ax.set_facecolor(SURF)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color(RULE)
        ax.tick_params(colors=MUTED, labelsize=10, length=0)
        ax.grid(True, axis="x", color=RULE, lw=0.6, alpha=0.7)
        ax.set_axisbelow(True)
        ax.barh(y, vals, color=cols, height=0.58, linewidth=0)
        ax.set_xlim(0, max(vals) * 1.42)
        ax.set_xticklabels([])

        best = min(vals)
        for yy, v, c in zip(y, vals, cols):
            ax.annotate((fmt + " %s") % (v, unit), (v, yy),
                        textcoords="offset points", xytext=(9, 1), va="center",
                        color=INK, fontsize=14, weight="bold")
            if v > best:
                ax.annotate(u"%.1f×" % (v / best), (v, yy),
                            textcoords="offset points", xytext=(9, -17),
                            va="center", color=MUTED, fontsize=10.5)
        ax.set_yticks(y)
        ax.set_yticklabels([n for _, n, _ in CONFIGS], fontsize=11.5, color=INK)
        ax.set_title(title, color=INK, fontsize=16, weight="bold",
                     loc="left", pad=26)
        ax.annotate(sub + u"   ·   lower is better", (0.0, 1.045),
                    xycoords="axes fraction", color=MUTED, fontsize=10.5)

    fig.suptitle(u"Latency and device power — the two the panel asked for",
                 x=0.03, y=0.955, ha="left", color=INK, fontsize=18, weight="bold")
    fig.text(0.03, 0.035,
             u"Same converter, same 25 mΩ device class, same parasitics and "
             u"solver options. Silicon → base paper changes the DEVICE; base "
             u"paper → ours changes the CONTROL.\n"
             u"ngspice on sim/buck.cir · results/panel_metrics.csv · "
             u"regenerate with scripts/latency_power_figure.py",
             ha="left", color=MUTED, fontsize=10, linespacing=1.6)

    fig.savefig(OUT, dpi=170, bbox_inches="tight", facecolor=SURF)
    print("wrote %s" % OUT)
    for key, title, _, unit, fmt in PANELS:
        vs = [(n, float(pm[c][key])) for c, n, _ in CONFIGS]
        best = min(v for _, v in vs)
        print("  %s" % title)
        for n, v in vs:
            print("    %-24s " % n + (fmt % v) + " %s" % unit +
                  ("" if v == best else "   %.1fx" % (v / best)))


if __name__ == "__main__":
    main()
