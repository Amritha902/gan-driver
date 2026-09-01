"""
plot_lloop.py -- the design chart: is adaptive gate control worth building?

The eight-point sweep contradicted the shape a three-point read had suggested.
The ceiling is NOT monotonic in loop inductance: it peaks near 1.5 nH and
falls again at 1.0 nH. That is not noise and it is not the clamp-chatter
artefact - excluding every chatter point leaves all eight ceilings unchanged
to the digit, because the cost function penalises overshoot and never selects
those words anyway.

The mechanism is feasibility. The count of control words safe at both corners
rises monotonically with inductance (165 -> 484): a looser loop commutates
more slowly, couples less charge through C_GD, and more words stay below
threshold. At 1.0-1.5 nH so few words survive that the fixed word and the
per-corner optima are forced into the same narrow region, and the gap between
them - which is what scheduling can exploit - shrinks again.

So the honest deliverable is a BAND, not a threshold, and the second axis is
part of the result rather than decoration.
"""
import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lloop_analyse import load, ceiling

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "results", "fig_lloop.png")
INK, MUTED, RULE, SHADE, ACC = "#141414", "#5E5E5E", "#B4B4B4", "#ECECEC", "#8A8A8A"

data = load()
pts = []
for L in sorted(data):
    c, _, n = ceiling(data[L])
    if c is not None: pts.append((L, c, n))
if len(pts) < 3:
    sys.exit("not enough points")

xs  = [p[0] for p in pts]
ys  = [p[1] for p in pts]
ns  = [p[2] for p in pts]
pk  = max(pts, key=lambda p: p[1])

# highest inductance at which the ceiling still exceeds the threshold, scanning
# DOWN from the loose end - the meaningful reading when the curve is not monotonic
THR = 6.0
above = [p[0] for p in pts if p[1] >= THR]
band_hi = max(above) if above else None

import matplotlib.transforms as mtransforms

fig, (ax, ax2) = plt.subplots(2, 1, figsize=(11.6, 6.25), sharex=True,
                              gridspec_kw={"height_ratios": [2.5, 1], "hspace": 0.14})
# x in data units, y in axes fraction - lets the region labels sit in the
# headroom above the curve instead of crossing it
blend = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)

if band_hi:
    ax.axvspan(min(xs), band_hi, color=SHADE, zorder=0)
    ax.text((min(xs) + band_hi) / 2, 0.955,
            "adaptive control earns its hardware", transform=blend,
            fontsize=9.2, fontweight="bold", color=INK, ha="center", va="top",
            family="DejaVu Sans")
    ax.text(band_hi + (max(xs) - band_hi) / 2, 0.955,
            "one fixed word is as good", transform=blend, fontsize=9.2,
            color=MUTED, ha="center", va="top", family="DejaVu Sans")
    ax.axvline(band_hi, color=INK, lw=1.3, ls=(0, (5, 3)), zorder=3)
    ax.text(band_hi + 0.05, 0.015, "%.1f nH" % band_hi, transform=blend,
            fontsize=9.5, fontweight="bold", color=INK, ha="left", va="bottom",
            family="DejaVu Sans",
            bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none"))

ax.axhline(THR, color=RULE, lw=1.0, ls=(0, (3, 3)), zorder=1)
ax.text(max(xs), THR + 0.45, "%.0f %% threshold" % THR, fontsize=8.4,
        color=MUTED, ha="right", family="DejaVu Sans")
ax.plot(xs, ys, "-o", color=INK, lw=2.0, ms=6.2, zorder=4,
        markerfacecolor="#FFFFFF", markeredgewidth=1.7)
for x, y, _ in pts:
    # the point sitting on the band edge would print its label over the
    # dashed rule, so nudge that one clear of it
    off = (17, 4) if (band_hi and abs(x - band_hi) < 1e-9) else (0, 10)
    ha  = "left" if off[0] else "center"
    ax.annotate("%.1f%%" % y, (x, y), textcoords="offset points",
                xytext=off, ha=ha, fontsize=8.2, color=INK,
                family="DejaVu Sans")
ax.annotate("peak %.1f %%" % pk[1], (pk[0], pk[1]),
            textcoords="offset points", xytext=(22, 20), fontsize=8.8,
            fontweight="bold", color=INK, family="DejaVu Sans",
            arrowprops=dict(arrowstyle="-", color=INK, lw=0.9))
ax.annotate("falls back: only %d of 720\nwords still feasible here" % ns[0],
            (xs[0], ys[0]), textcoords="offset points", xytext=(30, -46),
            fontsize=8.2, color=MUTED, family="DejaVu Sans",
            arrowprops=dict(arrowstyle="-", color=ACC, lw=0.9))

ax.set_ylabel("Ceiling on per-corner scheduling  (%)", fontsize=9.6, color=INK,
              family="DejaVu Sans")
ax.set_title("When is adaptive gate-driver control worth building?",
             fontsize=12.5, fontweight="bold", color=INK, pad=12,
             family="DejaVu Sans")
ax.set_ylim(0, max(ys) * 1.34)
for s in ("top", "right"): ax.spines[s].set_visible(False)
for s in ("left", "bottom"): ax.spines[s].set_color(MUTED)
ax.tick_params(colors=MUTED, labelsize=9)
ax.grid(axis="y", color="#F0F0F0", lw=0.8, zorder=0)

# the second panel explains the shape rather than decorating it
ax2.plot(xs, ns, "-s", color=ACC, lw=1.6, ms=5.0,
         markerfacecolor="#FFFFFF", markeredgewidth=1.4)
ax2.set_ylabel("words safe at\nboth corners", fontsize=8.8, color=MUTED,
               family="DejaVu Sans")
ax2.set_xlabel("Power-loop inductance  (nH)   —   set by board layout, not by the device",
               fontsize=9.6, color=INK, family="DejaVu Sans")
ax2.set_ylim(0, 620)
for s in ("top", "right"): ax2.spines[s].set_visible(False)
for s in ("left", "bottom"): ax2.spines[s].set_color(MUTED)
ax2.tick_params(colors=MUTED, labelsize=8.4)
ax2.grid(axis="y", color="#F4F4F4", lw=0.8)
ax2.text(xs[0], 495, "below ~2 nH feasibility, not optimisation, is what binds",
         fontsize=8, color=MUTED, family="DejaVu Sans")

fig.text(0.012, 0.012,
         "Full 720-word search at two corners for every point, 7,200 transients. "
         "Excluding clamp-chatter points changes no ceiling. "
         "scripts/lloop_sweep.py, lloop_analyse.py.",
         fontsize=7.6, color=MUTED, family="DejaVu Sans")
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig(OUT, dpi=200, facecolor="white")
print("wrote", OUT, " points:", len(pts), " peak %.1f%% @ %.1f nH" % (pk[1], pk[0]),
      " band up to %.1f nH" % band_hi if band_hi else "")
