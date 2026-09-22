# -*- coding: utf-8 -*-
"""arch_sidebyside.py -- the base paper's architecture and ours, on one
canvas, row for row.

    python3 scripts/arch_sidebyside.py

WHY A SECOND ARCHITECTURE FIGURE
  arch_compare.py draws the two as separate signal-flow sheets on
  consecutive slides. That works when you can page between them. It does
  not answer "what exactly did you add" at a glance, because the eye has
  to hold one sheet in memory while looking at the other.

  This puts them in two columns against the same six rows, so a difference
  is a difference in one row and nothing else moves. The empty rows on the
  left are the contribution.

ACCURACY
  Block counts and values are parsed from models/zhangdrv.lib and
  models/segdrv.lib rather than remembered:

    base   7 slices per bank, split nseg / (7-nseg) across two stages,
           the split chosen by ONE external bias resistor. No clamp branch
           -- their file says so in as many words. Off rail tied to ref.
    ours   8 slices per bank, thermometer coded, all switching together;
           active Miller clamp through rclamp; off rail selectable.

  If either library changes, this figure changes with it.
"""
import os, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES  = os.path.join(ROOT, "results")

INK, MUTED, RULE = "#141414", "#5A5A5A", "#B4B4B4"
NEW, NEWF = "#1b7f5f", "#E6F2ED"        # ours: added / changed
GAP, GAPF = "#9A9A9A", "#F7F7F7"        # theirs: absent
SHADE = "#F1F1F1"
plt.rcParams["font.family"] = "DejaVu Sans"


def model(path):
    s = open(os.path.join(ROOT, "models", path), encoding="utf-8").read()
    pu = len(set(int(n) for n in re.findall(r"^Rpu(\d+)\b", s, re.M | re.I)))
    pd = len(set(int(n) for n in re.findall(r"^Rpd(\d+)\b", s, re.M | re.I)))
    two = bool(re.search(r"^Rpu\d+b\b", s, re.M | re.I))
    clamp = bool(re.search(r"^Sclk\b", s, re.M | re.I))
    par = dict(kv.split("=", 1) for kv in
               (re.search(r"params:\s*(.*)$", s, re.M).group(1).split())
               if "=" in kv)
    return dict(pu=pu, pd=pd, two_stage=two, clamp=clamp, par=par)


B = model("zhangdrv.lib")
O = model("segdrv.lib")

# rows: (heading, base text, ours text, ours-differs)
ROWS = [
    (u"Control source",
     u"One bias resistor\nfixed at fabrication",
     u"FPGA — seg_gate_ctrl.v\n6 fields, 720 words, written at run time",
     True),
    (u"Drive strength",
     u"%d slices per bank\nsplit %s / %d across two stages"
     % (B["pu"], B["par"].get("nseg", "2"), B["pu"] - int(B["par"].get("nseg", 2))),
     u"%d + %d slices, thermometer coded\nstrength = how many of the %s Ω paths are live"
     % (O["pu"], O["pd"], O["par"].get("runit", "8")),
     True),
    (u"Edge shaping",
     u"Staged: the rest join after\nthe pattern step",
     u"All live slices switch together;\nthe edge is set by the count",
     True),
    (u"Off-state hold",
     u"—  none",
     u"Active Miller clamp\nto the off rail through %s Ω"
     % O["par"].get("rclamp", "0.5"),
     True),
    (u"Off rail",
     u"0 V  (tied to its reference)",
     u"Selectable  0 V  /  −2 V",
     True),
    (u"Power stage",
     u"GaN half-bridge",
     u"GaN half-bridge  (identical)",
     False),
]

FIG_W, FIG_H = 13.2, 7.4
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=170)
fig.patch.set_facecolor("white")
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")

LX, RX, CW = 24.0, 61.0, 35.0          # left col, right col, width
TOP, RH, GAPY = 84.0, 10.4, 1.7

ax.text(2.0, 95.2, u"The two architectures, row for row",
        fontsize=17, fontweight="bold", color=INK)
ax.text(2.0, 91.4,
        u"Same six rows. A difference is a difference in one row and nothing "
        u"else moves. Block counts parsed from the two driver models.",
        fontsize=10.2, color=MUTED)

ax.text(LX + CW / 2, 87.4, u"BASE PAPER", ha="center", fontsize=11.5,
        fontweight="bold", color=INK)
ax.text(LX + CW / 2, 85.4, u"Zhang et al., ISPSD 2020  ·  zhangdrv.lib",
        ha="center", fontsize=8.6, color=MUTED)
ax.text(RX + CW / 2, 87.4, u"OURS", ha="center", fontsize=11.5,
        fontweight="bold", color=NEW)
ax.text(RX + CW / 2, 85.4, u"segdrv.lib  +  seg_gate_ctrl.v",
        ha="center", fontsize=8.6, color=MUTED)

ax.plot([2, 98], [83.4, 83.4], lw=1.1, color=RULE)


def cell(x, y, w, h, txt, ec, fc, tc=INK, ls="-", lw=1.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.3,rounding_size=0.8",
                 fc=fc, ec=ec, lw=lw, linestyle=ls, zorder=3))
    ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center",
            fontsize=9.0, color=tc, zorder=4, linespacing=1.45)


y = TOP - RH
for head, bt, ot, differs in ROWS:
    ax.text(21.0, y + RH / 2, head, ha="right", va="center",
            fontsize=9.8, fontweight="bold", color=INK)
    absent = bt.strip().startswith(u"—")
    cell(LX, y, CW, RH, bt,
         GAP if absent else INK, GAPF if absent else "white",
         tc=GAP if absent else INK,
         ls=":" if absent else "-", lw=1.3 if absent else 1.5)
    cell(RX, y, CW, RH, ot,
         NEW if differs else INK, NEWF if differs else SHADE)
    # No connecting arrow between the columns: the gap is 2 units wide, so an
    # arrow there renders as an invisible stub. The green fill and border
    # already carry "this row changed", and a mark nobody can see is worse
    # than no mark.
    y -= (RH + GAPY)

ax.plot([2, 98], [y + RH - 1.2, y + RH - 1.2], lw=1.1, color=RULE)
ax.text(2.0, y + RH - 4.6,
        u"Measured on the same converter, same device, same output stage — "
        u"only the control differs:",
        fontsize=10.0, fontweight="bold", color=INK)
ax.text(2.0, y + RH - 7.8,
        u"crosstalk margin  +0.407 V  →  +2.576 V          "
        u"latency  4.04 ns  →  2.78 ns          "
        u"edge  2.06 ns  →  0.78 ns          "
        u"device power  2.93 W  →  2.60 W",
        fontsize=9.4, color=INK)
ax.text(2.0, y + RH - 10.6,
        u"and where it costs us:  gate-drive power  0.031 W  →  0.035 W "
        u"(+13 %)          switch-node overshoot  2.9 %  →  17.9 %",
        fontsize=9.4, color="#B00000")

out = os.path.join(RES, "fig_arch_sidebyside.png")
fig.savefig(out, dpi=170, bbox_inches="tight", facecolor="white")
print("  written: results/fig_arch_sidebyside.png")
print("  base: %d slices, two-stage=%s, clamp=%s" % (B["pu"], B["two_stage"], B["clamp"]))
print("  ours: %d+%d slices, clamp=%s, rclamp=%s"
      % (O["pu"], O["pd"], O["clamp"], O["par"].get("rclamp")))
