# -*- coding: utf-8 -*-
"""title_circuit.py -- the circuit, on the title slide.

The cover page said what the project is called and showed nothing of what it
is. A reviewer's first two seconds decided "some simulation study" rather
than "a gate driver for a GaN half-bridge", and every slide after that was
spent climbing out of that first impression.

This is deliberately the simplest true drawing of the thing: one half-bridge,
the two gate drivers that drive it, the output filter, the load, and the
crosstalk path the project exists to fix. No slice detail, no component
values, no annotations -- slides 7 to 17 do all of that. At title-slide size
anything more becomes grey texture.

Drawn rather than cropped from KiCad on purpose: a 2560x1440 screen capture
of eeschema shrunk into 4 inches is unreadable, and an unreadable circuit is
worse than no circuit.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "fig_title_circuit.png")

INK = "#1a1a1a"
WIRE = "#333333"
DRV = "#1D2F82"       # the block this project designs
FAULT = "#c0392b"     # the coupling it fixes
MUTE = "#6b6b6b"


def _gan(ax, x, y, label):
    """One enhancement-mode HEMT, drawn the way a power-electronics reader
    expects: gate plate on the left, a broken channel beside it, drain lead
    up and source lead down, arrow into the channel.

    The first attempt drew a rounded box with a bar in it, which reads as a
    capacitor -- on a title slide that is worse than drawing nothing.
    """
    xg, xc = x - 0.30, x - 0.10          # gate plate, channel
    ax.plot([xg - 0.46, xg], [y, y], color=INK, lw=1.5, zorder=4)   # gate lead
    ax.plot([xg, xg], [y - 0.34, y + 0.34], color=INK, lw=2.0, zorder=4)
    for y0, y1 in ((y + 0.12, y + 0.34), (y - 0.11, y + 0.11),
                   (y - 0.34, y - 0.12)):               # broken channel
        ax.plot([xc, xc], [y0, y1], color=INK, lw=2.4, zorder=4,
                solid_capstyle="butt")
    ax.plot([xc, x + 0.34], [y + 0.28, y + 0.28], color=INK, lw=1.5, zorder=4)
    ax.plot([x + 0.34, x + 0.34], [y + 0.28, y + 0.62], color=INK, lw=1.5,
            zorder=4)
    ax.plot([xc, x + 0.34], [y - 0.28, y - 0.28], color=INK, lw=1.5, zorder=4)
    ax.plot([x + 0.34, x + 0.34], [y - 0.62, y - 0.28], color=INK, lw=1.5,
            zorder=4)
    ax.plot([xc, x + 0.34], [y, y], color=INK, lw=1.5, zorder=4)   # body
    ax.annotate("", xy=(xc + 0.02, y), xytext=(xc + 0.22, y),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.3),
                zorder=4)
    ax.text(x + 0.50, y - 0.46, label, fontsize=8.8, color=INK, va="center",
            ha="left", zorder=5)


def main():
    fig, ax = plt.subplots(figsize=(6.8, 3.05), dpi=260)
    ax.set_xlim(0, 11.6); ax.set_ylim(0, 5.0)
    ax.set_axis_off()

    YT, YB = 4.30, 0.95                  # top rail, ground rail
    XB = 4.35                            # the half-bridge column
    YH, YL = 3.45, 1.95                  # high-side and low-side devices
    YSW = 2.70                           # switch node

    # ---- 100 V source, drawn as a source and not as a loop -----------
    ax.plot([0.72, 0.72], [YB, YT], color=WIRE, lw=1.6)
    ax.plot([0.46, 0.98], [2.86, 2.86], color=WIRE, lw=2.4)
    ax.plot([0.58, 0.86], [2.55, 2.55], color=WIRE, lw=1.6)
    ax.text(0.30, 2.70, u"100 V", fontsize=9.2, color=INK, rotation=90,
            va="center", ha="center", weight="bold")
    ax.plot([0.72, XB + 0.34], [YT, YT], color=WIRE, lw=1.6)
    ax.plot([0.72, XB + 0.34], [YB, YB], color=WIRE, lw=1.6)

    # ---- the half-bridge ---------------------------------------------
    _gan(ax, XB, YH, u"high side")
    _gan(ax, XB, YL, u"low side")
    ax.plot([XB + 0.34, XB + 0.34], [YH + 0.62, YT], color=WIRE, lw=1.6)
    ax.plot([XB + 0.34, XB + 0.34], [YL - 0.62, YB], color=WIRE, lw=1.6)
    ax.plot([XB + 0.34, XB + 0.34], [YL + 0.62, YH - 0.62], color=WIRE, lw=1.6)
    ax.plot([XB + 0.34], [YSW], marker="o", ms=4.0, color=WIRE, zorder=5)
    ax.text(XB + 0.52, YSW + 0.20, u"SW", fontsize=8.4, color=MUTE)

    # ---- the two gate drivers, the block this project designs --------
    for yy in (YH, YL):
        ax.add_patch(FancyBboxPatch((1.42, yy - 0.34), 1.86, 0.68,
                                    boxstyle="round,pad=0.02,rounding_size=0.08",
                                    fc="#eef1fb", ec=DRV, lw=1.7, zorder=3))
        ax.text(2.35, yy, u"gate driver", fontsize=8.6, color=DRV,
                ha="center", va="center", weight="bold", zorder=4)
        ax.annotate("", xy=(XB - 0.76, yy), xytext=(3.28, yy),
                    arrowprops=dict(arrowstyle="-|>", color=DRV, lw=1.6))

    # ---- the coupling the project exists to defeat -------------------
    # Drawn as a capacitor from the top rail to the high-side gate, because
    # that is what it is. A curved annotate() arrow collapsed into a small
    # red triangle at this scale and its label sat on the driver box.
    # The plates must sit BETWEEN the gate and the top rail. Placed at
    # YH + 0.82 / +1.04 the upper plate landed above YT and the capacitor
    # straddled the rail it is supposed to hang from.
    XG = XB - 0.76                       # the high-side gate lead
    _p1, _p2 = YH + 0.45, YH + 0.65
    assert YH < _p1 < _p2 < YT, "the C_GD plates must lie between gate and rail"
    ax.plot([XG, XG], [YH, _p1], color=FAULT, lw=1.6, zorder=4)
    ax.plot([XG - 0.24, XG + 0.24], [_p1, _p1], color=FAULT, lw=2.6, zorder=4)
    ax.plot([XG - 0.24, XG + 0.24], [_p2, _p2], color=FAULT, lw=2.6, zorder=4)
    ax.plot([XG, XG], [_p2, YT], color=FAULT, lw=1.6, zorder=4)
    ax.text(XG - 0.32, (_p1 + _p2) / 2.0, u"C$_{GD}$", fontsize=9.2,
            color=FAULT, ha="right", va="center", weight="bold")

    # ---- output filter, then the load --------------------------------
    XL, XC, XR = 5.90, 7.65, 9.05
    ax.plot([XB + 0.34, XL - 0.62], [YSW, YSW], color=WIRE, lw=1.6)
    for i in range(4):
        ax.add_patch(plt.Circle((XL - 0.45 + i * 0.30, YSW), 0.15, fc="none",
                                ec=WIRE, lw=1.6, zorder=3))
    ax.plot([XL + 0.60, XR], [YSW, YSW], color=WIRE, lw=1.6)
    # Kept clear of the "high side" label, which sits just left of it on
    # nearly the same baseline: at title-slide size the two read as one
    # phrase, "high side L".
    ax.text(XL + 0.02, YSW + 0.62, u"L", fontsize=9.2, color=INK, ha="center")

    ax.plot([XC, XC], [YSW, 2.16], color=WIRE, lw=1.6)
    ax.plot([XC - 0.30, XC + 0.30], [2.16, 2.16], color=WIRE, lw=2.4)
    ax.plot([XC - 0.30, XC + 0.30], [1.92, 1.92], color=WIRE, lw=2.4)
    ax.plot([XC, XC], [1.92, YB], color=WIRE, lw=1.6)
    ax.plot([XC], [YSW], marker="o", ms=4.0, color=WIRE, zorder=5)
    ax.text(XC + 0.42, 2.04, u"C", fontsize=9.2, color=INK, va="center")

    # The load hangs off the output node down to ground. Drawn across the
    # output wire it read as a component in series with the load.
    ax.plot([XR], [YSW], marker="o", ms=4.0, color=WIRE, zorder=5)
    ax.plot([XR, XR], [YSW, 2.44], color=WIRE, lw=1.6)
    ax.add_patch(plt.Rectangle((XR - 0.20, 1.44), 0.40, 1.00, fc="white",
                               ec=WIRE, lw=1.6, zorder=3))
    ax.plot([XR, XR], [YB, 1.44], color=WIRE, lw=1.6)
    ax.plot([XB + 0.34, XR], [YB, YB], color=WIRE, lw=1.6)
    ax.text(XR + 0.34, 1.94, u"load", fontsize=8.8, color=INK, va="center")

    ax.plot([XR, 10.30], [YSW, YSW], color=WIRE, lw=1.6)
    ax.text(10.45, YSW, u"48.5 V", fontsize=10.4, color=INK, va="center",
            weight="bold")

    ax.text(5.80, 0.30,
            u"GaN half-bridge, the two gate drivers this project designs, "
            u"and the C$_{GD}$ path they have to defeat",
            fontsize=8.0, color=MUTE, ha="center")

    fig.savefig(OUT, bbox_inches="tight", facecolor="white", pad_inches=0.04)
    plt.close(fig)
    from PIL import Image
    w, h = Image.open(OUT).size
    print("  wrote %s  (%dx%d, aspect %.2f:1)"
          % (os.path.relpath(OUT, ROOT), w, h, w / float(h)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
