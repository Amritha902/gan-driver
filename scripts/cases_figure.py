"""
cases_figure.py -- the named cases as a picture.

Left: the fix built one change at a time, so each change owns a bar.
Right: the same driver at two operating points, where the cheapest dead time
is a different number -- which is the entire case for adapting anything.
"""
import os, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV  = os.path.join(ROOT, "results", "cases.csv")
OUT  = os.path.join(ROOT, "results", "fig_cases.png")

INK, MUTED, RULE = "#141414", "#5A5A5A", "#B4B4B4"
RED, GREEN, BLUE, AMBER = "#B00000", "#1E7B34", "#1F4E9C", "#C77700"
plt.rcParams["font.family"] = "DejaVu Sans"

rows = list(csv.DictReader(open(CSV)))
p1 = [r for r in rows if r["part"] == "1"]
p2 = [r for r in rows if r["part"] == "2"]

fig, ax = plt.subplots(1, 2, figsize=(13.2, 5.4), dpi=170,
                       gridspec_kw=dict(width_ratios=[1.25, 1]))
fig.subplots_adjust(left=0.235, right=0.965, top=0.735, bottom=0.13, wspace=0.30)

# ------------------------------------------- left: the fix, step by step ---
a = ax[0]
labels = [r["case"].split(". ", 1)[1] for r in p1]
peak   = [float(r["peak_V"]) for r in p1]
loss   = [float(r["loss_uJ"]) for r in p1]
y = np.arange(len(p1))[::-1]
cols = [RED if float(r["margin_V"]) <= 0 else GREEN for r in p1]

a.barh(y, peak, height=0.55, color=cols, alpha=.88)
a.axvline(1.4, color=RED, lw=1.8, ls="--")
a.annotate("1.4 V — the device turns on above this", xy=(1.4, 1.0),
           xycoords=("data", "axes fraction"), xytext=(0, 6),
           textcoords="offset points", ha="center", fontsize=8.6,
           color=RED, fontweight="bold")
for yy, v, l in zip(y, peak, loss):
    a.text(v + (0.09 if v >= 0 else -0.09), yy, "%+.2f V" % v,
           va="center", ha="left" if v >= 0 else "right",
           fontsize=9.2, fontweight="bold", color=INK)
a.set_yticks(y)
a.set_yticklabels(["%d. %s\n     %.2f µJ lost" % (i + 1, s, l)
                   for i, (s, l) in enumerate(zip(labels, loss))], fontsize=9.2)
a.set_xlabel("peak voltage on the gate that should be OFF   [V]", fontsize=9.5)
a.set_xlim(-2.6, 2.5)
a.grid(axis="x", alpha=.25)
a.set_title("(a)  the fix, one change at a time — full load, 100 V and 10 A",
            fontsize=10.5, fontweight="bold", loc="left", pad=18)

# ------------------------------- right: cheapest dead time is not the same --
b = ax[1]
for pt, colour, mark in ((("100", "10"), BLUE, "o"), (("50", "2"), AMBER, "s")):
    sub = [r for r in p2 if r["VBUS"] == pt[0] and r["ILOAD"] == pt[1]]
    dt  = [float(r["dead_time"].rstrip("n")) for r in sub]
    ls_ = [float(r["loss_uJ"]) for r in sub]
    rel = [100.0 * v / min(ls_) for v in ls_]
    b.plot(dt, rel, mark + "-", lw=2.0, ms=7, color=colour,
           label="%s V, %s A" % pt)
    i = int(np.argmin(rel))
    b.plot([dt[i]], [rel[i]], "*", ms=19, color=colour, zorder=5)
    b.annotate("cheapest\nat %.0f ns" % dt[i], (dt[i], rel[i]),
               textcoords="offset points", xytext=(14, 10),
               fontsize=9.2, fontweight="bold", color=colour)
b.set_xlabel("dead time  [ns]", fontsize=9.5)
b.set_ylabel("energy lost, relative to that point's best  [%]", fontsize=9.5)
b.legend(fontsize=9, frameon=False, loc="upper right")
b.set_ylim(96, max(140, b.get_ylim()[1]))
b.grid(alpha=.25)
b.set_title("(b)  the same driver at two operating points",
            fontsize=10.5, fontweight="bold", loc="left")

fig.suptitle("Named cases, each a separate ngspice run of sim/dpt.cir   ·   "
             "python3 scripts/cases.py",
             fontsize=12.5, fontweight="bold", y=0.985)
fig.text(0.5, 0.895,
         "Left: turning the clamp on removes the fault; the −2 V rail buys margin; "
         "slowing the drive is safest but wastes 2× the energy.\n"
         "Right: the cheapest dead time is 15 ns at full load and 5 ns at light load. "
         "Those are different numbers, and that difference is the only thing "
         "worth adapting.",
         ha="center", fontsize=9.3, color=MUTED)
fig.savefig(OUT, dpi=170, facecolor="white")
print("wrote", OUT)
