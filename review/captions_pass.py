# -*- coding: utf-8 -*-
"""captions_pass.py -- last pass. Runs after converter_pass.py.

Three things.

ONE. The placeholder first slide goes. It carried instructions to ourselves
about getting the title page signed and scanned; it is not part of the talk,
and leaving it in a deck that gets handed over is how it ends up on a screen
in front of a panel. The title page is now slide 1, which is where the signed
scan belongs anyway.

TWO. The title says what is being improved. "GaN Based Power Converter" names
the thing but not the work; a project title should carry the contribution.

THREE. Every figure gets the same two lines under it and no more: what is
plotted, then what it means. Captions had drifted to eighty-odd words of
prose that repeated the slide body, which is the fastest way to make a
reviewer stop reading figures altogether. Two lines, one job each.
"""
import os, sys, copy as _copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lxml import etree
from pptx import Presentation
from pptx.util import Inches
from fill import para, set_body, q

HERE = os.path.dirname(os.path.abspath(__file__))
DECK = os.path.join(HERE, "Review1_GaN_Segmented_Gate_Driver.pptx")

TITLE = u"GaN Based DC–DC Power Converter with an Improved Gate Driver"

p = Presentation(DECK)
B, N = True, False
EM, MINUS = u"—", u"−"


def title_shape(slide):
    for s in slide.shapes:
        if s.has_text_frame and s.width and abs(s.width - Inches(10.5)) < Inches(0.3) \
           and s.top is not None and s.top < Inches(1.0):
            return s
    return None


def title_of(slide):
    sh = title_shape(slide)
    return sh.text_frame.text.strip() if sh else ""


def set_title(slide, text):
    sh = title_shape(slide)
    if sh is None:
        return
    for pa in sh.text_frame.paragraphs:
        for r in pa.runs:
            r.text = text
            return


def slide_titled(prefix):
    for s in p.slides:
        if title_of(s).startswith(prefix):
            return s
    raise KeyError(prefix)


def find_by_name(slide, name):
    for sh in slide.shapes:
        if sh.name == name:
            return sh
    raise KeyError(name)


def restyle(shape, blocks):
    tx = shape.text_frame._txBody
    olds = tx.findall(q("p"))
    styles = []
    for op in olds:
        r = op.find(q("r"))
        styles.append((op.find(q("pPr")), r.find(q("rPr")) if r is not None else None))
    if not styles:
        raise RuntimeError("nothing to take style from")
    for op in olds:
        tx.remove(op)
    for i, runs in enumerate(blocks):
        pPr, rPr = styles[i] if i < len(styles) else styles[-1]
        np_ = etree.SubElement(tx, q("p"))
        if pPr is not None:
            np_.append(_copy.deepcopy(pPr))
        for text, bold in runs:
            nr = etree.SubElement(np_, q("r"))
            if rPr is not None:
                nrp = _copy.deepcopy(rPr)
                if bold:
                    nrp.set("b", "1")
                else:
                    nrp.attrib.pop("b", None)
                nr.append(nrp)
            etree.SubElement(nr, q("t")).text = text


# ------------------------------------------------- 1. drop the placeholder --
def drop(prs, idx):
    lst = prs.slides._sldIdLst
    ids = list(lst)
    rId = ids[idx].get("{http://schemas.openxmlformats.org/officeDocument/2006/"
                       "relationships}id")
    prs.part.drop_rel(rId)
    lst.remove(ids[idx])


for i, s in enumerate(p.slides):
    if title_of(s).startswith(u"Slide 1 — Scanned"):
        drop(p, i)
        print("dropped the placeholder slide; the title page is now slide 1")
        break


# ------------------------------------------------------ 2. the title -------
hits = 0
for s in p.slides:
    for sh in s.shapes:
        if not sh.has_text_frame:
            continue
        if sh.text_frame.text.strip() == u"GaN Based Power Converter":
            for pa in sh.text_frame.paragraphs:
                for r in pa.runs:
                    r.text = TITLE
                    hits += 1
                    break
                break
print("title set on %d slide(s): %s" % (hits, TITLE))


# ------------------------------------------------------ 3. the captions ----
def cap(figure, meaning):
    return [
        [(u"The figure. ", B), (figure, N)],
        [(u"What it means. ", B), (meaning, N)],
    ]


