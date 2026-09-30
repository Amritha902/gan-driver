# -*- coding: utf-8 -*-
"""arch_figures.py -- the architecture slide and the what-we-add slide.

    python3 scripts/arch_figures.py
        -> results/fig_architecture.png   (slide 4)
        -> results/fig_arch_delta.png     (slide 6)

Both replace block diagrams that had gone stale and were, on a projector,
too small to read.

Slide 4 was a four-column diagram with sixteen boxes, and it still said the
adaptive block was worth 3.9 % of baseline -- the n=4 figure that
grid_analyse.py superseded with 2.6 % over 36 corners. It is now one
left-to-right path, because that is what the system is, and the number is
read out of RESULTS-SUMMARY.txt rather than typed.

Slide 6 drew the whole architecture twice, once for the base paper and once
for ours, so that a reader could find the three differences by comparing two
diagrams of sixteen boxes each. It is now a table of the five things that
differ, with the row that matters -- the crosstalk margin those differences
buy -- read from results/headtohead.csv.
"""
import csv
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")

INK = "#1D2F82"          # the deck's title blue
GREEN = "#0B5C36"
GREEN_BG = "#E7F3EC"
GREY = "#5A5F６A".replace("６", "6")
LINE = "#C8CCD4"
HOT = "#B3261E"
PAPER = "#F4F5F8"


def adaptive_share():
    """(B), what adapting per operating point is worth, from the summary."""
    path = os.path.join(RES, "RESULTS-SUMMARY.txt")
    txt = open(path).read()
    m = re.search(r"\(B\) adapting it per operating point\s+([\d.]+) %", txt)
    if not m:
        raise SystemExit("RESULTS-SUMMARY.txt: cannot find (B)")
    return float(m.group(1))


def margins():
    """Base-paper and our crosstalk margin at the headline corner."""
    with open(os.path.join(RES, "headtohead.csv")) as fh:
        for r in csv.DictReader(fh):
            if r["corner"].strip() == "100V_10A_25C":
                return float(r[" base_retuned"]), float(r[" ours"])
    raise SystemExit("headtohead.csv: no 100V_10A_25C row")


LABELS = []            # (text artist, box left, box width) for the fit check


def check_fits(fig, ax):
    """Does every label sit inside the box it belongs to?

    matplotlib will draw a string straight out through the side of a
    rectangle without complaint, and on a slide that reads as a mistake. The
    first version of this figure shipped with "8 pull-up . 8 pull-down .
    clamp . off-bias" hanging out of both sides of its box. Measure it
    instead: convert the drawn text's pixel width back into data units and
    compare with the box.
    """
    fig.canvas.draw()
    inv = ax.transData.inverted()
    bad = []
    for art, bx, bw in LABELS:
        ext = art.get_window_extent(fig.canvas.get_renderer())
        (x0, _), (x1, _) = inv.transform([(ext.x0, ext.y0), (ext.x1, ext.y1)])
        if (x1 - x0) > bw - 1.2:
            bad.append((art.get_text(), x1 - x0, bw))
    if bad:
        raise SystemExit(
            "arch_figures: label wider than its box -- "
            + "; ".join("%r needs %.1f, box is %.1f" % b for b in bad))


def box(ax, x, y, w, h, title, sub=None, fc="white", ec=INK, tc=INK, lw=1.6,
        ls="-"):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0,rounding_size=1.4",
                                fc=fc, ec=ec, lw=lw, ls=ls, zorder=2))
    t = ax.text(x + w / 2.0, y + h * (0.60 if sub else 0.5), title,
                ha="center", va="center", fontsize=12.5, fontweight="bold",
                color=tc, zorder=3)
    LABELS.append((t, x, w))
    if sub:
        t2 = ax.text(x + w / 2.0, y + h * 0.27, sub, ha="center", va="center",
                     fontsize=10.2, color=GREY, zorder=3)
        LABELS.append((t2, x, w))


def arrow(ax, x1, y1, x2, y2, color=INK, lw=2.0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), color=color, lw=lw,
                                 arrowstyle="-|>", mutation_scale=15,
                                 shrinkA=0, shrinkB=0, zorder=2))


