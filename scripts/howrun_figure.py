"""
howrun_figure.py -- one ngspice run, start to finish, with real values.

"We ran ngspice" is not an answer to "how did you run ngspice". This walks a
single case through: the parameters that were set, the command, what the
simulator wrote, the window the measurement was taken over, and the number
that came out. Every value is the one actually used for the crosstalk case at
full load.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrow

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "results", "fig_howrun.png")

INK, MUTED, RULE = "#141414", "#5A5A5A", "#B4B4B4"
BLUE, GREEN, RED, PAPER = "#1F4E9C", "#1E7B34", "#B00000", "#F7F7F7"
plt.rcParams["font.family"] = "DejaVu Sans"

fig, ax = plt.subplots(figsize=(13.2, 6.5), dpi=170)
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")
fig.patch.set_facecolor("white")
fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)

ax.text(0, 96.5, "How one ngspice run is set up and taken",
        fontsize=17, fontweight="bold", color=INK)
ax.text(0, 91,
        "The case: full load, 100 V bus, 10 A, fastest drive, no Miller clamp, "
        "gate parked at 0 V — the run that shows the fault.",
        fontsize=10.8, color=MUTED)
ax.plot([0, 100], [87.5, 87.5], lw=1.2, color=RULE)

STEPS = [
 ("1", "Set the parameters", BLUE,
  [".param VBUS=100        bus voltage",
   ".param ILOAD=10        load current",
   ".param NPU_LS=8        pull-up slices, low side",
   ".param NPD_HS=8        pull-down slices, HS",
   ".param DT=15n          dead time",
   ".param CLKEN=0         Miller clamp OFF",
   ".param VNEG=0          gate at 0 V when off",
   ".param TJ=25           junction temperature"],
  "set in sim/dpt.cir by scripts/gansim.py"),
 ("2", "Run it", GREEN,
  ["$ ngspice -b dpt.cir",
   "",
   ".tran 0.02n 3u 0 0.05n uic",
   "   0.02 ns steps, 3 µs of circuit time,",
   "   0.05 ns maximum step, trapezoidal"],
  "1.6 s of wall time on this laptop"),
 ("3", "Read what it wrote", RED,
  ["wrdata out.dat v(sw) v(lsd) v(lsg)",
   "                v(hsg) v(hsd)",
   "                i(vsls) i(vshs)",
   "",
   "60,073 time points × 14 columns"],
  "the raw transient, not a summary"),
]

x = 0
for n, title, colour, lines, foot in STEPS:
    ax.add_patch(FancyBboxPatch((x, 26), 31, 58,
                 boxstyle="round,pad=0.6,rounding_size=1.2",
                 fc=PAPER, ec=colour, lw=1.8))
    ax.text(x + 2.4, 78.5, n, fontsize=19, fontweight="bold", color=colour)
    ax.text(x + 6.5, 78.5, title, fontsize=12.4, fontweight="bold", color=INK)
    y = 71
    for ln in lines:
        ax.text(x + 2.4, y, ln, fontsize=8.9, family="DejaVu Sans Mono",
                color=INK if not ln.startswith("$") else GREEN)
        y -= 4.4
    ax.text(x + 2.4, 29, foot, fontsize=8.8, color=MUTED, style="italic")
    if n != "3":
        ax.add_patch(FancyArrow(x + 31.6, 55, 2.2, 0, width=0.9,
                                head_width=2.8, head_length=1.3,
                                fc=INK, ec=INK, length_includes_head=True))
    x += 34.5

ax.add_patch(FancyBboxPatch((0, 5), 100, 16,
             boxstyle="round,pad=0.6,rounding_size=1.2",
             fc="#F2F7F2", ec=GREEN, lw=1.8))
ax.text(2.4, 16.5, "4", fontsize=19, fontweight="bold", color=GREEN)
ax.text(6.5, 16.5, "Take the measurement", fontsize=12.4, fontweight="bold",
        color=INK)
ax.text(6.5, 11.5,
        "The high-side device is off from 2.000 µs. The low side turns on at "
        "2.015 µs. We take the largest value of V(hsg) − V(sw) between "
        "2.015 and 2.100 µs —",
        fontsize=10.2, color=INK)
ax.text(6.5, 7.6,
        "the 85 ns after the disturbance. It comes out at ",
        fontsize=10.2, color=INK)
ax.text(38.5, 7.6, "+1.6486 V, against a threshold of 1.4 V.",
        fontsize=10.6, fontweight="bold", color=RED)
ax.text(72, 7.6, "The window is fixed in scripts/gansim.py.",
        fontsize=9.4, color=MUTED)

ax.text(0, 1.2,
        "The same four steps run 2,880 times for the setting search, and about "
        "35,000 times in total across every sweep in the project.",
        fontsize=9.6, color=MUTED)

fig.savefig(OUT, dpi=170, bbox_inches="tight", facecolor="white")
print("wrote", OUT)
