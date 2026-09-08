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


def caption(s, figure, meaning, top=6.22):
    add_text(s, 0.55, top, 12.25, 0.92, [
        para([(u"The figure. ", B), (figure, N)],
             level=0, sz=1150, spc=60, bullet=False),
        para([(u"What it means. ", B), (meaning, N)],
             level=0, sz=1150, spc=0, bullet=False)])


# ------------------------------------------------------- new figure slides --
SRC = index_of(u"Result 1")
NEW = [
 ("fig_gan_1.png", u"What a GaN HEMT is",
  u"Silicon against gallium nitride, side by side, on the properties that "
  u"matter for switching.",
  u"GaN holds off the same voltage in a much thinner layer, so there is far "
  u"less charge to move and it switches in nanoseconds. That speed is the "
  u"reason to use it."),
 ("fig_gan_2.png", u"Why the GaN HEMT causes the problem we solve",
  u"Three properties of the device and what each one does inside a half-bridge.",
  u"A 1.4 V threshold, an unavoidable 150 pF path from drain to gate, and no "
  u"body diode. The fault follows from the device, not from a mistake."),
 ("fig_settings.png", u"The driver's settings, and where 720 comes from",
  u"The six fields the gate driver exposes, and the values each one is swept "
  u"over.",
  u"6 × 2 × 3 × 5 × 2 × 2 = 720 settings. Each is simulated at four operating "
  u"points, so 2,880 runs in all."),
 ("fig_input.png", u"The input — what an operating point is",
  u"The four conditions every setting is tested at: bus voltage, load current "
  u"and junction temperature.",
  u"If the best setting were the same at all four there would be nothing to "
  u"adapt to. Whether it moves is the question the project answers."),
 ("fig_output.png", u"The output — what is actually measured",
  u"Two things: what the converter delivers, and what each individual "
  u"simulation reports.",
  u"48.56 V at 4.875 A, 97.62 % efficient. Per run: the peak on the OFF gate, "
  u"the margin, the switching energy and four more."),
 ("fig_margin.png", u"What “margin” means",
  u"How far the OFF device's gate stays below the voltage that would switch "
  u"it on, for three configurations.",
  u"Positive is safe, negative is a fault. Without the fix it is "
  + MINUS + u"0.249 V; with the clamp and the " + MINUS + u"2 V rail it is "
  u"+2.576 V."),
]
for fname, title, figtxt, meaning in NEW:
    s = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(s)
    set_title(s, title)
    place(s, fname, 1.28, 4.82)
    caption(s, figtxt, meaning)
    print("added: %s" % title)

# ------------------------------------------------- the circuit, redrawn ----
ci = index_of(u"The circuit that is simulated")
if ci is not None:
    s = p.slides[ci]
    strip(s)
    set_title(s, u"The circuit, drawn and simulated")
    place(s, "fig_circuit_ltspice.png", 1.24, 4.86)
    caption(s,
            u"ltspice/BUCK_converter.asc as LTspice draws it: the 100 V supply "
            u"and its loop parasitics, the two GaN HEMTs, a segmented driver on "
            u"each gate, the output filter and the load.",
            u"This is not a picture of a circuit — it is the circuit. Press "
            u"Run and it gives 48.84 V and 4.88 A, against the netlist's "
            u"48.56 V and 4.875 A.")
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
        u"Two minutes recorded on the project laptop. The converter in "
        u"ngspice, the crosstalk fault and its fix, the named cases, the "
        u"Verilog controller, then LTspice opening the schematic and running it.",
        u"Every number in this deck appears in that recording, produced by a "
        u"tool while the clock in the corner runs. Click the frame to play.",
        top=6.10)
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
    u"What “margin” means",
    u"How it works — one use case",
    u"The circuit, drawn and simulated",
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

used, ordered = set(), []
for want in ORDER:
    for i, t in enumerate(titles):
        if i not in used and t.startswith(want):
            ordered.append(i); used.add(i); break

dropped = [titles[i] or "(untitled)" for i in range(len(titles)) if i not in used]
for el in entries:
    lst.remove(el)
for i in ordered:
    lst.append(entries[i])

for d in dropped:
    print("dropped: %s" % d[:56])
print("kept %d slides in the specified order" % len(ordered))

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
