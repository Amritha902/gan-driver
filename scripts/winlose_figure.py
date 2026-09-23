# -*- coding: utf-8 -*-
"""winlose_figure.py -- where the design wins and where it loses, per parameter.

    python3 scripts/winlose_figure.py

THE FORM
  The data's job here is POLARITY -- for each measured parameter, are we
  better or worse than what we are compared against? That is a diverging
  bar chart: two hues with a neutral zero, bars left for worse and right
  for better, never a rainbow and never a second axis.

  Percentage change is the right scale because the six parameters are in
  four different units (ns, W, %, %). Plotting nanoseconds and watts on one
  axis would be meaningless; plotting them on two axes would be the single
  worst chart mistake there is. Normalising to "% better than the thing we
  are compared with" puts them on one honest axis.

COLOUR
  Diverging blue/red from the reference palette, validated rather than
  eyeballed:
    light  #2a78d6 / #d03b3b  -- all six checks PASS on #fcfcfb
    dark   #3987e5 / #e34948  -- all six checks PASS on #1a1a19
  Worst adjacent pair separates by dE 23.8 under protanopia and 31.6 for
  normal vision, so the two poles are distinguishable without relying on
  colour alone. Every bar is also directly labelled and the sign of the bar
  carries the meaning, which is the secondary encoding.

WHAT IS DELIBERATELY NOT HIDDEN
  Two bars go the wrong way in each panel and they are drawn at full length
  in red with their numbers on them. A chart of a design's wins with its
  losses trimmed off is not a result, it is an advertisement, and a panel
  that spots the omission stops believing the rest of the figure.
"""
import csv, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES  = os.path.join(ROOT, "results")

BETTER, WORSE = "#2a78d6", "#d03b3b"
INK, MUTED, RULE, SURF = "#0b0b0b", "#52514e", "#d8d7d2", "#fcfcfb"
plt.rcParams["font.family"] = "DejaVu Sans"

rows = {}
with open(os.path.join(RES, "panel_metrics.csv")) as fh:
    for r in csv.DictReader(fh):
        rows[r["config"]] = r

# (key, label, unit, lower_is_better)
PARAMS = [
    ("latency_ns", u"Latency\nPWM → switch node", "ns", True),
    ("trans_ns",   u"Edge time\n10 → 90 %",        "ns", True),
    ("p_dev_W",    u"Power in the devices",             "W",  True),
    ("p_gate_W",   u"Power in the gate drive",          "W",  True),
    ("eff_pct",    u"Converter efficiency",             "%",  False),
    ("ov_pct",     u"Switch-node overshoot",            "%",  True),
]


def pct_better(ours, theirs, lower_better):
    """Symmetric relative difference, signed, bounded to +/-100 %.

        (better - worse) / (|ours| + |theirs|) * 100

    NOT plain percentage change. Percentage change divides by the
    comparison value, and that is invalid the moment the comparison is near
    zero or has the opposite sign. Silicon's switch-node overshoot is
    -1.5 %, so plain percentage change put our overshoot row at -1283.9 % --
    a number with no meaning that set the axis limit and squashed the other
    five parameters into slivers.

    The symmetric form divides by the sum of magnitudes instead. It cannot
    exceed +/-100, it behaves when a value crosses zero, and it keeps the
    sign that matters: positive means ours is better. A row that pins at
    -100 is saying "as far the wrong way as this scale goes", and the raw
    numbers printed under every bar say by how much in real units.
    """
    a, b = float(ours), float(theirs)
    denom = abs(a) + abs(b)
    if denom == 0:
        return 0.0
    return ((b - a) if lower_better else (a - b)) / denom * 100.0


