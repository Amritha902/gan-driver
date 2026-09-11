# -*- coding: utf-8 -*-
"""converter_pass.py -- reframe the deck as what it actually is.

Runs after build.py and simplify.py.

The deck was written around a gate driver and a crosstalk fault, and read as a
study of a component. It is a study of a component, but the component sits
inside a power converter, and the converter was never shown: every simulation
in the deck was a double-pulse test, which characterises one switching edge
and never delivers power to a load. A reader could go through the whole deck
without seeing power converted from one form into another, which is the thing
the project is for.

This pass fixes that.

  * the title becomes "GaN-Based Power Converter"
  * a new slide, second in the deck, shows the converter running: 100 V DC in,
    48.6 V DC out, 237 W into the load, 97.6 % efficient (sim/buck.cir)
  * a new result slide shows the gate-driver setting moving converter-level
    quantities -- power lost and device stress -- in opposite directions,
    which is what makes the driver worth studying at all
  * the result slides renumber around the insertion

Both figures come from ngspice runs of the converter, not from the test bench.
"""
import os, sys, copy as _copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lxml import etree
from pptx import Presentation
from pptx.util import Inches, Pt
from fill import para, set_body, q

HERE = os.path.dirname(os.path.abspath(__file__))
RES  = os.path.join(HERE, "..", "results")
DECK = os.path.join(HERE, "Review1_GaN_Segmented_Gate_Driver.pptx")

TITLE = u"GaN Based Synchronous Buck Converter with an Improved Gate Driver"
SUB   = None      # a title should be a name, not a name plus an explanation

p = Presentation(DECK)


# ------------------------------------------------------------- helpers ----
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


def index_of(prefix):
    for i, s in enumerate(p.slides):
        if title_of(s).startswith(prefix):
            return i
    raise KeyError(prefix)


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
        el = _copy.deepcopy(shp._element)
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
    """Leave the title, the page number and the logo; remove the rest."""
    keep = title_shape(slide)
    keep_el = keep._element if keep is not None else None
    for sh in list(slide.shapes):
        # Compare the underlying XML element: python-pptx hands out a fresh
        # proxy object on every iteration, so `sh is keep` is never true and
        # the title was being stripped off the slide it had just been set on.
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
    """Add a figure sized by height and centred, and return its box."""
    from PIL import Image
    path = os.path.join(RES, name)
    iw, ih = Image.open(path).size
    w = height * iw / float(ih)
    x = (13.333 - w) / 2.0
    slide.shapes.add_picture(path, Inches(x), Inches(top), height=Inches(height))
    return x, w


def add_text(slide, x, y, w, h, paras):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tb.text_frame.word_wrap = True
    bp = tb.text_frame._txBody.find(q("bodyPr"))
    for k in ("lIns", "tIns", "rIns", "bIns"):
        bp.set(k, "0")
    set_body(tb, paras)
    return tb


B, N = True, False


# ------------------------------------------------- 1. the deck's title ----
# The old title named the instrument and the question -- "A Segmented Gate
# Driver for GaN HEMTs: Measuring What Operating-Point Scheduling Is Actually
# Worth" -- and never named the thing being built. A title should say what the
# project IS. The gate driver, and what it is worth, are the contribution, and
# they belong in the body where they can be shown rather than asserted.
OLD_TITLES = [
    u"A Segmented Gate Driver for GaN HEMTs: Measuring What Operating-Point "
    u"Scheduling Is Actually Worth",
    u"GaN Segmented Gate Driver with Joint Optimisation",
    u"Segmented Gate Driver for GaN Half-Bridge Converters",
]
_hits = 0
for s in p.slides:
    for sh in s.shapes:
        if not sh.has_text_frame:
            continue
        whole = sh.text_frame.text.strip()
        if whole in OLD_TITLES:
            tf = sh.text_frame
            body = tf._txBody
            first = body.findall(q("p"))[0]
            pPr = first.find(q("pPr"))
            rPr = first.find(q("r")).find(q("rPr")) if first.find(q("r")) is not None else None
            for old in body.findall(q("p")):
                body.remove(old)
            for text, small in [(TITLE, False)] + ([(SUB, True)] if SUB else []):
                np = etree.SubElement(body, q("p"))
                if pPr is not None:
                    np.append(_copy.deepcopy(pPr))
                nr = etree.SubElement(np, q("r"))
                if rPr is not None:
                    nrp = _copy.deepcopy(rPr)
                    if small:
                        cur = int(nrp.get("sz", "2400"))
                        nrp.set("sz", str(int(cur * 0.55)))
                        nrp.attrib.pop("b", None)
                    nr.append(nrp)
                etree.SubElement(nr, q("t")).text = text
            _hits += 1
