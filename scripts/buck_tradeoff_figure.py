"""
buck_tradeoff_figure.py -- the gate-driver knob, seen from the converter.

The point of the whole project in one picture: the driver setting is not a
detail of the gate waveform, it moves the two numbers a converter is judged
on, and it moves them in opposite directions.
"""
import os, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV  = os.path.join(ROOT, "results", "buck_sweep.csv")
OUT  = os.path.join(ROOT, "results", "fig_buck_tradeoff.png")

INK, MUTED, RULE = "#141414", "#5A5A5A", "#B4B4B4"
RED, GREEN, BLUE = "#B00000", "#1E7B34", "#1F4E9C"
plt.rcParams["font.family"] = "DejaVu Sans"

rows = [r for r in csv.DictReader(open(CSV))]
main = [r for r in rows if r["config"] == "clamp on, -2 V"]
main.sort(key=lambda r: int(r["slices"]))
n    = [int(r["slices"]) for r in main]
loss = [float(r["loss"]) for r in main]
peak = [float(r["sw_pk"]) for r in main]

nc = {int(r["slices"]): r for r in rows if r["config"] == "no clamp, 0 V"}

fig, ax = plt.subplots(1, 2, figsize=(13.0, 5.2), dpi=170)
fig.subplots_adjust(left=0.065, right=0.975, top=0.80, bottom=0.14, wspace=0.28)

# ---- left: the two curves, opposite directions ---------------------------
a = ax[0]
a.plot(n, loss, "o-", lw=2.0, ms=7, color=RED)
a.set_xlabel("pull-up slices turned on   (how hard the device is switched)", fontsize=9.5)
a.set_ylabel("power lost in the converter  [W]", fontsize=9.5, color=RED)
a.tick_params(axis="y", labelcolor=RED)
a.grid(alpha=.25)
b = a.twinx()
b.plot(n, peak, "s--", lw=2.0, ms=7, color=BLUE)
b.set_ylabel("peak switch-node voltage  [V]", fontsize=9.5, color=BLUE)
b.tick_params(axis="y", labelcolor=BLUE)

imin = int(np.argmin(loss))
a.annotate("lowest loss\n%d slices, %.3f W" % (n[imin], loss[imin]),
           (n[imin], loss[imin]), textcoords="offset points", xytext=(14, 18),
           fontsize=9, fontweight="bold", color=RED,
           arrowprops=dict(arrowstyle="->", color=RED, lw=1.3))
a.set_title("(a)  slower switching wastes more power, but stresses the devices less",
            fontsize=10.5, fontweight="bold", loc="left")

# ---- right: the same points as a trade-off -------------------------------
c = ax[1]
c.plot(peak, loss, "-", lw=1.4, color=MUTED, zorder=1)
sc = c.scatter(peak, loss, s=140, c=n, cmap="viridis", zorder=3,
               edgecolor="white", linewidth=1.4)
for x, y, k in zip(peak, loss, n):
    c.annotate("%d" % k, (x, y), fontsize=8.6, fontweight="bold",
               color="white", ha="center", va="center", zorder=4)
c.set_xlabel("peak switch-node voltage  [V]      (device stress →)", fontsize=9.5)
c.set_ylabel("power lost  [W]      (← better)", fontsize=9.5)
c.grid(alpha=.25)
c.set_title("(b)  the same runs as a trade-off — labels are the slice count",
            fontsize=10.5, fontweight="bold", loc="left")

if 8 in nc:
    c.scatter([float(nc[8]["sw_pk"])], [float(nc[8]["loss"])], s=150,
              marker="X", color=RED, zorder=5, edgecolor="white", linewidth=1.4)
    c.annotate("no clamp, 0 V rail\n%.2f W but crosstalk unsafe"
               % float(nc[8]["loss"]),
               (float(nc[8]["sw_pk"]), float(nc[8]["loss"])),
               textcoords="offset points", xytext=(16, 4), ha="left",
               fontsize=8.8, fontweight="bold", color=RED)
    c.set_ylim(min(min(loss), float(nc[8]["loss"])) - 0.12, max(loss) + 0.10)
    c.set_xlim(min(peak) - 8, max(peak) + 12)

span = (max(loss) - min(loss)) / min(loss) * 100
fig.suptitle("The gate-driver setting, measured on the running converter  —  "
             "8 ngspice runs of sim/buck.cir",
             fontsize=12.5, fontweight="bold", y=0.955)
fig.text(0.5, 0.885,
         "Loss moves %.1f %% and peak device voltage moves %.0f %% across the same knob. "
         "Crosstalk safety costs %.2f W, or %.2f points of efficiency."
         % (span, (max(peak) - min(peak)) / min(peak) * 100,
            float(main[-1]["loss"]) - float(nc[8]["loss"]),
            float(nc[8]["eff"]) - float(main[-1]["eff"])),
         ha="center", fontsize=9.4, color=MUTED)
fig.savefig(OUT, dpi=170, facecolor="white")
print("wrote", OUT)
