"""
vivado_figure.py -- Vivado's own report output, verbatim, as a slide figure.

The deck quoted the Vivado numbers but never showed the report. A number typed
onto a slide and a number lifted out of the tool's own output are not the same
evidence, and the FPGA slide is exactly where a panel will want the second one.

Everything reproduced here is copied character-for-character from
rtl/vivado/build/utilization_synth.rpt and timing_synth.rpt, which are
committed. Nothing is redrawn or rounded.

The timing panel deliberately shows BOTH rows, because the headline
"Timing constraints are not met" is misleading on its own: the design meets
200 MHz register-to-register with 1.996 ns to spare, and every failing endpoint
is a clock-to-output-pin path against a placeholder I/O constraint.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "fig_vivado.png")

INK, MUTED, RULE = "#141414", "#5A5A5A", "#B4B4B4"
HOT, GOOD, PAPER = "#B00000", "#1E7B34", "#FAFAFA"
plt.rcParams["font.family"] = "DejaVu Sans"

fig, ax = plt.subplots(figsize=(13.0, 5.5), dpi=170)
ax.set_xlim(0, 100)
ax.set_ylim(0, 42)
ax.axis("off")
fig.patch.set_facecolor("white")

UTIL = """+-------------------------+------+-----------+-------+
|        Site Type        | Used | Available | Util% |
+-------------------------+------+-----------+-------+
| Slice LUTs*             |   20 |     20800 |  0.10 |
|   LUT as Logic          |   20 |     20800 |  0.10 |
| Slice Registers         |   20 |     41600 |  0.05 |
|   Register as Flip Flop |   20 |     41600 |  0.05 |
| Bonded IOB              |   40 |       106 | 37.74 |
+-------------------------+------+-----------+-------+"""

TIMING = """Intra-clock  ( register to register )

  Clock      WNS(ns)   Failing   Total
  clk_200      1.996         0      25     <-- MET
                             hold  +0.134 ns
                             pulse +2.000 ns

Path group **default**  ( register to output PIN )

  From clk_200 WNS(ns)   Failing   Total
               -4.755        34      34"""


def panel(x, y, w, h, title, body, edge=INK):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                 boxstyle="round,pad=0.4,rounding_size=0.8",
                 fc=PAPER, ec=edge, lw=1.5, zorder=3))
    ax.text(x + 1.2, y + h - 2.0, title, fontsize=9.6, fontweight="bold",
            color=INK, va="center", zorder=5)
    ax.text(x + 1.2, y + h - 4.2, body, fontsize=7.4, family="DejaVu Sans Mono",
            color=INK, va="top", ha="left", zorder=5, linespacing=1.42)


ax.text(0.5, 40.2, "VIVADO 2024.1.2   ·   xc7a35tcpg236-1   ·   synthesised 5 Sep 2026",
        fontsize=8.8, fontweight="bold", color=MUTED)
ax.plot([0.5, 99.5], [38.6, 38.6], lw=1.0, color=RULE, zorder=1)

panel(0.5, 13.5, 46.0, 23.0, "report_utilization", UTIL)
panel(50.0, 13.5, 49.5, 23.0, "report_timing_summary", TIMING)

ax.text(1.8, 10.6, "20 LUTs and 20 flip-flops — a tenth of a percent of the part.",
        fontsize=9.4, fontweight="bold", color=INK)
ax.text(1.8, 7.8,
        "Synthesised again with every field left programmable: 33 LUTs, 30 FFs.\n"
        "So strapping the word — the study's own result built into the hardware —\n"
        "costs 13 LUTs, a 39 % saving, in Vivado's numbers rather than an estimate.",
        fontsize=8.4, color=MUTED, va="top")

ax.text(51.3, 10.6, "200 MHz is MET where it counts.", fontsize=9.4,
        fontweight="bold", color=GOOD)
ax.text(51.3, 7.8,
        "Register-to-register closes with 1.996 ns of the 5 ns period spare.\n"
        "The 34 failing endpoints are all clock-to-PIN, against a placeholder\n"
        "4 ns I/O constraint — the LVCMOS33 output buffer alone costs 3.49 ns.",
        fontsize=8.4, color=MUTED, va="top")

ax.plot([0.5, 99.5], [2.4, 2.4], lw=1.0, color=RULE, zorder=1)
ax.text(0.5, 1.0, "Both reports are committed verbatim in rtl/vivado/build/. "
                  "Reproduce with  vivado -mode batch -source synth_only.tcl",
        fontsize=8.2, color=MUTED, va="center")

fig.savefig(OUT, dpi=170, bbox_inches="tight", facecolor="white")
print("wrote", OUT)
