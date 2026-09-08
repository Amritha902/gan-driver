#!/bin/zsh
# STEP 9 -- run ngspice and put the waveforms on screen, live.
cd ~/gan-driver
print -P "%F{cyan}================================================================%f"
print -P "%F{cyan} STEP 9  The waveforms, straight out of ngspice, on screen%f"
print -P "%F{cyan}================================================================%f"
echo "No saved picture. ngspice runs now, and the plot window that opens"
echo "is drawn from the numbers it just produced."
echo
python3 - <<'PY'
import sys, os, time
sys.path.insert(0, 'scripts')
import numpy as np, gansim
import matplotlib
matplotlib.use("MacOSX")
import matplotlib.pyplot as plt

t0 = time.time()
print("  running ngspice: case (a) fastest drive, no clamp, 0 V off-bias ...")
A, pa = gansim.run_raw(CLKEN=0, VNEG=0)
print("  running ngspice: case (b) same circuit, clamp on, -2 V off-bias ...")
B, pb = gansim.run_raw(CLKEN=1, VNEG=-2)
print("  ngspice finished in %.1f s -- %d and %d time points"
      % (time.time()-t0, A.shape[0], B.shape[0]))

# The high-side device is OFF from T3 onward; the low side turns on at T4 and
# that edge is what kicks the high-side gate. Window: T3 -> T4 + 200 ns.
T3 = 2e-6
def cut(d, p):
    dt = gansim._sec(p["DT"]); T4 = T3 + dt
    t   = d[:, 0]
    sw  = d[:, 1]
    hsg = d[:, 7] - d[:, 1]        # gate-source of the OFF (high-side) device
    m = (t >= T3 + 8e-9) & (t <= T4 + 110e-9)
    return t[m] * 1e6, sw[m], hsg[m], T4 * 1e6

fig, ax = plt.subplots(2, 2, figsize=(12.5, 6.6), sharex=True)
fig.canvas.manager.set_window_title("ngspice output - run %s" % time.strftime("%H:%M:%S"))
for col, (d, p, title, colour) in enumerate((
        (A, pa, "(a) fastest drive, NO clamp, 0 V off-bias", "#B00000"),
        (B, pb, "(b) clamp ON, -2 V off-bias", "#1E7B34"))):
    t, sw, hsg, t4 = cut(d, p)
    ax[0][col].axvline(t4, ls=":", lw=1.1, color="#888888")
    ax[1][col].axvline(t4, ls=":", lw=1.1, color="#888888")
    ax[0][col].plot(t, sw, lw=1.4, color="#1F4E9C")
    ax[0][col].set_title(title, fontsize=11, fontweight="bold")
    ax[0][col].set_ylabel("switch node  V(sw)  [V]")
    ax[0][col].grid(alpha=.25)

    ax[1][col].plot(t, hsg, lw=1.4, color=colour)
    ax[1][col].axhline(1.4, ls="--", lw=1.2, color="#B00000")
    ax[1][col].text(t[-1]-0.002, 1.60, "threshold 1.4 V - above this it turns ON",
                    fontsize=8.5, color="#B00000", ha="right")
    ax[0][col].text(t4 + 0.003, 55, "low side turns ON", fontsize=8.5, color="#555555")
    pk = float(hsg.max())
    ax[1][col].plot([t[int(np.argmax(hsg))]], [pk], "o", ms=6, color=colour)
    ax[1][col].annotate("peak %+.3f V" % pk,
                        (t[int(np.argmax(hsg))], pk),
                        textcoords="offset points", xytext=(10, 6),
                        fontsize=10, fontweight="bold", color=colour)
    ax[1][col].set_ylabel("gate of the OFF device  [V]")
    ax[1][col].set_xlabel("time  [us]")
    ax[1][col].set_ylim(-2.6, 2.9)
    ax[1][col].grid(alpha=.25)

fig.suptitle("Live ngspice run - sim/dpt.cir - %s" % time.strftime("%Y-%m-%d %H:%M:%S"),
             fontsize=12, fontweight="bold")
fig.tight_layout(rect=(0, 0, 1, 0.96))
out = os.path.expanduser("~/GAN_MAIN/PROOF/screenshots/15-live-waveforms.png")
fig.savefig(out, dpi=150)
print("  peak on the OFF gate: (a) %+.4f V   (b) %+.4f V   threshold 1.400 V"
      % (cut(A, pa)[2].max(), cut(B, pb)[2].max()))
print("  saved a copy to PROOF/screenshots/15-live-waveforms.png")
print()
print("  Close the plot window to finish this step.")
plt.show()
PY
