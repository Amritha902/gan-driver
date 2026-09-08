"""
tools_figure.py -- which tool did what, on one page.

Asked directly: mark what ngspice was used for and what LTspice was used for.
Worth answering in a picture, because "we used several simulators" is exactly
the sentence that makes a study look scattered, and the actual split is not
scattered at all: one tool does the work, the other checks the result that
everything else rests on.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "results", "fig_tools.png")

INK, MUTED, RULE = "#141414", "#5A5A5A", "#B4B4B4"
BLUE, GREEN, PAPER = "#1F4E9C", "#1E7B34", "#FAFAFA"
plt.rcParams["font.family"] = "DejaVu Sans"

fig, ax = plt.subplots(figsize=(13.2, 6.4), dpi=170)
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
fig.patch.set_facecolor("white")

NG = [
    ("The converter", "sim/buck.cir  —  100 V DC in, 48.6 V DC out, 97.6 % efficient"),
    ("The switching test bench", "sim/dpt.cir  —  one switching edge, measured precisely"),
    ("Every setting, every corner", "720 driver settings × 4 operating points = 2,880 runs"),
    ("The named cases", "13 runs: the fix built one change at a time"),
    ("Robustness", "21,600 runs across five device parameters"),
    ("Board inductance and EMI", "7,200 runs across eight loop inductances"),
]
LT = [
    ("The circuit, drawn", "ltspice/*_design_*.asc  —  open it and press Run"),
    ("An independent check", "the same three cases, in a second simulator"),
]

def panel(x, w, title, sub, colour, rows, foot):
    ax.add_patch(FancyBboxPatch((x, 8), w, 78,
                 boxstyle="round,pad=0.8,rounding_size=1.6",
                 fc=PAPER, ec=colour, lw=2.2))
    ax.text(x + 3, 79, title, fontsize=18, fontweight="bold", color=colour)
    ax.text(x + 3, 73.5, sub, fontsize=9.6, color=MUTED)
    ax.plot([x + 3, x + w - 3], [70, 70], lw=1.1, color=RULE)
    y = 64
    for head, detail in rows:
        ax.text(x + 3, y, "•  " + head, fontsize=11.2, fontweight="bold", color=INK)
        ax.text(x + 6, y - 3.6, detail, fontsize=9.0, color=MUTED)
        y -= 8.7
    ax.plot([x + 3, x + w - 3], [13.5, 13.5], lw=1.1, color=RULE)
    ax.text(x + 3, 10, foot, fontsize=9.4, color=colour, fontweight="bold")

panel(1, 55, "ngspice", "every circuit simulation in the study", BLUE, NG,
      "about 35,000 transient runs in total")
panel(58.5, 40.5, "LTspice", "the drawing, and one check", GREEN, LT,
      "agrees with ngspice to within 2 mV")

ax.text(50, 95.5, "Which tool did what", ha="center", fontsize=17,
        fontweight="bold", color=INK)
ax.text(50, 90.5,
        "Two tools for the circuit. Every number in this project is produced by "
        "ngspice; LTspice draws the same circuit and re-measures the result "
        "everything else rests on.",
        ha="center", fontsize=10.2, color=MUTED)
ax.text(50, 2.5,
        "The FPGA controller is separate work: written in Verilog, simulated in "
        "Icarus Verilog, synthesised in Xilinx Vivado (20 LUTs, 200 MHz met).",
        ha="center", fontsize=9.4, color=MUTED)

fig.savefig(OUT, dpi=170, bbox_inches="tight", facecolor="white")
print("wrote", OUT)
