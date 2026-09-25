# -*- coding: utf-8 -*-
"""demo_video.py -- the project demonstrated end to end: the code, the run,
and the result, in one video.

    python3 scripts/demo_video.py

WHY A NEW ONE
  results/demo_crosstalk_explained.mp4 animates the waveforms and does that
  well, but it starts at the answer. A viewer never sees the circuit that
  produced it or the simulator producing it, so the traces have to be taken
  on trust. This shows the control word in the model file, the ngspice run
  that consumes it, and only then the waveforms -- so the result arrives
  attached to its cause.

FIVE ACTS
  1  what is being shown
  2  THE CODE      models/segdrv.lib -- the eight slices and the clamp,
                   the real file, typed on
  3  THE RUN       ngspice invoked on sim/dpt.cir, twice, and its real
                   stdout as it comes back
  4  THE RESULT    the crosstalk event from those two runs, animated
  5  THE FINDING   the margin, and what moved it

EVERYTHING IS REAL
  The code frames are read from the repository at build time. The terminal
  frames are the actual stdout of the actual ngspice runs made by this
  script -- not a transcript, not a re-enactment. The waveforms are those
  runs' own output. Only pacing and captions are presentational.

ENCODING
  Frames are piped as raw RGB into ffmpeg. The environment has no system
  ffmpeg; imageio-ffmpeg ships a static binary and that is what is used, so
  the script is self-contained rather than depending on the host.
"""
import os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM  = os.path.join(ROOT, "sim")
OUT  = os.path.join(ROOT, "results", "demo_full.mp4")

W, H, FPS = 1600, 900, 25
BG, INK, MUT = (14, 14, 16), (232, 232, 230), (135, 135, 130)
GRN, RED, BLU, YEL = (110, 214, 150), (226, 96, 88), (108, 168, 238), (235, 190, 90)
VTH = 1.4
T0, T1 = 2.010e-6, 2.075e-6


def font(px, bold=False):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono%s.ttf"
              % ("-Bold" if bold else ""),
              "/usr/share/fonts/truetype/liberation/LiberationMono-%s.ttf"
              % ("Bold" if bold else "Regular")):
        if os.path.exists(p):
            return ImageFont.truetype(p, px)
    return ImageFont.load_default()


def sans(px, bold=False):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf"
              % ("-Bold" if bold else ""),):
        if os.path.exists(p):
            return ImageFont.truetype(p, px)
    return font(px, bold)


F_CODE, F_CODE_B = font(21), font(21, True)
F_H1, F_H2, F_CAP = sans(52, True), sans(30, True), sans(23)


def blank():
    return Image.new("RGB", (W, H), BG)


# ------------------------------------------------------------------ data --
def run_case(clken, vneg, tag):
    """One real ngspice run. Returns (stdout, t_ns, v_sw, v_gs)."""
    src = open(os.path.join(SIM, "dpt.cir")).read()
    src = re.sub(r"^\.param CLKEN=.*$", ".param CLKEN=%d" % clken, src, flags=re.M)
    src = re.sub(r"^\.param VNEG=.*$",  ".param VNEG=%d"  % vneg,  src, flags=re.M)
    dat = "/tmp/dv_%s.dat" % tag
    src = src.replace("wrdata out.dat", "wrdata %s" % dat)
    cir = "/tmp/dv_%s.cir" % tag
    open(cir, "w").write(src)
    r = subprocess.run(["ngspice", "-b", cir], capture_output=True, text=True,
                       cwd=SIM, timeout=1800)
    d = np.loadtxt(dat)
    t, vsw, vhsg = d[:, 0], d[:, 1], d[:, 7]
    m = (t >= T0) & (t <= T1)
    return r.stdout, t[m] * 1e9, vsw[m], (vhsg - vsw)[m]


# ----------------------------------------------------------------- acts ---
def act_title(frames, secs=3.0):
    for k in range(int(FPS * secs)):
        im = blank(); d = ImageDraw.Draw(im)
        a = min(1.0, k / (FPS * 0.8))
        def c(col): return tuple(int(x * a) for x in col)
        d.text((90, 300), "GaN segmented gate driver", font=F_H1, fill=c(INK))
        d.text((90, 375), "the code, the run, and the result", font=F_H2, fill=c(BLU))
        d.text((90, 470), "Every frame after this is real: the model file as it is on disk,",
               font=F_CAP, fill=c(MUT))
        d.text((90, 505), "ngspice's own output, and the waveforms those runs produced.",
               font=F_CAP, fill=c(MUT))
        d.text((90, 800), "SENSE, VIT Chennai", font=F_CAP, fill=c(MUT))
        frames.append(im)


