"""
three_way_figure.py -- silicon, the base paper, and ours, on one sheet.

The Review-1 panel asked for two things: why GaN instead of silicon, and what
our driver does that the base paper's does not -- with latency and device
power measured precisely, plus other parameters.

scripts/winlose_figure.py answers that as two PAIRWISE comparisons side by
side, which is the right form for "how much better, and where do we lose".
It is the wrong form for "put the three of them next to each other", because
a reader cannot read silicon against the base paper off it at all: they never
appear in the same panel.

This is that missing view. Three configurations, six measured parameters, one
small panel per parameter -- small multiples rather than one chart, because
the six are in four different units and a single axis would be a lie. Every
bar carries its own number, so the picture never has to be read off a scale.

All three columns are the same converter (sim/buck.cir), the same 25 mOhm
device class, the same parasitics and the same solver options. Between column
1 and the others only the DEVICE changes; between columns 2 and 3 only the
CONTROL changes.

Source: results/panel_metrics.csv, written by scripts/panel_metrics.py.
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUT = os.path.join(RES, "fig_three_way.png")

# node scripts/validate_palette.js "#2a78d6,#b8761a,#1b7f5f" --mode light
# -> ALL CHECKS PASS on #fcfcfb (worst adjacent CVD dE 8.6 protan,
#    tritan 23.1, normal 19.5). Bars are also directly labelled, which is
#    the secondary encoding the validator asks for.
SI, BASE, OURS = "#1b7f5f", "#b8761a", "#2a78d6"
INK, MUTED, RULE, SURF = "#0b0b0b", "#52514e", "#d8d7d2", "#fcfcfb"

CONFIGS = [("si_ours",   u"Silicon MOSFET\n+ our driver",   SI),
           ("gan_base",  u"GaN + base paper's\ndriver [10]", BASE),
           ("gan_ours",  u"GaN + our driver",                OURS)]

# key, title, unit, format, lower-is-better
PARAMS = [
    ("latency_ns", u"Latency, PWM → switch node", u"ns", "%.2f", True),
    ("p_dev_W",    u"Power lost in the devices",       u"W",  "%.2f", True),
    ("trans_ns",   u"Switching edge, 10 → 90 %",  u"ns", "%.2f", True),
    ("p_gate_W",   u"Power lost in the gate drive",    u"W",  "%.3f", True),
    ("eff_pct",    u"Converter efficiency",            u"%",  "%.2f", False),
    ("ov_pct",     u"Switch-node overshoot",           u"%",  "%.1f", True),
]


def main():
    pm = {r["config"]: r for r in csv.DictReader(
        open(os.path.join(RES, "panel_metrics.csv")))}

    fig, axes = plt.subplots(3, 2, figsize=(12.6, 9.4), facecolor=SURF)
    fig.subplots_adjust(hspace=0.62, wspace=0.34, top=0.86, bottom=0.10)

    for ax, (key, title, unit, fmt, lower_better) in zip(axes.ravel(), PARAMS):
        vals = [float(pm[c][key]) for c, _, _ in CONFIGS]
        cols = [c for _, _, c in CONFIGS]
        y = list(range(len(vals)))[::-1]          # first config on top

        ax.set_facecolor(SURF)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
        ax.spines["bottom"].set_color(RULE)
        ax.tick_params(colors=MUTED, labelsize=9, length=0)
        ax.grid(True, axis="x", color=RULE, lw=0.6, alpha=0.7)
        ax.set_axisbelow(True)

        ax.barh(y, vals, color=cols, height=0.62, linewidth=0)
        lo, hi = min(min(vals), 0.0), max(max(vals), 0.0)
        pad = (hi - lo) * 0.30 or 1.0
        ax.set_xlim(lo - (pad if lo < 0 else 0), hi + pad)

        for yy, v, c in zip(y, vals, cols):
            off = 5 if v >= 0 else -5
            # unit can itself be "%", so format the number first and
            # concatenate -- "%.2f %" % v is an incomplete format string.
            ax.annotate((fmt % v) + " " + unit, (v, yy),
                        textcoords="offset points", xytext=(off, 0),
                        ha="left" if v >= 0 else "right", va="center",
                        color=INK, fontsize=10, weight="bold")

        ax.set_yticks(y)
        ax.set_yticklabels([n for _, n, _ in CONFIGS], fontsize=9.5,
                           color=MUTED, linespacing=1.35)
        ax.set_xticklabels([])
        # The direction-and-spread line used to sit at the title's own
        # height, right-aligned, and collided with every long title. It has
        # its own line under the title now.
        best = min(vals) if lower_better else max(vals)
        ax.set_title(title, color=INK, fontsize=11.5, weight="bold",
                     loc="left", pad=22)
        sub = u"lower is better" if lower_better else u"higher is better"
        if lower_better and best > 0:
            sub += u"   \u00b7   %.1f\u00d7 between best and worst" % (max(vals) / best)
        ax.annotate(sub, (0.0, 1.045), xycoords="axes fraction", ha="left",
                    color=MUTED, fontsize=9.5)

    fig.suptitle(u"Silicon, the base paper, and ours — same converter, "
                 u"same device class, measured", x=0.012, y=0.975,
                 ha="left", color=INK, fontsize=16, weight="bold")
    fig.text(0.012, 0.925,
             u"Column 1 → 2 changes only the DEVICE. Column 2 → 3 "
             u"changes only the CONTROL. 100 V → 50 V, 500 kHz, 10 Ω, "
             u"3 nH power loop.",
             ha="left", color=MUTED, fontsize=10.5)
    fig.text(0.012, 0.028,
             u"Six parameters in four different units, so one small chart each "
             u"rather than one chart with one axis — every bar carries its "
             u"own number.\nSilicon does not overshoot because its edge is nine "
             u"times slower, which is the same slowness that costs it 6.0 W in "
             u"the devices. Speed and device stress are one knob.\n"
             u"ngspice on sim/buck.cir · results/panel_metrics.csv · "
             u"regenerate with scripts/three_way_figure.py",
             ha="left", color=MUTED, fontsize=9.5, linespacing=1.6)

    fig.savefig(OUT, dpi=170, bbox_inches="tight", facecolor=SURF)
    print("wrote %s" % OUT)

    w = max(len(n.replace("\n", " ")) for _, n, _ in CONFIGS)
    print("\n  %-34s %s" % ("", "  ".join("%12s" % n.replace("\n", " ")[:12]
                                          for _, n, _ in CONFIGS)))
    for key, title, unit, fmt, lb in PARAMS:
        print("  %-34s %s   %s" % (
            title, "  ".join("%12s" % (fmt % float(pm[c][key]))
                             for c, _, _ in CONFIGS), unit))


if __name__ == "__main__":
    main()
