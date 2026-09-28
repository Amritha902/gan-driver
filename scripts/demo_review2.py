# -*- coding: utf-8 -*-
"""demo_review2.py -- the demo film: implementation, tools, output, comparison.

    python3 scripts/record_kicad.py     # once, or after the sheets change
    python3 scripts/demo_review2.py

FOUR PARTS
  1  THE IMPLEMENTATION   the circuit, in KiCad, on screen
  2  THE SOFTWARE         what drew it and what ran it, named and versioned
  3  THE OUTPUT           the waveforms, with the thing to look at pointed at
  4  THEIRS AND OURS      the base paper's driver and this one, measured on
                          the same bench at the same corner

HOW IT IS SHOT
  The schematic shots are screen captures of eeschema with the sheet open --
  the application, its toolbars, its hierarchy pane -- made by
  scripts/record_kicad.py on a virtual X display. The film moves a crop across
  those frames to go from the whole window to the half-bridge to the clamp.
  That is an edit over real pixels: nothing in this container can drive the
  GUI, so nothing pretends a session took place.

  The ngspice pane is not a screen capture, and does not claim to be: there is
  no terminal emulator here. It is the simulator's real stdout, captured while
  the film builds, typeset.

  Every frame carries a subtitle band. The film is played without anyone
  talking over it, so what the viewer needs to understand has to be on screen.

WHAT IS MEASURED WHILE IT BUILDS
  Three ngspice runs: our driver on the double-pulse bench, the base paper's
  driver on the SAME bench at the same corner, and the converter delivering
  power. Every annotated number was measured from the trace it points at.

THE BASE PAPER
  Zhang, Yu, Leng, Cui, Deng, Ng, ISPSD 2020. models/zhangdrv.lib is that
  driver: segmented, with no active Miller clamp and no negative off rail.
  scripts/headtohead.py searched its two controls at each corner, and the film
  runs it at the setting that search found BEST for it, read out of
  results/headtohead.txt -- not a setting chosen here.

ENCODING
  Raw RGB frames streamed to the static ffmpeg from imageio-ffmpeg. Frames are
  never accumulated: at 1600x900x3 a list of them exhausts memory long before
  the film ends, which is how the first build died.
"""
import csv
import io
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
SIDE = os.path.join(RES, "demo_review2.txt")
POSTER = os.path.join(ROOT, "review", "poster_review2.png")
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

# ------------------------------------------------------------ presentation --
# Every frame is the same two bands: the picture, and a subtitle strip under
# it. The strip is not decoration -- the film is played without a presenter
# talking over it, so whatever the viewer is supposed to understand about the
# frame has to be on the frame.
CH = H - 96                                   # picture height; the rest is the strip


