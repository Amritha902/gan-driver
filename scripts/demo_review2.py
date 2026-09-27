# -*- coding: utf-8 -*-
"""demo_review2.py -- the whole project as one film: netlist, circuit, run,
waveform, and every headline result with the file that produced it.

    python3 scripts/demo_review2.py

WHY ANOTHER ONE
  results/demo_full.mp4 shows the driver model, one ngspice run and the
  crosstalk waveform. That is a third of the project. It never shows the
  circuit those netlists describe, never shows the converter, and ends on a
  single finding -- so a viewer sees a terminal and two traces and has to
  take the rest on trust.

  This shows the chain end to end, twice: for the double-pulse bench that
  measures crosstalk, and for the converter that delivers power. Netlist ->
  schematic -> ngspice running -> waveform -> number. Then every headline
  result in the project, one card at a time, each with the file it is read
  from on screen beside it.

WHAT IS REAL
  Every netlist frame is the file on disk, read at build time.
  Every schematic is the KiCad sheet generated from that netlist.
  Every terminal frame is the actual stdout of an ngspice run made by this
  script while it builds -- not a transcript.
  Every waveform is that run's own output.
  Every result card reads its number from the result file named on the card.
  Only pacing, colour and captions are presentational.

ENCODING
  Raw RGB frames piped to the static ffmpeg that ships with imageio-ffmpeg,
  so the script does not depend on a system ffmpeg.
"""
import csv
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM = os.path.join(ROOT, "sim")
RES = os.path.join(ROOT, "results")
OUT = os.path.join(RES, "demo_review2.mp4")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "review"))

W, H, FPS = 1600, 900, 25
BG, PANEL = (14, 14, 16), (22, 22, 26)
INK, MUT, FAINT = (233, 233, 231), (138, 138, 133), (74, 74, 80)
GRN, RED, BLU, YEL = (110, 214, 150), (226, 96, 88), (108, 168, 238), (235, 190, 90)
VTH = 1.4
T0, T1 = 2.010e-6, 2.075e-6


def _font(paths, px):
    for p in paths:
        if os.path.exists(p):
            return ImageFont.truetype(p, px)
    return ImageFont.load_default()


def mono(px, bold=False):
    return _font(["/usr/share/fonts/truetype/dejavu/DejaVuSansMono%s.ttf"
                  % ("-Bold" if bold else ""),
                  "/usr/share/fonts/truetype/liberation/LiberationMono-%s.ttf"
                  % ("Bold" if bold else "Regular")], px)


def sans(px, bold=False):
    return _font(["/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf"
                  % ("-Bold" if bold else "")], px)


F_CODE, F_CODE_B = mono(20), mono(20, True)
F_BIG = mono(64, True)
F_H1, F_H2, F_H3 = sans(50, True), sans(29, True), sans(22, True)
F_CAP, F_SM = sans(22), sans(18)


def blank():
    return Image.new("RGB", (W, H), BG)


def hold(frames, secs):
    for _ in range(int(FPS * secs)):
        frames.append(frames[-1].copy())


def chapter(d, n, title):
    """The running chapter mark, same place on every frame that has one."""
    d.text((60, 40), "%d" % n, font=F_H2, fill=FAINT)
    d.text((100, 44), title, font=F_H3, fill=BLU)


# ------------------------------------------------------------------ data --
def run_dpt(clken, vneg, tag):
    """One real ngspice run of the double-pulse bench."""
    src = open(os.path.join(SIM, "dpt.cir")).read()
    src = re.sub(r"^\.param CLKEN=.*$", ".param CLKEN=%d" % clken, src, flags=re.M)
    src = re.sub(r"^\.param VNEG=.*$", ".param VNEG=%d" % vneg, src, flags=re.M)
    dat = "/tmp/dr2_%s.dat" % tag
    src = src.replace("wrdata out.dat", "wrdata %s" % dat)
    cir = "/tmp/dr2_%s.cir" % tag
    open(cir, "w").write(src)
    r = subprocess.run(["ngspice", "-b", cir], capture_output=True, text=True,
                       cwd=SIM, timeout=1800)
    d = np.loadtxt(dat)
    t, vsw, vhsg = d[:, 0], d[:, 1], d[:, 7]
    m = (t >= T0) & (t <= T1)
    return r.stdout, t[m] * 1e9, vsw[m], (vhsg - vsw)[m]


