"""
live_buck.py -- run the CONVERTER in front of the panel, right now.

live_demo.py runs the double-pulse bench: one switching edge, which is the
right instrument for measuring crosstalk but is not a converter. It never
delivers power to a load, so it cannot answer the question a reviewer asks
next -- does the thing actually work?

This runs sim/buck.cir: the same GaN devices and the same segmented gate
drivers, switching continuously at 500 kHz into a 22 uH / 4.7 uF filter and
a 10 ohm load, converting 100 V into 48.5 V at 236 W. 150 switching cycles,
300 us of converter time, about nine seconds of wall clock per run.

    python3 scripts/live_buck.py            both runs, ~20 s, writes a plot
    python3 scripts/live_buck.py --no-plot  numbers only, for a terminal
    python3 scripts/live_buck.py --deck     also writes the deck's figure

Two runs of ONE circuit file, with nothing changed between them except the
two control parameters this project is about:

    CLKEN   active Miller clamp     0 = off, 1 = on
    VNEG    gate off-rail voltage   0 V or -2 V

The second run is not a straw man. The converter is MORE efficient without
the crosstalk fix, and this prints that difference rather than hiding it:
the fix is bought, not free, and the double-pulse result is what buys it.
"""
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
sys.path.insert(0, os.path.join(ROOT, "review"))

C = dict(dim="\033[2m", b="\033[1m", g="\033[32m", r="\033[31m",
         y="\033[33m", c="\033[36m", off="\033[0m")
if not sys.stdout.isatty() or os.environ.get("NO_COLOR"):
    C = {k: "" for k in C}


def say(s=""):
    print(s, flush=True)                     # flush: the panel watches it appear


def _panel_ov():
    """The overshoot the head-to-head tables print, from the file they print."""
    import csv
    with open(os.path.join(RES, "panel_metrics.csv")) as fh:
        for r in csv.DictReader(fh):
            if r["config"] == "gan_ours":
                return float(r["ov_pct"])
    raise SystemExit("panel_metrics.csv: no gan_ours row")


