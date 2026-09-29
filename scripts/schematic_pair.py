# -*- coding: utf-8 -*-
"""schematic_pair.py -- the two gate driver sheets, side by side, unedited.

    python3 scripts/schematic_pair.py

Writes results/fig_schematics_pair.png.

The novelty figure (scripts/novelty_circuit.py) crops both sheets down to the
part that differs and rings it. That answers "where is the difference" and is
the right figure for that question, but it is a crop: a reviewer cannot see
what else is on either sheet, and cropping is exactly where a comparison can
be made to flatter one side.

This figure is the other half of that answer -- both sheets whole, at the
same scale, nothing ringed and nothing removed. It is deliberately plain, so
that anything it appears to show can be checked against the .kicad_sch files
it names.

Both captures come from scripts/record_kicad.py, which opens the real
eeschema on a virtual display and photographs the window, so neither is a
redrawing.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")

PANELS = [
    ("kicad_zhangdrv.png", u"BASE PAPER",
     u"kicad/gan_zhangdrv.kicad_sch", (0x1F, 0x3A, 0x5F)),
    ("kicad_segdrv.png", u"OURS",
     u"kicad/gan_segdrv.kicad_sch", (0x0B, 0x5C, 0x36)),
]

BAR = 130           # height of the label strip over each sheet
GAP = 40            # between the two panels
PAD = 28
RULE = (0xC8, 0xC8, 0xC8)


# eeschema paints its drawing area one flat colour and its toolbars another.
# Cropping to that colour drops the menus, the two tool rails and the status
# bar, which is most of the frame: the sheets themselves are what the slide
# is for, and at 12 in wide the chrome was costing about a third of the width
# they could have had.
CANVAS = np.array([245, 244, 239])


def canvas_box(im):
    """The drawing area of an eeschema window, found rather than assumed."""
    a = np.asarray(im.convert("RGB")).astype(int)
    m = np.abs(a - CANVAS).max(axis=2) <= 3
    xs = np.where(m.mean(axis=0) > 0.5)[0]
    ys = np.where(m.mean(axis=1) > 0.5)[0]
    if xs.size == 0 or ys.size == 0:
        return (0, 0, im.width, im.height)      # not a window we recognise
    box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    # A crop that keeps almost nothing means the detection was wrong, and a
    # sliver of a schematic on a slide is worse than the whole window.
    if (box[2] - box[0]) < im.width * 0.4 or (box[3] - box[1]) < im.height * 0.4:
        return (0, 0, im.width, im.height)
    return box


def font(size, bold=False):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf"
                 % ("-Bold" if bold else ""),
                 "/usr/share/fonts/truetype/liberation/LiberationSans%s.ttf"
                 % ("-Bold" if bold else "-Regular")):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def main():
    sheets = []
    for name, _, _, _ in PANELS:
        path = os.path.join(RES, name)
        if not os.path.exists(path):
            raise SystemExit("missing %s -- run scripts/record_kicad.py" % path)
        im = Image.open(path).convert("RGB")
        sheets.append(im.crop(canvas_box(im)))

    w = max(s.width for s in sheets)
    h = max(s.height for s in sheets)
    W = PAD * 2 + w * 2 + GAP
    H = PAD * 2 + BAR + h

    out = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(out)
    f_big, f_small = font(62, True), font(40)

    for i, (sheet, (_, who, path, colour)) in enumerate(zip(sheets, PANELS)):
        x = PAD + i * (w + GAP)
        d.rectangle([x, PAD, x + w, PAD + BAR], fill=colour)
        d.text((x + 26, PAD + 18), who, font=f_big, fill="white")
        tw = d.textlength(path, font=f_small)
        d.text((x + w - tw - 26, PAD + 40), path, font=f_small,
               fill=(0xDD, 0xDD, 0xDD))
        out.paste(sheet, (x, PAD + BAR))
        d.rectangle([x, PAD, x + w, PAD + BAR + sheet.height],
                    outline=RULE, width=3)

    dest = os.path.join(RES, "fig_schematics_pair.png")
    out.save(dest)

    # A capture that failed leaves a black or blank frame, and a blank frame
    # on a slide is worse than no slide. Refuse to ship one.
    grey = np.asarray(out.convert("L"))
    mean = float(grey.mean())
    if not 60 < mean < 250:
        raise SystemExit("%s: mean luminance %.0f -- capture looks wrong"
                         % (dest, mean))
    print("wrote %s  %dx%d  mean luminance %.0f"
          % (os.path.relpath(dest, ROOT), out.width, out.height, mean))


if __name__ == "__main__":
    sys.exit(main())