def band(im, text, colour=INK):
    d = ImageDraw.Draw(im)
    d.rectangle([0, CH, W, H], fill=(9, 9, 11))
    d.rectangle([0, CH, W, CH + 1], fill=(48, 48, 54))
    if not text:
        return im
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=F_CAP) > W - 180:
            lines.append(cur)
            cur = w
        else:
            cur = t
    lines.append(cur)
    lines = lines[:2]
    y = CH + (96 - len(lines) * 30) // 2
    for ln in lines:
        d.text(((W - d.textlength(ln, font=F_CAP)) // 2, y), ln,
               font=F_CAP, fill=colour)
        y += 30
    return im


def _ease(u):
    return u * u * (3.0 - 2.0 * u)


def _box(img, cx, cy, w):
    """A crop box of the picture's aspect, centred on (cx, cy), clamped."""
    h = w * CH / float(W)
    w = min(w, img.width)
    h = min(h, img.height)
    x = min(max(cx - w / 2.0, 0), img.width - w)
    y = min(max(cy - h / 2.0, 0), img.height - h)
    return (x, y, x + w, y + h)


def establish(frames, img, secs, sub=None, stamp=None):
    """The whole application window, letterboxed, nothing cropped away.

    camera() fills the picture band, which means a 16:9 capture loses its top
    and bottom -- the toolbars and the status bar, which are the evidence that
    this is the program and not an export of it. The opening shot of each
    sheet fits instead of fills.
    """
    sc = min(W / float(img.width), CH / float(img.height))
    shot = img.resize((int(img.width * sc), int(img.height * sc)), Image.LANCZOS)
    im = blank()
    im.paste(shot, ((W - shot.width) // 2, (CH - shot.height) // 2))
    if stamp:
        d = ImageDraw.Draw(im)
        tw = d.textlength(stamp, font=F_SM)
        d.rectangle([W - tw - 40, 18, W - 16, 48], fill=(9, 9, 11))
        d.text((W - tw - 28, 24), stamp, font=F_SM, fill=(150, 150, 146))
    band(im, sub)
    n = max(2, int(FPS * 0.45))
    for k in range(n):
        frames.append(Image.blend(blank(), im, _ease((k + 1) / float(n))))
    for _ in range(int(FPS * max(0.0, secs - 0.45))):
        frames.append(im.copy())



def camera(frames, img, a, b, secs, sub=None, stamp=None):
    """Move across a still. a and b are (cx, cy, width) in source pixels.

    The KiCad frames are screen captures of a window nothing in this container
    can drive -- no zoom, no scroll, no menu opened on camera. Moving the crop
    is how the film looks at different parts of them. It is an edit over real
    pixels, not a re-enactment of a session that never happened.
    """
    n = max(2, int(FPS * secs))
    for k in range(n):
        u = _ease(k / float(n - 1))
        box = tuple(p + (q - p) * u for p, q in zip(_box(img, *a), _box(img, *b)))
        crop = img.crop(tuple(int(round(v)) for v in box)).resize((W, CH),
                                                                  Image.LANCZOS)
        im = blank()
        im.paste(crop, (0, 0))
        if stamp:
            d = ImageDraw.Draw(im)
            tw = d.textlength(stamp, font=F_SM)
            d.rectangle([W - tw - 40, 18, W - 16, 48], fill=(9, 9, 11))
            d.text((W - tw - 28, 24), stamp, font=F_SM, fill=(150, 150, 146))
        band(im, sub)
        frames.append(im)


def dissolve(frames, secs=0.55):
    """Hold the last frame, then let the next act cut in over it."""
    if frames[-1] is None:
        return
    a = frames[-1]
    n = max(2, int(FPS * secs))
    for k in range(n):
        frames.append(Image.blend(a, blank(), _ease((k + 1) / float(n))))


def fig_frame(fig, sub=None):
    """A matplotlib figure, drawn into the picture band with a subtitle."""
    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba())[:, :, :3]
    im = blank()
    im.paste(Image.fromarray(buf).resize((W, CH)), (0, 0))
    return band(im, sub)


def newfig():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure(figsize=(W / 100.0, CH / 100.0), dpi=100)
    fig.patch.set_facecolor("#0e0e10")
    return plt, fig


def card(frames, secs, draw_fn, sub=None, fade_in=0.5):
    """A drawn card, faded up from black, held, with its subtitle."""
    im = blank()
    draw_fn(ImageDraw.Draw(im))
    band(im, sub)
    n = max(2, int(FPS * fade_in))
    for k in range(n):
        frames.append(Image.blend(blank(), im, _ease((k + 1) / float(n))))
    for _ in range(int(FPS * max(0.0, secs - fade_in))):
        frames.append(im.copy())


def _dark_axes(ax):
    ax.set_facecolor("#0e0e10")
    for s in ax.spines.values():
        s.set_color("#4a4a4a")
    ax.tick_params(colors="#9a9a96", labelsize=11)
    ax.grid(alpha=0.18, lw=0.6, color="#8a8a8a")


ARROW = dict(arrowstyle="-|>", lw=1.6, shrinkA=0, shrinkB=5)


# ----------------------------------------------------------------- scenes ---
def scene_kicad(frames, png, stamp, opening, moves, poster=None):
    img = Image.open(os.path.join(RES, png)).convert("RGB")
    establish(frames, img, opening[0], sub=opening[1], stamp=stamp)
    if poster:
        # Save the ESTABLISHING frame, not whatever is last. The poster used
        # to be taken after the whole scene, which ends in a dissolve -- so
        # the deck's demo slide showed a black rectangle until it was clicked.
        save_poster(frames[-1], poster)
    for a, b, secs, sub in moves:
        camera(frames, img, a, b, secs, sub=sub, stamp=stamp)
    dissolve(frames)


def save_poster(im, path):
    """The still the deck shows before the film is played."""
    im.save(path)
    lum = float(np.asarray(im.convert("L")).mean())
    if lum < 40:
        raise SystemExit("poster frame is almost black (mean luminance %.0f) "
                         "-- the demo slide would show a black rectangle. "
                         "It is being taken from the wrong frame." % lum)
    print("  poster:  %s   (mean luminance %.0f)" % (path, lum))


def scene_software(frames, ver, secs=7.5):
    rows = [("the schematic", "KiCad %s" % ver[1], "the window you just watched", BLU),
            ("the simulation", ver[0], "ngspice -b sim/dpt.cir    "
                                       "ngspice -b sim/buck.cir", GRN),
            ("the device", "models/egan.lib", "eGaN HEMT, junction-diode C_GD, "
                                              "temperature-derated", INK),
            ("our driver", "models/segdrv.lib", "8 pull-up + 8 pull-down slices, "
                                                "clamp, off rail", INK),
            ("their driver", "models/zhangdrv.lib", "Zhang et al., ISPSD 2020", YEL)]

    def draw(d):
        d.text((90, 120), "What drew it, and what ran it", font=F_H1, fill=INK)
        y = 250
        for lab, name, detail, col in rows:
            d.text((90, y), lab, font=F_SM, fill=FAINT)
            d.text((90, y + 24), name, font=F_H3, fill=col)
            d.text((560, y + 26), detail, font=F_CODE, fill=MUT)
            y += 92
    card(frames, secs, draw,
         "Two programs and four model files. Nothing here is a drawing of "
         "something else — the sheet and the netlist describe one circuit.")
    dissolve(frames)


def scene_terminal(frames, cmd, out, sub, keep=16):
    lines = [l.rstrip() for l in out.splitlines() if l.strip()][:keep]
    base = blank()
    d = ImageDraw.Draw(base)
    d.text((60, 70), "the simulator, running", font=F_H2, fill=INK)
    d.text((60, 118), "ngspice's own output, captured while this film was "
                      "being built", font=F_SM, fill=MUT)
    d.text((60, 178), "$ " + cmd, font=F_CODE_B, fill=GRN)
    band(base, sub)
    frames.append(base.copy())
    for _ in range(int(FPS * 1.0)):
        frames.append(base.copy())
    for k in range(1, len(lines) + 1):
        im = base.copy()
        dd = ImageDraw.Draw(im)
        y = 228
        for ln in lines[:k]:
            col = YEL if ("vspur" in ln.lower() or "margin" in ln.lower()) else INK
            dd.text((60, y), ln[:108], font=F_CODE, fill=col)
            y += 25
        for _ in range(max(1, int(FPS * 0.055))):
            frames.append(im)
    for _ in range(int(FPS * 1.4)):
        frames.append(frames[-1].copy())
    dissolve(frames)


def scene_output(frames, t, sw, vgs, peak, secs=12.0):
    plt, _ = newfig()
    n = len(t)
    total, held = int(FPS * secs), int(FPS * 5.0)
    sweep = total - held
    i_edge = int(np.argmin(np.gradient(sw)))
    i_peak = int(np.argmax(vgs))
    for k in range(total):
        done = k >= sweep
        j = n if done else max(2, int(n * (k + 1) / float(sweep)))
        _, fig = newfig()
        gs = fig.add_gridspec(2, 1, height_ratios=[1, 1.2], hspace=0.42,
                              left=0.085, right=0.955, top=0.84, bottom=0.12)
        ax1, ax2 = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
        for ax in (ax1, ax2):
            _dark_axes(ax)
            ax.set_xlim(0, t[-1])
        ax1.plot(t[:j], sw[:j], color="#e26058", lw=2.0)
        ax1.set_ylim(-18, 132)
        ax1.set_ylabel("switch node  V(sw)   [V]", color="#e8e8e6", fontsize=12)
        ax1.set_title("the output, and what to look at in it", color="#6ca8ee",
                      fontsize=16, fontweight="bold", loc="left", pad=14)
        ax2.plot(t[:j], vgs[:j], color="#6ed696", lw=2.4)
        ax2.axhline(VTH, color="#ebbe5a", lw=1.6, ls="--")
        ax2.set_ylim(-2.9, 2.4)
        ax2.set_ylabel("OFF device gate  V(gs)   [V]", color="#e8e8e6", fontsize=12)
        ax2.set_xlabel("time from the switching edge   [ns]", color="#e8e8e6",
                       fontsize=12)
        if done:
            ax1.annotate("the bus collapses here — this edge is the cause",
                         xy=(t[i_edge], sw[i_edge]), xytext=(t[-1] * 0.36, 110),
                         color="#e26058", fontsize=13, fontweight="bold",
                         arrowprops=dict(color="#e26058", **ARROW))
            ax2.annotate("worst the gate reaches: %s V"
                         % ("%+.3f" % peak).replace("-", "−"),
                         xy=(t[i_peak], vgs[i_peak]), xytext=(t[-1] * 0.38, 0.45),
                         color="#6ed696", fontsize=13, fontweight="bold",
                         arrowprops=dict(color="#6ed696", **ARROW))
            ax2.annotate("threshold 1.400 V — above this the device turns "
                         "itself on", xy=(t[-1] * 0.10, VTH),
                         xytext=(t[-1] * 0.10, 1.85), color="#ebbe5a",
                         fontsize=13, fontweight="bold",
                         arrowprops=dict(color="#ebbe5a", **ARROW))
            xm = t[-1] * 0.82
            ax2.annotate("", xy=(xm, VTH), xytext=(xm, peak),
                         arrowprops=dict(arrowstyle="<->", color="#e8e8e6", lw=1.6))
            ax2.text(xm - t[-1] * 0.015, (VTH + peak) / 2.0,
                     "%.3f V of margin" % (VTH - peak), color="#e8e8e6",
                     fontsize=13, fontweight="bold", ha="right", va="center")
        frames.append(fig_frame(
            fig, "The edge on top is the cause. Under it is the other "
                 "device's gate: it has to stay below 1.400 V, and it "
                 "clears that by %.3f V." % (VTH - peak)))
        plt.close(fig)
    dissolve(frames)


def scene_converter(frames, d, m, secs=9.5):
    plt, _ = newfig()
    t, vsw, vout, il = d[:, 0], d[:, 5], d[:, 7], d[:, 9]
    tsw = 1.0 / 500e3
    win = t >= t[-1] - 3 * tsw
    tw = (t[win] - t[win][0]) * 1e6
    vsw_w, il_w = vsw[win], il[win]
    nf, nw = len(t), len(tw)
    total, held = int(FPS * secs), int(FPS * 4.5)
    sweep = total - held
    for k in range(total):
        done = k >= sweep
        f = 1.0 if done else (k + 1) / float(sweep)
        jf, jw = (nf, nw) if done else (max(2, int(nf * f)), max(2, int(nw * f)))
        _, fig = newfig()
        gs = fig.add_gridspec(2, 2, hspace=0.50, wspace=0.22, left=0.075,
                              right=0.965, top=0.83, bottom=0.12)
        ax1, ax2 = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1])
        ax3, ax4 = fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])
        for ax in (ax1, ax2, ax3, ax4):
            _dark_axes(ax)
        ax1.plot(t[:jf] * 1e6, vout[:jf], color="#6ca8ee", lw=1.8)
        ax1.axhline(m["Vout"], color="#ebbe5a", lw=1.3, ls="--")
        ax1.set_xlim(0, t[-1] * 1e6)
        ax1.set_ylim(-4, 82)
        ax1.set_title("output voltage, whole run", color="#e8e8e6", fontsize=13,
                      fontweight="bold", loc="left", pad=8)
        ax1.set_ylabel("V(out)  [V]", color="#e8e8e6", fontsize=11)
        ax1.set_xlabel("time  [us]", color="#9a9a96", fontsize=10.5)
        if done:
            ax1.annotate("settles at %.2f V" % m["Vout"],
                         xy=(t[-1] * 1e6 * 0.78, m["Vout"]),
                         xytext=(t[-1] * 1e6 * 0.28, 70), color="#ebbe5a",
                         fontsize=12, fontweight="bold",
                         arrowprops=dict(color="#ebbe5a", **ARROW))
        ax2.plot(tw[:jw], vsw_w[:jw], color="#e26058", lw=1.4)
        ax2.axhline(m["Vin"], color="#9a9a96", lw=1.0, ls=(0, (4, 4)))
        ax2.set_xlim(0, tw[-1])
        ax2.set_ylim(-14, m["sw_pk"] + 24)
        ax2.set_title("switch node, three settled cycles", color="#e8e8e6",
                      fontsize=13, fontweight="bold", loc="left", pad=8)
        ax2.set_ylabel("V(sw)  [V]", color="#e8e8e6", fontsize=11)
        ax2.set_xlabel("time  [us]", color="#9a9a96", fontsize=10.5)
        if done:
            ip = int(np.argmax(vsw_w))
            ax2.annotate("peaks %.1f V on a %.0f V bus" % (m["sw_pk"], m["Vin"]),
                         xy=(tw[ip], vsw_w[ip]),
                         xytext=(tw[-1] * 0.26, m["sw_pk"] + 15),
                         color="#e26058", fontsize=12, fontweight="bold",
                         arrowprops=dict(color="#e26058", **ARROW))
        ax3.plot(tw[:jw], il_w[:jw], color="#6ed696", lw=1.6)
        ax3.axhline(m["Iout"], color="#ebbe5a", lw=1.3, ls="--")
        ax3.set_xlim(0, tw[-1])
        ax3.set_ylim(3.0, 7.2)
        ax3.set_title("inductor current", color="#e8e8e6", fontsize=13,
                      fontweight="bold", loc="left", pad=8)
        ax3.set_ylabel("I(L)  [A]", color="#e8e8e6", fontsize=11)
        ax3.set_xlabel("time  [us]", color="#9a9a96", fontsize=10.5)
        if done:
            ax3.annotate("%.2f A ripple on %.2f A"
                         % (float(il_w.max() - il_w.min()), m["Iout"]),
                         xy=(tw[int(np.argmax(il_w))], float(il_w.max())),
                         xytext=(tw[-1] * 0.30, 6.8), color="#6ed696",
                         fontsize=12, fontweight="bold",
                         arrowprops=dict(color="#6ed696", **ARROW))
        ax4.axis("off")
        rows = [("in", "%.0f V x %.3f A = %.2f W" % (m["Vin"], m["Iin"], m["Pin"]),
                 "#e8e8e6"),
                ("out", "%.2f V x %.3f A = %.2f W"
                 % (m["Vout"], m["Iout"], m["Pout"]), "#e8e8e6"),
                ("efficiency", "%.2f %%" % m["eff"], "#6ed696"),
                ("loss", "%.3f W" % m["loss"], "#e8e8e6")]
        for i, (lab, val, col) in enumerate(
                rows[:len(rows) if done else max(1, int(len(rows) * f) + 1)]):
            yy = 0.84 - i * 0.24
            ax4.text(0.0, yy, lab, color="#9a9a96", fontsize=12,
                     transform=ax4.transAxes)
            ax4.text(0.0, yy - 0.10, val, color=col, fontsize=16,
                     fontweight="bold", transform=ax4.transAxes)
        fig.suptitle("the converter's output, delivering power", color="#6ca8ee",
                     fontsize=16, fontweight="bold", x=0.075, ha="left", y=0.94)
        frames.append(fig_frame(
            fig, "The same drivers, now switching continuously into a filter and "
                 "a 10 ohm load: %.0f V in, %.2f V out, %.2f %% efficient."
                 % (m["Vin"], m["Vout"], m["eff"])))
        plt.close(fig)
    dissolve(frames)