def panel(ax, us, them, them_name, title, subtitle):
    labels, vals, raw = [], [], []
    for key, lab, unit, lower in PARAMS:
        v = pct_better(us[key], them[key], lower)
        labels.append(lab)
        vals.append(v)
        fmt = "%.3f" if key == "p_gate_W" else "%.2f"
        raw.append(((fmt % float(us[key])) + " " + unit,
                    (fmt % float(them[key])) + " " + unit))

    y = range(len(labels))[::-1]
    for yy, v in zip(y, vals):
        ax.barh(yy, v, height=0.52, color=(BETTER if v >= 0 else WORSE),
                edgecolor=SURF, linewidth=2, zorder=3)

    lim = 100.0 * 1.55          # the measure is bounded, so fix the axis
    ax.set_xlim(-lim, lim)
    ax.axvline(0, color=INK, lw=1.4, zorder=4)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=9.6, color=INK)
    ax.tick_params(axis="y", length=0, pad=6)
    ax.set_xticks([])
    for s in ("top", "right", "bottom", "left"):
        ax.spines[s].set_visible(False)
    ax.set_facecolor(SURF)

    for yy, v, (a, b) in zip(y, vals, raw):
        off = lim * 0.035
        ax.text(v + (off if v >= 0 else -off), yy,
                ("%+.1f %%" % v), va="center",
                ha="left" if v >= 0 else "right",
                fontsize=9.6, fontweight="bold", color=INK, zorder=5)
        # the underlying numbers, so the percentage is never the only claim
        ax.text(-lim * 0.985, yy - 0.34, u"ours %s  ·  %s %s" % (a, them_name, b),
                va="center", ha="left", fontsize=7.9, color=MUTED, zorder=5)

    # Title, subtitle and the axis hint each get their own band. The first
    # version stacked all three within a few pixels and they overprinted.
    ax.set_title(title, fontsize=12.5, fontweight="bold", color=INK,
                 loc="left", pad=34)
    ax.text(0, 1.085, subtitle, transform=ax.transAxes, fontsize=9.2,
            color=MUTED, ha="left", va="bottom")
    # No "<- worse  better ->" hint: it shared a baseline with the subtitle
    # and overprinted it, and it was redundant anyway -- every bar carries a
    # signed label and the two poles are already blue/red.


fig, axes = plt.subplots(1, 2, figsize=(13.2, 6.8), dpi=170)
fig.patch.set_facecolor(SURF)

panel(axes[0], rows["gan_ours"], rows["si_ours"], "Si",
      u"GaN against silicon",
      u"Same converter, same driver. Only the device changes.")
panel(axes[1], rows["gan_ours"], rows["gan_base"], "theirs",
      u"Ours against the base paper",
      u"Same converter, same device. Only the control changes.")

fig.text(0.008, 0.085,
         u"Symmetric relative difference: (better − worse) / (|ours| + "
         u"|theirs|), bounded to ±100 %. The six parameters are in four\n"
         u"different units, so they are normalised rather than put on two axes. "
         u"Raw values are printed under every bar.",
         fontsize=8.8, color=MUTED)
fig.text(0.008, 0.040,
         u"Plain percentage change was wrong here and was replaced: silicon's "
         u"overshoot is −1.5 %, so dividing by a\nnear-zero, opposite-sign "
         u"baseline put that row at −1284 % and flattened the other five.",
         fontsize=8.8, color=MUTED)
fig.text(0.008, 0.004,
         u"Red bars are where our design loses, drawn at full length. "
         u"Source: results/panel_metrics.csv, ngspice on sim/buck.cir.",
         fontsize=8.8, color=INK, fontweight="bold")

fig.subplots_adjust(left=0.135, right=0.975, top=0.84, bottom=0.26, wspace=0.52)
out = os.path.join(RES, "fig_winlose.png")
fig.savefig(out, dpi=170, facecolor=SURF)
print("  written: results/fig_winlose.png")
for name, us, them in (("vs silicon", rows["gan_ours"], rows["si_ours"]),
                       ("vs base paper", rows["gan_ours"], rows["gan_base"])):
    line = []
    for key, lab, unit, lower in PARAMS:
        line.append("%s %+.1f%%" % (key, pct_better(us[key], them[key], lower)))
    print("  %-14s %s" % (name, "  ".join(line)))