# ------------------------------------------------------------ slide 4 ------
def architecture():
    """The architecture, with the driver opened up.

    This was five boxes in a row -- PWM, FPGA, driver, half-bridge, load --
    which is a signal path, not an architecture: it showed nothing of what is
    inside the block the project designs, so a reviewer could not tell what
    was built from what was bought. The driver is now exploded into the four
    things it contains, and the control word is shown as the six fields the
    FPGA emits rather than as an unlabelled arrow.

    The FPGA block is drawn by hand rather than with box(): box() centres its
    title at mid-height, which lands it on top of a field list.
    """
    fig, ax = plt.subplots(figsize=(13.0, 5.4))
    ax.set_xlim(0, 133); ax.set_ylim(6, 62); ax.axis("off")

    # ---- control plane ------------------------------------------------
    box(ax, 1, 40, 19, 11, "PWM in", "duty / frequency", fc=PAPER, ec=GREY,
        tc="#33363D")
    arrow(ax, 20, 45.5, 22, 45.5)

    ax.add_patch(FancyBboxPatch((22, 26), 30, 29,
                                boxstyle="round,pad=0,rounding_size=1.4",
                                fc="white", ec=INK, lw=1.6, zorder=2))
    ax.text(37, 52.0, "seg_gate_ctrl.v", ha="center", va="center",
            fontsize=13.5, fontweight="bold", color=INK, zorder=3)
    ax.text(37, 48.8, "FPGA \u00b7 20 LUT / 20 FF", ha="center", va="center",
            fontsize=11.2, color=GREY, zorder=3)
    for i, f in enumerate(["NPU \u00b7 pull-up strength",
                           "NPD \u00b7 pull-down strength",
                           "DT \u00b7 dead time",
                           "CLKEN \u00b7 clamp enable",
                           "VNEG \u00b7 off-rail select",
                           "CLKDEL \u00b7 clamp timing"]):
        ax.text(24.5, 44.2 - i * 2.5, f, ha="left", va="center", fontsize=9.4,
                color=INK, zorder=3)
    ax.text(37, 28.6, "six fields \u2192 720 control words", ha="center",
            va="center", fontsize=11.2, color=INK, fontweight="bold", zorder=3)

    arrow(ax, 52, 45.5, 56, 45.5)
    ax.text(54, 47.6, "word", ha="center", va="bottom", fontsize=9.2,
            color=INK)

    # ---- the driver, opened up ----------------------------------------
    ax.add_patch(FancyBboxPatch((56, 26), 40, 29,
                                boxstyle="round,pad=0,rounding_size=1.4",
                                fc=GREEN_BG, ec=GREEN, lw=1.6, zorder=2))
    ax.text(76, 52.0, "Segmented gate driver", ha="center", va="center",
            fontsize=13.5, fontweight="bold", color=GREEN, zorder=3)
    ax.text(76, 48.8, "\u00d7 2 \u2014 one per gate", ha="center",
            va="center", fontsize=11.2, color=GREEN, zorder=3)
    for i, (t, sub) in enumerate([
            ("8 pull-up segments", "from VP, thermometer coded"),
            ("8 pull-down segments", "to VN, thermometer coded"),
            ("active Miller clamp", "own switch, 0.5 \u03a9 to VN"),
            ("off-bias mux", "VN = 0 V or \u22122 V")]):
        yy = 41.4 - i * 4.6
        ax.add_patch(FancyBboxPatch((58.5, yy), 35, 3.9,
                                    boxstyle="round,pad=0,rounding_size=1.0",
                                    fc="white", ec=GREEN, lw=1.1, zorder=3))
        ax.text(60.2, yy + 2.55, t, ha="left", va="center", fontsize=9.8,
                color=GREEN, fontweight="bold", zorder=4)
        ax.text(60.2, yy + 1.10, sub, ha="left", va="center", fontsize=8.8,
                color=GREY, zorder=4)

    # ---- power plane ---------------------------------------------------
    arrow(ax, 96, 41.5, 99, 41.5)
    box(ax, 99, 35, 24, 13, "GaN half-bridge", "high side + low side")
    ax.text(111, 32.6, "SW node", ha="center", va="center", fontsize=9.4,
            color=GREY)
    arrow(ax, 123, 41.5, 125, 41.5)
    box(ax, 125, 35, 8, 13, "L-C", None, fc=PAPER, ec=GREY, tc="#33363D")
    ax.text(129, 32.6, "\u2192 load", ha="center", va="center", fontsize=9.4,
            color=GREY)
    ax.text(116, 28.4, "100 V \u2192 48.50 V, 97.49 %", ha="center",
            va="center", fontsize=10.6, color=INK, fontweight="bold")

    # ---- the fault, from the switch node back into the driver ----------
    ax.plot([111, 111, 76, 76], [35, 20, 20, 26], color=HOT, lw=2.0,
            zorder=1)
    ax.add_patch(FancyArrowPatch((76, 20), (76, 25.6), color=HOT, lw=2.0,
                                 arrowstyle="-|>", mutation_scale=14,
                                 shrinkA=0, shrinkB=0, zorder=2))
    ax.text(93, 17.6, "C$_{GD}$ crosstalk \u2014 the switching edge lifts "
            "the gate that should stay off", ha="center", va="top",
            fontsize=11.0, color=HOT, fontweight="bold")

    # ---- the one sentence the whole project turns on -------------------
    b_ = adaptive_share()
    ax.text(66, 9.6, "The control word is set once at power-up \u2014 no "
            "sensor, no lookup table. Re-tuning it while the converter runs "
            "is worth a further %.1f %%." % b_,
            ha="center", va="center", fontsize=11.2, color=INK,
            fontweight="bold")

    check_fits(fig, ax)
    p = os.path.join(RES, "fig_architecture.png")
    fig.savefig(p, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  wrote %s  (adaptive share %.1f %%)"
          % (os.path.relpath(p, ROOT), b_))


