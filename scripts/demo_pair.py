# -*- coding: utf-8 -*-
"""demo_pair.py -- one film for the base paper, one for ours.

    python3 scripts/record_kicad.py     # once, for the sheet captures
    python3 scripts/demo_pair.py

    results/demo_basepaper.mp4   their circuit, their run, their output
    results/demo_ours.mp4        our circuit,  our run,  our output

WHY TWO FILMS AND NOT ONE
  demo_review2.mp4 ends by overlaying the two drivers on one axis, which is
  the right way to show the answer once the viewer knows what they are
  looking at. It is the wrong way to introduce them. These two run the same
  four beats over each driver separately -- sheet, simulator, waveform,
  reading -- so each can be played on its own, or the pair played back to
  back with nothing to untangle.

THE TWO FILMS ARE DELIBERATELY IDENTICAL EXCEPT FOR THE DRIVER
  Same template, same beat lengths, same fonts, and -- this is the part that
  matters -- the SAME AXIS LIMITS on the waveform. A comparison where one
  plot is autoscaled and the other is not is not a comparison, it is two
  pictures. Both films say on screen that the scale is fixed, so a viewer
  who flicks between them is reading a real difference in trace position and
  not a difference in zoom.

  Both are run from sim/dpt.cir verbatim at 100 V, 10 A, 25 C. Only the
  driver subcircuit is swapped. Their driver runs at the setting
  scripts/headtohead.py found BEST for it at that corner, read out of
  results/headtohead.txt rather than chosen here.
"""
import io
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import demo_review2 as D                                    # noqa: E402

ROOT = D.ROOT
RES = D.RES
W, H, CH, FPS, VTH = D.W, D.H, D.CH, D.FPS, D.VTH

# One scale for both films. Fixed here, not derived from either trace, so
# neither film can quietly rescale itself around its own result.
T_MAX = 65.0
VGS_LO, VGS_HI = -2.9, 2.4
SW_LO, SW_HI = -18.0, 132.0


def reading_card(frames, title, peak, margin, colour, note, secs=6.5):
    def draw(d):
        d.text((90, 150), title, font=D.F_H2, fill=D.MUT)
        d.text((90, 225), "%s V" % ("%+.3f" % peak).replace("-", "−"),
               font=D.F_BIG, fill=colour)
        d.text((90, 330), "peak on the OFF device's gate", font=D.F_CAP, fill=D.INK)
        d.text((90, 420), "threshold", font=D.F_SM, fill=D.FAINT)
        d.text((90, 448), "1.400 V", font=D.F_H3, fill=D.INK)
        d.text((420, 420), "margin", font=D.F_SM, fill=D.FAINT)
        d.text((420, 448), "%.3f V" % margin, font=D.F_H3, fill=colour)
        y = 560
        for ln in note:
            d.text((90, y), ln, font=D.F_CAP, fill=D.MUT)
            y += 34
    D.card(frames, secs, draw, "")


def waveform(frames, t, sw, vgs, peak, colour, who, secs=12.0):
    """The output, on the fixed scale both films share."""
    plt, _ = D.newfig()
    n = len(t)
    total, held = int(FPS * secs), int(FPS * 5.5)
    sweep = total - held
    i_edge = int(np.argmin(np.gradient(sw)))
    i_peak = int(np.argmax(vgs))
    for k in range(total):
        done = k >= sweep
        j = n if done else max(2, int(n * (k + 1) / float(sweep)))
        _, fig = D.newfig()
        gs = fig.add_gridspec(2, 1, height_ratios=[1, 1.2], hspace=0.42,
                              left=0.085, right=0.955, top=0.84, bottom=0.12)
        ax1, ax2 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
        for ax in (ax1, ax2):
            D._dark_axes(ax)
            ax.set_xlim(0, T_MAX)
        ax1.plot(t[:j], sw[:j], color="#e26058", lw=2.0)
        ax1.set_ylim(SW_LO, SW_HI)
        ax1.set_ylabel("switch node  V(sw)   [V]", color="#e8e8e6", fontsize=12)
        ax1.set_title("the output — %s" % who, color="#6ca8ee", fontsize=16,
                      fontweight="bold", loc="left", pad=14)
        ax2.plot(t[:j], vgs[:j], color=colour, lw=2.4)
        ax2.axhline(VTH, color="#ebbe5a", lw=1.8, ls="--")
        ax2.set_ylim(VGS_LO, VGS_HI)
        ax2.set_ylabel("OFF device gate  V(gs)   [V]", color="#e8e8e6", fontsize=12)
        ax2.set_xlabel("time from the switching edge   [ns]", color="#e8e8e6",
                       fontsize=12)
        if done:
            ax1.annotate("the switching edge that causes it",
                         xy=(t[i_edge], sw[i_edge]), xytext=(T_MAX * 0.38, 110),
                         color="#e26058", fontsize=13, fontweight="bold",
                         arrowprops=dict(color="#e26058", **D.ARROW))
            ax2.annotate("peak %s V" % ("%+.3f" % peak).replace("-", "−"),
                         xy=(t[i_peak], vgs[i_peak]),
                         xytext=(T_MAX * 0.34, peak + 1.05),
                         color=colour, fontsize=13.5, fontweight="bold",
                         arrowprops=dict(color=colour, **D.ARROW))
            ax2.annotate("threshold 1.400 V", xy=(T_MAX * 0.06, VTH),
                         xytext=(T_MAX * 0.06, 1.95), color="#ebbe5a",
                         fontsize=12.5, fontweight="bold",
                         arrowprops=dict(color="#ebbe5a", **D.ARROW))
            xm = T_MAX * 0.84
            ax2.annotate("", xy=(xm, VTH), xytext=(xm, peak),
                         arrowprops=dict(arrowstyle="<->", color="#e8e8e6", lw=1.6))
            ax2.text(xm - T_MAX * 0.015, (VTH + peak) / 2.0,
                     "%.3f V of margin" % (VTH - peak), color="#e8e8e6",
                     fontsize=13, fontweight="bold", ha="right", va="center")
        frames.append(D.fig_frame(
            fig, "Fixed scale — the other film uses exactly these axes, so "
                 "the two can be compared by eye."))
        plt.close(fig)
    D.dissolve(frames)


