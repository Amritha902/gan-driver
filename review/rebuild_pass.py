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
 ("fig_segdrv_inside.png", u"Inside the segmented gate driver",
  u"Contents of models/segdrv.lib, drawn as ltspice/SEGDRV_inside.asc: eight "
  u"pull-up slices from the +5 V rail to the gate, eight pull-down slices to "
  u"the off rail, and the Miller clamp on its own 0.5 \u03a9 path. It runs \u2014 "
  u"the gate charges to 5.000 V."),
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
 ("fig_si_vs_gan.png", u"Why GaN and not silicon — measured, same converter",
  u"Same buck converter, same job, only the device swapped. Rₓₛ(on) "
  u"matched 25.0 mΩ GaN against 24.0 mΩ Si, each at its own rated gate "
  u"drive, so conduction loss is equal by construction and what is left is "
  u"switching, gate drive and the body-diode recovery GaN does not have. At "
  u"500 kHz GaN wastes 5.9 W against silicon's 17.3 W; the lead widens to 78 % "
  u"at 1 MHz and 90 % at light load (scripts/si_vs_gan_sweep.py)."),
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
 ("toolout/17-converter-power.png", u"Circuit simulation \u2014 the converter",
  u"scripts/bucksim.py driving ngspice over sim/buck.cir. 100.0 V and 2.426 A "
  u"in, 48.56 V and 4.875 A out: 242.63 W drawn, 236.85 W delivered, "
  u"97.62 % efficient."),
 ("toolout/01-ngspice-crosstalk.png", u"Crosstalk simulation \u2014 the fault, and the fix",
  u"Two runs of sim/dpt.cir. Fastest drive, no clamp, 0 V rail: gate reaches "
  u"+1.6486 V against a 1.400 V threshold, false_turn_on = 1. Clamp on with "
  u"\u22122 V rail: \u22121.1757 V, margin +2.5757 V, false_turn_on = 0."),
 ("toolout/18-named-cases.png", u"Driver simulation \u2014 the segmented driver, case by case",
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
               u"\u201cBuck\u201d means step-down: 100 V in, 48.6 V out. The two "
               u"yellow blocks are the segmented gate drivers \u2014 the part "
               u"this project designs. Around them: the 100 V supply with its "
               u"power-loop parasitics, the two GaN HEMTs, the output filter "
               u"and a 10 \u03a9 load.", N)],
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
    para([(u"GaN Based Synchronous Buck Converter with an Improved Gate Driver", B)],
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



# ===================================================================== goal ==
# WHY THESE THREE SLIDES EXIST
# A reviewer asked the only question that actually matters: the goal is a GaN
# buck converter for an energy-storage system -- does this project serve that
# goal, and does the architecture close the gaps the literature leaves open?
# The deck could answer that from its results, but it never asked the question
# out loud, so the answer was spread across six slides and nobody assembled
# it. These three assemble it: what the goal is, whether the architecture
# closes each gap, and how much of the project that amounts to.

from pptx.util import Pt as _Pt
from pptx.dml.color import RGBColor as _RGB

GREEN = _RGB(0x1B, 0x7F, 0x3B)
AMBER = _RGB(0xB5, 0x6A, 0x00)
GREY  = _RGB(0x55, 0x55, 0x55)
BLUE  = _RGB(0x2A, 0x78, 0xD6)


def grid(s, x, y, w, h, rows, widths, sizes=(10.0, 9.5), head_fill=None):
    """A table sized for a projector: no borders to read around, one rule
    under the header, and columns proportioned by content rather than evenly.

    Written here rather than reusing build.py's set_cell because these tables
    carry a status column that has to be coloured per row, which set_cell has
    no way to express."""
    tb = s.shapes.add_table(len(rows), len(widths), Inches(x), Inches(y),
                            Inches(w), Inches(h)).table
    tb.first_row = True
    tb.horz_banding = False
    total = float(sum(widths))
    for i, frac in enumerate(widths):
        tb.columns[i].width = Inches(w * frac / total)
    for r, row in enumerate(rows):
        for c, cell in enumerate(row):
            txt, colour, bold = (cell if isinstance(cell, tuple)
                                 else (cell, None, r == 0))
            tc = tb.cell(r, c)
            tc.margin_left = tc.margin_right = Inches(0.055)
            tc.margin_top = tc.margin_bottom = Inches(0.03)
            tf = tc.text_frame
            tf.word_wrap = True
            pa = tf.paragraphs[0]
            run = pa.add_run()
            run.text = txt
            run.font.size = _Pt(sizes[0] if r == 0 else sizes[1])
            run.font.bold = bool(bold)
            run.font.name = "Calibri"
            if colour is not None:
                run.font.color.rgb = colour
    return tb


# ---- slide: the goal, stated as a goal -------------------------------------
s = clone_after(p, SRC, len(p.slides._sldIdLst))
strip(s)
set_title(s, u"The goal, and whether this serves it")
add_text(s, 0.70, 1.25, 12.10, 1.05, [
    para([(u"THE GOAL.  ", B),
          (u"Build a synchronous buck converter for an energy-storage system "
           u"out of GaN HEMTs, and make it work at the switching speed GaN is "
           u"bought for. Everything else in this deck exists to serve that "
           u"sentence.", N)], level=0, sz=1350, spc=0, bullet=False)])

add_text(s, 0.70, 2.35, 3.85, 0.38, [
    para([(u"1.  Why GaN at all", B)], level=0, sz=1300, spc=0, bullet=False)])
add_text(s, 0.70, 2.78, 3.85, 1.95, [
    para([(u"Same converter, same job, only the device swapped. At 500 kHz "
           u"GaN wastes 5.9 W against silicon's 17.3 W. The lead widens to "
           u"78 % at 1 MHz and 90 % at light load, and never turns back.", N)],
         level=0, sz=1150, spc=120, bullet=False),
    para([(u"Raising the frequency to shrink the magnetics is nearly free on "
           u"GaN and ruinous on silicon.", B)],
         level=0, sz=1150, spc=0, bullet=False)])

add_text(s, 4.80, 2.35, 3.85, 0.38, [
    para([(u"2.  What GaN costs you", B)], level=0, sz=1300, spc=0, bullet=False)])
add_text(s, 4.80, 2.78, 3.85, 1.95, [
    para([(u"The same speed that wins is what breaks it. A 1.4 V threshold "
           u"and 150 pF of drain-to-gate capacitance mean the device that is "
           u"supposed to be OFF gets pushed toward ON by its partner "
           u"switching.", N)], level=0, sz=1150, spc=120, bullet=False),
    para([(u"Measured: the off gate reaches 1.65 V against a 1.4 V "
           u"threshold. That is a shoot-through.", B)],
         level=0, sz=1150, spc=0, bullet=False)])

add_text(s, 8.90, 2.35, 3.90, 0.38, [
    para([(u"3.  What we build about it", B)], level=0, sz=1300, spc=0, bullet=False)])
add_text(s, 8.90, 2.78, 3.90, 1.95, [
    para([(u"A segmented gate driver: 8 pull-up steps, 8 pull-down steps, an "
           u"adjustable dead time, a Miller clamp and a −2 V off rail — "
           u"driven by an FPGA, so every one of them is a setting that can be "
           u"changed and measured.", N)], level=0, sz=1150, spc=120, bullet=False),
    para([(u"Result: −0.249 V of margin becomes +2.576 V.", B)],
         level=0, sz=1150, spc=0, bullet=False)])

add_text(s, 0.70, 4.92, 12.10, 1.90, [
    para([(u"SO THE TEST OF PURPOSE IS NOT “does the converter run”.  ", B),
          (u"It runs — 100 V in, 48.6 V out at 4.88 A, 97.6 % efficient. "
           u"Any textbook buck converter runs. The test is whether the "
           u"architecture we put around it answers the questions the "
           u"published work on these drivers leaves open, because that is the "
           u"only part of this that is ours.", N)],
         level=0, sz=1250, spc=180, bullet=False),
    para([(u"The next slide is that question, gap by gap, with the evidence "
           u"for each.", B)], level=0, sz=1250, spc=0, bullet=False)])
print("added: The goal, and whether this serves it")


# ---- slide: the scorecard --------------------------------------------------
s = clone_after(p, SRC, len(p.slides._sldIdLst))
strip(s)
set_title(s, u"Does the architecture close the gaps?")
add_text(s, 0.70, 1.22, 12.10, 0.42, [
    para([(u"Nine gaps in the published work, what our architecture does about "
           u"each, and the evidence. Every row names the script that produces "
           u"it.", N)], level=0, sz=1200, spc=0, bullet=False)])

ROWS = [
    (u"Gap in the published work", u"What the architecture does",
     u"Evidence", u"Status"),
    (u"Segmented drivers report one number. Nobody separates a better FIXED "
     u"setting from live RE-TUNING.",
     u"720 control words × 4 operating points, every combination run.",
     u"Fixed 25.1 %, adaptive 3.9 % — adaptive is 13.4 % of the gain "
     u"(novelty.py).", u"CLOSED"),
    (u"Nobody says how much CONTROLLER the adaptive part justifies.",
     u"A complexity ladder: constant word → one comparator → two "
     u"→ full lookup table.",
     u"One comparator takes 46 % of it. 7.2 % is left to justify a sense + "
     u"ADC + LUT (controller_ladder.py).", u"CLOSED"),
    (u"Prior segmented drivers stage the slices but carry no Miller clamp and "
     u"no negative off rail.",
     u"8 + 8 slices AND a clamp AND a −2 V off-bias, each measurable on "
     u"its own.",
     u"Base paper at its best +0.407 V; ours +2.576 V — 6.3× "
     u"(basepaper_compare.py).", u"CLOSED"),
    (u"The driver is asserted to be programmable; the logic is rarely "
     u"synthesised.",
     u"seg_gate_ctrl.v, thermometer-coded, with its own dead-time generator.",
     u"8 properties in Icarus; 20 LUT / 20 FF on xc7a35t, 200 MHz met, "
     u"1.996 ns slack.", u"CLOSED"),
    (u"Controller and power stage are verified separately and never made to "
     u"meet.",
     u"The RTL's own VCD drives the SPICE slices — one source per wire, "
     u"no integer in between.",
     u"Margins agree to 0.081 V, and it found a one-cycle dead-time error "
     u"(rtl_cosim.py).", u"CLOSED"),
    (u"Whether a fitted schedule GENERALISES to an unseen operating point is "
     u"never tested.",
     u"Leave-one-corner-out: fit the comparator on three corners, test on the "
     u"fourth.",
     u"Worse than the fixed word on 3 of 4 held-out corners. n = 4, so weak "
     u"— and we say so.", u"ANSWERED, NEGATIVE"),
    (u"Segmented-driver papers characterise one switching EDGE. The converter "
     u"is never closed-loop regulated.",
     u"A type-III loop around the same power stage and the same drivers, then "
     u"disturbed on purpose.",
     u"0.05 % error through a 2× load step and a 20 % line step; open loop "
     u"walks to 58 V (closedloop.py).", u"CLOSED"),
    (u"Segmented output stages are published as ideal switches. Whether the "
     u"result survives real devices is untested.",
     u"The same output stage rebuilt in SKY130 5 V transistors and re-run.",
     u"Sign and ordering both survive — and the clamp ALONE turns out to give "
     u"only +0.031 V (silicon_check.py).", u"CLOSED"),
    (u"All of the above is simulation.",
     u"—",
     u"No silicon measured. The DRIVER is now rebuilt on a real PDK; the GaN "
     u"model has no equivalent check.", u"OPEN → Review-III"),
]
coloured = []
for r, row in enumerate(ROWS):
    if r == 0:
        coloured.append([(c, None, True) for c in row])
        continue
    st = row[3]
    col = GREEN if st == u"CLOSED" else (AMBER if st.startswith(u"ANSWERED")
                                         else GREY)
    coloured.append([(row[0], None, False), (row[1], None, False),
                     (row[2], None, False), (st, col, True)])
grid(s, 0.62, 1.74, 12.14, 4.62, coloured, widths=(30, 26, 32, 12),
     sizes=(10.0, 8.0))

add_text(s, 0.70, 6.46, 11.70, 0.80, [
    para([(u"DOES IT SERVE ITS PURPOSE?  ", B),
          (u"Yes, for a simulation study, and that is what it is titled as. "
           u"Seven gaps closed, one answered in the negative — which is a "
           u"result, not a failure — and one that needs a bench. The "
           u"honest summary is that the architecture is finished and the "
           u"measurement of it on real silicon is not.", N)],
         level=0, sz=1200, spc=0, bullet=False)])
print("added: Does the architecture close the gaps?")


# ---- slide: the RTL and the power stage, made to meet ----------------------
s = clone_after(p, SRC, len(p.slides._sldIdLst))
strip(s)
set_title(s, u"The architecture, end to end")

add_text(s, 0.70, 1.22, 5.85, 0.38, [
    para([(u"The gap we found in our OWN work", B)],
         level=0, sz=1300, spc=0, bullet=False)])
add_text(s, 0.70, 1.66, 5.85, 2.05, [
    para([(u"The controller was verified in Icarus. The power stage was "
           u"verified in ngspice. The two never touched.", N)],
         level=0, sz=1200, spc=140, bullet=False),
    para([(u"The FPGA emits eight thermometer-coded wires per bank. The SPICE "
           u"driver took an INTEGER slice count. A fault in the decoder would "
           u"have passed the Verilog bench and stayed invisible in every "
           u"figure ngspice produced.", N)],
         level=0, sz=1200, spc=0, bullet=False)])

add_text(s, 7.00, 1.22, 5.80, 0.38, [
    para([(u"What we did about it", B)], level=0, sz=1300, spc=0, bullet=False)])
add_text(s, 7.00, 1.66, 5.80, 2.05, [
    para([(u"rtl/seg_gate_ctrl_dpt_tb.v reproduces the double-pulse schedule "
           u"at the real 200 MHz clock, letting the RTL's own dead-time "
           u"generator make the edges.", N)],
         level=0, sz=1200, spc=140, bullet=False),
    para([(u"Its VCD becomes sixteen PWL sources, one per wire, into "
           u"models/segdrv_bus.lib. Same deck, same devices, same "
           u"measurement — only the slice selection changes.", N)],
         level=0, sz=1200, spc=0, bullet=False)])

grid(s, 2.35, 3.85, 8.65, 1.05, [
    (u"", u"margin, RTL bus", u"margin, .param", u"difference"),
    ((u"clamp off", None, True), (u"−0.242 V", None, True),
     (u"−0.249 V", None, False), (u"0.007 V", None, False)),
    ((u"clamp on", None, True), (u"+0.651 V", GREEN, True),
     (u"+0.570 V", None, False), (u"0.081 V", None, False)),
], widths=(20, 28, 28, 24), sizes=(11.0, 11.0))

add_text(s, 0.70, 5.20, 12.10, 1.90, [
    para([(u"Worst disagreement anywhere: 0.081 V", B),
          (u" — and it is timing, not encoding. The ideal stimulus turns "
           u"the low side on at 2.015 µs; the RTL's dead-time generator "
           u"puts it at 2.0175 µs. The clamp's sign change, which is this "
           u"project's central claim, is now produced by the actual logic "
           u"rather than by a parameter.", N)],
         level=0, sz=1250, spc=170, bullet=False),
    para([(u"And it found a real bug, which is the whole argument for doing "
           u"it: ", B),
          (u"dead time is (dt_cycles + 1) × 5 ns. The counter loads and "
           u"then counts down THROUGH zero, so 15 ns is 2 cycles, not the "
           u"obvious 15/5 = 3. Anyone mapping our swept dead-time grid onto "
           u"hardware by dividing by the clock period builds a driver that is "
           u"one cycle slow at every operating point — and neither half "
           u"of the verification could have seen it alone.", N)],
         level=0, sz=1250, spc=0, bullet=False)])
print("added: The architecture, end to end")


# ---- slide: how much of the project this is, and how that was counted ------
# "50 %" was a placeholder from the template, asserted rather than counted.
# A reviewer is entitled to ask what the denominator is. So the slide now
# carries the denominator: twelve blocks with a weight each, eight of them
# done. Arguing with the weights is a real conversation; arguing with a bare
# percentage is not.
COMPLETION = [
    (u"The converter itself, built and converting", 8, True,
     u"100 V → 48.6 V at 4.88 A, 97.6 % efficient (buck.cir)"),
    (u"The device choice justified against silicon", 8, True,
     u"5.9 W vs 17.3 W at 500 kHz; 3 sweeps, 4 duty profiles"),
    (u"The base paper implemented, not just cited", 10, True,
     u"zhangdrv.lib in our own deck; quoted at ITS best, +0.407 V"),
    (u"The segmented driver; the fault reproduced and fixed", 12, True,
     u"−0.249 V → +2.576 V, one change at a time"),
    (u"The full study: 720 words × 4 corners", 12, True,
     u"34,622 transients; fixed 25.1 % vs adaptive 3.9 %"),
    (u"How much controller that justifies", 8, True,
     u"ladder + leave-one-corner-out; two implementations agree"),
    (u"FPGA: RTL written, verified, synthesised, timing met", 12, True,
     u"8 properties; 20 LUT / 20 FF; 200 MHz, 1.996 ns slack"),
    (u"The two halves made to meet in one simulation", 5, True,
     u"RTL VCD drives the SPICE slices; agree to 0.081 V"),
    (u"Closed-loop regulation, disturbed on purpose", 8, True,
     u"type-III loop: 0.05 % error through a 2x load and a 20 % line step"),
    (u"Transistor-level output stage, on a real PDK", 7, True,
     u"SKY130 5 V devices: sign and ordering of the result both survive"),
    (u"Place-and-route on a chosen board", 3, False,
     u"Needs real package pins and an MMCM for the clock"),
    (u"A hardware half-bridge, measured", 7, False,
     u"Review-III. Until then this is a simulation study, and is titled as one"),
]
DONE = sum(w for _, w, d, _ in COMPLETION if d)
assert sum(w for _, w, _, _ in COMPLETION) == 100

wi = index_of(u"Work Completed")
if wi is not None:
    s = p.slides[wi]
    strip(s)
    set_title(s, u"Work Completed — %d %%" % DONE)
    add_text(s, 0.70, 1.18, 12.10, 0.46, [
        para([(u"Counted, not asserted. ", B),
              (u"Twelve blocks, weighted by how much of the project each is. "
               u"Eight are finished. The weights are on the slide so they can "
               u"be argued with.", N)], level=0, sz=1200, spc=0, bullet=False)])

    rows = [(u"", u"Block of work", u"Weight", u"Evidence, or why not yet")]
    for name, w, done, ev in COMPLETION:
        mark = (u"✔", GREEN, True) if done else (u"—", GREY, True)
        rows.append([mark, (name, None, done), (u"%d" % w, None, False),
                     (ev, None if done else GREY, False)])
    grid(s, 0.62, 1.74, 12.14, 4.45, rows, widths=(4, 36, 8, 52),
         sizes=(10.0, 9.0))

    add_text(s, 0.70, 6.34, 11.70, 0.90, [
        para([(u"%d of 100 done. " % DONE, B),
              (u"Review-I's rubric asks for 50 %%. We are past it because this "
               u"is a simulation study and the simulation half is finished — "
               u"the remaining %d %% is place-and-route on a chosen board and "
               u"a hardware half-bridge on a bench, and no amount of further "
               u"simulating will deliver either." % (100 - DONE), N)],
             level=0, sz=1250, spc=140, bullet=False),
        para([(u"Stated plainly: the architecture is finished. The "
               u"measurement of it on real silicon is not.", B)],
             level=0, sz=1250, spc=0, bullet=False)])
    print("rebuilt: Work Completed — %d %%" % DONE)
else:
    print("  MISSING: Work Completed slide to rebuild")


# ---- slide: closing the loop ----------------------------------------------
s = clone_after(p, SRC, len(p.slides._sldIdLst))
strip(s)
set_title(s, u"Closing the loop")

add_text(s, 0.70, 1.20, 12.10, 0.80, [
    para([(u"Every result so far was measured OPEN LOOP — the duty ratio was "
           u"a parameter and nothing moved while we measured. That is the right "
           u"instrument for a switching edge and the wrong description of a "
           u"converter: a storage system's pack voltage sags all day and its "
           u"load steps whenever something downstream turns on.", N)],
         level=0, sz=1250, spc=0, bullet=False)])

grid(s, 1.30, 2.14, 10.70, 1.10, [
    (u"", u"nominal  100 V / 5 A", u"after 2\u00d7 load step",
     u"after 100 \u2192 120 V line step", u"worst error"),
    ((u"closed loop", None, True), (u"50.02 V", GREEN, True),
     (u"50.00 V", GREEN, True), (u"50.01 V", GREEN, True),
     (u"0.05 %", GREEN, True)),
    ((u"open loop", None, True), (u"49.45 V", None, False),
     (u"48.69 V", None, False), (u"58.33 V", AMBER, True),
     (u"16.7 %", AMBER, True)),
], widths=(16, 21, 21, 26, 16), sizes=(10.0, 11.0))

add_text(s, 0.70, 3.44, 5.85, 0.34, [
    para([(u"What the loop buys", B)], level=0, sz=1250, spc=0, bullet=False)])
add_text(s, 0.70, 3.82, 5.85, 2.10, [
    para([(u"Load step 5 \u2192 10 A: dips 1.8 %, back inside \u00b11 % in 4 \u00b5s.", N)],
         level=0, sz=1150, spc=110, bullet=False),
    para([(u"Line step 100 \u2192 120 V: peaks 1.3 %, recovers in 19 \u00b5s.", N)],
         level=0, sz=1150, spc=110, bullet=False),
    para([(u"Output ripple 0.28 %. Soft-start overshoot 10.9 % — the one "
           u"number here we are not proud of, and it is on the slide.", N)],
         level=0, sz=1150, spc=110, bullet=False),
    para([(u"Open loop is not merely less accurate. On the line step it walks "
           u"to 58 V, because V_out = D \u00d7 V_in and nothing in it knows "
           u"V_in moved.", B)], level=0, sz=1150, spc=0, bullet=False)])

add_text(s, 7.00, 3.44, 5.80, 0.34, [
    para([(u"Two compensators that did NOT work", B)],
         level=0, sz=1250, spc=0, bullet=False)])
add_text(s, 7.00, 3.82, 5.80, 2.10, [
    para([(u"The first period-doubled: a 4 \u00b5s triangle on a 2 \u00b5s "
           u"switching period — the textbook f", N), (u"sw", N),
          (u"/2 limit cycle.", N)], level=0, sz=1150, spc=110, bullet=False),
    para([(u"A proper type-II could not be made to work at all. One zero "
           u"cannot beat the output LC's \u2212180\u00b0: cross above the "
           u"corner and the phase margin is negative, cross below and the loop "
           u"cannot settle between two disturbances. Both measured — 30 \u00b5S "
           u"drifts 23 V, 100 \u00b5S rails 98 V.", N)],
         level=0, sz=1150, spc=110, bullet=False),
    para([(u"Type III adds the second zero, which is exactly the missing "
           u"phase. Crossover ~30 kHz, f", N), (u"sw", N), (u"/16.", N)],
         level=0, sz=1150, spc=0, bullet=False)])

add_text(s, 0.70, 6.10, 11.70, 1.00, [
    para([(u"Said out loud: the K-factor design was 4\u00d7 out. ", B),
          (u"It predicted 30 kHz; the measured step response said about 2 kHz, "
           u"109 % overshoot, 119 \u00b5s to settle. The gain was scaled "
           u"empirically and re-measured at each step. No phase margin is "
           u"claimed anywhere — that needs an AC analysis about a periodic "
           u"operating point, which ngspice cannot do on a switching deck.", N)],
         level=0, sz=1200, spc=0, bullet=False)])
print("added: Closing the loop")


# ---- slide: does it survive real transistors? ------------------------------
s = clone_after(p, SRC, len(p.slides._sldIdLst))
strip(s)
set_title(s, u"Does the result survive real transistors?")

add_text(s, 0.70, 1.18, 12.10, 0.76, [
    para([(u"Every margin in this deck was measured with an output stage whose "
           u"slices are IDEAL SWITCHES — 10 m\u03a9 on, 1 G\u03a9 off, no gate "
           u"charge, no threshold, no transition. Fair for comparing control "
           u"words. Not a driver anyone can fabricate. So we rebuilt the same "
           u"output stage in real SKY130 5 V devices and ran it again.", N)],
         level=0, sz=1250, spc=0, bullet=False)])

grid(s, 1.90, 2.08, 9.50, 1.35, [
    (u"configuration", u"ideal switches", u"SKY130 transistors", u""),
    ((u"constant word, no clamp", None, False), (u"\u22120.249 V", None, False),
     (u"\u22120.563 V", None, False), (u"FALSE TURN-ON", AMBER, True)),
    ((u"clamp on", None, False), (u"+0.570 V", None, False),
     (u"+0.031 V", AMBER, True), (u"barely holds", AMBER, True)),
    ((u"clamp + \u22122 V off-bias", None, True), (u"+2.576 V", None, False),
     (u"+2.032 V", GREEN, True), (u"safe", GREEN, True)),
], widths=(30, 22, 24, 24), sizes=(10.5, 11.0))

add_text(s, 0.70, 3.66, 12.10, 1.55, [
    para([(u"The architecture survives — and the reason it survives changes.", B)],
         level=0, sz=1350, spc=180, bullet=False),
    para([(u"Sign and ordering hold on both stages: the constant word fails on "
           u"real transistors too, the clamp beats no clamp, and clamp plus "
           u"negative bias beats clamp alone. That is what had to be true, and "
           u"it is. But on real devices ", N),
          (u"the clamp ALONE gives +0.031 V", B),
          (u" — thirty-one millivolts, at one corner, with nothing left over "
           u"for temperature or a worse layout. That is not a fix.", N)],
         level=0, sz=1200, spc=0, bullet=False)])

add_text(s, 0.70, 5.34, 11.70, 1.75, [
    para([(u"So we correct our own headline. ", B),
          (u"The \u22122 V off-bias is the fix; the clamp is what makes the "
           u"off-bias hold. The ideal-switch model was flattering the clamp, "
           u"because an ideal switch pulls the gate down through 10 m\u03a9 "
           u"while a real NMOS pulls it through a channel that has to be "
           u"turned on first.", N)],
         level=0, sz=1250, spc=170, bullet=False),
    para([(u"Stated limit: the predrivers in this stage are still behavioural. "
           u"The output stage is what is being checked. And there is no "
           u"equivalent check on the GaN side — no open PDK ships a 200 V GaN "
           u"HEMT — so that model remains the single assumption everything "
           u"rests on.", N)], level=0, sz=1150, spc=0, bullet=False)])
print("added: Does the result survive real transistors?")


# ---- slide: head to head ---------------------------------------------------
s = clone_after(p, SRC, len(p.slides._sldIdLst))
strip(s)
set_title(s, u"Head to head with the base paper")

add_text(s, 0.70, 1.16, 12.10, 0.56, [
    para([(u"Same deck, same GaN, same power loop, same parasitics — only the "
           u"driver is swapped. We hold ONE fixed word at all four corners. "
           u"They are re-optimised at EVERY corner, which is more freedom than "
           u"their own design has.", N)],
         level=0, sz=1200, spc=0, bullet=False)])

grid(s, 0.62, 1.80, 12.14, 1.55, [
    (u"crosstalk margin", u"base, as their paper builds it",
     u"base, re-tuned at every corner", u"ours, ONE fixed word", u"vs their best"),
    ((u"50 V / 2 A / 25 \u00b0C", None, True), (u"+0.503 V", None, False),
     (u"+0.503 V", None, False), (u"+2.757 V", GREEN, True), (u"5.5\u00d7", None, True)),
    ((u"100 V / 10 A / 25 \u00b0C", None, True), (u"+0.407 V", None, False),
     (u"+0.407 V", None, False), (u"+2.576 V", GREEN, True), (u"6.3\u00d7", None, True)),
    ((u"200 V / 2 A / 125 \u00b0C", None, True), (u"+0.261 V", None, False),
     (u"+0.261 V", None, False), (u"+2.309 V", GREEN, True), (u"8.9\u00d7", None, True)),
    ((u"200 V / 10 A / 125 \u00b0C", None, True), (u"+0.181 V", AMBER, True),
     (u"+0.181 V", None, False), (u"+2.251 V", GREEN, True), (u"12.4\u00d7", None, True)),
], widths=(24, 21, 22, 20, 13), sizes=(10.0, 10.0))

add_text(s, 0.70, 3.54, 5.85, 0.34, [
    para([(u"The gap WIDENS with stress", B)], level=0, sz=1250, spc=0, bullet=False)])
add_text(s, 0.70, 3.92, 5.85, 1.55, [
    para([(u"Their margin falls +0.503 \u2192 +0.181 V from the mildest corner "
           u"to the hottest. Ours goes +2.757 \u2192 +2.251. They degrade where "
           u"it matters most; a clamp does not care how hot the device is.", N)],
         level=0, sz=1150, spc=110, bullet=False),
    para([(u"Worst corner is what a converter has to survive: +0.181 V against "
           u"+2.251 V.", B)], level=0, sz=1150, spc=0, bullet=False)])

add_text(s, 7.00, 3.54, 5.80, 0.34, [
    para([(u"And we slew HARDER, not softer", B)], level=0, sz=1250, spc=0, bullet=False)])
add_text(s, 7.00, 3.92, 5.80, 1.55, [
    para([(u"Their scheme reduces crosstalk by slowing the edge: 67\u2013103 "
           u"V/ns at the switch node. Ours runs 101\u2013175 V/ns — about "
           u"twice as fast — and still wins by a factor of several.", N)],
         level=0, sz=1150, spc=110, bullet=False),
    para([(u"The margin is not bought with switching speed. That is the useful "
           u"form of the result.", B)], level=0, sz=1150, spc=0, bullet=False)])

add_text(s, 0.70, 5.60, 11.70, 1.50, [
    para([(u"What it costs, and what the claim is NOT. ", B),
          (u"Our turn-on energy is higher at three of four corners — the "
           u"\u22122 V rail deepens GaN's dead-time reverse drop, a penalty "
           u"this project already measures at 1.0\u20133.4 % of total loss. "
           u"Their driver needs one bias resistor; ours needs a clamp device, "
           u"a negative supply and 20 LUTs. For a converter that never leaves "
           u"one operating point, theirs may be the right engineering.", N)],
         level=0, sz=1200, spc=160, bullet=False),
    para([(u"And this is OUR implementation of their described scheme in OUR "
           u"testbench — their netlist is not published. It is not 6.3\u00d7 "
           u"their measured result, and we do not say it is.", B)],
         level=0, sz=1200, spc=0, bullet=False)])
print("added: Head to head with the base paper")


# ---- two slides the transistor-level result makes stale -------------------
# "the clamp fixes it" was true of the ideal-switch stage and is not true of
# real devices, where the clamp alone gives +0.031 V. Leaving the old title up
# and correcting it four slides later is how a reviewer decides you knew.
i = index_of(u"Result 1")
if i is not None:
    set_title(p.slides[i], u"Result 1 \u2014 crosstalk is real, and what fixes it")
    print("retitled: Result 1")

# Review-II was "close the loop". The loop is closed, so the plan has to say
# what is actually left rather than list work already in the deck.
i = index_of(u"Where we are, and what is next")
if i is not None:
    s = p.slides[i]
    strip(s)
    set_title(s, u"Where we are, and what is next")
    add_text(s, 0.70, 1.35, 12.10, 5.30, [
        para([(u"Where we are", B)], level=0, sz=1700, spc=200, bullet=False),
        para([(u"90 % by the count on the previous slide. The converter is "
               u"built and regulating, the fault is reproduced and fixed, the "
               u"720-word study is run, the controller is written, verified and "
               u"synthesised, its output drives the SPICE power stage directly, "
               u"and the driver has been rebuilt in real transistors.", N)],
             level=0, sz=1300, spc=260, bullet=True),
        para([(u"What is actually left \u2014 and it is not more simulating", B)],
             level=0, sz=1700, spc=200, bullet=False),
        para([(u"Place-and-route on a chosen board. ", B),
              (u"Synthesis is done; the flow stops there because the XDC pins "
               u"are placeholders. Doing it properly also means driving the "
               u"200 MHz clock from an MMCM rather than straight off a pin, "
               u"which is what makes 34 clock-to-pin paths fail today.", N)],
             level=0, sz=1300, spc=220, bullet=True),
        para([(u"A hardware half-bridge, measured. ", B),
              (u"This is the whole of the remaining honest risk. Everything in "
               u"this deck is a simulation of a converter that has never been "
               u"built, and one behavioural GaN model underlies all of it.", N)],
             level=0, sz=1300, spc=220, bullet=True),
        para([(u"Also worth doing: transcribe the silicon MOSFET datasheet "
               u"digits rather than using datasheet-class values, and re-run "
               u"the ceiling on the transistor-level stage now that it is "
               u"known to work.", N)], level=0, sz=1200, spc=0, bullet=True),
    ])
    print("rebuilt: Where we are, and what is next")


# --------------------------------------------------------------- ordering --
# "How the work was run" and "What Python does" are cut: the demo video shows
# both of them happening, and 36 slides does not fit a 10-minute slot. The
# figures are still built and live in results/, so either can be put back by
# naming it here again.
ORDER = [
    u"Slide 1", u"School of", u"Review-I",
    u"Problem Statement",
    u"The goal, and whether this serves it",
    u"Aim, and how we approached it",
    u"What a GaN HEMT is",
    u"Why GaN and not silicon",
    u"Why the GaN HEMT causes",
    u"The base paper we build on",
    # build.py creates this slide and simplify.py writes its text, but it was
    # never named here -- so ORDER dropped it and the deck cited a base paper
    # it never compared against, while the speech script talked the audience
    # through a slide that did not exist.
    u"We implemented the base paper",
    u"Head to head with the base paper",
    u"The five closest published drivers",
    u"The gap this project fills",
    u"The driver's settings",
    u"The input — what an operating point is",
    u"The output — what is actually measured",
    u"Crosstalk margin",
    u"How it works — one use case",
    u"The circuit we simulate",
    u"What ngspice runs",
    u"Inside the segmented gate driver",
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
    u"The architecture, end to end",
    u"Closing the loop",
    u"Does the result survive real transistors?",
    u"Does the architecture close the gaps?",
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
    u"School of",                                  # signed title page
    u"Problem Statement",                          # problem
    u"The five closest published drivers",         # literature, BASE tagged
    u"The gap this project fills",
    u"The goal, and whether this serves it",
    u"Aim, and how we approached it",              # solution, method, scope, tools
    u"System Architecture",
    u"How it works — one use case",                # the master flowchart
    u"The circuit we simulate",
    u"How we run ngspice",
    u"Demo — ngspice and LTspice",                 # the video
    u"Circuit simulation",
    u"Crosstalk simulation",
    u"Driver simulation",
    u"Head to head with the base paper",            # the comparison
    u"Closing the loop",                            # the converter regulates
    u"Does the result survive real transistors?",
    u"Does the architecture close the gaps?",       # the reviewer's question
    u"Work Completed",                             # completion
    u"References  (1–15)",
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
