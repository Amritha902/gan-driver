# -*- coding: utf-8 -*-
"""rebuild_pass.py -- final pass. Puts the deck in teaching order.

The deck could defend every number in it and still leave a reader unable to
follow it, because it never explained the things the numbers are made of:
what the device is, what a "setting" is, what the input conditions are, what
comes out, and what margin means. Someone who has to infer those is entitled
to distrust everything downstream, and that is what happened.

This adds those slides and then sets the order explicitly: problem, aim,
device, base paper, gap, then the definitions, then the story, the circuit,
the method, the tools, the demo, and only then the results.

It also replaces the circuit diagram. The old one was drawn in matplotlib and
looked like an illustration of a circuit rather than a circuit; the new one is
ltspice/BUCK_converter.asc, a drawn schematic with real wires that simulates
to 48.84 V against the netlist's 48.56 V.

ORDER below is the whole specification: anything not named in it is dropped.
"""
import os, sys, copy as _copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lxml import etree
from pptx import Presentation
from pptx.util import Inches
from fill import para, set_body, q
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
RES  = os.path.join(HERE, "..", "results")
DECK = os.path.join(HERE, "Review1_GaN_Segmented_Gate_Driver.pptx")
VIDEO = os.path.expanduser("~/GAN_MAIN/PROOF/DEMO-VIDEO.mp4")

p = Presentation(DECK)
B, N = True, False
EM, MINUS = u"—", u"−"


def title_shape(s):
    for sh in s.shapes:
        if sh.has_text_frame and sh.width and abs(sh.width - Inches(10.5)) < Inches(0.3) \
           and sh.top is not None and sh.top < Inches(1.0):
            return sh
    return None


def title_of(s):
    sh = title_shape(s)
    return sh.text_frame.text.strip() if sh else ""


def set_title(s, text):
    sh = title_shape(s)
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
    return None


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


def strip(s):
    keep = title_shape(s)
    keep_el = keep._element if keep is not None else None
    for sh in list(s.shapes):
        if keep_el is not None and sh._element is keep_el:
            continue
        if sh.has_text_frame:
            t = sh.text_frame.text.strip()
            if t.isdigit() or (sh.left and sh.left > Inches(12.0)):
                continue
            sh._element.getparent().remove(sh._element)
        elif sh.shape_type is not None and sh.left and sh.left < Inches(11.0):
            sh._element.getparent().remove(sh._element)


def add_text(s, x, y, w, h, paras):
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tb.text_frame.word_wrap = True
    bp = tb.text_frame._txBody.find(q("bodyPr"))
    for k in ("lIns", "tIns", "rIns", "bIns"):
        bp.set(k, "0")
    set_body(tb, paras)
    return tb


def place(s, name, top, height):
    path = os.path.join(RES, name)
    iw, ih = Image.open(path).size
    w = height * iw / float(ih)
    if w > 12.4:
        w = 12.4
        height = w * ih / float(iw)
    s.shapes.add_picture(path, Inches((13.333 - w) / 2.0), Inches(top),
                         height=Inches(height))


def caption(s, text, top=6.30):
    """One line, in the register a journal figure caption is written in."""
    add_text(s, 0.55, top, 12.25, 0.72, [
        para([(u"@FIG@ ", B), (text, N)],
             level=0, sz=1150, spc=0, bullet=False)])