def act_code(frames, path, title, show, hi=()):
    """Type a real source file on, then hold.

    `show` is a list of 1-based line numbers and (first, last) ranges taken
    from the file as it is on disk.  A gap between two entries is drawn as an
    explicit marker saying how many lines were skipped, so what is on screen
    is the real file with the repetition folded, never a paraphrase of it.
    """
    raw = [l.rstrip() for l in open(os.path.join(ROOT, path))]

    want = []
    for e in show:
        want += list(range(e[0], e[1] + 1)) if isinstance(e, tuple) else [e]

    lines, prev = [], None
    for n in want:
        if prev is not None and n > prev + 1:
            gap = raw[prev:n - 1]
            # A gap that is only blank lines is just whitespace we stepped
            # over; saying "lines skipped" there would overstate it.
            if any(g.strip() for g in gap):
                nsl = sum(1 for g in gap if g.strip().lower().startswith("s"))
                lines.append((None, "%d more lines -- slices %d to %d, identical "
                                    "but for the index"
                                    % (len(gap), 3, 2 + nsl)))
        lines.append((n, raw[n - 1]))
        prev = n

    per = max(1, int(FPS * 0.055))
    for shown in range(0, len(lines) + 1):
        im = blank(); d = ImageDraw.Draw(im)
        d.text((60, 42), title, font=F_H2, fill=BLU)
        d.text((60, 86), "%s   (%d lines)" % (path, len(raw)), font=F_CAP, fill=MUT)
        y = 136
        for n, ln in lines[:shown]:
            if n is None:                       # elision marker
                d.text((124, y), "\u22ee  " + ln, font=F_CAP, fill=MUT)
                y += 24
                continue
            col, f = INK, F_CODE
            if any(h in ln for h in hi):
                col, f = YEL, F_CODE_B
            if ln.strip().startswith("*"):
                col = MUT
            d.text((60, y), "%3d" % n, font=F_CAP, fill=(70, 70, 76))
            d.text((124, y), ln[:106], font=f, fill=col)
            y += 24
            if y > H - 60:
                break
        for _ in range(per):
            frames.append(im.copy())
    for _ in range(int(FPS * 2.2)):
        frames.append(frames[-1].copy())


def act_terminal(frames, cmd, out, title, keep=26):
    lines = [l.rstrip() for l in out.splitlines() if l.strip()][:keep]
    im0 = blank(); d = ImageDraw.Draw(im0)
    d.text((60, 42), title, font=F_H2, fill=BLU)
    d.text((60, 140), "$ " + cmd, font=F_CODE_B, fill=GRN)
    frames += [im0.copy() for _ in range(int(FPS * 1.1))]
    y0 = 185
    for n in range(1, len(lines) + 1):
        im = im0.copy(); d = ImageDraw.Draw(im)
        y = y0
        for ln in lines[:n]:
            col = INK
            if "margin" in ln.lower() or "vspur" in ln.lower():
                col = YEL
            d.text((60, y), ln[:110], font=F_CODE, fill=col)
            y += 26
        for _ in range(max(1, int(FPS * 0.06))):
            frames.append(im)
    for _ in range(int(FPS * 1.8)):
        frames.append(frames[-1].copy())


def act_waves(frames, tb, swb, vgsb, sws, vgss, secs=9.0):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    n = len(tb)
    total = int(FPS * secs)
    hold = int(FPS * 2.0)
    sweep = total - hold
    for k in range(total):
        j = n if k >= sweep else max(2, int(n * (k + 1) / sweep))
        fig = plt.figure(figsize=(W / 100.0, H / 100.0), dpi=100)
        fig.patch.set_facecolor("#0e0e10")
        gs = fig.add_gridspec(2, 1, height_ratios=[1, 1.15], hspace=0.42,
                              left=0.085, right=0.975, top=0.86, bottom=0.10)
        ax1, ax2 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
        for ax in (ax1, ax2):
            ax.set_facecolor("#0e0e10")
            for s in ax.spines.values():
                s.set_color("#4a4a4a")
            ax.tick_params(colors="#9a9a96", labelsize=11)
            ax.grid(alpha=0.18, lw=0.6, color="#8a8a8a")
            ax.set_xlim(0, tb[-1])
        ax1.plot(tb[:j], swb[:j], color="#e26058", lw=2.0, label="switch node")
        ax1.set_ylim(-15, 130)
        ax1.set_ylabel("V(sw)   [V]", color="#e8e8e6", fontsize=12)
        ax1.set_title("the switching edge that causes it",
                      color="#6ca8ee", fontsize=15, fontweight="bold", pad=10)
        ax2.plot(tb[:j], vgsb[:j], color="#e26058", lw=2.2,
                 label="no clamp, 0 V off rail")
        ax2.plot(tb[:j], vgss[:j], color="#6ed696", lw=2.2,
                 label="clamp on, −2 V off rail")
        ax2.axhline(VTH, color="#ebbe5a", lw=1.6, ls="--")
        ax2.text(tb[-1] * 0.985, VTH + 0.12, "threshold 1.4 V", color="#ebbe5a",
                 fontsize=11.5, ha="right")
        ax2.set_ylim(-2.7, 3.0)
        ax2.set_ylabel("OFF gate  V(gs)   [V]", color="#e8e8e6", fontsize=12)
        ax2.set_xlabel("time  [ns]", color="#e8e8e6", fontsize=12)
        leg = ax2.legend(loc="upper right", fontsize=11.5, framealpha=0.0)
        for t in leg.get_texts():
            t.set_color("#e8e8e6")
        fig.canvas.draw()
        buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
        frames.append(Image.fromarray(buf).resize((W, H)))
        plt.close(fig)


