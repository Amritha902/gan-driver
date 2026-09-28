# -*- coding: utf-8 -*-
"""novelty_circuit.py -- where the novelty is, on the circuit itself.

    python3 scripts/novelty_circuit.py       -> results/fig_novelty_circuit.png

WHY
  The architecture diagram says three blocks were added. A reviewer is
  entitled to be shown them on the circuit, and the deck could previously
  only offer two schematics side by side and an assurance that one had
  something the other did not. This rings the difference.

WHAT IT IS MADE FROM
  The two eeschema screen captures scripts/record_kicad.py takes, of sheets
  generated from models/zhangdrv.lib and models/segdrv.lib. Nothing is
  redrawn: the rings and labels are painted over real screenshots.

TWO THINGS IT DELIBERATELY DOES NOT DO
  It does not ring empty space on their sheet. The first version did, to
  mean "the clamp would go here" -- and the space was not empty, because
  their columns run further right than the crop assumed, so it ringed seven
  slices and captioned them "no clamp branch". Their absence is now stated in
  the header and shown by ringing THEIR OWN rail label, which says it in
  KiCad's rendering of their own model file.

  It does not compare sizes. The two sheets open at different zoom levels in
  eeschema, so this is a presence-and-absence comparison only, and the
  caption says so.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUT = os.path.join(RES, "fig_novelty_circuit.png")

W = 2000
BG = (252, 252, 251)
INK, MUT, RULE = (16, 16, 18), (92, 92, 88), (214, 214, 210)
GRN, RED = (20, 122, 88), (198, 58, 52)
PAD = 34

# (capture, crop box in the 2560x1440 screen grab). Their sheet is wider and
# its VN rail sits lower, so its crop runs further down than ours.
THEIRS = ("kicad_zhangdrv.png", (490, 230, 2120, 1150))
OURS = ("kicad_segdrv.png", (490, 240, 1760, 900))

# Regions of interest, in full-capture coordinates.
THEIR_RAIL = (505, 1068, 840, 1128)          # "VN (tied to ref - NO negative rail)"
OUR_CLAMP = (1495, 555, 1700, 800)           # the Sclk + Rclk column
OUR_RAIL = (505, 800, 900, 860)              # "VN (off rail: 0 V or -2 V)"


def font(px, bold=False):
    p = ("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf"
         % ("-Bold" if bold else ""))
    return ImageFont.truetype(p, px) if os.path.exists(p) else ImageFont.load_default()


F_H, F_S, F_T, F_N = font(38, True), font(24), font(26, True), font(22, True)


def main():
    for f, _ in (THEIRS, OURS):
        if not os.path.exists(os.path.join(RES, f)):
            raise SystemExit("results/%s missing -- run "
                             "scripts/record_kicad.py first" % f)

    iw = W - 2 * PAD

    def panel(spec):
        src = Image.open(os.path.join(RES, spec[0])).convert("RGB").crop(spec[1])
        sc = iw / float(src.width)
        return src.resize((iw, int(src.height * sc)), Image.LANCZOS), sc, spec[1]

    a, sc_a, crop_a = panel(THEIRS)
    b, sc_b, crop_b = panel(OURS)

    # cap_h allows for three wrapped caption blocks at two to three lines
    # each. At 190 the last line fell off the bottom of the image.
    head_h, gap, cap_h = 104, 30, 300
    H = 2 * head_h + a.height + b.height + gap + cap_h + 3 * PAD
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)

    def ring(box, colour, label):
        d.rounded_rectangle(box, radius=14, outline=colour, width=5)
        tw = d.textlength(label, font=F_N)
        x = min(max(box[0] + (box[2] - box[0] - tw) / 2.0, PAD), W - PAD - tw)
        yy = box[3] + 12
        d.rectangle([x - 10, yy - 4, x + tw + 10, yy + 28], fill=BG)
        d.text((x, yy), label, font=F_N, fill=colour)

    def region(r, sc, crop, top):
        return (PAD + int((r[0] - crop[0]) * sc), top + int((r[1] - crop[1]) * sc),
                PAD + int((r[2] - crop[0]) * sc), top + int((r[3] - crop[1]) * sc))

    def wrapped(txt, f, col, yy, lead):
        line = ""
        for wd in txt.split():
            t = (line + " " + wd).strip()
            if d.textlength(t, font=f) > W - 2 * PAD:
                d.text((PAD, yy), line, font=f, fill=col)
                yy += lead
                line = wd
            else:
                line = t
        d.text((PAD, yy), line, font=f, fill=col)
        return yy + lead

    y = PAD
    d.text((PAD, y), "THEIRS", font=F_H, fill=INK)
    d.text((PAD + 168, y + 12),
           u"Zhang et al., ISPSD 2020  ·  kicad/gan_zhangdrv.kicad_sch",
           font=F_S, fill=MUT)
    d.text((PAD, y + 56),
           u"Seven slices a bank in two stages: a pull-up bank, a pull-down "
           u"bank, the rail — and nothing else.", font=F_S, fill=MUT)
    y += head_h
    im.paste(a, (PAD, y))
    ring(region(THEIR_RAIL, sc_a, crop_a, y), RED,
         u"their off rail, in their own sheet's words")
    y += a.height + gap

    d.text((PAD, y), "OURS", font=F_H, fill=INK)
    d.text((PAD + 136, y + 12),
           u"kicad/gan_segdrv.kicad_sch  ·  same output stage",
           font=F_S, fill=MUT)
    d.text((PAD, y + 56),
           u"Eight slices a bank — and then one column their sheet does "
           u"not have, and a rail that can go below zero.", font=F_S, fill=MUT)
    y += head_h
    im.paste(b, (PAD, y))
    ring(region(OUR_CLAMP, sc_b, crop_b, y), GRN,
         u"1. the active Miller clamp — one switch, one 0.5 Ω resistor")
    ring(region(OUR_RAIL, sc_b, crop_b, y), GRN,
         u"2. the off rail, selectable to −2 V")
    y += b.height + PAD

    d.rectangle([PAD, y, W - PAD, y + 2], fill=RULE)
    y += 20
    y = wrapped(u"THE NOVELTY IS THE RINGED COLUMN AND THE RINGED RAIL. "
                u"Everything else on the two sheets is the same idea, built "
                u"the same way.", F_T, INK, y, 40)
    y += 10
    y = wrapped(u"What the two are worth: the clamp alone buys +0.82 V of "
                u"crosstalk margin, the −2 V rail a further +2.01 V. "
                u"Together, −0.249 V of margin becomes +2.576 V — "
                u"the device stops turning itself on.", F_S, GRN, y, 32)
    y += 10
    wrapped(u"Both sheets are generated from their model files and opened in "
            u"KiCad 7.0.11; these are annotated screen captures, not "
            u"redrawings. The two open at different zoom levels in eeschema, "
            u"so this is a presence-and-absence comparison and not a size "
            u"one.", F_S, MUT, y, 32)

    im.save(OUT)
    print("  written: %s  (%d x %d)" % (OUT, im.width, im.height))
    return 0


if __name__ == "__main__":
    sys.exit(main())