CAPTIONS = [
 (u"What we are building", "TextBox 5", cap(
   u"(a) the output charging from zero and settling; (b) three switching "
   u"cycles of the half-bridge; (c) power in against power out.",
   u"The converter works. 100 V DC becomes 48.6 V DC at 4.88 A, and 97.6 % of "
   u"the power gets through.")),

 (u"How it works", "TextBox 5", cap(
   u"One switching edge followed through. Top row: what the controller "
   u"decides. Bottom row: what the circuit then does.",
   u"The one shaded diamond is the only live decision. Everything else is set "
   u"once at power-up.")),

 (u"The circuit that is simulated", "TextBox 5", cap(
   u"The half-bridge as ngspice runs it, from sim/dpt.cir. The red path is "
   u"Cᴳᴰ on Q2.",
   u"Charge crosses that red path into the gate that should be OFF. The clamp "
   u"and the " + MINUS + u"2 V rail are what stop it.")),

 (u"The cases we ran", "TextBox 5", cap(
   u"(a) five settings at full load, each its own ngspice run; (b) the same "
   u"driver swept at two operating points.",
   u"The clamp removes the fault. The cheapest dead time is 15 ns at full load "
   u"and 5 ns at light load " + EM + u" two different numbers, and that gap is "
   u"the only thing worth adapting.")),

 (u"Result 1", "TextBox 5", cap(
   u"Voltage on the gate that is supposed to be OFF, with the fix and without.",
   u"1.65 V against a 1.4 V threshold turns the device on. The clamp and the "
   + MINUS + u"2 V rail leave 2.58 V of margin.")),

 (u"Result 2", "TextBox 5", cap(
   u"Power lost and peak device voltage against drive strength, measured on "
   u"the running converter.",
   u"They move in opposite directions, so no setting is best at both. Lowest "
   u"loss is 4 slices, not the fastest.")),

 (u"Result 5", "TextBox 5", cap(
   u"What re-tuning is worth, against the inductance of the power loop. Eight "
   u"values, 7,200 runs.",
   u"It only pays below about 2.5 nH. Loop inductance is board layout, so this "
   u"is a layout decision, not a device one.")),

 (u"Demo", "TextBox 5", cap(
   u"ngspice waveforms from sim/dpt.cir, the same file every number in this "
   u"deck comes from. Click to play, 22 s.",
   u"Left panel crosses the 1.4 V line and the device turns on. Right panel, "
   u"same circuit with the fix, peaks at " + MINUS + u"1.18 V.")),

 (u"FPGA Controller", "TextBox 6", cap(
   u"The controller's own output, captured by Icarus Verilog.",
   u"The two pull-up banks never overlap. The shaded gap is the dead time, so "
   u"no shoot-through window exists.")),
]

for prefix, name, blocks in CAPTIONS:
    try:
        s = slide_titled(prefix)
        restyle(find_by_name(s, name), blocks)
        print("caption set: %s" % prefix[:40])
    except KeyError as e:
        print("SKIPPED %-30s (%s)" % (prefix[:30], e))


# --- Result 3 and 4 carry prose blocks rather than figure captions ---------
try:
    s = slide_titled(u"Result 3")
    restyle(find_by_name(s, "TextBox 6"), cap(
        u"What one fixed setting costs at each of the four operating points.",
        u"Three points lose 1" + u"–" + u"4 %. One loses 12.7 %. So "
        u"re-tuning is worth 5.2 % at the very most."))
    print("caption set: Result 3")
except KeyError as e:
    print("SKIPPED Result 3 (%s)" % e)

try:
    s = slide_titled(u"Result 4")
    restyle(find_by_name(s, "TextBox 14"), [
        [(u"What it means. ", B),
         (u"The full sensor + ADC + lookup table is left justifying 3.7 % of "
          u"the gain, over one fixed setting plus a single comparator.", N)],
        [(u"The split does not depend on how the two goals are weighted: across "
          u"106 weightings, (A) stays 23.4" + u"–" + u"29.0 % and (B) 1.3"
          + u"–" + u"6.4 %, and (A) wins every time.", N)],
    ])
    print("caption set: Result 4")
except KeyError as e:
    print("SKIPPED Result 4 (%s)" % e)


# --- the architecture slide had no caption at all -------------------------
try:
    s = slide_titled(u"System Architecture")
    tb = s.shapes.add_textbox(Inches(0.55), Inches(6.45), Inches(12.25), Inches(0.75))
    tb.text_frame.word_wrap = True
    bp = tb.text_frame._txBody.find(q("bodyPr"))
    for k in ("lIns", "tIns", "rIns", "bIns"):
        bp.set(k, "0")
    set_body(tb, [
        para([(u"The figure. ", B),
              (u"What talks to what, left to right: the PWM command, the FPGA, "
               u"the segmented driver, the power stage.", N)],
             level=0, sz=1150, spc=60, bullet=False),
        para([(u"What it means. ", B),
              (u"Only the dashed block needs sensing, and 72 % of what it buys "
               u"needs one comparator.", N)],
             level=0, sz=1150, spc=0, bullet=False)])
    print("caption added: System Architecture")
except KeyError as e:
    print("SKIPPED System Architecture (%s)" % e)


# --------------------------------------- 4. two slides asked for directly ---
# "mark what ngspice has been used for and what LTspice for" -- and the
# waveform with its meaning written on it rather than left to be inferred.
import copy as _c