def act_finding(frames, peak_bad, peak_good, secs=5.0):
    # Derived, not quoted: whichbit re-runs the freeze test over the same
    # sweep CSVs and tells us what pull-up drive strength is worth.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import whichbit
    npu = whichbit.freeze_cost("NPU_LS")

    for k in range(int(FPS * secs)):
        im = blank(); d = ImageDraw.Draw(im)
        d.text((90, 120), "the finding", font=F_H1, fill=INK)
        rows = [
            ("no clamp, 0 V off rail",
             "OFF gate reaches %+.2f V   against a 1.4 V threshold" % peak_bad,
             RED if peak_bad >= VTH else GRN),
            ("clamp on, −2 V off rail",
             "OFF gate reaches %+.2f V   margin %+.2f V" % (peak_good, VTH - peak_good),
             GRN),
        ]
        y = 280
        for lab, val, col in rows:
            d.text((90, y), lab, font=F_H2, fill=MUT)
            d.text((90, y + 46), val, font=F_CODE_B, fill=col)
            y += 150
        d.text((90, 640), "The clamp and the negative rail carry the result.",
               font=F_CAP, fill=INK)
        d.text((90, 676), "Freezing the eight drive-strength slices costs "
                          "%.2f %%." % npu, font=F_CAP, fill=MUT)
        d.text((90, 800), "sim/dpt.cir  ·  ngspice  ·  regenerate with "
                          "scripts/demo_video.py", font=F_CAP, fill=MUT)
        frames.append(im)


# ----------------------------------------------------------------- main ---
def encode(frames, path):
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    p = subprocess.Popen(
        [exe, "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
         "-an", "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", path],
        stdin=subprocess.PIPE)
    for im in frames:
        p.stdin.write(im.tobytes())
    p.stdin.close()
    return p.wait()


def main():
    print("  running ngspice twice (real runs, this is the video's data) ...")
    out_b, tb, swb, vgsb = run_case(0, 0, "bad")
    out_g, tg, swg, vgss = run_case(1, -2, "good")
    n = min(len(tb), len(tg))
    tb, swb, vgsb, vgss = tb[:n], swb[:n], vgsb[:n], vgss[:n]
    tb = tb - tb[0]
    pb, pg = float(np.max(vgsb)), float(np.max(vgss))
    print("    %d samples; OFF-gate peak  no-clamp %+.3f V   shipped %+.3f V"
          % (n, pb, pg))

    frames = []
    act_title(frames)
    # The switch model, the subckt header with its npu/npd params, the first
    # and last slice of each bank, and the clamp -- the repeated middle slices
    # are folded away with a marker rather than scrolled past.
    act_code(frames, "models/segdrv.lib", "1 — the code",
             show=[21, 23, 25, (26, 29), (40, 41), 43, (44, 47), (58, 59),
                   61, (62, 63), 65],
             hi=("Spu", "Rpu", "Spd", "Rpd", "Sclk", "Rclk"))
    act_terminal(frames, "ngspice -b dpt.cir      # no clamp, 0 V off rail",
                 out_b, "2 — the run")
    act_terminal(frames, "ngspice -b dpt.cir      # clamp on, −2 V off rail",
                 out_g, "2 — the run")
    act_waves(frames, tb, swb, vgsb, swg[:n], vgss)
    act_finding(frames, pb, pg)

    print("  %d frames, %.1f s at %d fps" % (len(frames), len(frames) / FPS, FPS))

    # Sidecar so the deck can quote this video's length and measurements
    # without anyone retyping them; the caption then cannot drift from the
    # file it describes.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import whichbit
    side = os.path.join(ROOT, "results", "demo_full.txt")
    with open(side, "w") as fh:
        fh.write("# written by scripts/demo_video.py -- do not edit by hand\n")
        fh.write("frames      %d\n" % len(frames))
        fh.write("fps         %d\n" % FPS)
        fh.write("duration_s  %.1f\n" % (len(frames) / float(FPS)))
        fh.write("peak_noclamp %+.3f\n" % pb)
        fh.write("peak_shipped %+.3f\n" % pg)
        fh.write("margin       %+.3f\n" % (VTH - pg))
        fh.write("npu_freeze_pct %.2f\n" % whichbit.freeze_cost("NPU_LS"))
    print("  sidecar: %s" % side)

    rc = encode(frames, OUT)
    print("  %s: %s  (%.1f MB)" % ("written" if rc == 0 else "ffmpeg FAILED",
                                   OUT, os.path.getsize(OUT) / 1e6 if rc == 0 else 0))
    return rc


if __name__ == "__main__":
    sys.exit(main())
