"""
arch_diagram.py -- the system architecture: what talks to what.

Rewritten. The previous version fanned four diagonal arrows out of one block
and routed the crosstalk path as two long curves across the whole figure,
which read as arrows scattered over the page rather than a drawn system.

Rules this version keeps to:
  * every connection is orthogonal -- horizontal and vertical only, no
    diagonals and no curves
  * the one-to-many fan-out goes through a single vertical BUS with short
    stubs, the way a real block diagram does it
  * the crosstalk return has its own reserved lane down the right edge and
    along the bottom, crossing nothing
  * four columns, each with a header, left to right in signal order

The dashed block is the only part that needs sensing. That is the whole point
of the figure, so it is the only dashed thing in it.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "fig_architecture.png")

INK, MUTED, RULE = "#141414", "#5A5A5A", "#B4B4B4"
HOT, SHADE, DASH = "#B00000", "#F1F1F1", "#FFF1CC"
plt.rcParams["font.family"] = "DejaVu Sans"

fig, ax = plt.subplots(figsize=(13.0, 6.9), dpi=170)
ax.set_xlim(0, 100)
ax.set_ylim(2, 62)
ax.axis("off")
fig.patch.set_facecolor("white")


def box(x, y, w, h, title, sub=None, fc="white", ec=INK, lw=1.5, ls="-",
        tc=INK, fs=9.4):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.25,rounding_size=0.7",
                 fc=fc, ec=ec, lw=lw, linestyle=ls, zorder=4))
    if sub:
        ax.text(x + w / 2, y + h * 0.62, title, ha="center", va="center",
                fontsize=fs, fontweight="bold", color=tc, zorder=5)
        ax.text(x + w / 2, y + h * 0.28, sub, ha="center", va="center",
                fontsize=fs - 1.8, color=MUTED, zorder=5)
    else:
        ax.text(x + w / 2, y + h / 2, title, ha="center", va="center",
                fontsize=fs, fontweight="bold", color=tc, zorder=5)


def arrow(x1, y1, x2, y2, color=INK, lw=1.7):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                 mutation_scale=13, lw=lw, color=color,
                 shrinkA=0, shrinkB=0, zorder=3))


def line(pts, color=INK, lw=1.7, ls="-"):
    for i in range(len(pts) - 1):
        ax.plot([pts[i][0], pts[i + 1][0]], [pts[i][1], pts[i + 1][1]],
                lw=lw, color=color, linestyle=ls, zorder=3,
                solid_capstyle="round")


def dot(x, y, r=0.7, color=INK):
    ax.add_patch(plt.Circle((x, y), r, fc=color, ec=color, zorder=7))


def header(x, text):
    ax.text(x, 58.6, text, fontsize=8.8, fontweight="bold", color=MUTED)


def tag(x, y, text, color=MUTED, fs=7.8, ha="center", b=False):
    ax.text(x, y, text, ha=ha, va="center", fontsize=fs, color=color,
            fontweight="bold" if b else "normal", zorder=6)


# --------------------------------------------------------------- columns --
header(2.0, "COMMAND")
header(24.0, "CONTROL  (FPGA)")
header(52.0, "SEGMENTED DRIVER")
header(80.0, "POWER STAGE")
ax.plot([2, 98], [57.0, 57.0], lw=1.0, color=RULE, zorder=1)

# ------------------------------------------------------------- 1. command --
box(2.0, 36.0, 14.0, 8.0, "PWM in", "duty / frequency", fc=SHADE)
arrow(16.0, 40.0, 24.0, 40.0)

# ------------------------------------------------------------- 2. control --
box(24.0, 34.0, 20.0, 12.0, "", None, fc="white")
ax.text(34.0, 41.6, "seg_gate_ctrl.v", ha="center", va="center",
        fontsize=10.0, fontweight="bold", color=INK, zorder=5)
ax.text(34.0, 38.8, "dead_time_gen.v  ·  5–35 ns", ha="center", va="center",
        fontsize=8.0, color=MUTED, zorder=5)
ax.text(34.0, 36.6, "thermo_decode.v  ·  8 + 8 slices", ha="center",
        va="center", fontsize=8.0, color=MUTED, zorder=5)

box(24.0, 18.0, 20.0, 11.0, "Sensing → ADC → LUT", "operating-point scheduler",
    fc=DASH, ls="--", lw=1.8)
line([(34.0, 29.0), (34.0, 32.0)], ls="--")
arrow(34.0, 32.0, 34.0, 34.0)
tag(34.0, 15.6, "the only block that needs sensing", color=HOT, fs=8.0, b=True)
tag(34.0, 13.2, "worth 3.9 % of baseline", color=HOT, fs=8.0, b=True)

# ------------------------------------------------- 3. driver, fed by a bus --
BUS = 48.0
arrow(44.0, 40.0, BUS, 40.0)
line([(BUS, 50.0), (BUS, 20.0)])          # the vertical bus
for cy in (50.0, 40.0, 30.0, 20.0):
    dot(BUS, cy, r=0.6)
    arrow(BUS, cy, 52.0, cy)

box(52.0, 46.0, 20.0, 8.0, "8 × pull-up slice", "thermometer · strapped")
box(52.0, 36.0, 20.0, 8.0, "8 × pull-down slice", "thermometer · strapped")
box(52.0, 26.0, 20.0, 8.0, "Active Miller clamp", "always on")
box(52.0, 16.0, 20.0, 8.0, "Off-bias mux", "0 V  /  −2 V")

# ----------------------------------------------------------- 4. power stage --
arrow(72.0, 50.0, 80.0, 50.0)
box(80.0, 46.0, 15.0, 8.0, "GaN half-bridge", "high side + low side")
box(80.0, 34.0, 15.0, 8.0, "L$_{loop}$ = 3 nH", "layout parasitic")
box(80.0, 22.0, 15.0, 8.0, "Load", "2–10 A  ·  50–200 V")

SWX = 87.5
line([(SWX, 46.0), (SWX, 44.5)])
dot(SWX, 44.5)
tag(SWX - 1.3, 44.5, "SW", color=INK, fs=8.2, ha="right", b=True)
arrow(SWX, 44.5, SWX, 42.0)
arrow(SWX, 34.0, SWX, 30.0)

# ------------------------------------ crosstalk: its own lane, crosses nothing
LANE_X, LANE_Y, UP_X = 98.0, 8.0, 76.0
line([(SWX, 44.5), (LANE_X, 44.5), (LANE_X, LANE_Y), (UP_X, LANE_Y),
      (UP_X, 40.0)], color=HOT, lw=1.9)
arrow(UP_X, 40.0, 72.0, 40.0, color=HOT, lw=1.9)
tag(87.0, LANE_Y - 2.2, "C$_{GD}$ crosstalk — the dV/dt couples into the OFF gate",
    color=HOT, fs=8.2, b=True)

# ---------------------------------------------------------------- footer ---
ax.plot([2, 98], [4.6, 4.6], lw=1.0, color=RULE, zorder=1)
ax.text(2.0, 3.0,
        "Solid blocks are set once at power-up — no sensing, no lookup table. "
        "The dashed block is the adaptive machinery, and 72 % of what it buys "
        "needs only one comparator.",
        fontsize=8.8, color=INK, va="center")

fig.savefig(OUT, dpi=170, bbox_inches="tight", facecolor="white")
print("wrote", OUT)