# ------------------------------------------------------------ slide 6 ------
def delta_table():
    base, ours = margins()
    rows = [
        ("Control of the driver",
         "one analogue bias resistor,\nset at fabrication",
         "seg_gate_ctrl.v — digital,\nre-writable while it runs", True),
        ("Output stage",
         "7 + 7 segments, two stages",
         "8 + 8 segments, thermometer coded", False),
        ("Active Miller clamp", "none", "always on", True),
        ("Gate off rail", "0 V", "selectable 0 V / −2 V", True),
        ("Crosstalk margin\nat 100 V / 10 A",
         "%+.3f V" % base, "%+.3f V" % ours, False),
    ]

    fig, ax = plt.subplots(figsize=(13.0, 6.0))
    ax.set_xlim(0, 130); ax.set_ylim(2, 66); ax.axis("off")

    x0, x1, x2, w1, w2 = 1.0, 41.0, 86.0, 43.0, 43.0
    ax.text(x1 + w1 / 2.0, 61.5, "BASE PAPER — Zhang et al., ISPSD 2020",
            ha="center", va="center", fontsize=12, fontweight="bold",
            color="#33363D")
    ax.text(x2 + w2 / 2.0, 61.5, "OURS", ha="center", va="center",
            fontsize=12, fontweight="bold", color=GREEN)

    y = 47.0
    for label, a, b, added in rows:
        h = 9.4
        ax.plot([x0, 129], [y + h, y + h], color=LINE, lw=1.0, zorder=1)
        ax.text(x0 + 1.0, y + h / 2.0, label, ha="left", va="center",
                fontsize=11.5, fontweight="bold", color=INK)
        ax.text(x1 + w1 / 2.0, y + h / 2.0, a, ha="center", va="center",
                fontsize=11, color="#33363D")
        if added:
            ax.add_patch(FancyBboxPatch((x2, y + 0.7), w2, h - 1.4,
                                        boxstyle="round,pad=0,rounding_size=1.2",
                                        fc=GREEN_BG, ec=GREEN, lw=1.4, zorder=1))
        last = label.startswith("Crosstalk")
        ax.text(x2 + w2 / 2.0, y + h / 2.0, b, ha="center", va="center",
                fontsize=13 if last else 11,
                color=GREEN if (added or last) else "#33363D",
                fontweight="bold" if (added or last) else "normal")
        y -= h

    ax.plot([x0, 129], [y + 9.4, y + 9.4], color=LINE, lw=1.0)
    ax.text(x0 + 1.0, y + 4.0,
            "Shaded: the three blocks we add. Everything else is theirs, "
            "unchanged — same command, same power stage. "
            "%.1f× the margin, from one fixed setting." % (ours / base),
            ha="left", va="center", fontsize=10.8, color=GREY)

    p = os.path.join(RES, "fig_arch_delta.png")
    fig.savefig(p, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  wrote %s  (%.3f V vs %.3f V, %.1fx)"
          % (os.path.relpath(p, ROOT), base, ours, ours / base))


def main():
    architecture()
    delta_table()
    return 0


if __name__ == "__main__":
    sys.exit(main())
