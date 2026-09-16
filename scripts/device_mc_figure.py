# -*- coding: utf-8 -*-
"""device_mc_figure.py -- the device-population result, as one picture.

    python3 scripts/device_mc_figure.py   ->  results/fig_device_mc.png

Left:  the shipped word's worst-corner crosstalk margin on every sampled
       device, against the zero line that separates safe from false turn-on.
Right: (A) and (B) on each device, paired, so the ordering claim is read
       device by device rather than as an average that could hide a failure.
"""
import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import device_mc_analyse as A

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "results", "fig_device_mc.png")
INK, BLUE, RED, GREY = "#1a1a1a", "#1b5e9c", "#c0392b", "#9aa0a6"

rows = A.load()
devs = A.per_device(rows)
complete = {d: rs for d, rs in devs.items() if len(rs) >= 100}

worst, AA, BB = {}, {}, {}
for d, rs in sorted(complete.items()):
    ms = [r["margin"] for r in rs if A.word_of(r) == A.SHIPPED]
    if ms:
        worst[d] = min(ms)
    r = A.decompose(rs)
    if r:
        AA[d], BB[d] = r[0], r[1]

fig, ax = plt.subplots(1, 2, figsize=(11.0, 4.3), dpi=150)

# ---- left: safety -------------------------------------------------------
ks = sorted(worst)
vs = [worst[k] for k in ks]
ax[0].axhline(0, color=RED, lw=1.6, ls="--")
ax[0].text(len(ks) - 0.5, 0.06, "false turn-on below this line",
           ha="right", fontsize=8, color=RED)
ax[0].bar(range(len(ks)), vs, color=BLUE, width=0.72)
ax[0].set_xlabel("sampled device")
ax[0].set_ylabel("crosstalk margin at the worst corner  (V)")
ax[0].set_title("Shipped word stays safe on every device", fontsize=10.5,
                fontweight="bold", color=INK)
ax[0].set_ylim(min(0, min(vs)) - 0.25, max(vs) * 1.20)
ax[0].grid(axis="y", alpha=0.25, lw=0.6)
ax[0].text(0.4, max(vs) * 1.06, "worst case %+.2f V   (n = %d devices)"
           % (min(vs), len(vs)), fontsize=8.5, color=INK)

# ---- right: ordering ----------------------------------------------------
ks2 = sorted(AA)
for i, k in enumerate(ks2):
    ax[1].plot([i, i], [BB[k], AA[k]], color=GREY, lw=1.0, zorder=1)
ax[1].scatter(range(len(ks2)), [AA[k] for k in ks2], s=26, color=BLUE,
              zorder=3, label="(A) better fixed word")
ax[1].scatter(range(len(ks2)), [BB[k] for k in ks2], s=26, color=RED,
              zorder=3, label="(B) adaptation on top")
ax[1].set_xlabel("sampled device")
ax[1].set_ylabel("% of baseline switching energy")
n_ok = sum(1 for k in ks2 if AA[k] > BB[k])
ax[1].set_title("(A) beats (B) on %d of %d devices" % (n_ok, len(ks2)),
                fontsize=10.5, fontweight="bold", color=INK)
ax[1].legend(frameon=False, fontsize=8.5, loc="center right")
ax[1].grid(axis="y", alpha=0.25, lw=0.6)
ax[1].set_ylim(0, max(AA.values()) * 1.25)

fig.text(0.5, 0.005,
         "Vth, transconductance, Cgs and Cgd varied JOINTLY, +-3 sigma at the bounds "
         "robust.py uses one at a time.  36-word candidate set: a subset deflates (A) and "
         "inflates (B), so the ordering test is conservative.  scripts/device_mc.py.",
         ha="center", fontsize=7.4, color=GREY)
fig.tight_layout(rect=(0, 0.035, 1, 1))
fig.savefig(OUT)
print("wrote", OUT, "-- %d devices" % len(ks))