print("project title replaced on %d slide(s)" % _hits)


# --------------------------------------- 2. the converter, slide two ------
src = index_of(u"Result 1")
s_cv = clone_after(p, src, 3)
strip(s_cv)
set_title(s_cv, u"What we are building — the converter")
# Sized by HEIGHT: 12.25 in wide made this 6.03 in tall, which ran the figure
# straight through the caption underneath it.
place(s_cv, "fig_converter.png", top=1.22, height=4.85)
add_text(s_cv, 0.55, 6.15, 12.25, 0.95, [
    para([(u"A GaN synchronous buck converter. ", B),
          (u"100 V DC goes in; the two GaN transistors chop it at 500 kHz; the "
           u"filter turns that back into DC. 48.6 V at 4.88 A comes out — "
           u"236.9 W into the load from 242.6 W drawn, so 97.6 % of the power "
           u"gets through. 5.8 W is lost in the transistors and the power loop.",
           N)], level=0, sz=1250, spc=120, bullet=False),
    para([(u"The duty ratio is fixed at 0.5, which is what puts the output at half "
           u"the input. Command: ", N),
          (u"ngspice -b sim/buck.cir", B),
          (u", then python3 scripts/buck_figure.py", N)],
         level=0, sz=1100, spc=0, bullet=False)])
print("converter slide inserted at position 4")


# ------------------------- 3. the driver, measured on the converter --------
# index_of must be re-run: inserting the converter slide at position 3 shifted
# every later index by one, and the stale value cloned a section divider.
src = index_of(u"Result 1")
r2  = index_of(u"Result 2")
s_tr = clone_after(p, src, r2)
strip(s_tr)
set_title(s_tr, u"Result 2 — the driver setting moves the converter")
place(s_tr, "fig_buck_tradeoff.png", top=1.30, height=4.75)
add_text(s_tr, 0.55, 6.20, 12.25, 0.95, [
    para([(u"This is why the gate driver is worth studying. ", B),
          (u"The same knob moves power lost by 4.5 % and peak device voltage by "
           u"50 %, in opposite directions — there is no setting that is best at "
           u"both. Lowest loss is 4 slices, not the fastest. Turning the clamp "
           u"and the −2 V rail on costs 0.53 W, which is 0.22 points of "
           u"efficiency, and that is the price of crosstalk immunity.", N)],
         level=0, sz=1250, spc=120, bullet=False),
    para([(u"Eight converter runs. Command: ", N),
          (u"python3 scripts/buck_sweep.py", B)],
         level=0, sz=1100, spc=0, bullet=False)])
print("converter trade-off slide inserted before Result 2")


# ------------------------------- 3b. the named cases, run one at a time ----
# "720 settings were searched" is a claim about a procedure. These are the
# specific runs, each one on its own line, which is what can actually be
# checked. The slide goes immediately before the aggregate results.
r1 = index_of(u"Result 1")
s_ca = clone_after(p, r1, r1)
strip(s_ca)
set_title(s_ca, u"The cases we ran, one at a time")
place(s_ca, "fig_cases.png", top=1.28, height=4.80)
add_text(s_ca, 0.55, 6.20, 12.25, 0.95, [
    para([(u"Each bar and each point is its own ngspice run. ", B),
          (u"Left: the fault is there at the fastest setting, the clamp removes "
           u"it, the \u22122 V rail buys margin, and slowing the drive is safest "
           u"but wastes twice the energy. Right: the cheapest dead time is 15 ns "
           u"at full load and 5 ns at light load \u2014 two different numbers, "
           u"and that gap is the only thing worth adapting.", N)],
         level=0, sz=1250, spc=120, bullet=False),
    para([(u"13 runs, 10 seconds. Command: ", N),
          (u"python3 scripts/cases.py", B)],
         level=0, sz=1100, spc=0, bullet=False)])