# ----------------------------------------------------------------- acts ---
def act_title(frames, secs=4.5):
    for k in range(int(FPS * secs)):
        im = blank()
        d = ImageDraw.Draw(im)
        a = min(1.0, k / (FPS * 0.9))

        def c(col):
            return tuple(int(x * a) for x in col)

        d.text((90, 250), "GaN Synchronous Buck Converter", font=F_H1, fill=c(INK))
        d.text((90, 315), "with an Improved Gate Driver", font=F_H1, fill=c(INK))
        d.text((90, 410), "netlist  →  circuit  →  simulation  →  result",
               font=F_H2, fill=c(BLU))
        d.text((90, 490), "Nothing in this film is a mock-up. The netlists are the files "
                          "on disk, the", font=F_CAP, fill=c(MUT))
        d.text((90, 524), "schematics are drawn from those netlists, the terminal output "
                          "is ngspice's own,", font=F_CAP, fill=c(MUT))
        d.text((90, 558), "and every number names the file it was read from.",
               font=F_CAP, fill=c(MUT))
        d.text((90, 800), "SENSE, VIT Chennai  ·  Review-II",
               font=F_CAP, fill=c(MUT))
        frames.append(im)


def act_statement(frames, n, chap, head, body, secs=6.0):
    im = blank()
    d = ImageDraw.Draw(im)
    chapter(d, n, chap)
    d.text((90, 210), head, font=F_H1, fill=INK)
    y = 330
    for ln, col in body:
        d.text((90, y), ln, font=F_CAP, fill=col)
        y += 38
    frames.append(im)
    hold(frames, secs)


def act_code(frames, n, chap, path, title, show, hi=(), fold_label=None):
    """Type a real source file on, then hold.

    `show` is 1-based line numbers and (first, last) ranges from the file as
    it is on disk. A gap between entries is drawn as a marker saying how many
    lines were folded away, so what is on screen is the real file with its
    repetition folded -- never a paraphrase of it.
    """
    raw = [l.rstrip() for l in open(os.path.join(ROOT, path))]
    want = []
    for e in show:
        want += list(range(e[0], e[1] + 1)) if isinstance(e, tuple) else [e]

    lines, prev = [], None
    for ln_no in want:
        if prev is not None and ln_no > prev + 1:
            gap = raw[prev:ln_no - 1]
            if any(g.strip() for g in gap):
                lines.append((None, "%d more lines%s"
                              % (len(gap), (" — " + fold_label) if fold_label else "")))
        lines.append((ln_no, raw[ln_no - 1]))
        prev = ln_no

    per = max(1, int(FPS * 0.05))
    for shown in range(0, len(lines) + 1):
        im = blank()
        d = ImageDraw.Draw(im)
        chapter(d, n, chap)
        d.text((60, 92), title, font=F_H2, fill=INK)
        d.text((60, 134), "%s   ·   %d lines on disk" % (path, len(raw)),
               font=F_SM, fill=MUT)
        y = 182
        for ln_no, ln in lines[:shown]:
            if ln_no is None:
                d.text((128, y), "⋮  " + ln, font=F_SM, fill=FAINT)
                y += 23
                continue
            col, f = INK, F_CODE
            if any(h in ln for h in hi):
                col, f = YEL, F_CODE_B
            elif ln.strip().startswith(("*", "$")):
                col = MUT
            d.text((60, y), "%3d" % ln_no, font=F_SM, fill=FAINT)
            d.text((128, y), ln[:104], font=f, fill=col)
            y += 23
            if y > H - 60:
                break
        for _ in range(per):
            frames.append(im.copy())
    hold(frames, 2.0)


