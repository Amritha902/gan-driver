# -*- coding: utf-8 -*-
"""kicad_previews.py -- render the KiCad sheets to trimmed PNGs for the deck.

    python3 scripts/kicad_previews.py

WHY TRIM
  The sheets are drawn on A3 and A2 with a title block and a wide margin.
  Dropped into a slide whole, the circuit ends up a third of the frame and
  unreadable from the back of a room. This renders at high dpi and then
  crops to the ink, so the circuit fills the picture.

  The title block goes with the margin. That is deliberate: the slide has
  its own title and caption, and a second title inside the image competes
  with it. The full sheets with their title blocks are in kicad/ as PDF and
  SVG for anyone who wants them.

WHY PyMuPDF AND NOT kicad-cli
  kicad-cli exports SVG and PDF, not PNG, and python-pptx needs a raster.
  This is the only place PyMuPDF is used and it is a convenience, not part
  of the schematic toolchain -- the .kicad_sch files and their PDF/SVG
  exports are produced entirely by KiCad.
"""
import os, sys, warnings
warnings.filterwarnings("ignore")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KI   = os.path.join(ROOT, "kicad")
RES  = os.path.join(ROOT, "results")

# (sheet, output, dpi, keep-top-fraction)
#
# The fourth field drops the explanatory notes block that sits under each
# circuit. On the sheet those notes belong; in a slide they pad the image
# into a tall aspect, and place() then scales the whole thing to fit the
# HEIGHT -- which put a 14-column schematic on screen 5.9 inches wide on a
# 13.3 inch slide. Cropping to the circuit gives a wide, short picture that
# fills the slide width and is legible from the back of a room. The notes
# are still on the PDF and SVG in kicad/, where someone reading can read them.
# (sheet, output, dpi, clip in SHEET MILLIMETRES: top, bottom)
#
# The clip drops the explanatory notes block under each circuit. On the sheet
# those notes belong; in a slide they pad the image into a tall aspect and
# place() then scales to fit the HEIGHT, which put a 14-column schematic on
# screen 5.9 inches wide on a 13.3 inch slide.
#
# The bounds are in millimetres of the sheet, taken from the generators' own
# rail coordinates, NOT as a fraction of the rendered image. A fraction was
# the first attempt and it cut the pull-down bank in half and lost the VN
# rail: the trimmed image starts at the title, so a fraction of it does not
# correspond to anything in the drawing. An incomplete circuit on a slide is
# worse than a small one.
#
#   segdrv  A3: rails at VP 52, OUT 112, VN 172  -> clip to 185
#   zhangdrv A2: rails at VP 60, OUT 200, VN 340 -> clip to 356
#   buck    A3: circuit runs from about 20 to 150
MM = 72.0 / 25.4          # millimetres to PDF points
SHEETS = [
    ("gan_buck",     "fig_sch_converter.png", 200,  14, 152),
    ("gan_segdrv",   "fig_sch_ours.png",      170,  14, 186),
    ("gan_zhangdrv", "fig_sch_base.png",      150,  14, 358),
]


def trim(im, bg=(255, 255, 255), tol=12):
    """Crop uniform margin off every side.

    KiCad plots on a near-white background (#F0F0EC in these exports), not
    pure white, so the test is a tolerance rather than equality -- an exact
    match trims nothing and you get the whole A2 sheet back.
    """
    from PIL import Image, ImageChops
    ref = Image.new("RGB", im.size, im.getpixel((2, 2)))
    diff = ImageChops.difference(im.convert("RGB"), ref)
    bbox = diff.convert("L").point(lambda v: 255 if v > tol else 0).getbbox()
    if not bbox:
        return im
    pad = 14
    x0, y0, x1, y1 = bbox
    return im.crop((max(0, x0 - pad), max(0, y0 - pad),
                    min(im.width, x1 + pad), min(im.height, y1 + pad)))


def main():
    import fitz
    from PIL import Image
    import io as _io
    for base, out, dpi, y0_mm, y1_mm in SHEETS:
        pdf = os.path.join(KI, base + ".pdf")
        if not os.path.exists(pdf):
            print("  MISSING: %s -- run its generator first" % pdf)
            continue
        d = fitz.open(pdf)
        page = d[0]
        clip = fitz.Rect(0, y0_mm * MM, page.rect.width, y1_mm * MM)
        pix = page.get_pixmap(dpi=dpi, clip=clip)
        im = Image.open(_io.BytesIO(pix.tobytes("png")))
        before = im.size
        im = trim(im)
        # keep the deck's pictures to a sane pixel budget
        if im.width > 3000:
            im = im.resize((3000, int(im.height * 3000.0 / im.width)),
                           Image.LANCZOS)
        p = os.path.join(RES, out)
        im.save(p)
        print("  %-22s %s -> %s  (trimmed from %dx%d)"
              % (base, str(before), str(im.size), before[0], before[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
