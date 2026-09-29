# -*- coding: utf-8 -*-
"""layout_pass.py -- give the text-only slides some structure.

    python3 review/layout_pass.py

Slides 2, 3 and 19 carry no figure, and they were a single box of bulleted
text from edge to edge. Everything was on them and none of it was findable:
the section labels sat in the same weight and colour as the sentences under
them, so "Problem Statement", "Existing Solutions" and "Research Gap" read as
one grey wall. A reviewer skimming for the gap could not see where it started.

Nothing here changes a word or a number. It changes three things:

  the labels   the run that ends in a colon becomes the deck's title blue,
               a point larger, with air above it and no bullet -- so the
               sections separate without a single extra word
  the bullets  removed from the body: under a heading that already separates
               the sections, a dash before every sentence only supplies the
               rhythm of a machine-written deck

check_consistency.py reads bolded figures out of the deck, so bold is left
exactly as it was -- only colour, size, spacing and bullets move.
"""
import os
import sys

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Emu, Inches, Pt

HERE = os.path.dirname(os.path.abspath(__file__))

DECKS = ["GaN_Review2_PRESENT.pptx", "GaN_Review2_BACKUP.pptx",
         "Review2_GaN_Segmented_Gate_Driver.pptx"]

ACCENT = RGBColor(0x1D, 0x2F, 0x82)      # the title blue already in the deck
BAR_W = Inches(0.07)
BAR_X = Inches(0.60)                     # the left edge the titles sit on
BODY_X = Inches(0.84)                    # body moves right of the bar
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def needed_inches(shape):
    """Roughly how tall the text in this box wants to be.

    The same estimate rebuild_pass.py uses for its own overflow check, kept
    deliberately identical in shape: characters times a nominal width, over
    the usable column, times line height, plus the paragraph spacing. It is
    approximate, and it only has to be good enough to notice that a slide has
    stopped fitting.
    """
    w = Emu(shape.width).inches
    need = 0.0
    for pa in shape.text_frame.paragraphs:
        txt = "".join(r.text for r in pa.runs)
        if not txt:
            continue
        szs = [r.font.size.pt for r in pa.runs if r.font.size]
        sz = max(szs) if szs else 15.0
        pPr = pa._p.find(A + "pPr")
        marL = pPr.get("marL") if pPr is not None else None
        ind = (int(marL) / 914400.0) if marL else 0.0
        avail = max(0.5, w - ind)
        cw = sz * 0.50 / 72.0
        lines = max(1, int(len(txt) * cw / avail) +
                    (1 if (len(txt) * cw) % avail else 0))
        spc = 0.0
        if pPr is not None:
            for tag in ("spcAft", "spcBef"):
                el = pPr.find(A + tag)
                if el is not None and len(el):
                    v = el[0].get("val")
                    if v:
                        spc += int(v) / 100.0 / 72.0
        need += lines * sz * 1.22 / 72.0 + spc
    return need


def shrink_runs(shape, delta):
    for pa in shape.text_frame.paragraphs:
        for r in pa.runs:
            if r.font.size:
                r.font.size = Pt(max(9.0, r.font.size.pt - delta))


# A title is one line of 28 pt in a 0.75 in box. Two lines need about 0.78 in,
# so any title long enough to wrap spills out of the bottom of its own box and
# lands on the lead line underneath. Slides 10, 11 and 15 each had their second
# line printed through the sentence below it. Shrink the title until it fits on
# one line instead -- 24 pt still reads from the back of a room, and a title
# that has to shrink is a title worth shortening anyway.
#
# 0.58 is the average character width of bold Calibri as a fraction of point
# size, fitted to this deck: "Head to head with the base paper" (31 characters)
# fits on one line at 28 pt and "Silicon, the base paper, and ours - six
# parameters" (49) does not, which brackets it between 0.55 and 0.87.
CHAR_W = 0.58
TITLE_FLOOR = 22.0
# A linear character-width model lands within a few per cent, which is not
# enough when the answer sits on the boundary: "Ours, simulated - same bench,
# same corner, same axes" was computed to need 10.47 in of a 10.50 in box at
# 25 pt, and wrapped anyway. Leave 8 % of the box spare.
TITLE_SLACK = 0.92


def fit_titles(prs):
    """Shrink any title that would wrap, so it cannot print over the lead."""
    fixed = []
    for sl in prs.slides:
        title = None
        for sh in sl.shapes:
            if (sh.has_text_frame and sh.width and sh.top is not None
                    and abs(Emu(sh.width).inches - 10.5) < 0.35
                    and Emu(sh.top).inches < 1.0):
                title = sh
                break
        if title is None:
            continue
        txt = title.text_frame.text.strip()
        runs = [r for pa in title.text_frame.paragraphs for r in pa.runs]
        if not txt or not runs:
            continue
        w = Emu(title.width).inches
        sz = runs[0].font.size.pt if runs[0].font.size else 28.0
        start = sz
        while sz > TITLE_FLOOR and len(txt) * sz * CHAR_W / 72.0 > w * TITLE_SLACK:
            sz -= 1.0
        if sz < start:
            for r in runs:
                r.font.size = Pt(sz)
            fixed.append((txt[:38], start, sz))
    return fixed


