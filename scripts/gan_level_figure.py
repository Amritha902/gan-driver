# -*- coding: utf-8 -*-
"""gan_level_figure.py -- the architecture at device level.

    python3 scripts/gan_level_figure.py  -> results/fig_gan_level.png

The block diagram on the architecture slide says what the parts are called.
It does not say what happens inside the GaN device, which is the only thing
this project is about: a fast edge on the switch node pushes charge through
C_GD into the gate that is supposed to stay off, and the gate rises because
that charge has to leave through whatever impedance the driver presents.

This draws that: the path the charge takes, and the three things the driver
does about it. The numbers are read from results/waveform_anatomy.txt, the
same file the crosstalk slide quotes, so the picture and the waveform cannot
disagree.
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "review"))
import waveform_numbers as W

RES = os.path.join(ROOT, "results")
INK = "#1B1F27"
BLUE = "#1D2F82"
GREEN = "#0B5C36"
GREENBG = "#E7F3EC"
HOT = "#B3261E"
GREY = "#5A5F6A"
RULE = "#C9CDD6"


def main():
    fig, ax = plt.subplots(figsize=(13.2, 6.0))
    ax.set_xlim(0, 200); ax.set_ylim(0, 92); ax.axis("off")

    def wire(pts, c=INK, lw=1.8, ls="-"):
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=c, lw=lw, ls=ls,
                zorder=2, solid_capstyle="round")

    def dot(x, y, c=INK):
        ax.plot([x], [y], "o", ms=5, color=c, zorder=4)

    def dev(x, y, label, sub):
        ax.add_patch(FancyBboxPatch((x, y), 17, 15,
                                    boxstyle="round,pad=0,rounding_size=1.2",
                                    fc="white", ec=INK, lw=1.8, zorder=3))
        ax.text(x + 8.5, y + 9.4, label, ha="center", va="center",
                fontsize=11.5, fontweight="bold", color=INK, zorder=4)
        ax.text(x + 8.5, y + 4.6, sub, ha="center", va="center",
                fontsize=9, color=GREY, zorder=4)

    def cap(x, y, w=7.0, gap=2.4, c=INK):
        wire([(x - w / 2.0, y + gap / 2.0), (x + w / 2.0, y + gap / 2.0)], c, 2.2)
        wire([(x - w / 2.0, y - gap / 2.0), (x + w / 2.0, y - gap / 2.0)], c, 2.2)

    # ---------------- left: the device and the charge path -----------------
    # The gate terminal is drawn on the RIGHT of the device so the charge
    # path runs left to right into the driver, the way the sentence reads.
    # The first version put it on the left and the wire had to double back
    # across the half-bridge, which made the one thing this figure exists to
    # show the hardest thing on it to follow.
    ax.text(2, 87, "THE MECHANISM, AT THE DEVICE", fontsize=11,
            fontweight="bold", color=INK)

    wire([(26, 82), (62, 82)])
    ax.text(26, 84.2, "VIN  100 V", fontsize=9.5, color=GREY)
    wire([(38, 82), (38, 75)])
    dev(30, 60, "Q$_{HS}$", "stays OFF")
    wire([(38, 60), (38, 52)])
    wire([(26, 52), (72, 52)])
    dot(38, 52)
    ax.text(66, 54.4, "SW", fontsize=10, fontweight="bold", color=INK)
    wire([(38, 52), (38, 43)])
    dev(30, 28, "Q$_{LS}$", "turns ON")
    wire([(38, 28), (38, 22)])
    wire([(32, 22), (44, 22)])
    ax.text(38, 18.8, "GND", fontsize=9, color=GREY, ha="center")

    ax.add_patch(FancyArrowPatch((18, 80), (18, 54), color=HOT, lw=2.2,
                                 arrowstyle="-|>", mutation_scale=15,
                                 shrinkA=0, shrinkB=0, zorder=5))
    ax.text(2, 70, "the edge\n%.0f V in %.2f ns\npeak %.0f V/ns"
            % (W.VBUS, W.FALL_NS, W.SLEW_PK), fontsize=9.4, color=HOT,
            va="top", fontweight="bold")

    wire([(56, 82), (56, 74)], HOT, 1.8)
    cap(56, 72, c=HOT)
    wire([(56, 70), (56, 67.5)], HOT, 1.8)
    ax.text(60.5, 72, "C$_{GD}$", fontsize=10.5, fontweight="bold",
            color=HOT, va="center")
    dot(56, 67.5, HOT)
    wire([(47, 67.5), (56, 67.5)], HOT, 1.8)
    wire([(56, 67.5), (56, 61)])
    cap(56, 59)
    wire([(56, 57), (56, 52)])
    ax.text(60.5, 59, "C$_{GS}$", fontsize=10.5, color=GREY, va="center")

    ax.text(2, 14, "Q$_{LS}$ turning on drags SW down. That dv/dt\n"
                   "drives i = C$_{GD}\\cdot$dv/dt into the gate of\n"
                   "Q$_{HS}$, which is supposed to be off. The gate\n"
                   "rises by whatever that charge cannot shed.",
            fontsize=9.5, color=INK, va="top")

    # ---------------- the crossing --------------------------------------
    ax.add_patch(FancyArrowPatch((60, 67.5), (92, 67.5), color=HOT, lw=2.4,
                                 arrowstyle="-|>", mutation_scale=17,
                                 shrinkA=0, shrinkB=0, zorder=5))
    ax.text(76, 63.4, "injected charge", fontsize=10, color=HOT,
            ha="center", fontweight="bold")
    ax.plot([86, 86], [6, 86], color=RULE, lw=1.4, ls=(0, (4, 4)))

    # ---------------- right: what the driver does -------------------------
    ax.text(92, 87, "WHAT THE DRIVER DOES ABOUT IT", fontsize=11,
            fontweight="bold", color=GREEN)
    wire([(92, 67.5), (196, 67.5)])
    dot(96, 67.5, HOT)
    ax.text(96, 70.0, "gate node of the OFF device", fontsize=9.5, color=GREY)

    # Short labels on purpose: the first version wrote a sentence in each
    # box and all three ran out through the sides.
    paths = [
        (98,  "Pull-down slices",  "8 $\\Omega$ / n\nhow hard it is held", False),
        (133, "Active Miller clamp", "0.5 $\\Omega$, own switch\nengaged on the edge", True),
        (168, "Off rail select",   "0 V or \u22122 V\nwhere the gate starts", True),
    ]
    for x, name, sub, ours in paths:
        wire([(x + 15, 67.5), (x + 15, 52)])
        ax.add_patch(FancyBboxPatch((x, 36), 30, 16,
                                    boxstyle="round,pad=0,rounding_size=1.2",
                                    fc=GREENBG if ours else "white",
                                    ec=GREEN if ours else INK, lw=1.8, zorder=3))
        ax.text(x + 15, 47, name, ha="center", va="center", fontsize=10,
                fontweight="bold", color=GREEN if ours else INK, zorder=4)
        ax.text(x + 15, 41, sub, ha="center", va="center", fontsize=8.6,
                color=GREY, zorder=4)
        wire([(x + 15, 36), (x + 15, 30)])
        if ours:
            ax.text(x + 15, 53.6, "added here", ha="center", fontsize=8.4,
                    color=GREEN, fontweight="bold")

    wire([(113, 30), (183, 30)])
    ax.text(185, 30, "V$_{N}$", fontsize=10, va="center", color=INK)

    # ---------------- the result -----------------------------------------
    ax.plot([92, 196], [24, 24], color=RULE, lw=1.4)
    ax.text(92, 20.5, "The gate that should stay off, measured:",
            fontsize=9.8, fontweight="bold", color=INK, va="top")
    ax.text(92, 15.5,
            "0 V rail, no clamp:  rests %+.3f V, lifted %+.3f V, "
            "peaks %+.3f V  — past the 1.4 V threshold"
            % (W.REST_BAD, W.LIFT_BAD, W.PEAK_BAD),
            fontsize=9.6, color=HOT, va="top")
    ax.text(92, 10.5,
            "−2 V rail + clamp:  rests %+.3f V, lifted only %+.3f V, "
            "peaks %+.3f V  — %.3f V of margin"
            % (W.REST_GOOD, W.LIFT_GOOD, W.PEAK_GOOD, 1.4 - W.PEAK_GOOD),
            fontsize=9.6, color=GREEN, va="top")
    ax.text(92, 5.5, "Two different mechanisms: the rail moves where the gate "
                     "starts, the clamp shortens the lift.",
            fontsize=9.4, color=GREY, va="top", style="italic")

    p = os.path.join(RES, "fig_gan_level.png")
    fig.savefig(p, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  wrote %s  (peak %+.3f V without, %+.3f V with)"
          % (os.path.relpath(p, ROOT), W.PEAK_BAD, W.PEAK_GOOD))
    return 0


if __name__ == "__main__":
    sys.exit(main())