# ------------------------------------------------------- new figure slides --
SRC = index_of(u"Result 1")
NEW = [
 ("fig_howrun.png", u"How we run ngspice",
  u"One case end to end: the parameters set into sim/dpt.cir, the command, "
  u"what the simulator wrote, and the window the measurement is taken over. "
  u"Full load, 100 V / 10 A, no clamp: +1.6486 V against a 1.4 V threshold."),
 ("fig_netlist.png", u"What ngspice runs",
  u"Power stage of sim/buck.cir. ngspice reads the circuit as a netlist, not "
  u"a schematic; it is the same converter the schematic draws. ngspice "
  u"48.56 V, LTspice 48.84 V."),
 ("fig_method.png", u"How the work was run",
  u"Method, in the order carried out. Steps 1\u20133 on one switching edge; "
  u"steps 4\u20136 the study built on it."),
 ("fig_gan_1.png", u"What a GaN HEMT is",
  u"Silicon MOSFET against GaN HEMT on the properties that govern switching. "
  u"Device modelled: EPC2010C class, 200 V, 25 m\u03a9, V" + u"th" +
  u" = 1.4 V (models/egan.lib)."),
 ("fig_gan_2.png", u"Why the GaN HEMT causes the problem we solve",
  u"Three device properties and their consequence in a half-bridge: a 1.4 V "
  u"threshold, 150 pF from drain to gate, and no body diode."),
 ("fig_settings.png", u"The driver's settings, and where 720 comes from",
  u"The six fields of the control word and the values swept over each. "
  u"6 \u00d7 2 \u00d7 3 \u00d7 5 \u00d7 2 \u00d7 2 = 720 settings, "
  u"\u00d7 4 operating points = 2,880 transients."),
 ("fig_input.png", u"The input \u2014 what an operating point is",
  u"The four corners every setting is evaluated at: bus voltage, load current "
  u"and junction temperature."),
 ("fig_output.png", u"The output \u2014 what is actually measured",
  u"Converter-level output, and the eight quantities extracted from every "
  u"transient. Definitions fixed in scripts/gansim.py before the sweeps ran."),
 ("fig_margin.png", u"Crosstalk margin",
  u"Peak gate\u2013source voltage on the off-state device against the 1.4 V "
  u"threshold, three configurations. Margin is the threshold minus the peak; "
  u"negative is a false turn-on."),
]
for fname, title, figtxt in NEW:
    s = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(s)
    set_title(s, title)
    place(s, fname, 1.28, 4.82)
    caption(s, figtxt)
    print("added: %s" % title)

# ------------------------------------------ the tools' own output ---------
# The results slides were matplotlib charts drawn from the CSVs. The data was
# real and the charts were honest, but a chart is a thing we drew, and this
# project has already been accused of inventing its numbers. A terminal with
# the tool's name, the machine's name and the number in it is a different
# kind of claim. These slides carry the output as it was printed.
TOOLOUT = [
 ("toolout/17-converter-power.png", u"ngspice output \u2014 the converter",
  u"scripts/bucksim.py driving ngspice over sim/buck.cir. 100.0 V and 2.426 A "
  u"in, 48.56 V and 4.875 A out: 242.63 W drawn, 236.85 W delivered, "
  u"97.62 % efficient."),
 ("toolout/01-ngspice-crosstalk.png", u"ngspice output \u2014 the fault, and the fix",
  u"Two runs of sim/dpt.cir. Fastest drive, no clamp, 0 V rail: gate reaches "
  u"+1.6486 V against a 1.400 V threshold, false_turn_on = 1. Clamp on with "
  u"\u22122 V rail: \u22121.1757 V, margin +2.5757 V, false_turn_on = 0."),
 ("toolout/18-named-cases.png", u"ngspice output \u2014 the named cases",
  u"scripts/cases.py, 13 runs. Part 1: the fix built one change at a time at "
  u"100 V / 10 A. Part 2: dead-time sweep at two operating points \u2014 "
  u"cheapest is 15 ns at full load, 5 ns at light load."),
 ("toolout/12-result2-ceiling.png", u"ngspice output \u2014 what re-tuning is worth",
  u"scripts/ceiling.py over results/full_corners.csv. 474 of 720 words "
  u"feasible at all four corners. Ceiling on scheduling 5.2 %; per-corner "
  u"penalty 1.1 / 2.3 / 12.7 / 3.8 %."),
 ("toolout/13-result3-split.png", u"ngspice output \u2014 the split",
  u"scripts/novelty.py. Choosing a fixed word (A) 25.1 %; adapting per "
  u"operating point (B) 3.9 %; B is 13.4 % of the gain. Across 106 overshoot "
  u"weights (A) stays 23.4\u201329.0 %, (B) 1.3\u20136.4 %."),
 ("toolout/03-verilog-8-properties.png", u"Icarus Verilog output \u2014 the controller",
  u"iverilog and vvp over rtl/seg_gate_ctrl.v and its testbench. Eight "
  u"asserted properties, 591 individual assertions, 0 failures."),
 ("toolout/11-vivado-synthesis-console.png", u"Vivado output \u2014 synthesis",
  u"Vivado 2024.1.2 on xc7a35t. 20 LUTs and 20 flip-flops strapped, 33 LUTs "
  u"fully programmable; 200 MHz register-to-register met with 1.996 ns "
  u"slack."),
]
for fname, title, cap_text in TOOLOUT:
    sl = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(sl)
    set_title(sl, title)
    place(sl, fname, 1.30, 4.72)
    caption(sl, cap_text, top=6.28)
    print("added: %s" % title)