def scene_versus(frames, t, vgs_base, vgs_ours, pk_base, pk_ours, setting,
                 secs=11.5):
    plt, _ = newfig()
    n = len(t)
    total, held = int(FPS * secs), int(FPS * 6.0)
    sweep = total - held
    ib, io_ = int(np.argmax(vgs_base)), int(np.argmax(vgs_ours))
    for k in range(total):
        done = k >= sweep
        j = n if done else max(2, int(n * (k + 1) / float(sweep)))
        _, fig = newfig()
        ax = fig.add_axes([0.085, 0.135, 0.875, 0.665])
        _dark_axes(ax)
        ax.set_xlim(0, t[-1])
        ax.set_ylim(-2.9, 2.4)
        ax.plot(t[:j], vgs_base[:j], color="#ebbe5a", lw=2.4,
                label="base paper's driver  (%s)" % setting)
        ax.plot(t[:j], vgs_ours[:j], color="#6ed696", lw=2.4,
                label="ours  (clamp on, −2 V off rail)")
        ax.axhline(VTH, color="#e26058", lw=1.8, ls="--")
        ax.set_ylabel("OFF device gate  V(gs)   [V]", color="#e8e8e6", fontsize=13)
        ax.set_xlabel("time from the switching edge   [ns]", color="#e8e8e6",
                      fontsize=13)
        leg = ax.legend(loc="upper right", fontsize=12.5, framealpha=0.0)
        for tx in leg.get_texts():
            tx.set_color("#e8e8e6")
        fig.text(0.085, 0.915, "their driver and ours, same bench, same corner",
                 color="#6ca8ee", fontsize=16, fontweight="bold")
        fig.text(0.085, 0.868, "sim/dpt.cir verbatim at 100 V, 10 A, 25 °C. "
                               "Only the driver subcircuit is swapped.",
                 color="#8a8a85", fontsize=11.5)
        if done:
            ax.annotate("theirs peaks %+.3f V — %.3f V of margin left"
                        % (pk_base, VTH - pk_base), xy=(t[ib], vgs_base[ib]),
                        xytext=(t[-1] * 0.30, 1.85), color="#ebbe5a",
                        fontsize=13.5, fontweight="bold",
                        arrowprops=dict(color="#ebbe5a", **ARROW))
            ax.annotate("ours peaks %s V — %.3f V of margin"
                        % (("%+.3f" % pk_ours).replace("-", "−"),
                           VTH - pk_ours), xy=(t[io_], vgs_ours[io_]),
                        xytext=(t[-1] * 0.26, -2.55), color="#6ed696",
                        fontsize=13.5, fontweight="bold",
                        arrowprops=dict(color="#6ed696", **ARROW))
            ax.annotate("threshold 1.400 V", xy=(t[-1] * 0.035, VTH),
                        xytext=(t[-1] * 0.035, 2.05), color="#e26058",
                        fontsize=12.5, fontweight="bold",
                        arrowprops=dict(color="#e26058", **ARROW))
        frames.append(fig_frame(
            fig, "Same netlist, same device, same corner — only the driver "
                 "changes. Theirs ends up %.3f V under the threshold; ours "
                 "%.3f V." % (VTH - pk_base, VTH - pk_ours)))
        plt.close(fig)
    dissolve(frames)


