# -*- coding: utf-8 -*-
"""make_demo_video.py -- the explanatory demo video.

Animates the REAL ngspice waveforms of the crosstalk event, side by side:
the failing configuration and the shipped one, with the threshold drawn and
captions saying what is happening as it happens.

    python3 scripts/make_demo_video.py

Nothing here is drawn by hand. The traces come from sim/dpt.cir run twice,
once at CLKEN=0 VNEG=0 and once at CLKEN=1 VNEG=-2; only the pacing and the
captions are presentational.
"""
import os, subprocess, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import animation

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM  = os.path.join(ROOT, "sim")
OUT  = os.path.join(ROOT, "results", "demo_crosstalk_explained.mp4")
VTH  = 1.4
T0, T1 = 2.010e-6, 2.075e-6          # the crosstalk event

def capture(clken, vneg, tag):
    src = open(os.path.join(SIM, "dpt.cir")).read()
    import re
    src = re.sub(r"^\.param CLKEN=.*$", ".param CLKEN=%d" % clken, src, flags=re.M)
    src = re.sub(r"^\.param VNEG=.*$",  ".param VNEG=%d"  % vneg,  src, flags=re.M)
    dat = "/tmp/%s.dat" % tag
    src = src.replace("wrdata out.dat", "wrdata %s" % dat)
    p = "/tmp/%s.cir" % tag
    open(p, "w").write(src)
    subprocess.run(["ngspice", "-b", p], capture_output=True, cwd=SIM, timeout=900)
    d = np.loadtxt(dat)
    t, vsw, vhsg = d[:, 0], d[:, 1], d[:, 7]
    m = (t >= T0) & (t <= T1)
    return t[m] * 1e9, vsw[m], (vhsg - vsw)[m]

print("running ngspice twice ...")
tb, swb, vgsb = capture(0,  0, "vid_base")
ts, sws, vgss = capture(1, -2, "vid_ship")
n = min(len(tb), len(ts))
tb, swb, vgsb = tb[:n], swb[:n], vgsb[:n]
ts, sws, vgss = ts[:n], sws[:n], vgss[:n]
t0 = tb[0]; tb, ts = tb - t0, ts - t0
print("  %d samples over %.1f ns" % (n, tb[-1]))

FPS, SECS = 25, 22
FRAMES = FPS * SECS
HOLD   = int(FPS * 3.5)                    # frames held at the end of each phase
SWEEP  = FRAMES - 2 * HOLD

fig = plt.figure(figsize=(10.0, 5.84), dpi=150)
fig.patch.set_facecolor("white")
gs  = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.25], hspace=0.52, wspace=0.27,
                       left=0.080, right=0.975, top=0.850, bottom=0.165)
axS = [fig.add_subplot(gs[0, i]) for i in range(2)]
axG = [fig.add_subplot(gs[1, i]) for i in range(2)]

RED, GRN, INK, MUT = "#c0392b", "#1e8449", "#1a1a1a", "#8a8a8a"
titles = ["FAILING  —  fastest drive, no clamp, 0 V off-bias",
          "SHIPPED  —  Miller clamp on, −2 V off-bias"]
cols   = [RED, GRN]

for i in range(2):
    axS[i].set_xlim(0, tb[-1]); axS[i].set_ylim(-15, 125)
    axS[i].set_ylabel("switch node\nV(sw)   [V]", fontsize=11)
    axS[i].set_title(titles[i], fontsize=11.5, color=cols[i], fontweight="bold", pad=8)
    axS[i].grid(alpha=0.25, lw=0.6); axS[i].tick_params(labelsize=10)
    # Top is 2.9, not 2.2: the threshold caption sits at VTH + 0.50 and the
    # failing peak marker at 1.65, so the old top clipped the caption.
    axG[i].set_xlim(0, tb[-1]); axG[i].set_ylim(-2.6, 2.9)
    axG[i].set_xlabel("time from the low-side turn-on  [ns]", fontsize=11)
    axG[i].set_ylabel("high-side gate\nV(hsg,sw)   [V]", fontsize=11)
    axG[i].grid(alpha=0.25, lw=0.6); axG[i].tick_params(labelsize=10)
    axG[i].axhline(VTH, color=RED, lw=2.2, ls="--")
    # Sits well above the line, not just clear of it: the failing panel's peak
    # marker lands at 1.65 V and covered this text when it was at VTH + 0.10.
    axG[i].text(tb[-1] * 0.985, VTH + 0.50, "threshold 1.4 V  —  above this the device turns on",
                fontsize=10, color=RED, ha="right", va="bottom", fontweight="bold")