# ------------------------------------------------- the circuit, redrawn ----
ci = index_of(u"The circuit that is simulated")
if ci is not None:
    s = p.slides[ci]
    strip(s)
    set_title(s, u"The circuit we simulate")
    # Full slide height. The side-by-side composite made the schematic 6.6 in
    # wide; on its own it gets 8.2 in, which is the difference between a
    # reviewer reading the component names and squinting at them.
    place(s, "fig_circuit_ltspice.png", 1.16, 5.28)
    add_text(s, 0.55, 6.58, 12.25, 0.60, [
        para([(u"@FIG@ ", B),
              (u"GaN synchronous buck converter, ltspice/BUCK_converter.asc. "
               u"100 V supply with power-loop parasitics, two GaN HEMTs, a "
               u"segmented gate driver on each gate, output filter, 10 \u03a9 "
               u"load.", N)],
             level=0, sz=1150, spc=0, bullet=False)])
    print("circuit slide replaced with the drawn LTspice schematic")

# ------------------------------------------------------------ demo video ---
s = clone_after(p, SRC, len(p.slides._sldIdLst))
strip(s)
set_title(s, u"Demo — ngspice and LTspice, running")
if os.path.exists(VIDEO):
    s.shapes.add_movie(VIDEO, Inches(1.55), Inches(1.30), Inches(10.2),
                       Inches(4.55),
                       poster_frame_image=os.path.join(HERE, "poster_demo.png"),
                       mime_type="video/mp4")
caption(s,
        u"Demo recording: the converter in ngspice, the crosstalk fault and "
        u"its fix, the named cases, the Verilog controller, and LTspice "
        u"running the schematic. 2 min. Click to play.",
        top=6.18)
print("added: demo video slide")

# ---------------------------------------------------- closing slide -------
# The Thank You slide was lost by an earlier pass's clone; a review deck should
# not simply stop on the reference list.
s = clone_after(p, SRC, len(p.slides._sldIdLst))
strip(s)
set_title(s, u"Thank you")
add_text(s, 0.70, 2.30, 11.90, 3.20, [
    para([(u"GaN Based DC–DC Power Converter with an Improved Gate Driver", B)],
         level=0, sz=2600, spc=400, bullet=False),
    para([(u"Amritha S  23BEC1368     ·     Sanjay Kumar  23BEC1447     ·     "
           u"Aamir Abdullah  23BPS1197", N)],
         level=0, sz=1500, spc=240, bullet=False),
    para([(u"Guide: Dr. Bindu  —  SENSE, VIT Chennai", N)],
         level=0, sz=1500, spc=400, bullet=False),
    para([(u"Everything in this deck runs on request: ", N),
          (u"github.com/Amritha902/gan-driver", B)],
         level=0, sz=1400, spc=0, bullet=False)])
print("added: Thank you")


# --------------------------------------------------------------- ordering --
# "How the work was run" and "What Python does" are cut: the demo video shows
# both of them happening, and 36 slides does not fit a 10-minute slot. The
# figures are still built and live in results/, so either can be put back by
# naming it here again.
ORDER = [
    u"Slide 1", u"School of", u"Review-I",
    u"Problem Statement",
    u"Aim, and how we approached it",
    u"What a GaN HEMT is",
    u"Why the GaN HEMT causes",
    u"The base paper we build on",
    u"The Five Closest",
    u"We implemented the base paper",
    u"The gap this project fills",
    u"The driver's settings",
    u"The input — what an operating point is",
    u"The output — what is actually measured",
    u"Crosstalk margin",
    u"How it works — one use case",
    u"The circuit we simulate",
    u"What ngspice runs",
    u"How we run ngspice",
    u"How the work was run",
    u"Which tool did what",
    u"Demo — ngspice and LTspice",
    u"What we are building — the converter",
    u"The cases we ran",
    u"Result 1",
    u"The same result in LTspice",
    u"Result 2",
    u"Result 3",
    u"Result 4",
    u"Result 5",
    u"FPGA Controller",
    u"Vivado — simulation and synthesis",
    u"Work Completed",
    u"Where we are, and what is next",
    u"Conclusion",
    u"References  (1–15)",
    u"References  (16–30)",
    u"Thank you",
]

lst = p.slides._sldIdLst
entries = list(lst)
titles = [title_of(s) for s in p.slides]

# the signature page has no heading of its own; find it by its own text
for i, s in enumerate(p.slides):
    txt = "\n".join(sh.text_frame.text for sh in s.shapes if sh.has_text_frame)
    if u"Guide's Signature" in txt:
        titles[i] = u"School of"