def scene_table(frames, corners, lat, pdev, secs=9.5):
    def draw(d):
        d.text((60, 62), "Crosstalk margin at four corners", font=F_H2, fill=INK)
        d.text((60, 110), "Their driver re-optimised at EVERY corner; ours is "
                          "one fixed control word at all four.", font=F_SM, fill=MUT)
        y = 180
        for lab, x in (("corner", 90), ("base paper", 470), ("ours", 740),
                       ("ours / theirs", 980)):
            d.text((x, y), lab, font=F_SM, fill=FAINT)
        y += 34
        for name, b, o, ratio in corners:
            d.text((90, y), name, font=F_CODE, fill=INK)
            d.text((470, y), "%+.3f V" % b, font=F_CODE, fill=YEL)
            d.text((740, y), "%+.3f V" % o, font=F_CODE, fill=GRN)
            d.text((980, y), "%.1f×" % ratio, font=F_CODE_B, fill=INK)
            y += 38
        y += 26
        d.rectangle([90, y, W - 90, y + 1], fill=FAINT)
        y += 26
        d.text((90, y), "and what it costs, same converter, same GaN device",
               font=F_H3, fill=INK)
        y += 44
        for lab, b, o, unit, fmt in (
                ("propagation latency", lat[0], lat[1], "ns", "%.2f"),
                ("device dissipation", pdev[0], pdev[1], "W", "%.3f")):
            d.text((90, y), lab, font=F_CODE, fill=MUT)
            d.text((470, y), (fmt + " %s") % (b, unit), font=F_CODE, fill=YEL)
            d.text((740, y), (fmt + " %s") % (o, unit), font=F_CODE, fill=GRN)
            d.text((980, y), ("−" + fmt + " %s") % (b - o, unit),
                   font=F_CODE_B, fill=INK)
            y += 38
        d.text((90, CH - 46), "results/headtohead.txt   ·   "
                              "results/panel_metrics.csv", font=F_CODE, fill=BLU)
    card(frames, secs, draw,
         "Ratios from the unrounded margins. Their driver is given a freedom "
         "their paper does not have — a new setting at every corner — "
         "and still trails at all four.")
    dissolve(frames)