def main():
    plot = "--no-plot" not in sys.argv
    deck = "--deck" in sys.argv
    import bucksim
    # What the slides claim, read from the shipped row of buck_sweep.csv --
    # the same module slides 6, 7, 14 and 31 read. Nothing is typed in here,
    # so a slide that drifts makes this comparison fail on screen.
    import converter_numbers as CN

    say()
    say("%s  GaN synchronous buck converter -- simulated live%s" % (C["b"], C["off"]))
    say("  %s%s%s" % (C["dim"], "-" * 66, C["off"]))
    host = subprocess.run(["hostname"], capture_output=True, text=True).stdout.strip()
    ver = subprocess.run(["ngspice", "-v"], capture_output=True, text=True)
    # `ngspice -v` opens with a banner of asterisks; the version line is the
    # one containing "ngspice-", and it still carries its own "** " prefix.
    ver = next((l.strip().lstrip("*").strip()
                for l in (ver.stdout + ver.stderr).split("\n")
                if "ngspice-" in l), "ngspice (version not reported)")[:48]
    say("  machine  %s        %s" % (host, time.strftime("%Y-%m-%d %H:%M:%S")))
    say("  spice    %s" % ver)
    say("  circuit  sim/buck.cir         device  models/egan.lib")
    say("  100 V bus, 500 kHz, D = 0.50, 22 uH / 4.7 uF into 10 ohm")
    say("  150 switching cycles = 300 us of converter time, each run")
    say("  changing ONLY  CLKEN (clamp)  and  VNEG (off rail)")
    say()

    t0 = time.time()
    say("  %s(a) shipped word: clamp on, -2 V off rail, 8 slices ...%s"
        % (C["y"], C["off"]))
    da, pa = bucksim.run_raw(CLKEN=1, VNEG=-2)
    if da is None:
        say("  %sngspice produced no output -- see proof/PREFLIGHT.sh%s"
            % (C["r"], C["off"]))
        return 1
    a = bucksim.metrics(da, pa)
    say("      in    %7.2f V  x  %6.4f A  =  %7.2f W"
        % (a["Vin"], a["Iin"], a["Pin"]))
    say("      out   %7.2f V  x  %6.4f A  =  %7.2f W"
        % (a["Vout"], a["Iout"], a["Pout"]))
    say("      efficiency  %s%.2f %%%s        loss %.3f W"
        % (C["g"], a["eff"], C["off"], a["loss"]))
    say("      switch node peaks at %.1f V on a %.0f V bus  (%.1f %% overshoot)"
        % (a["sw_pk"], a["Vin"], a["ov_pct"]))
    say("      output ripple %.0f mV  (%.2f %% of %.2f V)"
        % (a["ripple_mV"], 100.0 * a["ripple_mV"] / 1e3 / a["Vout"], a["Vout"]))
    say()

    say("  %s(b) same converter, clamp off, 0 V off rail ...%s" % (C["y"], C["off"]))
    db, pb = bucksim.run_raw(CLKEN=0, VNEG=0)
    b = bucksim.metrics(db, pb) if db is not None else None
    if b is None:
        say("      (run failed -- the shipped result above still stands)")
    else:
        say("      efficiency  %.2f %%        loss %.3f W" % (b["eff"], b["loss"]))
        say("      %sthe crosstalk fix costs %.2f efficiency points (%.3f W more loss)%s"
            % (C["c"], b["eff"] - a["eff"], a["loss"] - b["loss"], C["off"]))
        say("      that is the price. The double-pulse run is what buys it:")
        say("      without the fix the OFF device's gate crosses its threshold.")
    say()

    say("  %s%s%s" % (C["dim"], "-" * 66, C["off"]))
    say("  %-28s %14s %12s" % ("", "on the slide", "this run"))
    for lab, slide, got in (("output voltage      [V]", CN.V["Vout"], a["Vout"]),
                            ("output power        [W]", CN.V["Pout"], a["Pout"]),
                            ("efficiency          [%]", CN.V["eff"], a["eff"]),
                            ("switch-node peak    [V]", CN.V["sw_pk"], a["sw_pk"])):
        ok = abs(slide - got) <= 0.005 * max(1.0, abs(slide))
        say("  %-28s %14.2f %12.4f   %s"
            % (lab, slide, got,
               (C["g"] + "match" + C["off"]) if ok else (C["r"] + "DIFFERS" + C["off"])))
    say("  %s%s%s" % (C["dim"], "-" * 66, C["off"]))
    say("  two ngspice converter transients, %.1f s wall clock on this machine"
        % (time.time() - t0))
    # The head-to-head tables quote a different number for the same peak, and
    # a reviewer who spots that deserves the reason rather than a shrug. The
    # other number is read from the file that produced it, not typed here --
    # a note that goes stale is worse than no note.
    say("  %snote: the GaN-vs-Si table says %.1f %% for this overshoot, not %.1f %%."
        % (C["dim"], _panel_ov(), a["ov_pct"]))
    say("        Same operating point, finer instrument: panel_metrics.py")
    say("        re-runs three settled cycles at a 0.02 ns step to resolve the")
    say("        edge, where this uses the sweep's 0.2 ns step.%s" % C["off"])

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
    say("  drawing the waveforms that run produced ...")

    t = da[:, 0]
    vsw, vout, iout = da[:, 5], da[:, 7], da[:, 9]
    lsg, hsg = da[:, 11], da[:, 13]
    tsw = 1.0 / 500e3
    # three settled cycles at the very end of the run
    win = (t >= t[-1] - 3 * tsw)
    tw = (t[win] - t[win][0]) * 1e6

    BLUE, RED, GRN = "#2a78d6", "#d03b3b", "#1b7f5f"
    AMB, SURF = "#b8761a", "#fcfcfb"
    INK, MUTED, RULE = "#0b0b0b", "#52514e", "#d8d7d2"

    fig, axs = plt.subplots(2, 2, figsize=(12.4, 7.0), facecolor=SURF,
                            gridspec_kw=dict(hspace=0.42, wspace=0.24))
    for ax in axs.ravel():
        ax.set_facecolor(SURF)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(RULE)
        ax.tick_params(colors=MUTED, labelsize=9, length=3)
        ax.grid(True, color=RULE, lw=0.6, alpha=0.7)
        ax.set_axisbelow(True)

    # (a) the whole run: it starts up and it regulates
    ax = axs[0, 0]
    ax.plot(t * 1e6, vout, color=BLUE, lw=1.4)
    ax.axhline(a["Vout"], color=AMB, lw=1.2, ls=(0, (5, 3)))
    ax.annotate("settles at %.2f V" % a["Vout"], (t[-1] * 1e6, a["Vout"]),
                textcoords="offset points", xytext=(-6, 7), ha="right",
                color=AMB, fontsize=9.5, weight="bold")
    ax.annotate("ripple %.0f mV (%.2f %%)"
                % (a["ripple_mV"], 100.0 * a["ripple_mV"] / 1e3 / a["Vout"]),
                (t[-1] * 1e6, a["Vout"]), textcoords="offset points",
                xytext=(-6, -16), ha="right", color=MUTED, fontsize=9)
    ax.set_title("output voltage, whole run", color=INK, fontsize=11,
                 weight="bold", loc="left", pad=8)
    ax.set_xlabel("time  [us]", color=MUTED, fontsize=9.5)
    ax.set_ylabel("V(out)  [V]", color=MUTED, fontsize=9.5)

    # (b) the switch node doing the chopping
    ax = axs[0, 1]
    ax.plot(tw, vsw[win], color=RED, lw=1.2)
    ax.axhline(a["Vin"], color=MUTED, lw=1.0, ls=(0, (4, 4)))
    ax.annotate("bus %.0f V" % a["Vin"], (tw[-1], a["Vin"]),
                textcoords="offset points", xytext=(-4, -14), ha="right",
                color=MUTED, fontsize=9)
    ipk = int(np.argmax(vsw[win]))
    ax.annotate("peak %.1f V" % a["sw_pk"], (tw[ipk], a["sw_pk"]),
                textcoords="offset points", xytext=(8, -13), ha="left",
                color=RED, fontsize=10, weight="bold")
    ax.set_ylim(min(vsw[win]) - 8, a["sw_pk"] + 14)
    ax.set_title("switch node, three settled cycles", color=INK, fontsize=11,
                 weight="bold", loc="left", pad=8)
    ax.set_xlabel("time  [us]", color=MUTED, fontsize=9.5)
    ax.set_ylabel("V(sw)  [V]", color=MUTED, fontsize=9.5)

    # (c) the gate drives -- dead time and the -2 V rail, visible
    ax = axs[1, 0]
    one = (t >= t[-1] - tsw)
    to = (t[one] - t[one][0]) * 1e9
    ax.plot(to, hsg[one] - vsw[one], color=RED, lw=1.3, label="high side Vgs")
    ax.plot(to, lsg[one], color=BLUE, lw=1.3, label="low side Vgs")
    ax.axhline(0.0, color=MUTED, lw=0.9)
    ax.axhline(-2.0, color=GRN, lw=1.2, ls=(0, (5, 3)))
    ax.annotate("-2 V off rail", (to[-1], -2.0), textcoords="offset points",
                xytext=(-4, 5), ha="right", color=GRN, fontsize=9.5, weight="bold")
    ax.set_title("gate drive, one cycle", color=INK, fontsize=11,
                 weight="bold", loc="left", pad=8)
    ax.set_xlabel("time  [ns]", color=MUTED, fontsize=9.5)
    ax.set_ylabel("Vgs  [V]", color=MUTED, fontsize=9.5)
    ax.legend(frameon=False, fontsize=9, labelcolor=MUTED, loc="center right")

    # (d) the inductor current -- the triangle that says "buck converter"
    ax = axs[1, 1]
    il = iout[win]
    ax.plot(tw, il, color=GRN, lw=1.4)
    ax.axhline(a["Iout"], color=AMB, lw=1.2, ls=(0, (5, 3)))
    ax.annotate("mean %.3f A" % a["Iout"], (tw[-1], a["Iout"]),
                textcoords="offset points", xytext=(-6, 7), ha="right",
                color=AMB, fontsize=9.5, weight="bold")
    ax.set_title("inductor current, %.2f A ripple on %.2f A"
                 % (float(il.max() - il.min()), a["Iout"]),
                 color=INK, fontsize=11, weight="bold", loc="left", pad=8)
    ax.set_xlabel("time  [us]", color=MUTED, fontsize=9.5)
    ax.set_ylabel("I(L)  [A]", color=MUTED, fontsize=9.5)

    fig.suptitle("What `bash proof/LIVE-BUCK.sh` draws, in about twenty seconds"
                 if deck else
                 "sim/buck.cir, simulated on this machine at %s"
                 % time.strftime("%H:%M:%S"),
                 color=INK, fontsize=13.5, weight="bold", x=0.062, ha="left", y=0.985)

    out = os.path.join(RES, "fig_live_buck.png" if deck else "buck_run.png")
    fig.savefig(out, dpi=150, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)
    say("  wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