# The 10-minute deck and the backup are built here, from the same list, while
# the slide elements and their titles are still in step. Deriving the short
# deck afterwards by deleting slides from the saved file does not work: the
# package carries orphaned slide parts from the clone operations above, and in
# that state prs.slides and the sldIdLst stop corresponding, so deleting index
# i removes some other slide. Harmless for rendering, fatal for editing.

# 15 slides, one per rubric item plus the finding the project exists for.
SHORT = [
    u"School of",
    u"Problem Statement",
    u"The Five Closest",
    u"The gap this project fills",
    u"Aim, and how we approached it",
    u"How it works — one use case",
    u"The circuit we simulate",
    u"How we run ngspice",
    u"Demo — ngspice and LTspice",
    u"ngspice output — the converter",
    u"ngspice output — the fault, and the fix",
    u"ngspice output — the named cases",
    u"ngspice output — what re-tuning is worth",
    u"ngspice output — the split",
    u"Vivado output — synthesis",
    u"Work Completed",
    u"Where we are, and what is next",
    u"References  (1\u201315)",
    u"Thank you",
]


def pick(names):
    used, out = set(), []
    for want in names:
        for i, t in enumerate(titles):
            if i not in used and t.startswith(want):
                out.append(i); used.add(i); break
        else:
            print("  MISSING: %s" % want)
    return out, used


full_idx, full_used = pick(ORDER)
short_idx, _ = pick(SHORT)

for d in [titles[i] or "(untitled)" for i in range(len(titles)) if i not in full_used]:
    print("dropped: %s" % d[:56])


def strip_badges(prs):
    """Remove the repeated VIT logo from content slides.

    It is only 1.5 x 0.57 in in the file, but several phone viewers scale
    embedded images wrongly and render it across half the slide. The title
    page keeps its header logo, which is the mandated format.
    """
    n = 0
    for i, sl in enumerate(prs.slides):
        if i == 0:
            continue
        for sh in list(sl.shapes):
            if sh.shape_type is not None and "PICTURE" in str(sh.shape_type) \
               and sh.width and sh.width < Inches(2.2) \
               and sh.left and sh.left > Inches(10.5):
                sh._element.getparent().remove(sh._element)
                n += 1
    return n


def write(idxs, path, what):
    for el in list(lst):
        lst.remove(el)
    for i in idxs:
        lst.append(entries[i])
    # Figure numbers can only be assigned once the deck is in its final
    # order, so captions carry a marker until here. Captions written by
    # build.py already say "Fig. 1", "Fig. 2" and so on from the deck they
    # were written for -- those get renumbered too, or the deck ends up with
    # two figures called Fig. 2.
    import re as _re
    fign = 0
    for sl in p.slides:
        for sh in sl.shapes:
            if not sh.has_text_frame:
                continue
            txt = sh.text_frame.text
            if u"@FIG@" not in txt and not _re.match(r"\s*Fig\.\s*\d", txt):
                continue
            fign += 1
            done = False
            for pa in sh.text_frame.paragraphs:
                for r in pa.runs:
                    if done:
                        break
                    if u"@FIG@" in r.text:
                        r.text = r.text.replace(u"@FIG@", u"Fig. %d \u2014" % fign)
                        done = True
                    elif _re.match(r"\s*Fig\.\s*\d", r.text):
                        # the em dash has to be in the pattern too: write() runs once per
                        # output file, and without it the second pass leaves
                        # "Fig. 8 - - ".
                        r.text = _re.sub(u"^\\s*Fig\\.\\s*\\d+\\s*(\u2014\\s*)?",
                                         u"Fig. %d \u2014 " % fign, r.text)
                        done = True
                if done:
                    break
    for n, sl in enumerate(p.slides, start=1):
        for sh in sl.shapes:
            if sh.has_text_frame and sh.left and sh.left > Inches(12.0) \
               and sh.top and sh.top > Inches(6.8):
                for pa in sh.text_frame.paragraphs:
                    for r in pa.runs:
                        r.text = str(n)
                break
    removed = strip_badges(p)
    p.save(path)
    print("%-8s %2d slides, %d logos removed -> %s"
          % (what, len(idxs), removed, os.path.basename(path)))


write(short_idx, os.path.join(HERE, "GaN_Review1_PRESENT.pptx"), "PRESENT")
write(full_idx,  os.path.join(HERE, "GaN_Review1_BACKUP.pptx"),  "BACKUP")
write(full_idx,  DECK, "FULL")