def scene_close(frames, secs=5.5):
    def draw(d):
        d.text((90, 180), "All of it regenerates", font=F_H1, fill=INK)
        rows = [("this film", "python3 scripts/demo_review2.py"),
                ("the KiCad capture", "python3 scripts/record_kicad.py"),
                ("run it live", "bash proof/LIVE-SIM.sh    "
                                "bash proof/LIVE-BUCK.sh"),
                ("every number", "results/RESULTS-SUMMARY.txt names its script")]
        y = 310
        for lab, cmd in rows:
            d.text((90, y), lab, font=F_CAP, fill=MUT)
            d.text((470, y), cmd, font=F_CODE, fill=GRN)
            y += 54
        d.text((90, 640), "github.com/Amritha902/gan-driver", font=F_CAP, fill=BLU)
    card(frames, secs, draw, "")
# ------------------------------------------------------------------ data --
def _run(netlist, tag):
    """Run one prepared deck and return (stdout, t_ns, v_sw, v_gs)."""
    dat = "/tmp/dr2_%s.dat" % tag
    netlist = netlist.replace("wrdata out.dat", "wrdata %s" % dat)
    cir = "/tmp/dr2_%s.cir" % tag
    io.open(cir, "w", encoding="utf-8").write(netlist)
    r = subprocess.run(["ngspice", "-b", cir], capture_output=True, text=True,
                       cwd=SIM, timeout=1800)
    d = np.loadtxt(dat)
    t, vsw, vhsg = d[:, 0], d[:, 1], d[:, 7]
    m = (t >= T0) & (t <= T1)
    return r.stdout, (t[m] - T0) * 1e9, vsw[m], (vhsg - vsw)[m]


