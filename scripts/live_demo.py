"""
live_demo.py -- simulate the circuit in front of the panel, right now.

The deck has a recorded video. A recording proves nothing a sceptic cares
about: it was made somewhere else, at some other time, by someone who had
every chance to pick the take. This runs the same two simulations live, on
whatever machine is in the room, and puts the numbers it just measured next
to the numbers on the slide.

    python3 scripts/live_demo.py            both runs, ~5 s, writes a plot
    python3 scripts/live_demo.py --no-plot  numbers only, for a terminal

It is deliberately two runs of ONE circuit file. sim/dpt.cir is not modified
between them -- only the two control parameters the whole project is about:

    CLKEN   active Miller clamp     0 = off, 1 = on
    VNEG    gate off-rail voltage   0 V or -2 V

so a reviewer watching can see that nothing else changed.
"""
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
VTH = 1.4
# What the slides claim. Printed beside what this run measures, so the
# comparison is on screen rather than in the presenter's memory.
SLIDE = dict(spur=1.65, margin=2.576)

C = dict(dim="\033[2m", b="\033[1m", g="\033[32m", r="\033[31m",
         y="\033[33m", c="\033[36m", off="\033[0m")
if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
    C = {k: "" for k in C}


def say(s=""):
    print(s, flush=True)                     # flush: the panel watches it appear


def main():
    plot = "--no-plot" not in sys.argv
    import gansim

    say()
    say("%s  GaN half-bridge -- crosstalk, simulated live%s" % (C["b"], C["off"]))
    say("  %s%s%s" % (C["dim"], "-" * 64, C["off"]))
    host = subprocess.run(["hostname"], capture_output=True, text=True).stdout.strip()
    # `ngspice -v` prints a banner of asterisks first; the version line is
    # the one that actually contains "ngspice-".
    ver = subprocess.run(["ngspice", "-v"], capture_output=True, text=True)
    ver = next((l.strip() for l in (ver.stdout + ver.stderr).split("\n")
                if "ngspice-" in l), "ngspice (version not reported)")[:48]
    say("  machine  %s        %s" % (host, time.strftime("%Y-%m-%d %H:%M:%S")))
    say("  spice    %s" % ver)
    say("  circuit  sim/dpt.cir          device  models/egan.lib")
    say("  changing ONLY  CLKEN (clamp)  and  VNEG (off rail)")
    say()

    t0 = time.time()
    say("  %s(a) fastest drive, no clamp, 0 V off rail ...%s" % (C["y"], C["off"]))
    a = gansim.run(CLKEN=0, VNEG=0)
    say("      OFF-device gate reaches  %s%+.4f V%s   against a %.3f V threshold"
        % (C["r"], a["Vgs_spur"], C["off"], VTH))
    say("      margin %+.4f V     false_turn_on = %d   %s"
        % (a["margin"], a["false_on"],
           C["r"] + "SHOOT-THROUGH" + C["off"] if a["false_on"] else ""))
    say()

    say("  %s(b) same circuit, clamp on, -2 V off rail ...%s" % (C["y"], C["off"]))
    b = gansim.run(CLKEN=1, VNEG=-2)
    say("      OFF-device gate reaches  %s%+.4f V%s"
        % (C["g"], b["Vgs_spur"], C["off"]))
    say("      margin %+.4f V     false_turn_on = %d   %s"
        % (b["margin"], b["false_on"],
           "" if b["false_on"] else C["g"] + "SAFE" + C["off"]))
    say()

    say("  %s%s%s" % (C["dim"], "-" * 64, C["off"]))
    say("  %-26s %12s %12s" % ("", "on the slide", "this run"))
    say("  %-26s %12.2f %12.4f" % ("OFF gate, no clamp  [V]", SLIDE["spur"], a["Vgs_spur"]))
    say("  %-26s %12.3f %12.4f" % ("margin, shipped     [V]", SLIDE["margin"], b["margin"]))
    say("  %s%s%s" % (C["dim"], "-" * 64, C["off"]))
    say("  two ngspice transients, %.1f s wall clock on this machine"
        % (time.time() - t0))

    if not plot:
        return 0

    # ---- the picture, from the same two runs -----------------------------
    try:
        import numpy as np
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception as e:
        say("  (no plot: %s)" % e)
        return 0

    say()
    say("  drawing the waveforms those two runs produced ...")
    raws = {}
    for tag, kw in (("bad", dict(CLKEN=0, VNEG=0)), ("good", dict(CLKEN=1, VNEG=-2))):
        d, _ = gansim.run_raw(**kw)
        t, vsw, vhsg = d[:, 0], d[:, 1], d[:, 7]
        m = (t >= 2.010e-6) & (t <= 2.075e-6)
        raws[tag] = (t[m] * 1e9 - 2010.0, vsw[m], (vhsg - vsw)[m])

    BLUE, RED, SURF = "#2a78d6", "#d03b3b", "#fcfcfb"
    INK, MUTED, RULE = "#0b0b0b", "#52514e", "#d8d7d2"
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.6, 6.4), sharex=True,
                                   facecolor=SURF, gridspec_kw=dict(hspace=0.16))
    for ax in (ax1, ax2):
        ax.set_facecolor(SURF)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(RULE)
        ax.tick_params(colors=MUTED, labelsize=9, length=3)
        ax.grid(True, color=RULE, lw=0.6, alpha=0.7)
        ax.set_axisbelow(True)

    ax1.plot(raws["bad"][0], raws["bad"][1], color=RED, lw=1.8)
    ax1.set_ylabel("switch node V(sw)  [V]", color=MUTED, fontsize=10)
    ax1.set_title("Simulated on this machine at %s" % time.strftime("%H:%M:%S"),
                  color=INK, fontsize=13, weight="bold", loc="left", pad=10)

    ax2.plot(raws["bad"][0], raws["bad"][2], color=RED, lw=1.8,
             label="no clamp, 0 V off rail")
    ax2.plot(raws["good"][0], raws["good"][2], color=BLUE, lw=1.8,
             label="clamp on, −2 V off rail")
    ax2.axhline(VTH, color="#b8761a", lw=1.4, ls=(0, (5, 3)))
    ax2.annotate("threshold %.1f V" % VTH, (raws["bad"][0][0], VTH),
                 textcoords="offset points", xytext=(4, 5), ha="left",
                 color="#b8761a", fontsize=9.5)
    ax2.set_ylabel("OFF-device gate V(gs)  [V]", color=MUTED, fontsize=10)
    ax2.set_xlabel("time from the switching edge  [ns]", color=MUTED, fontsize=10)
    ax2.legend(frameon=False, fontsize=9.5, labelcolor=MUTED, loc="lower right")
    # anchor each label at its own trace's peak, offset away from the curve
    ia = int(np.argmax(raws["bad"][2]))
    ib = int(np.argmax(raws["good"][2]))
    ax2.annotate("peak %+.3f V" % a["Vgs_spur"], (raws["bad"][0][ia], raws["bad"][2][ia]),
                 textcoords="offset points", xytext=(10, 6), ha="left",
                 color=RED, fontsize=10, weight="bold")
    ax2.annotate("peak %+.3f V" % b["Vgs_spur"], (raws["good"][0][ib], raws["good"][2][ib]),
                 textcoords="offset points", xytext=(10, 2), ha="left",
                 color=BLUE, fontsize=10, weight="bold")
    ax2.set_ylim(min(raws["good"][2]) - 0.7, max(raws["bad"][2]) + 0.6)

    out = os.path.join(RES, "live_run.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)
    say("  wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
