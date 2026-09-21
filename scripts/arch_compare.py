# -*- coding: utf-8 -*-
"""arch_compare.py -- the base paper's architecture and ours, drawn to the
same grid so the difference is visible rather than asserted.

    python3 scripts/arch_compare.py

WHY THIS EXISTS
  The Review-1 panel asked to see, side by side, the blocks the base paper
  has and the blocks we add -- so that "I have some novelty" is something
  they can read off a picture instead of taking on trust.

  Both figures use the SAME four columns, the SAME block sizes and the SAME
  vertical positions. A block that exists in both sits at the same place in
  both. Anything that moves, moves because the architecture moved.

THE THREE OUTPUTS
  fig_arch_base.png   theirs alone      -- the "previous slide"
  fig_arch_ours.png   ours, with the four added blocks marked -- "this slide"
  fig_arch_delta.png  both at half width on one canvas, for the single-slide
                      version and for anyone reading the deck on paper

WHAT IS THEIRS, AND ON WHAT AUTHORITY
  Zhang, Yu, Leng, Cui, Deng and Ng, ISPSD 2020, pp. 102-105. Seven slices,
  a driving-strength pattern across the edge, the pattern chosen by ONE
  external bias resistor. No active clamp, no negative off rail, no
  per-field digital control. That is what models/zhangdrv.lib implements
  and it is what is drawn here -- the drawing and the netlist are the same
  claim, so a panel can check one against the other.

  The ISPSD paper is four pages and does not give slice sizing. Where this
  drawing shows "7 slices, 2 stages" that is stated in the paper; where it
  shows them equal-sized, that is our inference and it is labelled as one
  in models/zhangdrv.lib.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES  = os.path.join(ROOT, "results")

INK, MUTED, RULE = "#141414", "#5A5A5A", "#B4B4B4"
HOT, SHADE = "#B00000", "#F1F1F1"
NEW, NEWF  = "#1b7f5f", "#E3F2EC"      # the added blocks, and their fill
plt.rcParams["font.family"] = "DejaVu Sans"


class Canvas(object):
    """One architecture drawing on a fixed 100 x 62 grid.

    Everything is orthogonal -- no diagonals, no curves -- and the one
    fan-out goes through a single vertical bus with short stubs, so the two
    figures can be compared without the eye having to untangle routing.
    """

    def __init__(self, ax, scale=1.0):
        self.ax, self.s = ax, scale
        ax.set_xlim(0, 100); ax.set_ylim(2, 62); ax.axis("off")

    def box(self, x, y, w, h, title, sub=None, fc="white", ec=INK,
            lw=1.5, ls="-", tc=INK, fs=9.4):
        self.ax.add_patch(FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.25,rounding_size=0.7",
            fc=fc, ec=ec, lw=lw * self.s, linestyle=ls, zorder=4))
        f = fs * self.s
        if sub:
            self.ax.text(x + w / 2, y + h * 0.62, title, ha="center",
                         va="center", fontsize=f, fontweight="bold",
                         color=tc, zorder=5)
            self.ax.text(x + w / 2, y + h * 0.28, sub, ha="center",
                         va="center", fontsize=f - 1.8 * self.s,
                         color=MUTED, zorder=5)
        else:
            self.ax.text(x + w / 2, y + h / 2, title, ha="center",
                         va="center", fontsize=f, fontweight="bold",
                         color=tc, zorder=5)

    def arrow(self, x1, y1, x2, y2, color=INK, lw=1.7):
        self.ax.add_patch(FancyArrowPatch(
            (x1, y1), (x2, y2), arrowstyle="-|>",
            mutation_scale=13 * self.s, lw=lw * self.s, color=color,
            shrinkA=0, shrinkB=0, zorder=3))

    def line(self, pts, color=INK, lw=1.7, ls="-"):
        for i in range(len(pts) - 1):
            self.ax.plot([pts[i][0], pts[i + 1][0]],
                         [pts[i][1], pts[i + 1][1]], lw=lw * self.s,
                         color=color, linestyle=ls, zorder=3,
                         solid_capstyle="round")

    def dot(self, x, y, r=0.7, color=INK):
        self.ax.add_patch(plt.Circle((x, y), r * self.s ** 0.5, fc=color,
                                     ec=color, zorder=7))

    def header(self, x, text):
        self.ax.text(x, 58.6, text, fontsize=8.8 * self.s,
                     fontweight="bold", color=MUTED)

    def tag(self, x, y, text, color=MUTED, fs=7.8, ha="center", b=False):
        self.ax.text(x, y, text, ha=ha, va="center", fontsize=fs * self.s,
                     color=color, fontweight="bold" if b else "normal",
                     zorder=6)

    def rule(self, y):
        self.ax.plot([2, 98], [y, y], lw=1.0 * self.s, color=RULE, zorder=1)


# The four driver-column slots. Both drawings use the same y for the same
# function, so a missing block leaves a visible hole rather than closing up.
SLOT = {"pu": 46.0, "pd": 36.0, "clamp": 26.0, "off": 16.0}
BUS, DX, DW = 48.0, 52.0, 20.0


def power_stage(c, crosstalk_note):
    c.arrow(72.0, 50.0, 80.0, 50.0)
    c.box(80.0, 46.0, 15.0, 8.0, "GaN half-bridge", "high side + low side")
    c.box(80.0, 34.0, 15.0, 8.0, "L$_{loop}$ = 3 nH", "layout parasitic")
    c.box(80.0, 22.0, 15.0, 8.0, "Load", "2–10 A  ·  50–200 V")
    swx = 87.5
    c.line([(swx, 46.0), (swx, 44.5)]); c.dot(swx, 44.5)
    c.tag(swx - 1.3, 44.5, "SW", color=INK, fs=8.2, ha="right", b=True)
    c.arrow(swx, 44.5, swx, 42.0)
    c.arrow(swx, 34.0, swx, 30.0)
    lane_x, lane_y, up_x = 98.0, 8.0, 76.0
    c.line([(swx, 44.5), (lane_x, 44.5), (lane_x, lane_y), (up_x, lane_y),
            (up_x, SLOT["pd"] + 4.0)], color=HOT, lw=1.9)
    c.arrow(up_x, SLOT["pd"] + 4.0, 72.0, SLOT["pd"] + 4.0, color=HOT, lw=1.9)
    c.tag(87.0, lane_y - 2.2, crosstalk_note, color=HOT, fs=8.2, b=True)


def draw_base(c):
    """The base paper: one bias resistor sets the pattern, and that is all."""
    c.header(2.0, "COMMAND")
    c.header(24.0, "CONTROL")
    c.header(52.0, "SEGMENTED DRIVER")
    c.header(80.0, "POWER STAGE")
    c.rule(57.0)

    c.box(2.0, 36.0, 14.0, 8.0, "PWM in", "duty / frequency", fc=SHADE)
    c.arrow(16.0, 40.0, 24.0, 40.0)

    c.box(24.0, 34.0, 20.0, 12.0, "R$_{bias}$", "one resistor, set at design time")
    c.tag(34.0, 30.5, "analogue · fixed after fabrication", fs=8.0)
    c.tag(34.0, 27.8, "no sensing, no per-field control", fs=8.0)

    c.arrow(44.0, 40.0, BUS, 40.0)
    c.line([(BUS, SLOT["pu"] + 4.0), (BUS, SLOT["pd"] + 4.0)])
    for cy in (SLOT["pu"] + 4.0, SLOT["pd"] + 4.0):
        c.dot(BUS, cy, r=0.6); c.arrow(BUS, cy, DX, cy)

    c.box(DX, SLOT["pu"], DW, 8.0, "7 × pull-up slice", "2 stages · pattern step")
    c.box(DX, SLOT["pd"], DW, 8.0, "7 × pull-down slice", "2 stages · pattern step")

    # The holes. Same slots ours fills, drawn empty so the gap is the message.
    for key, label in (("clamp", "no active clamp"), ("off", "off rail = 0 V")):
        c.box(DX, SLOT[key], DW, 8.0, "—", label, fc="#FAFAFA", ec=RULE,
              lw=1.2, ls=":", tc=RULE)

    power_stage(c, "C$_{GD}$ crosstalk — nothing holds the OFF gate down")


def draw_ours(c, mark=True):
    """Ours: the same output stage, four blocks added around it."""
    c.header(2.0, "COMMAND")
    c.header(24.0, "CONTROL  (FPGA)")
    c.header(52.0, "SEGMENTED DRIVER")
    c.header(80.0, "POWER STAGE")
    c.rule(57.0)

    c.box(2.0, 36.0, 14.0, 8.0, "PWM in", "duty / frequency", fc=SHADE)
    c.arrow(16.0, 40.0, 24.0, 40.0)

    ec, fc = (NEW, NEWF) if mark else (INK, "white")
    c.box(24.0, 34.0, 20.0, 12.0, "", None, fc=fc, ec=ec, lw=1.8 if mark else 1.5)
    c.ax.text(34.0, 41.6, "seg_gate_ctrl.v", ha="center", va="center",
              fontsize=10.0 * c.s, fontweight="bold", color=INK, zorder=5)
    c.ax.text(34.0, 38.8, "dead_time_gen.v  ·  5–35 ns", ha="center",
              va="center", fontsize=8.0 * c.s, color=MUTED, zorder=5)
    c.ax.text(34.0, 36.6, "6 fields  ·  720 control words", ha="center",
              va="center", fontsize=8.0 * c.s, color=MUTED, zorder=5)
    if mark:
        c.tag(34.0, 31.4, "digital, re-writable at run time", color=NEW,
              fs=8.0, b=True)

    c.arrow(44.0, 40.0, BUS, 40.0)
    c.line([(BUS, SLOT["pu"] + 4.0), (BUS, SLOT["off"] + 4.0)])
    for cy in (SLOT[k] + 4.0 for k in ("pu", "pd", "clamp", "off")):
        c.dot(BUS, cy, r=0.6); c.arrow(BUS, cy, DX, cy)

    c.box(DX, SLOT["pu"], DW, 8.0, "8 × pull-up slice", "thermometer · strapped")
    c.box(DX, SLOT["pd"], DW, 8.0, "8 × pull-down slice", "thermometer · strapped")
    c.box(DX, SLOT["clamp"], DW, 8.0, "Active Miller clamp", "always on",
          ec=ec, fc=fc, lw=1.8 if mark else 1.5)
    c.box(DX, SLOT["off"], DW, 8.0, "Off-bias mux", "0 V  /  −2 V",
          ec=ec, fc=fc, lw=1.8 if mark else 1.5)

    power_stage(c, "C$_{GD}$ crosstalk — clamp and −2 V rail hold it off")


def save(draw, path, footer, figsize=(13.0, 6.9)):
    fig, ax = plt.subplots(figsize=figsize, dpi=170)
    fig.patch.set_facecolor("white")
    c = Canvas(ax)
    draw(c)
    c.rule(4.6)
    ax.text(2.0, 3.0, footer, fontsize=8.8, color=INK, va="center")
    fig.savefig(path, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  written: %s" % os.path.basename(path))


if __name__ == "__main__":
    save(draw_base, os.path.join(RES, "fig_arch_base.png"),
         "BASE PAPER — Zhang et al., ISPSD 2020. Seven slices in two stages, "
         "the pattern chosen by one bias resistor. Two slots sit empty: there "
         "is no clamp and no negative off rail.")

    save(draw_ours, os.path.join(RES, "fig_arch_ours.png"),
         "OURS — the same output stage, three blocks added (green): digital "
         "6-field control from an FPGA, an active Miller clamp and a "
         "switchable −2 V off rail. The slice count also goes 7 → 8, so the "
         "two banks are byte-addressable from the control word.")

    fig, axes = plt.subplots(2, 1, figsize=(13.0, 13.2), dpi=150)
    fig.patch.set_facecolor("white")
    for ax, draw, title in ((axes[0], draw_base, "BASE PAPER  —  Zhang et al., ISPSD 2020"),
                            (axes[1], draw_ours, "OURS  —  three blocks added, same output stage")):
        c = Canvas(ax, scale=0.95)
        draw(c)
        ax.text(2.0, 61.2, title, fontsize=11.5, fontweight="bold", color=INK)
    fig.subplots_adjust(hspace=0.06)
    p = os.path.join(RES, "fig_arch_delta.png")
    fig.savefig(p, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  written: %s" % os.path.basename(p))