def is_label(para):
    """A section heading: a short bold line that ends in a colon."""
    txt = "".join(r.text for r in para.runs).strip()
    if not txt.endswith(":") or len(txt) > 42:
        return False
    return any(r.font.bold for r in para.runs)


def space_before(para, hundredths):
    """spcBef in hundredths of a point, without disturbing spcAft."""
    pPr = para._p.get_or_add_pPr()
    for tag in (A + "spcBef",):
        for el in pPr.findall(tag):
            pPr.remove(el)
    from lxml import etree
    el = etree.SubElement(pPr, A + "spcBef")
    pts = etree.SubElement(el, A + "spcPts")
    pts.set("val", str(hundredths))
    # spcBef must precede spcAft in the schema
    sa = pPr.find(A + "spcAft")
    if sa is not None:
        pPr.remove(el)
        sa.addprevious(el)


def no_bullet(para):
    pPr = para._p.get_or_add_pPr()
    for tag in ("buChar", "buAutoNum", "buNone"):
        for el in pPr.findall(A + tag):
            pPr.remove(el)
    from lxml import etree
    etree.SubElement(pPr, A + "buNone")
    pPr.set("marL", "0")
    pPr.set("indent", "0")


def body_box(slide):
    """The one big text box on a text-only slide, if there is one."""
    best, area = None, 0.0
    for sh in slide.shapes:
        if not sh.has_text_frame or not sh.width or not sh.height:
            continue
        if len(sh.text_frame.text.strip()) < 120:
            continue
        a = Emu(sh.width).inches * Emu(sh.height).inches
        if a > area:
            best, area = sh, a
    return best


def has_picture(slide):
    for sh in slide.shapes:
        if sh._element.find(".//" + A + "blip") is not None:
            return True
    return False


def add_bar(slide, top, height):
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, BAR_X, top,
                                 BAR_W, height)
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT
    bar.line.fill.background()
    bar.shadow.inherit = False
    # behind nothing in particular, but never over the text
    slide.shapes._spTree.remove(bar._element)
    slide.shapes._spTree.insert(2, bar._element)
    return bar


def style(prs):
    labels = bars = 0
    for sl in prs.slides:
        if has_picture(sl):
            continue                      # figure slides are already anchored
        body = body_box(sl)
        if body is None:
            continue

        heads = [pa for pa in body.text_frame.paragraphs if is_label(pa)]
        if not heads:
            continue
        for para in heads:
            labels += 1
            no_bullet(para)
            for r in para.runs:
                r.font.color.rgb = ACCENT
                if r.font.size:
                    r.font.size = Pt(r.font.size.pt + 1)

        # Take the bullets off the body as well. A bold label, a dash, one
        # sentence, repeated four times down the slide, is the house style of
        # every deck a machine has ever written -- and three of these four
        # "lists" were a single sentence wearing a bullet. Under a heading
        # that is already doing the separating, the dash adds nothing but
        # that rhythm. The numbered steps keep their numbers, which is what a
        # reader follows anyway.
        for para in body.text_frame.paragraphs:
            if para in heads:
                continue
            if not "".join(r.text for r in para.runs).strip():
                continue
            no_bullet(para)
            para._p.get_or_add_pPr().set("marL", str(int(0.16 * 914400)))

        # Air between sections is the whole point, but a slide that has just
        # enough room for its words has none to spare: the first version put
        # 7 pt above every heading and pushed the last line of slide 3 off
        # the bottom edge. Take as much space as fits, then give back font
        # size only if even the tightest spacing overflows.
        room = Emu(body.height).inches
        for gap in (700, 550, 400, 250, 120):
            for para in heads:
                space_before(para, gap)
            if needed_inches(body) <= room:
                break
        for _ in range(6):
            if needed_inches(body) <= room:
                break
            shrink_runs(body, 0.5)
        if needed_inches(body) > room:
            print("     WARNING: %s still overflows its box"
                  % body.text_frame.text.strip()[:40])

        if Emu(body.left).inches < Emu(BODY_X).inches - 0.01:
            shift = BODY_X - body.left
            body.left = BODY_X
            body.width = max(Inches(1.0), body.width - shift)
    return labels, bars


def main():
    total_l = total_b = 0
    for name in DECKS:
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            continue
        prs = Presentation(path)
        for txt, was, now in fit_titles(prs):
            print("     title shrunk %.0f -> %.0f pt so it stays on one line: %r"
                  % (was, now, txt))
        l, b = style(prs)
        prs.save(path)
        total_l += l
        total_b += b
        print("  %-42s %2d section label(s), %d bar(s)" % (name, l, b))
    print("  %d label(s), %d bar(s) across %d deck(s)"
          % (total_l, total_b, len(DECKS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