def clone_after(prs, src_idx, dest_idx):
    src = prs.slides[src_idx]
    new = prs.slides.add_slide(src.slide_layout)
    for shp in list(new.shapes):
        shp._element.getparent().remove(shp._element)
    NOTES = ("http://schemas.openxmlformats.org/officeDocument/2006/"
             "relationships/notesSlide")
    idmap = {}
    for rid, rel in src.part.rels.items():
        if rel.reltype == NOTES:
            continue
        if rel.is_external:
            idmap[rid] = new.part.rels.get_or_add_ext_rel(rel.reltype, rel.target_ref)
        else:
            idmap[rid] = new.part.relate_to(rel.target_part, rel.reltype)
    R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
    for shp in src.shapes:
        el = _c.deepcopy(shp._element)
        for node in el.iter():
            for a in ("embed", "link", "id"):
                k = R + a
                if k in node.attrib and node.attrib[k] in idmap:
                    node.attrib[k] = idmap[node.attrib[k]]
        new.shapes._spTree.append(el)
    lst = prs.slides._sldIdLst
    items = list(lst)
    lst.remove(items[-1])
    lst.insert(dest_idx, items[-1])
    return prs.slides[dest_idx]


def strip(slide):
    keep = title_shape(slide)
    keep_el = keep._element if keep is not None else None
    for sh in list(slide.shapes):
        if keep_el is not None and sh._element is keep_el:
            continue
        if sh.has_text_frame:
            t = sh.text_frame.text.strip()
            if t.isdigit() or (sh.left and sh.left > Inches(12.0)):
                continue
            sh._element.getparent().remove(sh._element)
        elif sh.shape_type is not None and sh.left and sh.left < Inches(11.0):
            sh._element.getparent().remove(sh._element)


def place(slide, name, top, height):
    from PIL import Image
    path = os.path.join(HERE, "..", "results", name)
    iw, ih = Image.open(path).size
    w = height * iw / float(ih)
    slide.shapes.add_picture(path, Inches((13.333 - w) / 2.0), Inches(top),
                             height=Inches(height))


def add_text(slide, x, y, w, h, paras):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tb.text_frame.word_wrap = True
    bp = tb.text_frame._txBody.find(q("bodyPr"))
    for k in ("lIns", "tIns", "rIns", "bIns"):
        bp.set(k, "0")
    set_body(tb, paras)


r1 = None
for i, sl in enumerate(p.slides):
    if title_of(sl).startswith(u"Result 1"):
        r1 = i
        break

if r1 is not None:
    s_lt = clone_after(p, r1, r1 + 1)
    strip(s_lt)
    set_title(s_lt, u"The same result in LTspice, on the drawn circuit")
    place(s_lt, "fig_ltspice_annotated.png", 1.28, 4.80)
    add_text(s_lt, 0.55, 6.22, 12.25, 0.90, [
        para([(u"The figure. ", B),
              (u"LTspice's own output, from the schematic in ltspice/. Top: the "
               u"switch node falling 100 V. Bottom: what that does to the gate "
               u"of the device that is supposed to be OFF.", N)],
             level=0, sz=1150, spc=60, bullet=False),
        para([(u"What it means. ", B),
              (u"A second simulator, on a drawn circuit, gets +1.6476 V and "
               u"−1.1769 V where ngspice gets +1.6486 and −1.1757. About a "
               u"millivolt apart, so the result is the circuit's, not the "
               u"simulator's.", N)],
             level=0, sz=1150, spc=0, bullet=False)])
    print("LTspice slide inserted after Result 1")

    s_tl = clone_after(p, r1, r1)
    strip(s_tl)
    set_title(s_tl, u"Which tool did what")
    place(s_tl, "fig_tools.png", 1.35, 4.70)
    add_text(s_tl, 0.55, 6.20, 12.25, 0.90, [
        para([(u"The figure. ", B),
              (u"Every circuit simulation in the study is ngspice. LTspice draws "
               u"the same circuit and re-measures the crosstalk result.", N)],
             level=0, sz=1150, spc=60, bullet=False),
        para([(u"What it means. ", B),
              (u"One tool does the work. The second exists so that no headline "
               u"number rests on a single program.", N)],
             level=0, sz=1150, spc=0, bullet=False)])
    print("tools slide inserted before Result 1")


# ------------------------------------------------------------ renumber -----
for n, s in enumerate(p.slides, start=1):
    for sh in s.shapes:
        if sh.has_text_frame and sh.left and sh.left > Inches(12.0) \
           and sh.top and sh.top > Inches(6.8):
            for pa in sh.text_frame.paragraphs:
                for r in pa.runs:
                    r.text = str(n)
            break

p.save(DECK)
print("deck now %d slides" % len(list(p.slides)))
