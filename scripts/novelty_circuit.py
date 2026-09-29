# -*- coding: utf-8 -*-
"""novelty_circuit.py -- what differs in the circuit, theirs and ours.

    python3 scripts/novelty_circuit.py       -> results/fig_novelty_circuit.png

THREE PANELS, TOP TO BOTTOM
  1  the converter    where the driver plugs in: HSG and LSG, the two gates
                      of the half-bridge
  2  their driver     what is behind those two gates in the base paper
  3  our driver       the same, plus the two things they do not have

WHY THE CONVERTER IS THE FIRST PANEL
  The first version showed the two driver sheets and nothing else. That
  answers "what is different about your driver" but not "what is this a
  driver FOR". The project is a buck converter with an improved gate driver;
  a figure about the difference that never shows the converter leaves a reviewer
  to take on trust that the sheets below are wired into anything.

WHAT IT IS MADE FROM
  The three eeschema screen captures scripts/record_kicad.py takes, of sheets
  generated from sim/buck.cir, models/zhangdrv.lib and models/segdrv.lib.
  Nothing is redrawn: the rings and labels are painted over real screenshots.

TWO THINGS IT DELIBERATELY DOES NOT DO
  It does not ring empty space. An earlier version ringed what it took to be
  the margin where a clamp would go; that space was not empty, because their
  columns run further right than the crop assumed, so it ringed seven of
  their slices and captioned them "no clamp branch". Their absence is stated
  in the header and shown by ringing THEIR OWN rail label instead.

  It does not compare sizes. The three sheets open at different zoom levels
  in eeschema, so this is a presence-and-absence comparison only.
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
GRN, RED, BLU = (20, 122, 88), (198, 58, 52), (32, 92, 176)
PAD = 34

# (capture, crop box in the 2560x1440 screen grab)
# wide and tall enough to hold both driver sub-sheets as well as the
# half-bridge -- the point of this panel is now that the driver is IN the
# converter drawing, not beside it
CONV = ("kicad_buck.png", (575, 385, 1900, 785))
THEIRS = ("kicad_zhangdrv.png", (490, 230, 2120, 1150))
OURS = ("kicad_segdrv.png", (490, 240, 1760, 900))

# Regions of interest, in full-capture coordinates.
# Measured off the rendered figure and converted back through the crop and
# scale, not guessed: the first pair sat about 80 capture-pixels high and
# ringed empty sheet just above each label.
# the two hierarchical sheet instances, as eeschema draws them
# Wide enough to enclose the sheet NAME above the box and the Sheetfile
# line below it; drawn tight to the body, the ring struck through both.
CONV_HS = (700, 386, 932, 545)           # "Gate driver - high side"
CONV_LS = (700, 610, 932, 775)           # "Gate driver - low side"
THEIR_RAIL = (505, 1068, 840, 1128)      # "VN (tied to ref - NO negative rail)"
OUR_CLAMP = (1495, 555, 1700, 800)       # the Sclk + Rclk column
OUR_RAIL = (505, 800, 900, 860)          # "VN (off rail: 0 V or -2 V)"


def font(px, bold=False):
    p = ("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf"
         % ("-Bold" if bold else ""))
    return ImageFont.truetype(p, px) if os.path.exists(p) else ImageFont.load_default()


F_H, F_S, F_T, F_N = font(38, True), font(24), font(26, True), font(22, True)


def main():
    for spec in (CONV, THEIRS, OURS):
        if not os.path.exists(os.path.join(RES, spec[0])):
            raise SystemExit("results/%s missing -- run "
                             "scripts/record_kicad.py first" % spec[0])

    iw = W - 2 * PAD
    cw = (iw - 30) // 2                      # a driver column

    def panel(spec, width):
        src = Image.open(os.path.join(RES, spec[0])).convert("RGB").crop(spec[1])
        sc = width / float(src.width)
        return src.resize((width, int(src.height * sc)), Image.LANCZOS), sc, spec[1]

    # Three panels stacked at full width made a 2000 x 3757 image, and place()
    # scales a figure to the slide's HEIGHT -- so on a 13.33 in slide that
    # lands about 2.5 in wide and nothing on it can be read. The converter is
    # a wide strip across the top and the two drivers sit side by side under
    # it, which gets the aspect to something a slide can use.
    c, sc_c, crop_c = panel(CONV, iw)
    a_im, sc_a, crop_a = panel(THEIRS, cw)
    b_im, sc_b, crop_b = panel(OURS, cw)

    head_h, sub_h, gap = 86, 70, 30
    H = (head_h + c.height + gap + sub_h + max(a_im.height, b_im.height)
         + 96 + 3 * PAD)
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)

    def ring(box, colour, label, below=True):
        d.rounded_rectangle(box, radius=12, outline=colour, width=5)
        tw = d.textlength(label, font=F_N)
        x = min(max(box[0] + (box[2] - box[0] - tw) / 2.0, PAD), W - PAD - tw)
        yy = box[3] + 10 if below else box[1] - 34
        d.rectangle([x - 9, yy - 4, x + tw + 9, yy + 27], fill=BG)
        d.text((x, yy), label, font=F_N, fill=colour)

    def region(r, sc, crop, left, top):
        return (left + int((r[0] - crop[0]) * sc), top + int((r[1] - crop[1]) * sc),
                left + int((r[2] - crop[0]) * sc), top + int((r[3] - crop[1]) * sc))

    y = PAD
    d.text((PAD, y), "THE CONVERTER", font=F_H, fill=INK)
    # measured, not a guessed offset -- at PAD + 330 the subtitle started
    # inside the word "CONVERTER"
    d.text((PAD + d.textlength("THE CONVERTER", font=F_H) + 26, y + 12),
           u"sim/buck.cir  \u00b7  100 V in, 48.5 V out at 500 kHz into 10 \u03a9 "
           u"\u00b7  the driver is IN it, placed twice", font=F_S, fill=MUT)
    y += head_h
    im.paste(c, (PAD, y))
    ring(region(CONV_HS, sc_c, crop_c, PAD, y), BLU,
         u"the gate driver, high side", below=False)
    ring(region(CONV_LS, sc_c, crop_c, PAD, y), BLU,
         u"and again, low side \u2014 the same sheet both times", below=False)
    y += c.height + gap

    lx, rx = PAD, PAD + cw + 30
    d.text((lx, y), "THEIRS", font=F_H, fill=INK)
    d.text((lx + 172, y + 12), u"Zhang et al., ISPSD 2020", font=F_S, fill=MUT)
    d.text((lx, y + 44),
           u"seven slices a bank, two stages, the rail \u2014 and nothing else",
           font=F_S, fill=MUT)
    d.text((rx, y), "OURS", font=F_H, fill=INK)
    d.text((rx + 138, y + 12), u"models/segdrv.lib", font=F_S, fill=MUT)
    d.text((rx, y + 44),
           u"eight slices a bank, plus one column and a rail they do not have",
           font=F_S, fill=MUT)
    y += sub_h
    im.paste(a_im, (lx, y))
    im.paste(b_im, (rx, y))
    ring(region(THEIR_RAIL, sc_a, crop_a, lx, y), RED,
         u"their rail: tied to ref, 0 V")
    ring(region(OUR_CLAMP, sc_b, crop_b, rx, y), GRN, u"1. the Miller clamp",
         below=False)
    ring(region(OUR_RAIL, sc_b, crop_b, rx, y), GRN,
         u"2. the rail, selectable to \u22122 V")
    y += max(a_im.height, b_im.height) + PAD

    d.rectangle([PAD, y, W - PAD, y + 2], fill=RULE)
    y += 18
    # "THE NOVELTY IS ..." overstated it. Slide 2 of the deck lists clamping
    # the off gate and holding it at -2 V among the existing solutions,
    # citing [1]-[4]; this figure cannot then call them the novelty. What is
    # true, and is what the figure shows, is that the base paper has neither.
    lead = u"THE TWO GREEN RINGS ARE WHAT THEIRS DOES NOT HAVE."
    tail = u"Clamp +0.82 V, rail +2.01 V: \u22120.249 V becomes +2.576 V."
    d.text((PAD, y), lead, font=F_T, fill=INK)
    d.text((PAD + d.textlength(lead, font=F_T) + 20, y), tail, font=F_S, fill=GRN)

    # The footer is two strings laid side by side, so lengthening the first
    # pushes the second off the canvas -- silently, because nothing raises
    # when text is drawn past the edge. It has happened once: the numbers ran
    # to the last pixel column and the sentence was cut mid-word on the
    # slide. Measure the ink instead of trusting the arithmetic.
    import numpy as _np
    _a = _np.asarray(im.convert("L"))
    _ink = _np.where((_a < 200).sum(axis=0) > 0)[0]
    if _ink.size and im.width - (_ink.max() + 1) < PAD // 2:
        raise SystemExit(
            "%s: content reaches column %d of %d -- the footer is clipped; "
            "shorten it or drop a line" % (OUT, _ink.max(), im.width))

    im.save(OUT)
    print("  written: %s  (%d x %d, right margin %d px)"
          % (OUT, im.width, im.height,
             im.width - (_ink.max() + 1) if _ink.size else im.width))
    return 0


if __name__ == "__main__":
    sys.exit(main())