def base_setting(tag="100V_10A_25C"):
    """The setting scripts/headtohead.py found BEST for their driver here.

    Read from the file that search wrote, not chosen here -- running their
    driver at a setting picked by us would make the comparison ours to lose.
    """
    txt = io.open(os.path.join(RES, "headtohead.txt"), encoding="utf-8").read()
    m = re.search(r"^%s base .*\(nseg=(\d+) tstep=(\S+?)\) ours" % tag,
                  txt, re.M)
    if not m:
        raise SystemExit("headtohead.txt: no row for %s -- run "
                         "scripts/headtohead.py" % tag)
    return int(m.group(1)), m.group(2)


def corner_rows():
    """Every corner's margin, both drivers, and the ratio between them.

    The margins come from results/headtohead.txt, which prints them to three
    decimals. The RATIO does not: headtohead.py divides the unrounded margins,
    and at 200V_2A_125C that is 8.9x where 2.309 / 0.261 is 8.8x. Recomputing
    it here from the rounded figures would put a number on screen that
    contradicts results/RESULTS-SUMMARY.txt, so the ratios are read from that
    file instead -- the project's own record of what headtohead.py computed.
    """
    txt = io.open(os.path.join(RES, "headtohead.txt"), encoding="utf-8").read()
    rows = []
    for m in re.finditer(r"^(\S+) base ([+-][\d.]+) V \(nseg=\d+ tstep=\S+?\) "
                         r"ours ([+-][\d.]+) V", txt, re.M):
        rows.append([m.group(1), float(m.group(2)), float(m.group(3))])
    if len(rows) != 4:
        raise SystemExit("headtohead.txt: expected 4 corners, parsed %d"
                         % len(rows))

    sm = io.open(os.path.join(RES, "RESULTS-SUMMARY.txt"), encoding="utf-8").read()
    m = re.search(r"crosstalk margin, ours vs base paper, four corners\s+"
                  r"([\d.]+)x / ([\d.]+)x / ([\d.]+)x / ([\d.]+)x", sm)
    if not m:
        raise SystemExit("RESULTS-SUMMARY.txt: the four head-to-head ratios "
                         "are not where this expects them")
    for row, r in zip(rows, m.groups()):
        row.append(float(r))
    return [tuple(r) for r in rows]



