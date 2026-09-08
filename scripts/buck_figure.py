"""
buck_figure.py -- the converter doing its job: 100 V DC in, 48.5 V DC out.

Three panels, because three different questions get asked about a converter
and no single view answers them:
  (a) does it convert?      output charging from zero and settling
  (b) how?                  the switch node chopping, three cycles of it
  (c) at what cost?         power in, power out, and the difference
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrow
import bucksim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "results", "fig_converter.png")

INK, MUTED, RULE = "#141414", "#5A5A5A", "#B4B4B4"
BLUE, RED, GREEN = "#1F4E9C", "#B00000", "#1E7B34"
plt.rcParams["font.family"] = "DejaVu Sans"

print("running the converter in ngspice ...")
d, p = bucksim.run_raw()
m = bucksim.metrics(d, p)
t, vin, iin, sw, vout, iout = (d[:, 0], d[:, 1], d[:, 3],
                               d[:, 5], d[:, 7], d[:, 9])
print("  Vout %.2f V   Pin %.1f W   Pout %.1f W   eff %.2f %%"
      % (m["Vout"], m["Pin"], m["Pout"], m["eff"]))

fig = plt.figure(figsize=(13.2, 6.5), dpi=170)
gs = fig.add_gridspec(2, 2, height_ratios=[1, 1], width_ratios=[1.15, 1],
                      hspace=0.42, wspace=0.22,
                      left=0.055, right=0.985, top=0.88, bottom=0.09)

# ---------------------------------------------------- (a) it converts ------
ax = fig.add_subplot(gs[0, 0])
ax.plot(t * 1e6, vin, lw=1.6, color=MUTED)
ax.plot(t * 1e6, vout, lw=1.5, color=GREEN)
ax.text(t[-1] * 1e6 * 0.99, 103, "input  100 V DC", ha="right", fontsize=9,
        color=MUTED, fontweight="bold")
ax.text(t[-1] * 1e6 * 0.99, m["Vout"] + 5.5, "output  %.1f V DC" % m["Vout"],
        ha="right", fontsize=9, color=GREEN, fontweight="bold")
ax.set_title("(a)  the converter charges its own output and settles",
             fontsize=10.5, fontweight="bold", loc="left")
ax.set_xlabel("time  [µs]", fontsize=9)
ax.set_ylabel("volts", fontsize=9)
ax.set_ylim(-5, 118)
ax.grid(alpha=.25)

# ------------------------------------------- (b) how: the switch node ------
tsw = 1.0 / bucksim._sec(p["FSW"])
w = (t >= t[-1] - 3 * tsw) & (t <= t[-1] - 0.02 * tsw)
t0 = t[w][0]
ax = fig.add_subplot(gs[1, 0])
ax.plot((t[w] - t0) * 1e6, sw[w], lw=1.1, color=BLUE)
ax.axhline(m["Vin"], ls=":", lw=1.0, color=MUTED)
ax.set_title("(b)  three switching cycles: the half-bridge chopping 100 V at 500 kHz",
             fontsize=10.5, fontweight="bold", loc="left")
ax.set_xlabel("time  [µs]", fontsize=9)
ax.set_ylabel("switch node  [V]", fontsize=9)
ax.grid(alpha=.25)

axi = ax.twinx()
axi.plot((t[w] - t0) * 1e6, iout[w], lw=1.5, color=RED)
axi.set_ylabel("inductor current  [A]", fontsize=9, color=RED)
axi.tick_params(axis="y", labelcolor=RED)

# --------------------------------------------- (c) the power accounting ----
ax = fig.add_subplot(gs[:, 1])
ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")


def block(x, y, w_, h_, title, lines, ec=INK):
    ax.add_patch(FancyBboxPatch((x, y), w_, h_,
                 boxstyle="round,pad=0.6,rounding_size=1.4",
                 fc="#FAFAFA", ec=ec, lw=1.8))
    ax.text(x + w_ / 2, y + h_ - 6, title, ha="center", fontsize=10.5,
            fontweight="bold", color=ec)
    for i, (big, small) in enumerate(lines):
        ax.text(x + w_ / 2, y + h_ - 19 - i * 15, big, ha="center",
                fontsize=15.5, fontweight="bold", color=INK)
        ax.text(x + w_ / 2, y + h_ - 28 - i * 15, small, ha="center",
                fontsize=8.6, color=MUTED)


ax.text(50, 96, "WHAT GOES IN, AND WHAT COMES OUT", ha="center",
        fontsize=10.5, fontweight="bold", color=MUTED)
ax.plot([2, 98], [92, 92], lw=1.0, color=RULE)

block(2, 46, 42, 40, "ELECTRICAL POWER IN",
      [("100.0 V", "supply voltage"),
       ("%.2f A" % m["Iin"], "average current drawn")], ec=MUTED)
block(56, 46, 42, 40, "ELECTRICAL POWER OUT",
      [("%.1f V" % m["Vout"], "regulated output"),
       ("%.2f A" % m["Iout"], "into a 10 Ω load")], ec=GREEN)

ax.add_patch(FancyArrow(45.5, 66, 9, 0, width=2.2, head_width=6.5,
                        head_length=3.2, fc=INK, ec=INK, length_includes_head=True))

ax.text(23, 38, "%.1f W" % m["Pin"], ha="center", fontsize=19,
        fontweight="bold", color=INK)
ax.text(77, 38, "%.1f W" % m["Pout"], ha="center", fontsize=19,
        fontweight="bold", color=GREEN)

ax.plot([2, 98], [31, 31], lw=1.0, color=RULE)
ax.text(50, 22, "%.1f %%" % m["eff"], ha="center", fontsize=33,
        fontweight="bold", color=GREEN)
ax.text(50, 14.5, "efficiency", ha="center", fontsize=10.5,
        fontweight="bold", color=MUTED)
ax.text(50, 8.5,
        "%.2f W lost in the two transistors and the power loop.\n"
        "Output ripple %.0f mV." % (m["loss"], m["ripple_mV"]),
        ha="center", fontsize=8.4, color=MUTED)

fig.suptitle("GaN synchronous buck converter  —  sim/buck.cir, ngspice   "
             "·   100 V DC → %.1f V DC at %.2f A" % (m["Vout"], m["Iout"]),
             fontsize=12.5, fontweight="bold")
fig.savefig(OUT, dpi=170, facecolor="white")
print("wrote", OUT)