def act_sheet(frames, n, chap, png, title, caption, crop, zoom=None,
              zoom_caption=None, secs=4.5, zoom_secs=4.5):
    """A KiCad sheet, generated from the netlist just shown, then a detail."""
    def show(box, cap, dur):
        src = Image.open(os.path.join(RES, png)).convert("RGB").crop(box)
        avail_w, avail_h = W - 120, H - 300
        sc = min(avail_w / src.width, avail_h / src.height)
        src = src.resize((int(src.width * sc), int(src.height * sc)), Image.LANCZOS)
        im = blank()
        d = ImageDraw.Draw(im)
        chapter(d, n, chap)
        d.text((60, 92), title, font=F_H2, fill=INK)
        d.text((60, 134), caption, font=F_SM, fill=MUT)
        im.paste(src, ((W - src.width) // 2, 190))
        d = ImageDraw.Draw(im)
        d.text((60, H - 78), cap, font=F_CAP, fill=BLU)
        frames.append(im)
        hold(frames, dur)

    show(crop, caption if not zoom_caption else
         "the whole sheet — every value on it is read from the netlist", secs)
    if zoom:
        show(zoom, zoom_caption, zoom_secs)


def act_terminal(frames, n, chap, cmd, out, title, note=None, keep=24):
    lines = [l.rstrip() for l in out.splitlines() if l.strip()][:keep]
    base = blank()
    d = ImageDraw.Draw(base)
    chapter(d, n, chap)
    d.text((60, 92), title, font=F_H2, fill=INK)
    if note:
        d.text((60, 134), note, font=F_SM, fill=MUT)
    d.text((60, 190), "$ " + cmd, font=F_CODE_B, fill=GRN)
    frames.append(base.copy())
    hold(frames, 1.2)
    y0 = 240
    for k in range(1, len(lines) + 1):
        im = base.copy()
        d = ImageDraw.Draw(im)
        y = y0
        for ln in lines[:k]:
            col = INK
            low = ln.lower()
            if "margin" in low or "vspur" in low or "error" in low:
                col = YEL
            d.text((60, y), ln[:108], font=F_CODE, fill=col)
            y += 25
        for _ in range(max(1, int(FPS * 0.055))):
            frames.append(im)
    hold(frames, 1.8)


def _dark_axes(ax):
    ax.set_facecolor("#0e0e10")
    for s in ax.spines.values():
        s.set_color("#4a4a4a")
    ax.tick_params(colors="#9a9a96", labelsize=11)
    ax.grid(alpha=0.18, lw=0.6, color="#8a8a8a")


def act_waves(frames, t, sw, vgs_bad, vgs_good, secs=9.0):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    n = len(t)
    total, held = int(FPS * secs), int(FPS * 2.4)
    sweep = total - held
    for k in range(total):
        j = n if k >= sweep else max(2, int(n * (k + 1) / sweep))
        fig = plt.figure(figsize=(W / 100.0, H / 100.0), dpi=100)
        fig.patch.set_facecolor("#0e0e10")
        gs = fig.add_gridspec(2, 1, height_ratios=[1, 1.15], hspace=0.42,
                              left=0.085, right=0.975, top=0.84, bottom=0.10)
        ax1, ax2 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
        for ax in (ax1, ax2):
            _dark_axes(ax)
            ax.set_xlim(0, t[-1])
        ax1.plot(t[:j], sw[:j], color="#e26058", lw=2.0)
        ax1.set_ylim(-15, 130)
        ax1.set_ylabel("V(sw)   [V]", color="#e8e8e6", fontsize=12)
        ax1.set_title("5 — the waveform those two runs produced",
                      color="#6ca8ee", fontsize=16, fontweight="bold",
                      loc="left", pad=14)
        ax2.plot(t[:j], vgs_bad[:j], color="#e26058", lw=2.2,
                 label="no clamp, 0 V off rail")
        ax2.plot(t[:j], vgs_good[:j], color="#6ed696", lw=2.2,
                 label="clamp on, −2 V off rail")
        ax2.axhline(VTH, color="#ebbe5a", lw=1.6, ls="--")
        ax2.text(t[-1] * 0.985, VTH + 0.13, "threshold 1.4 V", color="#ebbe5a",
                 fontsize=11.5, ha="right")
        ax2.set_ylim(-2.7, 3.0)
        ax2.set_ylabel("OFF-device gate  V(gs)   [V]", color="#e8e8e6", fontsize=12)
        ax2.set_xlabel("time from the switching edge   [ns]",
                       color="#e8e8e6", fontsize=12)
        leg = ax2.legend(loc="upper right", fontsize=11.5, framealpha=0.0)
        for tx in leg.get_texts():
            tx.set_color("#e8e8e6")
        fig.canvas.draw()
        buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
        frames.append(Image.fromarray(buf).resize((W, H)))
        plt.close(fig)


def act_buck_waves(frames, d, m, secs=11.0):
    """The converter's own waveforms, swept on, from the run just made.

    All three traces advance together. The first version swept only the
    whole-run panel and drew the other two once it finished, so for most of
    the act three of the four panels were empty axes -- which reads as a
    broken render, not as a reveal.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    t, vsw, vout, il = d[:, 0], d[:, 5], d[:, 7], d[:, 9]
    tsw = 1.0 / 500e3
    win = t >= t[-1] - 3 * tsw
    tw = (t[win] - t[win][0]) * 1e6
    vsw_w, il_w = vsw[win], il[win]
    n_full, n_win = len(t), len(tw)

    total, held = int(FPS * secs), int(FPS * 4.0)
    sweep = total - held
    for k in range(total):
        f = 1.0 if k >= sweep else (k + 1) / float(sweep)
        done = f >= 1.0
        j_full = n_full if done else max(2, int(n_full * f))
        j_win = n_win if done else max(2, int(n_win * f))

        fig = plt.figure(figsize=(W / 100.0, H / 100.0), dpi=100)
        fig.patch.set_facecolor("#0e0e10")
        gs = fig.add_gridspec(2, 2, hspace=0.46, wspace=0.22,
                              left=0.075, right=0.975, top=0.84, bottom=0.10)
        ax1, ax2 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
        ax3, ax4 = fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])
        for ax in (ax1, ax2, ax3, ax4):
            _dark_axes(ax)

        ax1.plot(t[:j_full] * 1e6, vout[:j_full], color="#6ca8ee", lw=1.8)
        ax1.axhline(m["Vout"], color="#ebbe5a", lw=1.3, ls="--")
        ax1.set_xlim(0, t[-1] * 1e6)
        ax1.set_ylim(-4, 80)
        ax1.set_title("output voltage, whole run", color="#e8e8e6",
                      fontsize=13, fontweight="bold", loc="left", pad=8)
        ax1.set_ylabel("V(out)  [V]", color="#e8e8e6", fontsize=11)
        ax1.set_xlabel("time  [us]", color="#9a9a96", fontsize=10.5)

        ax2.plot(tw[:j_win], vsw_w[:j_win], color="#e26058", lw=1.4)
        ax2.axhline(m["Vin"], color="#9a9a96", lw=1.0, ls=(0, (4, 4)))
        ax2.set_xlim(0, tw[-1])
        ax2.set_ylim(-14, m["sw_pk"] + 16)
        ax2.set_title("switch node, three settled cycles", color="#e8e8e6",
                      fontsize=13, fontweight="bold", loc="left", pad=8)
        ax2.set_ylabel("V(sw)  [V]", color="#e8e8e6", fontsize=11)
        ax2.set_xlabel("time  [us]", color="#9a9a96", fontsize=10.5)

        ax3.plot(tw[:j_win], il_w[:j_win], color="#6ed696", lw=1.6)
        ax3.axhline(m["Iout"], color="#ebbe5a", lw=1.3, ls="--")
        ax3.set_xlim(0, tw[-1])
        ax3.set_ylim(3.0, 6.7)
        ax3.set_title("inductor current, %.2f A ripple on %.2f A mean"
                      % (float(il_w.max() - il_w.min()), m["Iout"]),
                      color="#e8e8e6", fontsize=13, fontweight="bold",
                      loc="left", pad=8)
        ax3.set_ylabel("I(L)  [A]", color="#e8e8e6", fontsize=11)
        ax3.set_xlabel("time  [us]", color="#9a9a96", fontsize=10.5)

        ax4.axis("off")
        rows = [("in", "%.0f V x %.3f A = %.2f W"
                 % (m["Vin"], m["Iin"], m["Pin"]), "#e8e8e6"),
                ("out", "%.2f V x %.3f A = %.2f W"
                 % (m["Vout"], m["Iout"], m["Pout"]), "#e8e8e6"),
                ("efficiency", "%.2f %%" % m["eff"], "#6ed696"),
                ("loss", "%.3f W" % m["loss"], "#e8e8e6"),
                ("switch-node peak", "%.1f V  (%.1f %% over the bus)"
                 % (m["sw_pk"], m["ov_pct"]), "#ebbe5a")]
        # the readings land one at a time as the traces fill, so the panel is
        # never a blank quarter of the frame
        shown = len(rows) if done else int(len(rows) * f)
        yy = 0.88
        for lab, val, col in rows[:shown]:
            ax4.text(0.0, yy, lab, color="#9a9a96", fontsize=12,
                     transform=ax4.transAxes)
            ax4.text(0.0, yy - 0.09, val, color=col, fontsize=15,
                     fontweight="bold", transform=ax4.transAxes)
            yy -= 0.21

        fig.suptitle("8 — the converter delivering power",
                     color="#6ca8ee", fontsize=16, fontweight="bold",
                     x=0.075, ha="left", y=0.95)
        fig.canvas.draw()
        buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
        frames.append(Image.fromarray(buf).resize((W, H)))
        plt.close(fig)



def act_results(frames, n, chap, cards, per=3.6):
    """Each headline result, with the file it is read from beside it."""
    for k, (label, value, meaning, source, col) in enumerate(cards):
        im = blank()
        d = ImageDraw.Draw(im)
        chapter(d, n, chap)
        d.text((60, 92), "%d of %d" % (k + 1, len(cards)), font=F_SM, fill=FAINT)
        d.text((90, 210), label, font=F_H2, fill=MUT)
        d.text((90, 290), value, font=F_BIG, fill=col)
        y = 430
        for ln in meaning:
            d.text((90, y), ln, font=F_CAP, fill=INK)
            y += 38
        d.rectangle([90, H - 190, W - 90, H - 189], fill=FAINT)
        d.text((90, H - 160), "read from", font=F_SM, fill=FAINT)
        d.text((90, H - 132), source, font=F_CODE, fill=BLU)
        frames.append(im)
        hold(frames, per)


def act_close(frames, secs=6.0):
    im = blank()
    d = ImageDraw.Draw(im)
    d.text((90, 230), "Everything here regenerates", font=F_H1, fill=INK)
    rows = [("the two live runs", "bash proof/LIVE-SIM.sh   ·   "
                                  "bash proof/LIVE-BUCK.sh"),
            ("this film", "python3 scripts/demo_review2.py"),
            ("the schematics", "python3 scripts/kicad_previews.py"),
            ("every number", "results/RESULTS-SUMMARY.txt names the script "
                             "for each one")]
    y = 360
    for lab, cmd in rows:
        d.text((90, y), lab, font=F_CAP, fill=MUT)
        d.text((430, y), cmd, font=F_CODE, fill=GRN if cmd.startswith(("bash", "python"))
               else INK)
        y += 56
    d.text((90, 790), "github.com/Amritha902/gan-driver", font=F_CAP, fill=BLU)
    frames.append(im)
    hold(frames, secs)


# -------------------------------------------------------------- numbers ---
def headline_cards(margin_bad, margin_good):
    """Every card's number, read from the file the card names."""
    import converter_numbers as CN

    grid = open(os.path.join(RES, "grid_analyse.txt")).read()
    fixed, adaptive = (float(x) for x in
                       re.search(r"split: fixed ([\d.]+) %, adaptive ([\d.]+) %",
                                 grid).groups())
    ceiling = float(re.search(r"grid\(n=36\) ([\d.]+) %", grid).group(1))

    sig = open(os.path.join(RES, "si_vs_gan.txt")).read()
    gan_loss, si_loss = (float(x) for x in
                         re.search(r"GaN wastes [\d.]+ W less: ([\d.]+) W against "
                                   r"([\d.]+) W", sig).groups())
    gan_eff, si_eff = (float(x) for x in
                       re.search(r"Efficiency ([\d.]+) % against ([\d.]+) %",
                                 sig).groups())

    pm = {r["config"]: r for r in
          csv.DictReader(open(os.path.join(RES, "panel_metrics.csv")))}
    lat_ours = float(pm["gan_ours"]["latency_ns"])
    lat_base = float(pm["gan_base"]["latency_ns"])
    pdev_ours = float(pm["gan_ours"]["p_dev_W"])
    pdev_base = float(pm["gan_base"]["p_dev_W"])

    util = open(os.path.join(ROOT, "rtl", "vivado", "build",
                             "utilization_synth.rpt")).read()
    luts = int(re.search(r"\|\s*Slice LUTs\*?\s*\|\s*(\d+)", util).group(1))
    ffs = int(re.search(r"\|\s*Slice Registers\s*\|\s*(\d+)", util).group(1))

    ntr = int(open(os.path.join(RES, "transient_count.value")).read().strip())

    # the 36-corner grid's own count: one row per (word, corner) that solved
    with open(os.path.join(RES, "full_grid.csv")) as fh:
        ngrid = sum(1 for _ in fh) - 1

    # the unsafe configuration, for the cost-of-safety card: same file, the
    # row with the clamp off and a 0 V rail at the same eight slices.
    with open(os.path.join(RES, "buck_sweep.csv")) as fh:
        rows = [r for r in csv.DictReader(fh)
                if r["CLKEN"] == "0" and float(r["VNEG"]) == 0.0
                and float(r["slices"]) == 8.0]
    if len(rows) != 1:
        raise SystemExit("buck_sweep.csv: expected one clamp-off 8-slice row, "
                         "found %d" % len(rows))
    unsafe = {k: float(rows[0][k]) for k in ("eff", "loss")}

    # The part of the extra loss that is arithmetic rather than assertion:
    # GaN has no body diode, so during dead time the off device conducts in
    # its third quadrant at Vth + |Voff| + I*Rds(on). Dropping the off rail
    # from 0 V to -2 V adds 2 V to that, for the dead time in every period.
    # The timing is read from the netlist, so the film cannot outlive it.
    buck_src = open(os.path.join(SIM, "buck.cir")).read()

    def _p(name):
        return re.search(r"^\.param %s\s*=\s*(\S+)\s*$" % name,
                         buck_src, re.M).group(1)

    _mul = {"n": 1e-9, "u": 1e-6, "m": 1e-3, "k": 1e3}

    def _sec(v):
        return float(v[:-1]) * _mul[v[-1]] if v[-1] in _mul else float(v)

    dt, fsw, duty = _sec(_p("DT")), _sec(_p("FSW")), float(_p("D"))
    tsw = 1.0 / fsw
    # one dead time at the high side's trailing edge, two around the low side
    dead = tsw - (duty * tsw - dt) - ((1 - duty) * tsw - 2 * dt)
    TQ_W = 2.0 * CN.V["Iout"] * dead / tsw

    return [
        ("the crosstalk margin, fastest drive",
         "%+.3f V → %+.3f V" % (margin_bad, margin_good),
         ["Without the clamp the OFF device's gate crosses its 1.40 V threshold",
          "and the device turns on when it should not. With the clamp and a",
          "−2 V off rail it sits 2.58 V clear. This is the result the project is for."],
         "scripts/gansim.py — the two runs in chapters 4 and 5 of this film", GRN),

        ("the converter, on the shipped word",
         "%s in → %s at %s" % (CN.VIN, CN.VOUT, CN.EFF),
         ["%s drawn, %s delivered, %s of loss."
          % (CN.PIN, CN.POUT, "%.3f W" % CN.V["loss"]),
          "Same devices and same drivers as the bench, now switching",
          "continuously at 500 kHz into a 22 uH / 4.7 uF filter and a 10 ohm load."],
         "results/buck_sweep.csv, via review/converter_numbers.py", GRN),

        ("what the crosstalk fix costs the converter",
         "−%.2f points" % (unsafe["eff"] - CN.V["eff"]),
         ["Clamp off and 0 V rail is MORE efficient: %.2f %% against %.2f %%."
          % (unsafe["eff"], CN.V["eff"]),
          "About %.2f W of the %.2f W is third-quadrant conduction you can compute"
          % (TQ_W, CN.V["loss"] - unsafe["loss"]),
          "by hand; the rest is the clamp's own switching."],
         "results/buck_sweep.csv — both rows, printed by scripts/live_buck.py", YEL),

        ("the search behind the shipped word",
         "%s transients" % format(ngrid, ","),
         ["720 control words over 36 corners of bus voltage, load current and",
          "junction temperature — %s of the project's %s simulations."
          % (format(ngrid, ","), format(ntr, ",")),
          "Choosing the fixed word well is worth %.2f %%; adapting it per operating"
          % fixed,
          "point adds %.2f %% on top, against a %.2f %% ceiling."
          % (adaptive, ceiling)],
         "results/full_grid.csv → results/grid_analyse.txt", BLU),

        ("GaN against silicon, same converter",
         "%.1f W → %.1f W" % (si_loss, gan_loss),
         ["Device swapped, everything else held, R_ds(on) matched at the 25 mOhm class.",
          "Efficiency %.2f %% against %.2f %% — worth %.2f points."
          % (gan_eff, si_eff, gan_eff - si_eff),
          "The loss almost halves. This is why the project is GaN and not silicon."],
         "results/si_vs_gan.txt", GRN),

        ("against the base paper's driver",
         "%.2f ns → %.2f ns" % (lat_base, lat_ours),
         ["Same converter, same GaN device, same output stage. Control swapped.",
          "Propagation latency falls %.2f ns and device dissipation falls %.3f W"
          % (lat_base - lat_ours, pdev_base - pdev_ours),
          "(%.3f W against %.3f W)." % (pdev_ours, pdev_base)],
         "results/panel_metrics.csv — Zhang et al., ISPSD 2020 as the baseline", BLU),

        ("what the controller costs in real fabric",
         "%d LUT / %d FF" % (luts, ffs),
         ["Synthesised for a Xilinx xc7a35t, not estimated: 0.10 % of its LUTs",
          "and 0.05 % of its flip-flops. The adaptive logic is not the expensive",
          "part of this design, which is the point the scheduling result rests on."],
         "rtl/vivado/build/utilization_synth.rpt", BLU),
    ]


# ----------------------------------------------------------------- main ---
class Sink(object):
    """An ffmpeg pipe that behaves enough like the frame list it replaces.

    The first version accumulated every frame in a list and encoded at the
    end. At 1600x900x3 that is 4.3 MB a frame, so a two-minute film wanted
    about 13 GB and the process was killed after the simulations had already
    run -- silently, with no output file. Frames now go down the pipe as they
    are drawn, so memory is flat however long the film gets. Only the most
    recent frame is kept, which is all `hold` ever asks for.
    """

    def __init__(self, path):
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        self.proc = subprocess.Popen(
            [exe, "-y", "-loglevel", "error", "-f", "rawvideo",
             "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS),
             "-i", "-", "-an", "-vcodec", "libx264", "-pix_fmt", "yuv420p",
             "-crf", "20", "-movflags", "+faststart", path],
            stdin=subprocess.PIPE)
        self.n = 0
        self.last = None

    def append(self, im):
        self.proc.stdin.write(im.tobytes())
        self.n += 1
        self.last = im

    def __getitem__(self, k):
        if k != -1:
            raise IndexError("a Sink only remembers its most recent frame")
        return self.last

    def __len__(self):
        return self.n

    def close(self):
        self.proc.stdin.close()
        return self.proc.wait()



def main():
    import bucksim

    print("  the film's data, measured now:")
    print("    double-pulse bench, no clamp ...")
    out_bad, t, sw_bad, vgs_bad = run_dpt(0, 0, "bad")
    print("    double-pulse bench, clamp on, -2 V ...")
    out_good, tg, sw_good, vgs_good = run_dpt(1, -2, "good")
    n = min(len(t), len(tg))
    t, sw_bad, vgs_bad, vgs_good = t[:n] - t[0], sw_bad[:n], vgs_bad[:n], vgs_good[:n]
    pk_bad, pk_good = float(np.max(vgs_bad)), float(np.max(vgs_good))
    print("      OFF-gate peak  %+.4f V (no clamp)   %+.4f V (shipped)"
          % (pk_bad, pk_good))

    print("    the converter, 150 switching cycles ...")
    bd, bp = bucksim.run_raw(CLKEN=1, VNEG=-2)
    if bd is None:
        raise SystemExit("the converter run produced no output")
    bm = bucksim.metrics(bd, bp)
    print("      %.2f V out, %.2f W, %.2f %% efficient"
          % (bm["Vout"], bm["Pout"], bm["eff"]))

    frames = Sink(OUT)
    act_title(frames)

    act_statement(frames, 1, "the problem",
                  "A GaN half-bridge can turn itself on",
                  [("When one device switches, its drain moves at over 100 V per nanosecond.",
                    INK),
                   ("That edge couples through the other device's gate-drain capacitance and",
                    INK),
                   ("lifts its gate. If the gate crosses the threshold, both devices conduct",
                    INK),
                   ("at once across the bus. GaN makes this worse than silicon does, because",
                    INK),
                   ("the edges are faster and the threshold is lower.", INK),
                   ("", INK),
                   ("Two things stop it: an active Miller clamp that shorts the gate during",
                    BLU),
                   ("the other device's edge, and holding the off gate below 0 V.", BLU),
                   ("", INK),
                   ("The base paper has neither.  — Zhang et al., ISPSD 2020", YEL)],
                  secs=8.0)

    act_code(frames, 2, "the netlist", "sim/dpt.cir",
             "The double-pulse bench, as it is on disk",
             show=[(1, 3), (21, 34)],
             hi=("CLKEN", "VNEG", "NPU", "NPD", "DT"),
             fold_label="the file header")

    act_sheet(frames, 3, "the circuit", "fig_sch_ours.png",
              "The segmented gate driver that netlist describes",
              "scripts/kicad_previews.py draws this sheet from models/segdrv.lib",
              crop=(150, 30, 1800, 1100),
              zoom=(1380, 610, 1805, 1095),
              zoom_caption="the active Miller clamp — one switch, one 0.5 ohm "
                           "resistor, across the gate")

    act_terminal(frames, 4, "the run",
                 "ngspice -b dpt.cir      # no clamp, 0 V off rail",
                 out_bad, "ngspice, running, now",
                 note="this is the simulator's own stdout, captured while this "
                      "film was built")
    act_terminal(frames, 4, "the run",
                 "ngspice -b dpt.cir      # clamp on, −2 V off rail",
                 out_good, "the same netlist, two parameters changed",
                 note="CLKEN 0 → 1 and VNEG 0 → −2. Nothing else in "
                      "the file moves.")

    act_waves(frames, t, sw_bad, vgs_bad, vgs_good)

    act_statement(frames, 6, "the reading",
                  "%+.3f V against a 1.400 V threshold" % pk_bad,
                  [("Without the clamp the OFF device's gate reaches %+.4f V. "
                    "The threshold is 1.400 V," % pk_bad, INK),
                   ("so the margin is −%.3f V — negative. It turns on."
                    % abs(VTH - pk_bad), RED),
                   ("", INK),
                   ("With the clamp and the −2 V rail it reaches −%.4f V."
                    % abs(pk_good), INK),
                   ("The margin is +%.3f V." % (VTH - pk_good), GRN),
                   ("", INK),
                   ("Both numbers were measured by the two runs you just watched.",
                    MUT)],
                  secs=7.0)

    act_code(frames, 7, "the converter", "sim/buck.cir",
             "The converter that bench is a measurement of",
             show=[(1, 2), (22, 40)],
             hi=("VIN", "FSW", "LOUT", "COUT", "RLOAD", "CLKEN", "VNEG"),
             fold_label="the file header")

    act_sheet(frames, 7, "the converter", "fig_sch_converter.png",
              "100 V in, 48.5 V out, 236 W into 10 ohm",
              "scripts/kicad_previews.py draws this sheet from sim/buck.cir",
              crop=(150, 40, 2150, 1010),
              zoom=(900, 480, 2150, 1010),
              zoom_caption="the half-bridge and its output filter — 22 uH, "
                           "4.7 uF, 10 ohm load",
              secs=5.0, zoom_secs=5.0)

    act_buck_waves(frames, bd, bm)

    act_results(frames, 9, "every result", headline_cards(VTH - pk_bad, VTH - pk_good))

    act_close(frames)

    n = len(frames)
    print("  %d frames, %.1f s at %d fps" % (n, n / float(FPS), FPS))
    rc = frames.close()
    print("  %s: %s  (%.1f MB)"
          % ("written" if rc == 0 else "ffmpeg FAILED", OUT,
             os.path.getsize(OUT) / 1e6 if rc == 0 else 0))
    return rc


if __name__ == "__main__":
    sys.exit(main())