def panel_pair(field):
    """(base paper, ours) for one column of results/panel_metrics.csv."""
    rows = {r["config"]: r for r in
            csv.DictReader(io.open(os.path.join(RES, "panel_metrics.csv")))}
    return float(rows["gan_base"][field]), float(rows["gan_ours"][field])

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



def kicad_version():
    out = subprocess.run(["kicad-cli", "version"], capture_output=True, text=True)
    return (out.stdout + out.stderr).strip().split()[0][:12] or "7.0"


def main():
    import bucksim
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    import headtohead as H

    for png in ("kicad_buck.png", "kicad_segdrv.png"):
        if not os.path.exists(os.path.join(RES, png)):
            raise SystemExit("results/%s missing -- run "
                             "scripts/record_kicad.py first" % png)

    ver = subprocess.run(["ngspice", "-v"], capture_output=True, text=True)
    ng = next((l.strip().lstrip("*").strip()
               for l in (ver.stdout + ver.stderr).split("\n")
               if "ngspice-" in l), "ngspice").split(":")[0].strip()[:24]
    kv = kicad_version()

    nseg, tstep = base_setting()
    setting = "nseg=%d, tstep=%s" % (nseg, tstep)
    print("  the film's data, measured now:")
    print("    our driver, 100 V / 10 A / 25 C ...")
    out_ours, t, sw, vgs_ours = _run(H.deck(100, 10, 25), "ours")
    print("    the base paper's driver, same bench, %s ..." % setting)
    _, tb, swb, vgs_base = _run(H.deck(100, 10, 25, base=(nseg, tstep)), "base")
    n = min(len(t), len(tb))
    t, sw, vgs_ours, vgs_base = t[:n], sw[:n], vgs_ours[:n], vgs_base[:n]
    pk_ours, pk_base = float(np.max(vgs_ours)), float(np.max(vgs_base))
    print("      ours %+.4f V   theirs %+.4f V   (threshold %.3f V)"
          % (pk_ours, pk_base, VTH))

    print("    the converter, 150 switching cycles ...")
    bd, bp = bucksim.run_raw(CLKEN=1, VNEG=-2)
    if bd is None:
        raise SystemExit("the converter run produced no output")
    bm = bucksim.metrics(bd, bp)
    print("      %.2f V out, %.2f W, %.2f %% efficient"
          % (bm["Vout"], bm["Pout"], bm["eff"]))

    frames = Sink(OUT)
    # No title card. A demo that opens on its own name spends its first
    # seconds telling the room what the slide behind it already says.
    # The first thing on screen is the circuit.

    stamp = "screen capture · KiCad %s" % kv
    # (centre x, centre y, crop width) in the 1600x900 capture. The wide shot
    # is the whole window, so the toolbars and the hierarchy pane are in it --
    # that is the point of the shot.
    scene_kicad(frames, "kicad_buck.png", stamp,
                (3.0, "This is KiCad, open on kicad/gan_buck.kicad_sch \u2014 the "
                      "converter we simulate. Toolbars and all: the application, "
                      "not a picture of one."),
                [((1250, 540, 1800), (1250, 540, 1700), 4.6,
                  "100 V in, 48.5 V out at 500 kHz. Every value on the sheet is "
                  "read out of the netlist when it is drawn."),
                 ((1250, 540, 1700), (1430, 580, 1050), 4.6,
                  "The half-bridge: two GaN HEMTs, the damped bus decoupling "
                  "branch to their left, the output filter and the load to "
                  "their right.")],
                poster=POSTER)
    scene_kicad(frames, "kicad_segdrv.png", stamp,
                (2.8, "The same application on kicad/gan_segdrv.kicad_sch \u2014 "
                      "the gate driver we built."),
                [((1150, 560, 1700), (1130, 560, 1350), 4.6,
                  "Eight pull-up slices from the +5 V rail to the gate, eight "
                  "pull-down slices to the off rail. The drive strength is how "
                  "many are live."),
                 ((1130, 560, 1350), (1480, 690, 980), 4.8,
                  "On the right, the active Miller clamp: one switch and a 0.5 "
                  "ohm resistor across the gate. The base paper has no such "
                  "path.")])


    # Their driver is not described, it is shown. kicad/gan_zhangdrv.kicad_sch
    # is generated from models/zhangdrv.lib by scripts/kicad_basepaper_sheet.py,
    # exactly as ours is generated from models/segdrv.lib -- so the two sheets
    # are comparable rather than one being a drawing and the other a claim.
    scene_kicad(frames, "kicad_zhangdrv.png", stamp,
                (3.0, "And the base paper's driver, in the same application. "
                      "Zhang et al., ISPSD 2020 \u2014 our reimplementation of "
                      "it, from their paper."),
                [((1280, 660, 1950), (1280, 620, 1750), 4.4,
                  "Seven slices per bank, engaged in two stages rather than one "
                  "\u2014 fourteen columns where ours has eight."),
                 ((1280, 620, 1750), (1500, 900, 1300), 4.8,
                  "And what is not here: no clamp column, and VN tied to the "
                  "local reference \u2014 no negative off rail. That absence is "
                  "the comparison.")])


    scene_software(frames, (ng, kv))
    scene_terminal(frames,
                   "ngspice -b dpt.cir      # our driver, 100 V / 10 A / 25 °C",
                   out_ours,
                   "No transcript and no re-enactment — this is what the "
                   "simulator printed while the film was being assembled.")

    scene_output(frames, t, sw, vgs_ours, pk_ours)
    scene_converter(frames, bd, bm)
    scene_versus(frames, t, vgs_base, vgs_ours, pk_base, pk_ours, setting)
    scene_table(frames, corner_rows(), panel_pair("latency_ns"),
                panel_pair("p_dev_W"))
    scene_close(frames)

    with io.open(SIDE, "w", encoding="utf-8") as fh:
        fh.write(u"# written by scripts/demo_review2.py -- do not edit by hand\n")
        fh.write(u"frames        %d\n" % len(frames))
        fh.write(u"fps           %d\n" % FPS)
        fh.write(u"duration_s    %.1f\n" % (len(frames) / float(FPS)))
        fh.write(u"parts         4\n")
        fh.write(u"kicad         %s\n" % kv)
        fh.write(u"ngspice       %s\n" % ng)
        fh.write(u"ours_peak     %+.4f\n" % pk_ours)
        fh.write(u"ours_margin   %+.4f\n" % (VTH - pk_ours))
        fh.write(u"base_peak     %+.4f\n" % pk_base)
        fh.write(u"base_margin   %+.4f\n" % (VTH - pk_base))
        fh.write(u"base_setting  %s\n" % setting.replace(", ", " "))
        fh.write(u"conv_vout     %.4f\n" % bm["Vout"])
        fh.write(u"conv_pout     %.4f\n" % bm["Pout"])
        fh.write(u"conv_eff      %.4f\n" % bm["eff"])
    print("  sidecar: %s" % SIDE)

    nf = len(frames)
    print("  %d frames, %.1f s at %d fps" % (nf, nf / float(FPS), FPS))
    rc = frames.close()
    print("  %s: %s  (%.1f MB)"
          % ("written" if rc == 0 else "ffmpeg FAILED", OUT,
             os.path.getsize(OUT) / 1e6 if rc == 0 else 0))
    return rc


if __name__ == "__main__":
    sys.exit(main())