lS = [axS[i].plot([], [], lw=2.4, color=INK)[0] for i in range(2)]
lG = [axG[i].plot([], [], lw=2.9, color=cols[i])[0] for i in range(2)]
pk = [axG[i].plot([], [], "o", ms=10, color=cols[i])[0] for i in range(2)]
an = [axG[i].annotate("", xy=(0, 0), xytext=(0, 0), fontsize=13.5,
                      fontweight="bold", color=cols[i]) for i in range(2)]

sup = fig.text(0.5, 0.958, "", ha="center", fontsize=16, fontweight="bold", color=INK)
cap = fig.text(0.5, 0.032, "", ha="center", fontsize=11, color=MUT)

PHASES = [
    ("The low-side device turns on. Watch the switch node fall.",
     "Real ngspice output from sim/dpt.cir — only the pacing is presentational."),
    ("That dV/dt couples through C_GD into the OFF device's gate.",
     "Left: the gate is pushed ABOVE threshold — false turn-on, a shoot-through path."),
    ("Same circuit, same control word, two actuators added.",
     "Right: active Miller clamp plus −2 V off-bias — 2.58 V of margin instead of −0.25 V."),
]

# Index of the true peak in each trace, computed once over the WHOLE trace.
# frame() must not re-derive it from the partially drawn segment: see below.
MPK = [int(np.argmax(vgsb)), int(np.argmax(vgss))]

def frame(k):
    if k < SWEEP:
        j = max(2, int(n * (k + 1) / SWEEP)); phase = 0 if k < SWEEP * 0.45 else 1
    elif k < SWEEP + HOLD:
        j = n; phase = 1
    else:
        j = n; phase = 2
    for i, (tt, sw, vg) in enumerate(((tb, swb, vgsb), (ts, sws, vgss))):
        lS[i].set_data(tt[:j], sw[:j])
        lG[i].set_data(tt[:j], vg[:j])
        # Label the peak only once the sweep has actually passed it. A running
        # argmax over the first samples reports the STARTING value, so frame 0
        # read "peak +0.03 V   safe" on the FAILING panel -- the exact opposite
        # of what that panel exists to show. Frame 0 is not a private detail:
        # Keynote ignores PowerPoint's poster_frame_image and shows frame 0 as
        # the slide's still, so it is what a reader sees before pressing play.
        if j <= MPK[i]:
            pk[i].set_data([], [])
            an[i].set_text("")
            continue
        m = MPK[i]
        vmax = vg[m]
        pk[i].set_data([tt[m]], [vmax])
        lab = "peak %+.2f V   %s" % (vmax, "FALSE TURN-ON" if vmax > VTH else "safe")
        an[i].set_text(lab)
        an[i].xy = (tt[m], vmax)
        an[i].set_position((tt[m] + 2.0, vmax + (0.30 if vmax < 1.0 else -0.95)))
    sup.set_text(PHASES[phase][0]); cap.set_text(PHASES[phase][1])
    return lS + lG + pk + an + [sup, cap]

print("rendering %d frames ..." % FRAMES)
anim = animation.FuncAnimation(fig, frame, frames=FRAMES, blit=False)
anim.save(OUT, fps=FPS, dpi=150,
          extra_args=["-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "23"])
print("wrote", OUT)