def simulate(tag, netlist):
    """One ngspice run. Both films' runs happen before either is assembled,
    so a caption may quote the other film's result."""
    stdout, t, sw, vgs = D._run(netlist, tag)
    peak = float(np.max(vgs))
    print("      %-5s OFF-gate peak %+.4f V   margin %+.3f V"
          % (tag, peak, VTH - peak))
    return dict(stdout=stdout, t=t, sw=sw, vgs=vgs, peak=peak)


def film(out_path, who, tag, png, moves, run, colour, note):
    frames = D.Sink(out_path)
    stamp = "screen capture \u00b7 KiCad %s" % D.kicad_version()
    D.scene_kicad(frames, png, stamp,
                  (3.2, "%s \u2014 the circuit, in KiCad." % who), moves,
                  poster=os.path.splitext(out_path)[0] + "_poster.png")
    D.scene_terminal(frames,
                     "ngspice -b dpt.cir      # %s, 100 V / 10 A / 25 \u00b0C" % tag,
                     run["stdout"], "The simulator's own output, captured while "
                                    "this film was being built.")
    waveform(frames, run["t"], run["sw"], run["vgs"], run["peak"], colour, who)
    reading_card(frames, "%s \u2014 the reading" % who, run["peak"],
                 VTH - run["peak"], colour, note)
    n = len(frames)
    rc = frames.close()
    print("      %s: %d frames, %.1f s, %.1f MB"
          % (os.path.basename(out_path), n, n / float(FPS),
             os.path.getsize(out_path) / 1e6))
    return rc



def main():
    for png in ("kicad_segdrv.png", "kicad_zhangdrv.png"):
        if not os.path.exists(os.path.join(RES, png)):
            raise SystemExit("results/%s missing -- run "
                             "scripts/record_kicad.py first" % png)
    import headtohead as HH

    nseg, tstep = D.base_setting()
    print("  both runs first, so either film can quote the other's number:")
    rb = simulate("base", HH.deck(100, 10, 25, base=(nseg, tstep)))
    ro = simulate("ours", HH.deck(100, 10, 25))
    pk_base, pk_ours = rb["peak"], ro["peak"]
    ratio = (VTH - pk_ours) / (VTH - pk_base)

    rc1 = film(
        os.path.join(RES, "demo_basepaper.mp4"),
        "Base paper \u2014 Zhang et al., ISPSD 2020", "base",
        "kicad_zhangdrv.png",
        [((1280, 660, 1950), (1280, 620, 1750), 4.4,
          "Seven segments per bank, engaged in two stages. Our reimplementation "
          "of their driver, from their paper."),
         ((1280, 620, 1750), (1500, 900, 1300), 4.6,
          "No clamp branch, and VN tied to the local reference \u2014 no "
          "negative off rail. Their paper has neither.")],
        rb, "#ebbe5a",
        ["Run at nseg=%d, tstep=%s \u2014 the setting scripts/headtohead.py found"
         % (nseg, tstep),
         "BEST for their driver at this corner, read from results/headtohead.txt.",
         "Their own paper sets one bias resistor once at design time, so this",
         "gives them a freedom the published design does not have."])

    rc2 = film(
        os.path.join(RES, "demo_ours.mp4"),
        "Ours \u2014 segmented driver with clamp and \u22122 V rail", "ours",
        "kicad_segdrv.png",
        [((1150, 560, 1700), (1130, 560, 1350), 4.4,
          "Eight pull-up segments from the +5 V rail to the gate, eight pull-down "
          "segments to the off rail."),
         ((1130, 560, 1350), (1480, 690, 980), 4.6,
          "And on the right, the active Miller clamp \u2014 one switch and a 0.5 "
          "ohm resistor across the gate. This is what their sheet does not have.")],
        ro, "#6ed696",
        ["One fixed control word: clamp on, \u22122 V off rail, all eight segments.",
         "The same word is used at every corner in the study \u2014 it is not",
         "re-tuned for this run.",
         "%.1f\u00d7 the margin of the driver in the other film." % ratio])


    side = os.path.join(RES, "demo_pair.txt")
    with io.open(side, "w", encoding="utf-8") as fh:
        fh.write(u"# written by scripts/demo_pair.py -- do not edit by hand\n")
        fh.write(u"base_peak    %+.4f\n" % pk_base)
        fh.write(u"base_margin  %+.4f\n" % (VTH - pk_base))
        fh.write(u"ours_peak    %+.4f\n" % pk_ours)
        fh.write(u"ours_margin  %+.4f\n" % (VTH - pk_ours))
        fh.write(u"ratio        %.2f\n" % ((VTH - pk_ours) / (VTH - pk_base)))
        # the deck quotes the setting their driver ran at, so it travels
        # with the numbers rather than being retyped on a slide
        fh.write(u"base_nseg    %d\n" % nseg)
        fh.write(u"base_tstep   %s\n" % tstep)
    print("  sidecar: %s" % side)
    return rc1 or rc2


if __name__ == "__main__":
    sys.exit(main())
