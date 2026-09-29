# -*- coding: utf-8 -*-
"""code_listing.py -- put the custom blocks' own source on a slide.

    python3 scripts/code_listing.py
        -> results/fig_code_segdrv.png   the segmented driver
        -> results/fig_code_egan.png     the GaN HEMT model

The deck says these two files are ours and cites them by path on nearly every
slide. A reviewer asking "what did you actually write" was being sent to a
repository. These slides answer it on the screen.

The listings are excerpts with the line numbers of the real file, and the gaps
are marked, so nothing is passed off as the whole file. The text is read from
the file at build time, which means a slide cannot drift from the code it
claims to show -- it is the same rule the rest of the deck follows for
numbers.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")

INK = "#1B1F27"
COMMENT = "#6B7280"
KEY = "#1D2F82"
NUM = "#A8ADB8"
MARK = "#0B5C36"
BG = "#FBFBFD"
RULE = "#E2E5EA"

PAD, LH, FS = 26, 30, 21


def mono(size, bold=False):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono%s.ttf"
              % ("-Bold" if bold else ""),
              "/usr/share/fonts/truetype/liberation/LiberationMono%s.ttf"
              % ("-Bold" if bold else "-Regular")):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def sans(size, bold=False):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf"
              % ("-Bold" if bold else ""),):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def find(lines, needle):
    """The 1-based line number whose text starts with `needle`."""
    for i, t in enumerate(lines, 1):
        if t.startswith(needle):
            return i
    raise SystemExit("code_listing: no line starts with %r -- the file moved "
                     "under the slide" % needle)


def excerpt(path, blocks):
    """[(lineno, text)] for each block, None between them.

    A block is (anchor text, how many lines to take). Hardcoding line numbers
    put an annotation on a blank line and every number one out, because the
    file had changed since they were typed. Anchoring on the code means the
    listing follows the file instead of a memory of it.
    """
    lines = open(os.path.join(ROOT, path)).read().split("\n")
    out = []
    for i, (anchor, count) in enumerate(blocks):
        if i:
            out.append(None)
        start = find(lines, anchor)
        for n in range(start, min(start + count - 1, len(lines)) + 1):
            out.append((n, lines[n - 1].rstrip()))
    return out


def render(path, ranges, notes, out_name, title):
    rows = excerpt(path, ranges)
    f, fb, fs_ = mono(FS), mono(FS, True), sans(FS - 2)

    width = 1860
    height = PAD * 2 + 54 + len(rows) * LH
    im = Image.new("RGB", (width, height), BG)
    d = ImageDraw.Draw(im)

    d.rectangle([0, 0, width, 46], fill="#EEF1F6")
    d.text((PAD, 12), path, font=mono(FS, True), fill=KEY)
    d.text((width - PAD - d.textlength(title, font=fs_), 14), title,
           font=fs_, fill=COMMENT)
    d.line([0, 46, width, 46], fill=RULE, width=2)

    y = PAD + 46
    for row in rows:
        if row is None:
            d.text((PAD + 58, y + 2), ". . .", font=f, fill=NUM)
            y += LH
            continue
        n, text = row
        d.text((PAD, y), "%4d" % n, font=f, fill=NUM)
        colour = COMMENT if text.lstrip().startswith("*") else INK
        if text.lstrip().startswith((".subckt", ".model", ".func", ".ends")):
            colour = KEY
        d.text((PAD + 58, y), text, font=fb if colour == KEY else f,
               fill=colour)
        for key, msg in notes:
            if text.startswith(key):
                x = PAD + 58 + d.textlength(text, font=f) + 26
                d.text((x, y), "◀ " + msg, font=fs_, fill=MARK)
        y += LH

    p = os.path.join(RES, out_name)
    im.save(p)

    # A listing that runs off its own canvas is worse than no listing.
    import numpy as np
    a = np.asarray(im.convert("L"))
    col = np.where((a < 200).sum(axis=0) > 0)[0]
    if col.size and width - (col.max() + 1) < 8:
        raise SystemExit("%s: a line reaches the right edge -- shorten the "
                         "excerpt or the note" % out_name)
    print("  wrote %s  (%dx%d, %d lines from %s)"
          % (os.path.relpath(p, ROOT), im.width, im.height, len(rows), path))


def main():
    render(
        "models/segdrv.lib",
        [(".subckt SEGDRV", 1), ("Spu1 ", 3), ("* ---- pull-down bank", 3),
         ("* ---- active Miller clamp", 3), (".ends SEGDRV", 1)],
        [(".subckt SEGDRV", u"npu / npd are the 4 + 4 bits the FPGA emits"),
         ("Rpu1 ", u"in circuit when npu \u2265 1, and 1 G\u03a9 out of it when not"),
         ("Sclk ", u"the clamp: its own switch, its own timing"),
         ("Rclk ", u"0.5 \u03a9 to the off rail \u2014 where the injected charge goes")],
        "fig_code_segdrv.png",
        u"the segmented output stage we wrote")

    render(
        "models/egan.lib",
        [(".func smax", 1), (".model DGD", 2), (".subckt EGAN", 1), ("Bch ", 2)],
        [(".func smax", u"smooth max, so the solver does not stall at the kink"),
         (".model DGD", u"C_GD \u2014 the crosstalk path, as a C(V) law"),
         ("Bch ", u"one symmetric square law \u2014 reverse conduction falls out of it")],
        "fig_code_egan.png",
        u"the GaN HEMT model, written from the datasheet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