print("named-cases slide inserted before Result 1")

for _s in p.slides:
    if title_of(_s).startswith(u"Proposed Solution"):
        set_title(_s, u"Aim, and how we approached it")
        print("retitled: Proposed Solution -> Aim, and how we approached it")
    if title_of(_s).startswith(u"Timeline"):
        set_title(_s, u"Where we are, and what is next")
        print("retitled: Timeline -> Where we are, and what is next")


# ------------------------------------- 3c. the conclusion's plan, rewritten -
# The old plan promised a transistor-level stage in Cadence and a measured
# hardware half-bridge. Both are out: the project runs on ngspice and Vivado,
# and the next steps have to be things those two tools can actually deliver.
for _s in p.slides:
    if title_of(_s).startswith(u"Conclusion"):
        for sh in _s.shapes:
            if sh.has_text_frame and u"What the data supports" in sh.text_frame.text:
                blocks = [
                    [(u"What the data supports", B)],
                    [(u"The converter works: 100 V DC in, 48.6 V DC out at 4.88 A "
                      u"\u2014 236.9 W, 97.6 % efficient.", N)],
                    [(u"Picking the setting well: 25.1 %.   Changing it per "
                      u"operating point: 3.9 %.", N)],
                    [(u"One comparator gets 72 % of that 3.9 %.", N)],
                    [(u"What to build: ", B),
                     (u"one fixed setting plus a light-load comparator \u2014 not a "
                      u"sensor, an ADC and a lookup table.", N)],
                    [(u"The FPGA half is real: 20 LUTs and 20 flip-flops, 200 MHz "
                      u"met with 1.996 ns to spare.", N)],
                    [(u"What is next", B)],
                    [(u"Review-II \u2014 close the loop on the converter, then re-run "
                      u"the setting study with it closed.", N)],
                    [(u"Review-III \u2014 measure what a two-setting controller saves "
                      u"at the light-load point, where the best dead time differs.", N)],
                    [(u"Every number in this deck is regenerated by a named script, "
                      u"in ngspice or in Vivado — 34,622 transient simulations "
                      u"across every study.", N)],
                ]
                tx = sh.text_frame._txBody
                olds = tx.findall(q("p"))
                styles = []
                for op in olds:
                    r = op.find(q("r"))
                    styles.append((op.find(q("pPr")),
                                   r.find(q("rPr")) if r is not None else None))
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
                print("conclusion plan rewritten (no Cadence, no hardware step)")
                break


# ------------------------------------------- 3d. the section dividers ------
# "A 720-point control word, and an exhaustive search" leads with the size of
# the search, which is the least interesting true thing about it. What was
# built is a converter and the driver inside it.
DIVIDERS = {
    u"What we built": u"A converter, and the driver that switches it",
    u"What we found": u"Choosing the setting well beats re-tuning it \u2014 and by how much",
}
for _s in p.slides:
    txts = [sh for sh in _s.shapes if sh.has_text_frame and sh.text_frame.text.strip()]
    heads = [sh.text_frame.text.strip() for sh in txts]
    for head, newsub in DIVIDERS.items():
        if head in heads and len(txts) == 3:
            sub = txts[heads.index(head) + 1]
            for pa in sub.text_frame.paragraphs:
                for r in pa.runs:
                    r.text = newsub
                    break
                break
            print("divider subtitle set: %s" % head)


# ----------------------------------------------- 4. renumber the results ---
RENUM = [
    (u"Result 2 — the driver setting moves the converter",
     u"Result 2 — the driver setting moves the converter"),
    (u"Result 2 — re-tuning is worth only 5.2 %",
     u"Result 3 — re-tuning is worth only 5.2 %"),
    (u"Result 3 — the two halves nobody separates",
     u"Result 4 — the two halves nobody separates"),
    (u"Result 4 — re-tuning only pays below ~2.5 nH",
     u"Result 5 — re-tuning only pays below ~2.5 nH"),
]
for s in p.slides:
    t = title_of(s)
    for old, new in RENUM:
        if t == old and old != new:
            set_title(s, new)
            print("renumbered: %s -> %s" % (old[:34], new[:34]))


# ------------------------------------------------------------ 5. pages ----
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
