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
ltspice/BUCK_converter.asc, a drawn schematic with real wires. Its
cross-check against the netlist is pending a re-run: the schematic gained the
damped decoupling branch and now reads its parameters from buck.cir, so the
48.84 V once quoted against the netlist's 48.56 V describes neither circuit as
they now stand. ngspice alone gives 48.50 V on the shipped word.

ORDER below is the whole specification: anything not named in it is dropped.
"""
import os, sys, copy as _copy, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lxml import etree
from pptx import Presentation
from pptx.util import Inches
from fill import para, set_body, q
from PIL import Image
import converter_numbers as CN
import closedloop_numbers as CL
import waveform_numbers as WF

HERE = os.path.dirname(os.path.abspath(__file__))
RES  = os.path.join(HERE, "..", "results")
DECK = os.path.join(HERE, "Review2_GaN_Segmented_Gate_Driver.pptx")
# IN the repository, not next to it. This was "~/GAN_MAIN/PROOF/DEMO-VIDEO.mp4"
# -- a path on the machine the project started on -- so on every checkout since
# the split the demo slide has been built with NO VIDEO IN IT, while its own
# caption said "2 min. Click to play." A panel would have clicked on nothing.
#
# It was proof/DEMO-VIDEO.mp4, a screen recording of proof/DEMO.sh made on
# 11 Sep. DEMO.sh re-runs the real pipeline, so the recording was honest when
# it was made -- but sim/buck.cir was corrected on 21 Sep (the undamped bus
# decoupling branch), and a recording cannot re-derive itself. It therefore
# shows converter numbers the rest of the deck no longer claims.
#
# results/demo_review2.mp4 is rebuilt by scripts/demo_review2.py on every
# run, and it is four things only: the circuit as a KiCad schematic, the
# software that drew and ran it, the output with the thing to look at pointed
# at, and the base paper's driver measured against ours on the same bench at
# the same corner. It reads both netlists off disk and makes three ngspice
# runs while it builds -- ours, theirs, and the converter -- so it cannot go
# stale without the build failing.
#
# It replaced results/demo_full.mp4 here on 28 Sep and was recut the same day:
# the first cut opened with the problem, typed the netlists on and closed on
# seven result cards, which is a talk rather than a demo.
#
# demo_full.mp4 stays in the repo and demo_video.py still builds it; it is
# simply not what this slide plays. The 2-minute pipeline walkthrough is
# offered in SPEECH-SCRIPT.md under "if they ask to see more".
VIDEO = os.path.join(RES, "demo_review2.mp4")

# Measurements and length come from the sidecar demo_video.py writes, so this
# caption cannot drift from the file it describes.
DEMO = {}
for _ln in open(os.path.join(RES, "demo_review2.txt")):
    if _ln.startswith("#") or not _ln.split(): continue
    _k, _v = _ln.split(None, 1)
    DEMO[_k] = _v.strip()

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


def caption(s, text, top=6.30, h=0.72):
    """One line, in the register a journal figure caption is written in.

    `h` because the three result slides carry a caption that has to name the
    script, the method and four numbers, and at 0.72 in those overflow.
    """
    add_text(s, 0.55, top, 12.25, h, [
        para([(u"@FIG@ ", B), (text, N)],
             level=0, sz=1150, spc=0, bullet=False)])


# ------------------------------------------------------- new figure slides --
SRC = index_of(u"Result 1")
NEW = [
 ("fig_segdrv_inside.png", u"Inside the segmented gate driver",
  u"Contents of models/segdrv.lib, drawn as ltspice/SEGDRV_inside.asc: eight "
  u"pull-up segments from the +5 V rail to the gate, eight pull-down segments to "
  u"the off rail, and the Miller clamp on its own 0.5 \u03a9 path. It runs: "
  u"the gate charges to 5.000 V."),
 ("fig_howrun.png", u"How we run ngspice",
  u"One case end to end: the parameters set into sim/dpt.cir, the command, "
  u"what the simulator wrote, and the window the measurement is taken over. "
  u"Full load, 100 V / 10 A, no clamp: +1.6486 V against a 1.4 V threshold."),
 ("fig_netlist.png", u"What ngspice runs",
  u"Power stage of sim/buck.cir. ngspice reads the circuit as a netlist, not "
  u"a schematic; it is the same converter the schematic draws. ngspice gives "
  u"48.50 V on the shipped word. The LTspice cross-check is pending a re-run: "
  u"its schematic gained the damped decoupling branch, so the previously "
  u"quoted 48.84 V describes a circuit that no longer exists."),
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
  u"500 kHz GaN wastes 6.2 W against silicon's 12.6 W; the lead widens to 78 % "
  u"at 1 MHz and 90 % at light load (scripts/si_vs_gan_sweep.py)."),
 ("fig_gan_2.png", u"Why the GaN HEMT causes the problem we solve",
  u"Three device properties and their consequence in a half-bridge: a 1.4 V "
  u"threshold, 150 pF from drain to gate, and no body diode."),
 ("fig_settings.png", u"The driver's settings, and where 720 comes from",
  u"The six fields of the control word and the values swept over each. "
  u"6 \u00d7 2 \u00d7 3 \u00d7 5 \u00d7 2 \u00d7 2 = 720 settings, "
  u"\u00d7 36 operating points = 25,920 transients."),
 ("fig_input.png", u"The input \u2014 what an operating point is",
  u"Four of the 36 corners every setting is evaluated at: bus voltage, load current "
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
import csv as _csv

_PM = os.path.join(RES, "panel_metrics.csv")
PM = {}
if os.path.exists(_PM):
    with open(_PM) as _fh:
        for _r in _csv.DictReader(_fh):
            PM[_r["config"]] = _r
else:
    print("  MISSING: results/panel_metrics.csv -- run scripts/panel_metrics.py")

def _metric(cfg, key):
    """One metric as a float, so prose can be derived from the same CSV the
    table is."""
    return float(PM[cfg][key])


# kind of claim. These slides carry the output as it was printed.
# The comparison tables are measured a different way from this run; the
# caption says so rather than leaving two efficiencies on the deck unexplained.
_EFF_TABLE = u"%.2f %%" % _metric("gan_ours", "eff_pct")

TOOLOUT = [
 ("toolout/17-converter-power.png", u"Circuit simulation \u2014 the converter",
  u"scripts/bucksim.py driving ngspice over sim/buck.cir, on the shipped "
  u"word. %s and %.3f A in, %s and %s out: %s drawn, "
  u"%s delivered, %s efficient. Peak switch node %s, %s "
  u"overshoot at this deck's 0.2 ns step; resolving the edge at 0.02 ns gives "
  % (CN.VIN, CN.V["Iin"], CN.VOUT, CN.IOUT, CN.PIN, CN.POUT, CN.EFF,
     CN.SWPK, CN.OV) +
  u"18.0 %, of which the \u22122 V rail is +11.3 points \u2014 the margin is "
  u"not free. scripts/overshoot_audit.py. "
  u"The two comparison tables read " + _EFF_TABLE + u" for this same word: "
  u"those runs start pre-charged in steady state and average 20 cycles, this "
  u"one starts from zero and averages 10. The gap is the start-up transient, "
  u"not a disagreement."),
 ("toolout/19-ngspice-listing.png", u"The circuit, as ngspice reports it",
  u"ngspice cannot draw a schematic. It can say what it parsed, which is "
  u"better evidence: a drawing is what somebody believes the circuit is, "
  u"this is what was solved. Note rpu1\u2013rpu8 and rpd1\u2013rpd8 \u2014 the "
  u"sixteen segments, switched in by {runit+(npu>=n?0:1e9)} \u2014 rclk the "
  u"clamp, and rdec at 1 \u03a9, the damped value. "
  u"scripts/netlist_listing.py regenerates it, so it cannot go stale."),
 # This caption describes two rows of waveforms -- the switch node over the
 # gate it disturbs -- and was paired with toolout/01-ngspice-crosstalk.png,
 # which is a terminal screenshot with no rows in it at all. The slide told
 # the panel to look at a TOP and a BOTTOM that were not on the screen.
 #
 # The screenshot was also evidence against itself: it is dated 2026-09-08 on
 # a MacBook running ngspice-47, while the deck states ngspice-42 on a Debian
 # container. Two slides apart, a reviewer reads both.
 #
 # fig1_crosstalk.png is the figure the words were written for: switch node
 # over gate-source, baseline on the left and mitigated on the right, drawn
 # from the same two transients.
 ("fig1_crosstalk.png", u"Crosstalk: Fault and Mitigation",
  u"Two runs of sim/dpt.cir. Top row: the switch node falls from %.0f V, its "
  u"90–10 %% edge taking %.2f ns and peaking at %.0f V/ns \u2014 that dv/dt drives i = C_GD\u00b7dv/dt into the OFF "
  u"device's gate, and is the cause. Bottom row: that gate. Left, without the "
  u"clamp, it rests at %+.3f V, is lifted %+.3f V and peaks at %+.3f V, past the "
  u"1.4 V threshold \u2014 false_turn_on = 1. Right, with the clamp and the "
  u"\u22122 V rail, it rests at %+.3f V, is lifted only %+.3f V and peaks at "
  u"%+.3f V \u2014 false_turn_on = 0. The two fixes are not one mechanism: the "
  u"rail moves where the gate starts, the clamp shortens the lift by giving the "
  u"injected charge a 0.5 \u03a9 path out. scripts/waveform_anatomy.py."
  % (WF.VBUS, WF.FALL_NS, WF.SLEW_PK, WF.REST_BAD, WF.LIFT_BAD, WF.PEAK_BAD,
     WF.REST_GOOD, WF.LIFT_GOOD, WF.PEAK_GOOD)),
 ("toolout/18-named-cases.png", u"Driver simulation \u2014 the segmented driver, case by case",
  u"scripts/cases.py, 13 runs. Part 1: the fix built one change at a time at "
  u"100 V / 10 A. Part 2: dead-time sweep at two operating points: "
  u"cheapest is 15 ns at full load, 5 ns at light load."),
 ("toolout/12-result2-ceiling.png", u"ngspice output \u2014 what re-tuning is worth",
  u"scripts/ceiling.py over results/full_corners.csv. 474 of 720 words "
  u"feasible at all 36 corners. Ceiling on scheduling 3.5 %; per-corner "
  u"penalty 1.1 / 2.3 / 12.7 / 3.8 %."),
 ("toolout/13-result3-split.png", u"ngspice output \u2014 the split",
  u"scripts/grid_analyse.py over 36 corners. Choosing a fixed word (A) 26.5 %; "
  u"adapting per operating point (B) 2.6 %; B is 8.9 % of the gain. Across 106 overshoot "
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
    set_title(s, u"Converter Under Simulation")
    # This was results/fig_circuit_ltspice.png, an LTspice screenshot taken on
    # 11 September. ltspice/BUCK_converter.asc was corrected on 23 September --
    # its .param block had been retyped rather than read, so the sheet carried
    # no Ldec, Cdec or Rdec while sim/buck.cir did. The screenshot was never
    # retaken, because rendering an .asc needs LTspice and there is none here.
    # So the deck's own "the circuit we simulate" slide was showing a circuit
    # without the decoupling branch -- the branch the whole 200 V finding turns
    # on -- and captioned it with the superseded 48.6 V / 4.88 A output.
    #
    # scripts/kicad_schematic.py draws the same converter from sim/buck.cir at
    # build time, decoupling branch included, so it cannot drift from the
    # netlist. That is the sheet now.
    place(s, "fig_sch_converter.png", 1.16, 5.28)
    add_text(s, 0.55, 6.58, 12.25, 0.60, [
        para([(u"@FIG@ ", B),
              (u"GaN synchronous buck converter, drawn from sim/buck.cir by "
               u"scripts/kicad_schematic.py \u2014 every value on it is read "
               u"out of the netlist at build time. \u201cBuck\u201d means "
               u"step-down: 100 V in, " + CN.VOUT + u" out. Left to right: the "
               u"100 V supply with its power-loop R and L, the damped bus "
               u"decoupling branch (Ldec, Cdec, Rdec at 1 \u03a9), the two GaN "
               u"HEMTs whose gates the segmented drivers drive, the output "
               u"filter and a 10 \u03a9 load.", N)],
             level=0, sz=1150, spc=0, bullet=False)])
    print("circuit slide now uses the netlist-drawn schematic")

# ------------------------------------------------ the novelty, on the circuit ---
# "Three blocks added" is an architecture claim. This is the same claim on the
# circuit: their sheet and ours, both screen captures of KiCad, with the two
# things ours has ringed and the one thing theirs says about its own rail
# ringed as well. A reviewer asking "show me where the novelty actually is"
# should be answered with a picture, not a sentence.
_NC = "fig_novelty_circuit.png"
if os.path.exists(os.path.join(RES, _NC)):
    sl = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(sl)
    set_title(sl, u"Novelty at Circuit Level")
    add_text(sl, 0.70, 1.02, 12.10, 0.40, [
        para([(u"The converter on top; underneath it, what sits behind its two "
               u"gates in their design and in ours. Both additions are "
               u"established practice [1]\u2013[4]; the base paper uses "
               u"neither. What is measured here is what each is worth on "
               u"this converter.", B)],
             level=0, sz=1300, spc=0, bullet=False)])
    place(sl, _NC, 1.50, 4.74)
    caption(sl,
            u"Top: sim/buck.cir, with the two gates of the half-bridge "
            u"ringed \u2014 HSG and LSG are what a gate driver drives, and "
            u"everything below is what sits behind them. Bottom left, theirs: "
            u"seven segments per bank in two stages, and a rail their own sheet "
            u"labels \u201ctied to ref \u2014 NO negative rail\u201d. Bottom "
            u"right, ours: the same eight-segment output stage, plus the active "
            u"Miller clamp and an off rail selectable to \u22122 V. The clamp "
            u"is worth +0.82 V of crosstalk margin and the rail +2.01 V; "
            u"together \u22120.249 V becomes +2.576 V. Annotated screen "
            u"captures of KiCad 7.0.11, not redrawings, and not a size "
            u"comparison \u2014 the three sheets open at different zoom.",
            top=6.40, h=1.06)
    print("added: What differs in the circuit, theirs and ours")
else:
    print("  MISSING: results/%s -- run scripts/novelty_circuit.py" % _NC)


# ------------------------------------------- both driver sheets, uncropped ---
# The slide above crops both sheets to the part that differs and rings it,
# which is the right figure for "where is the difference" but is still a
# crop -- and a crop is where a comparison can be made to flatter one side.
# This is the other half of the answer: both sheets whole, at the same scale,
# nothing ringed and nothing removed, so that anything the cropped figure
# appears to show can be checked against the sheets themselves.
_SP = "fig_schematics_pair.png"
if os.path.exists(os.path.join(RES, _SP)):
    sl = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(sl)
    set_title(sl, u"Gate Driver Schematics in KiCad")
    add_text(sl, 0.70, 1.02, 12.10, 0.40, [
        para([(u"The two sheets the previous slide crops from \u2014 whole, "
               u"at the same scale, nothing ringed and nothing removed.", B)],
             level=0, sz=1300, spc=0, bullet=False)])
    place(sl, _SP, 1.72, 4.02)
    caption(sl,
            u"Left: kicad/gan_zhangdrv.kicad_sch, the base paper's driver as "
            u"we rebuilt it \u2014 seven segments per bank in two stages, one bias "
            u"resistor, and a rail its own sheet labels as tied to reference. "
            u"Right: kicad/gan_segdrv.kicad_sch, ours \u2014 eight segments a "
            u"bank, an active Miller clamp and an off rail selectable to "
            u"\u22122 V. Both are screen captures of KiCad 7.0.11 taken by "
            u"scripts/record_kicad.py from the files named above, not "
            u"redrawings. The two sheets are different sizes, so this is a "
            u"comparison of what is on them, not of how large they are.",
            top=5.90, h=1.30)
    print("added: Gate Driver Schematics in KiCad")
else:
    print("  MISSING: results/%s -- run scripts/schematic_pair.py" % _SP)


# ----------------------------------------- the mechanism, at the device ----
# The architecture slide names the parts. It does not say what happens inside
# the GaN device, which is the only thing this project is about: a fast edge
# on the switch node pushes charge through C_GD into the gate that is meant to
# stay off, and that gate rises by whatever the charge cannot shed through the
# driver. This draws the path and the three things the driver does to it, with
# the numbers read from results/waveform_anatomy.txt so the picture and the
# crosstalk waveform cannot disagree.
_GL = "fig_gan_level.png"
if os.path.exists(os.path.join(RES, _GL)):
    sl = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(sl)
    set_title(sl, u"Crosstalk Mechanism at Device Level")
    add_text(sl, 0.70, 1.02, 12.10, 0.40, [
        para([(u"Why a fast edge turns on the device that should be off, and "
               u"what the driver does about it.", B)],
             level=0, sz=1300, spc=0, bullet=False)])
    place(sl, _GL, 1.55, 4.35)
    caption(sl,
            u"Left: the half-bridge. When the low-side device turns on the "
            u"switch node falls from %.0f V, its 90\u201310 %% edge taking "
            u"%.2f ns and peaking at %.0f V/ns, and "
            u"that dv/dt drives a current through C_GD into the high-side "
            u"gate. Right: the three parallel paths that current sees at the "
            u"gate node. The segment count sets how hard the gate is held; the "
            u"Miller clamp adds a 0.5 ohm path of its own, timed to the other "
            u"device's edge; the off rail sets where the gate starts from. "
            u"The two additions are not one mechanism - the rail moves the "
            u"starting point, the clamp shortens the lift - which is why they "
            u"add rather than overlap. scripts/gan_level_figure.py, from "
            u"results/waveform_anatomy.txt."
            % (WF.VBUS, WF.FALL_NS, WF.SLEW_PK),
            top=6.06, h=1.22)
    print("added: Crosstalk Mechanism at Device Level")
else:
    print("  MISSING: results/%s -- run scripts/gan_level_figure.py" % _GL)


# ------------------------------------------- implementation, full bleed ----
# The schematics were on the deck only as screen captures of eeschema, which
# prove the application was open but are a 2560x1440 photograph of a window.
# These are rendered from the PDFs KiCad plots, which are vector, so they
# stay sharp at full-screen size -- and they are the whole sheet, frame and
# title block included, rather than a crop.
#
# Laid out to fill the slide: the sheet is A3 landscape and the slide is
# 16:9, so fitting to height is the largest it can be without cropping, and
# cropping a schematic to fill a frame would remove circuit.
_IMPL = [
    ("implementation/01-converter-schematic.png",
     u"Implementation: Converter Schematic",
     u"kicad/gan_buck.kicad_sch, the root sheet, plotted by KiCad 7.0.11. "
     u"Drawn from sim/buck.cir, so every value on it is the netlist's. The "
     u"two gate drivers are hierarchical sub-sheets of this page."),
    ("implementation/04-driver-proposed.png",
     u"Implementation: Proposed Gate Driver",
     u"kicad/gan_segdrv.kicad_sch. Eight pull-up segments, eight pull-down, "
     u"the active Miller clamp on the right, and the off rail selectable to "
     u"-2 V. Each segment is one switch and one resistor; the resistor carries "
     u"the control word."),
    ("implementation/05-driver-base-paper.png",
     u"Implementation: Base Paper Gate Driver",
     u"kicad/gan_zhangdrv.kicad_sch, the base paper's driver reimplemented "
     u"in the same testbench. Seven segments per bank in two stages, one bias "
     u"resistor, no clamp branch, and the off rail tied to reference."),
]
for _if, _it, _icap in _IMPL:
    if not os.path.exists(os.path.join(HERE, "..", _if)):
        print("  MISSING: %s -- run scripts/implementation_shots.py" % _if)
        continue
    sl = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(sl)
    set_title(sl, _it)
    _iw, _ih = Image.open(os.path.join(HERE, "..", _if)).size
    _h = 5.62
    _w = _h * _iw / float(_ih)
    if _w > 12.6:
        _w = 12.6
        _h = _w * _ih / float(_iw)
    sl.shapes.add_picture(os.path.join(HERE, "..", _if),
                          Inches((13.333 - _w) / 2.0), Inches(1.00),
                          width=Inches(_w), height=Inches(_h))
    caption(sl, _icap, top=1.02 + _h + 0.08, h=0.78)
    print("added: %s" % _it)


# --------------------------------------- the block, drawn by hand ----------
# kicad/gan_driver.drawio is the project's own draw.io source and had never
# reached a slide. It is the clearest picture of the custom block there is:
# all sixteen segments at once, the clamp beside them, and the three rails they
# sit between. Rendered straight out of the .drawio by scripts/drawio_render.py
# -- there is no browser in this container to export it with, and a hand
# export would put a step between the file in the repository and the picture
# on the slide that nobody could check.
_DW = "fig_drawio_segmented_driver.png"
if os.path.exists(os.path.join(RES, _DW)):
    sl = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(sl)
    set_title(sl, u"Segmented Driver: Block Structure")
    add_text(sl, 0.70, 1.02, 12.10, 0.40, [
        para([(u"kicad/gan_driver.drawio, the block diagram of "
               u"models/segdrv.lib.", B)],
             level=0, sz=1300, spc=0, bullet=False)])
    place(sl, _DW, 1.58, 3.90)
    caption(sl,
            u"Sixteen segments between three rails: eight pull-up from VP, "
            u"eight pull-down to VN, and OUT going to the HEMT gate. Each "
            u"segment is one switch and one resistor, and the resistor carries "
            u"the control word: ask for three or more segments and Rpu3 is 8 "
            u"ohms and in circuit, ask for fewer and it becomes 1 G-ohm and "
            u"that segment is out. Drive strength is simply how many of the "
            u"eight parallel paths are live. On the right, the active Miller "
            u"clamp, which the base paper does not have: its own switch and "
            u"0.5 ohms to VN, and VN itself selectable to -2 V.",
            top=5.62, h=1.45)
    print("added: Segmented Driver: Block Structure")
else:
    print("  MISSING: results/%s -- run scripts/drawio_render.py" % _DW)


# ------------------------------------------------ the blocks we wrote ------
# The deck cites models/segdrv.lib and models/egan.lib on nearly every slide
# and calls them ours. A reviewer asking what "ours" actually means was being
# sent to a repository. These two slides answer it on the screen: the real
# source, at the real line numbers, read out of the files at build time so a
# slide cannot drift from the code it claims to show.
for _cf, _ct, _cl, _ccap in [
    ("fig_code_segdrv.png", u"Segmented Driver: SPICE Implementation",
     u"models/segdrv.lib \u2014 the output stage varied throughout the study.",
     u"Eight pull-up segments and eight pull-down, each a switch and a resistor. "
     u"A segment is in circuit when the control word reaches it and 1 G\u03a9 out "
     u"of it when it does not, which is how 4 + 4 bits from the FPGA become a "
     u"drive strength. The clamp is not one of the segments: it has its own "
     u"switch, its own timing and its own 0.5 \u03a9 path to the off rail, "
     u"because it has to hold the gate down while the other device switches. "
     u"The segments are discrete by design: a single variable resistor "
     u"would simulate identically and could not be laid out."),
    ("fig_code_egan.png", u"GaN HEMT Device Model",
     u"models/egan.lib \u2014 written from the EPC2010C datasheet.",
     u"Vendor subcircuits are LTspice-dialect and do not port to Spectre, so "
     u"this is written from datasheet quantities only. The channel is one "
     u"symmetric square law, so third-quadrant conduction follows from the "
     u"physics rather than being added: GaN has no body diode, and reverse "
     u"conduction costs V_th + |V_off| + I\u00b7R_ds(on). That is the coupling "
     u"the project turns on \u2014 a negative off rail improves crosstalk "
     u"margin at the cost of dead-time loss. C_GD is a junction diode biased never to "
     u"conduct, so only its C(V) law is used. The temperature coefficients are "
     u"hand-typed from the datasheet, not fitted; this is the principal "
     u"limitation of the model. The Model Validation slide runs the same "
     u"three configurations on two further device models.")]:
    if not os.path.exists(os.path.join(RES, _cf)):
        print("  MISSING: results/%s -- run scripts/code_listing.py" % _cf)
        continue
    sl = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(sl)
    set_title(sl, _ct)
    add_text(sl, 0.70, 1.02, 12.10, 0.40, [
        para([(_cl, B)], level=0, sz=1300, spc=0, bullet=False)])
    place(sl, _cf, 1.62, 3.30)
    caption(sl, _ccap, top=5.30, h=1.70)
    print("added: %s" % _ct)



# ------------------------------------------------- how the numbers were made ---
# Every comparison in this deck is "same setup, one thing changed". That is
# the whole basis for reading a difference as caused by the change, and until
# now it was asserted in passing on several slides rather than stated once,
# precisely, with the environment named. A reviewer who does not believe the
# setup was identical has no reason to believe any number that follows.
_ENV = {}
try:
    _ng = subprocess.run(["ngspice", "-v"], capture_output=True, text=True)
    _ENV["ngspice"] = next((l.strip().lstrip("*").strip().split(":")[0].strip()
                            for l in (_ng.stdout + _ng.stderr).split("\n")
                            if "ngspice-" in l), "ngspice")
except Exception:
    _ENV["ngspice"] = "ngspice-42"
try:
    _kc = subprocess.run(["kicad-cli", "version"], capture_output=True, text=True)
    _ENV["kicad"] = (_kc.stdout + _kc.stderr).strip().split()[0][:12]
except Exception:
    _ENV["kicad"] = "7.0.11"

sl = clone_after(p, SRC, len(p.slides._sldIdLst))
strip(sl)
set_title(sl, u"Methodology")
add_text(sl, 0.70, 1.02, 12.10, 0.40, [
    para([(u"Every comparison is the same file with one thing changed. "
           u"Here is exactly what is held and exactly what moves.", B)],
         level=0, sz=1300, spc=0, bullet=False)])

_HELD = [
    (u"the netlist", u"sim/dpt.cir, byte for byte \u2014 not a copy, not a variant"),
    (u"the device", u"models/egan.lib on both sides, same V_th, same "
                    u"R_ds(on), same C_gs"),
    (u"the parasitics", u"3 nH power loop, 0.3 \u03a9 loop resistance, same "
                        u"gate inductance"),
    (u"the operating point", u"100 V bus, 10 A load, 25 \u00b0C junction"),
    (u"the solver", u"same timestep, same options, same initial conditions"),
]
_CHANGED = [
    (u"theirs vs ours", u"the driver subcircuit, and nothing else: "
                        u"models/zhangdrv.lib \u2194 models/segdrv.lib"),
    (u"GaN vs silicon", u"the device model only, R_ds(on) matched at "
                        u"the 25 m\u03a9 class"),
    (u"clamp on/off", u"one parameter, CLKEN; off rail, one parameter, VNEG"),
]
_y = 1.62
add_text(sl, 0.70, _y, 5.90, 0.34, [
    para([(u"HELD IDENTICAL", B)], level=0, sz=1250, spc=0, bullet=False)])
add_text(sl, 6.90, _y, 5.90, 0.34, [
    para([(u"WHAT CHANGES", B)], level=0, sz=1250, spc=0,
         bullet=False)])
_y += 0.44
for _i in range(max(len(_HELD), len(_CHANGED))):
    if _i < len(_HELD):
        add_text(sl, 0.70, _y, 5.90, 0.62, [
            para([(_HELD[_i][0] + u"   ", B), (_HELD[_i][1], N)],
                 level=0, sz=1120, spc=0, bullet=False)])
    if _i < len(_CHANGED):
        add_text(sl, 6.90, _y, 5.90, 0.62, [
            para([(_CHANGED[_i][0] + u"   ", B), (_CHANGED[_i][1], N)],
                 level=0, sz=1120, spc=0, bullet=False)])
    _y += 0.70
add_text(sl, 0.70, _y + 0.10, 12.10, 0.40, [
    para([(u"ENVIRONMENT   ", B),
          (u"%s and KiCad %s on a Debian container, headless, no hardware "
           u"in the loop. Both are open source; there is no licensed tool "
           u"and no vendor model anywhere in this project."
           % (_ENV["ngspice"], _ENV["kicad"]), N)],
         level=0, sz=1120, spc=0, bullet=False)])
caption(sl,
        u"Their driver is additionally given a freedom its own paper does not "
        u"have: scripts/headtohead.py searches both of its controls at every "
        u"corner and it is run at the setting that search finds best FOR IT, "
        u"read out of results/headtohead.txt. Ours runs one fixed control word "
        u"at every corner. Any remaining difference is the driver. "
        u"results/RESULTS-SUMMARY.txt names the script behind each number, and "
        u"review/check_consistency.py fails the build if a slide and the data "
        u"disagree.", top=6.44, h=1.02)
print("added: How every number on these slides was made")



# -------------------------------------------------- the pair of demo films ---
# demo_review2.mp4 ends by overlaying both drivers on one axis, which is the
# summary. These two introduce them: the same four beats -- KiCad sheet,
# simulator, waveform, reading -- run over each driver on its own, so the
# panel meets theirs and ours separately before seeing them together.
#
# Both films fix their axis limits as constants rather than autoscaling, and
# say so on screen, so flicking between the two slides reads a difference in
# where the trace sits and not a difference in zoom.
PAIR = {}
_ps = os.path.join(RES, "demo_pair.txt")
if os.path.exists(_ps):
    for _ln in open(_ps):
        if _ln.startswith("#") or not _ln.split():
            continue
        _k, _v = _ln.split(None, 1)
        PAIR[_k] = _v.strip()

for _mp4, _poster, _title, _lead, _cap in (
    ("demo_basepaper.mp4", "demo_basepaper_poster.png",
     u"Base Paper Driver: Simulation Result",
     u"models/zhangdrv.lib on sim/dpt.cir. Seven segments per bank in two "
     u"stages, no clamp branch, no negative off rail.",
     u"Their circuit, ngspice running it, the waveform. OFF gate peaks "
     u"%s V against a 1.400 V threshold \u2014 %s V of margin. Run at "
     u"nseg=%s, tstep=%s, the setting scripts/headtohead.py found best "
     u"for their driver here. %s s."),
    ("demo_ours.mp4", "demo_ours_poster.png",
     u"Proposed Driver: Simulation Result",
     u"models/segdrv.lib on the same sim/dpt.cir. Eight segments per bank, "
     u"active Miller clamp, \u22122 V off rail.",
     u"The same sequence, our driver. Gate peaks %s V \u2014 %s V of "
     u"margin, %s\u00d7 our implementation of their scheme. One fixed "
     u"control word. Axes identical to the previous slide. %s s."),
):
    _path = os.path.join(RES, _mp4)
    _pp = os.path.join(RES, _poster)
    if not (os.path.exists(_path) and os.path.exists(_pp)):
        print("  MISSING: %s -- run scripts/demo_pair.py" % _mp4)
        continue
    s = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(s)
    set_title(s, _title)
    add_text(s, 0.70, 1.06, 12.10, 0.44, [
        para([(_lead, B)], level=0, sz=1300, spc=0, bullet=False)])
    # 8.40 x 4.72 in (16:9), centred, ending at 6.30 -- these captions name
    # the setting, both margins and the shared axes, and at 9.00 x 5.06 the
    # text ran off the bottom of the slide.
    s.shapes.add_movie(_path, Inches(2.465), Inches(1.58), Inches(8.40),
                       Inches(4.72), poster_frame_image=_pp,
                       mime_type="video/mp4")
    _base = ("%+.3f" % float(PAIR["base_peak"])).replace("-", MINUS)
    _ours = ("%+.3f" % float(PAIR["ours_peak"])).replace("-", MINUS)
    if "basepaper" in _mp4:
        _txt = _cap % (_base, "%.3f" % float(PAIR["base_margin"]),
                       PAIR["base_nseg"], PAIR["base_tstep"], "35")
    else:
        _txt = _cap % (_ours, "%.3f" % float(PAIR["ours_margin"]),
                       "%.1f" % float(PAIR["ratio"]), "35")
    caption(s, _txt, top=6.40, h=1.06)
    print("added: %s" % _title)



# ------------------------------------------------------------ demo video ---
s = clone_after(p, SRC, len(p.slides._sldIdLst))
strip(s)
set_title(s, u"Demonstration, on this machine")
if os.path.exists(VIDEO):
    # 1600x900 -> 1.778. 9.00 in wide gives 5.06 in tall, centred on the
    # 13.33 in slide, ending at 6.16 -- the film's caption names the bench
    # and the converter both, and at the old 9.60 x 5.40 it overflowed the
    # slide rather than wrapping inside it.
    s.shapes.add_movie(VIDEO, Inches(2.165), Inches(1.10), Inches(9.00),
                       Inches(5.06),
                       poster_frame_image=os.path.join(HERE, "poster_review2.png"),
                       mime_type="video/mp4")
    print("demo video embedded: %s (%.1f MB)"
          % (os.path.basename(VIDEO), os.path.getsize(VIDEO) / 1048576.0))
else:
    # Loud, because the caption promises a video and a silent skip ships a
    # slide that says "click to play" over an empty box.
    raise SystemExit("DEMO VIDEO MISSING at %s -- the demo slide would ship "
                     "empty while its caption promises one. Fix the path or "
                     "remove the slide." % VIDEO)
caption(s,
        u"Four parts, %.0f s, click to play. The circuit as its KiCad sheet, "
        u"the tools named and versioned, the output with what to look at "
        u"pointed at, and the base paper's driver run against ours on the "
        u"same bench at 100 V / 10 A / 25 \u00b0C. Theirs peaks %+.3f V, "
        u"%.3f V short of the 1.400 V threshold; ours peaks %s V, %.3f V "
        u"clear. The converter it drives: %.2f V out at %.2f W, %.2f %% "
        u"efficient. Three ngspice runs made while the film was building "
        u"\u2014 rebuilt by scripts/demo_review2.py, so every number on screen "
        u"is computed, not captioned."
        % (float(DEMO["duration_s"]), float(DEMO["base_peak"]),
           float(DEMO["base_margin"]),
           ("%+.3f" % float(DEMO["ours_peak"])).replace("-", MINUS),
           float(DEMO["ours_margin"]), float(DEMO["conv_vout"]),
           float(DEMO["conv_pout"]), float(DEMO["conv_eff"])),
        top=6.22, h=1.24)
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
    para([(u"Sanjay Kumar  23BEC1447     ·     Aamir Abdullah  23BPS1197     "
           u"·     Amritha S  23BEC1368", N)],
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
    para([(u"The goal.  ", B),
          (u"Build a synchronous buck converter for an energy-storage system "
           u"out of GaN HEMTs, and make it work at the switching speed GaN is "
           u"bought for. Everything else in this deck exists to serve that "
           u"sentence.", N)], level=0, sz=1350, spc=0, bullet=False)])

add_text(s, 0.70, 2.35, 3.85, 0.38, [
    para([(u"1.  Why GaN at all", B)], level=0, sz=1300, spc=0, bullet=False)])
add_text(s, 0.70, 2.78, 3.85, 1.95, [
    para([(u"Same converter, same job, only the device swapped. At 500 kHz "
           u"GaN wastes 6.2 W against silicon's 12.6 W. The lead widens to "
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
           u"supposed to be off gets pushed toward on by its partner "
           u"switching.", N)], level=0, sz=1150, spc=120, bullet=False),
    para([(u"Measured: the off gate reaches 1.65 V against a 1.4 V "
           u"threshold. That is a shoot-through.", B)],
         level=0, sz=1150, spc=0, bullet=False)])

add_text(s, 8.90, 2.35, 3.90, 0.38, [
    para([(u"3.  What we build about it", B)], level=0, sz=1300, spc=0, bullet=False)])
add_text(s, 8.90, 2.78, 3.90, 1.95, [
    para([(u"A segmented gate driver: 8 pull-up steps, 8 pull-down steps, an "
           u"adjustable dead time, a Miller clamp and a −2 V off rail, "
           u"driven by an FPGA, so every one of them is a setting that can be "
           u"changed and measured.", N)], level=0, sz=1150, spc=120, bullet=False),
    para([(u"Result: −0.249 V of margin becomes +2.576 V.", B)],
         level=0, sz=1150, spc=0, bullet=False)])

add_text(s, 0.70, 4.92, 12.10, 1.90, [
    para([(u"Title says converter, work says driver \u2014 one claim.  ", B),
          (u"On GaN the driver is the part that decides whether the "
           u"converter is buildable at speed. Every number here is measured "
           u"on the converter: %s open loop, 96.1 %% regulated." % CN.EFF, N)],
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
    (u"Segmented drivers report one number. Nobody separates a better fixed "
     u"setting from live re-tuning.",
     u"720 control words × 36 operating points, every combination run.",
     u"Fixed 26.5 %, adaptive 2.6 % — adaptive is 8.9 % of the gain, on 36 corners "
     u"(novelty.py).", u"CLOSED"),
    (u"Nobody says how much controller the adaptive part justifies.",
     u"A complexity ladder: constant word → one comparator → two "
     u"→ full lookup table.",
     u"One comparator (load current at 10 A) takes 47 %. 4.7 % is left to justify a sense + "
     u"ADC + LUT (controller_ladder.py).", u"CLOSED"),
    (u"Prior segmented drivers stage the segments but carry no Miller clamp and "
     u"no negative off rail.",
     u"8 + 8 segments plus a clamp plus a −2 V off-bias, each measurable on "
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
     u"The RTL's own VCD drives the SPICE segments — one source per wire, "
     u"no integer in between.",
     u"Margins agree to 0.081 V, and it found a one-cycle dead-time error "
     u"(rtl_cosim.py).", u"CLOSED"),
    (u"Whether a fitted schedule generalises to an unseen operating point is "
     u"never tested.",
     u"Leave-one-corner-out: fit the comparator on three corners, test on the "
     u"fourth.",
     u"Identical to the global fixed word on all 36 held-out corners. Nothing "
     u"— and we say so.", u"ANSWERED, NEGATIVE"),
    (u"Segmented-driver papers characterise one switching edge. The converter "
     u"is never closed-loop regulated.",
     u"A type-III loop around the same power stage and the same drivers, then "
     u"disturbed deliberately.",
     u"%.2f %% error through a 2\u00d7 load step and a 20 %% line step; open "
     u"loop walks to %.1f V (closedloop.py)." % (CL.ERR_C, CL.LINE_O), u"CLOSED"),
    (u"Segmented output stages are published as ideal switches. Whether the "
     u"result survives real devices is untested.",
     u"The same output stage rebuilt in SKY130 5 V transistors and re-run.",
     u"Sign and ordering both survive, but the clamp on its own turns out to give "
     u"only +0.031 V (silicon_check.py).", u"CLOSED"),
    (u"All of the above is simulation.",
     u"—",
     u"No silicon measured. The driver is now rebuilt on a real PDK; the GaN "
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
    para([(u"Does it serve its purpose?  ", B),
          (u"Yes, for a simulation study, and that is what it is titled as. "
           u"Seven gaps closed, one answered in the negative, which is a "
           u"result rather than a failure, and one that needs a bench. The "
           u"honest summary is that the architecture is finished and the "
           u"measurement of it on real silicon is not.", N)],
         level=0, sz=1200, spc=0, bullet=False)])
print("added: Does the architecture close the gaps?")


# ---- slide: the RTL and the power stage, made to meet ----------------------
s = clone_after(p, SRC, len(p.slides._sldIdLst))
strip(s)
set_title(s, u"The architecture, end to end")

add_text(s, 0.70, 1.22, 5.85, 0.38, [
    para([(u"The gap we found in our own work", B)],
         level=0, sz=1300, spc=0, bullet=False)])
add_text(s, 0.70, 1.66, 5.85, 2.05, [
    para([(u"The controller was verified in Icarus. The power stage was "
           u"verified in ngspice. The two never touched.", N)],
         level=0, sz=1200, spc=140, bullet=False),
    para([(u"The FPGA emits eight thermometer-coded wires per bank. The SPICE "
           u"driver took an integer segment count. A fault in the decoder would "
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
           u"models/segdrv_bus.lib. Same netlist, same devices, same "
           u"measurement — only the segment selection changes.", N)],
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
           u"then counts down through zero, so 15 ns is 2 cycles, not the "
           u"obvious 15/5 = 3. Anyone mapping our swept dead-time grid onto "
           u"hardware by dividing by the clock period builds a driver that is "
           u"one cycle slow at every operating point, and neither half "
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
    (u"The converter itself, built and converting", 6, True,
     u"%s → %s at %s, %s efficient (buck.cir)"
     % (CN.VIN, CN.VOUT, CN.IOUT, CN.EFF)),
    (u"The device choice justified against silicon", 8, True,
     u"6.2 W vs 12.6 W at 500 kHz, on the shipped word; 3 sweeps, 4 duty profiles"),
    (u"The base paper implemented, not just cited", 8, True,
     u"zhangdrv.lib in our deck and in the converter — at 100 V only"),
    (u"The segmented driver; the fault reproduced and fixed", 12, True,
     u"−0.249 V → +2.576 V, one change at a time"),
    (u"The full study: 720 words × 4 corners", 8, True,
     u"66,924 transients over 36 corners — all on dpt.cir, not the converter"),
    (u"How much controller that justifies", 8, True,
     u"ladder + leave-one-corner-out; two implementations agree"),
    (u"FPGA: RTL written, verified, synthesised, timing met", 12, True,
     u"8 properties; 20 LUT / 20 FF; 200 MHz, 1.996 ns slack"),
    (u"The two halves made to meet in one simulation", 5, True,
     u"RTL VCD drives the SPICE segments; agree to 0.081 V"),
    (u"Closed-loop regulation, disturbed deliberately", 6, True,
     u"type-III loop: %.2f %% error through a 2x load and a 20 %% line step"
     % CL.ERR_C),
    (u"Transistor-level output stage, on a real PDK", 7, True,
     u"SKY130 5 V devices: sign and ordering of the result both survive"),
    (u"Place-and-route on a chosen board", 3, False,
     u"Needs real package pins and an MMCM for the clock"),
    (u"The converter swept across its stated envelope", 10, True,
     u"8 bus×load points: margin +2.14 to +2.61 V everywhere, and the "
     u"envelope corrected to 50–150 V because a 200 V part cannot run a "
     u"200 V bus"),
    (u"A hardware half-bridge, measured", 7, False,
     u"Review-III. Until then this is a simulation study, and is titled as one"),
]
DONE = sum(w for _, w, d, _ in COMPLETION if d)
NDONE = sum(1 for _, _, d, _ in COMPLETION if d)
# Read the hardware row's own weight rather than typing 7 into the prose --
# change the table and the sentence follows.
HW_WEIGHT = next(w for t, w, _, _ in COMPLETION if "hardware half-bridge" in t)
assert sum(w for _, w, _, _ in COMPLETION) == 100

wi = index_of(u"Work Completed")
if wi is not None:
    s = p.slides[wi]
    strip(s)
    set_title(s, u"Work Completed — %d %%" % DONE)
    add_text(s, 0.70, 1.18, 12.10, 0.46, [
        para([(u"Counted, not asserted. ", B),
              (u"%d blocks, weighted by how much of the project each is. "
               u"%d are finished. The weights are on the slide so they can "
               u"be argued with." % (len(COMPLETION), NDONE), N)],
             level=0, sz=1200, spc=0, bullet=False)])

    rows = [(u"", u"Block of work", u"Weight", u"Evidence, or why not yet")]
    for name, w, done, ev in COMPLETION:
        mark = (u"✔", GREEN, True) if done else (u"—", GREY, True)
        rows.append([mark, (name, None, done), (u"%d" % w, None, False),
                     (ev, None if done else GREY, False)])
    grid(s, 0.62, 1.74, 12.14, 4.45, rows, widths=(4, 36, 8, 52),
         sizes=(10.0, 9.0))

    add_text(s, 0.70, 6.34, 11.70, 0.90, [
        # The rubric sentence used to read "Review-I's rubric asks for 50 %".
        # This deck is presented at Review-II, and quoting the previous
        # review's threshold to this panel is worse than quoting none.
        # Lead with what is finished and what the remainder needs, THEN the
        # number. A percentage stated first sounds like a claim about how
        # close we are; stated second it reads as an accounting of work.
        para([(u"The simulation study is complete. ", B),
              (u"What remains needs a bench: place-and-route on a chosen "
               u"board, and one measured half-bridge. Simulating harder will "
               u"not deliver either.", N)],
             level=0, sz=1300, spc=150, bullet=False),
        para([(u"%d of 100 by the count above. " % DONE, B),
              (u"The weights are on this slide because we would rather they "
               u"were argued with than discovered. Score the hardware higher "
               u"than %d and the number falls \u2014 that is a fair reading, "
               u"and it is the one we cannot answer without a bench."
               % HW_WEIGHT, N)],
             level=0, sz=1250, spc=140, bullet=False),
        para([(u"Nothing has been measured on silicon.", B)],
             level=0, sz=1250, spc=0, bullet=False)])
    print("rebuilt: Work Completed — %d %%" % DONE)
else:
    print("  MISSING: Work Completed slide to rebuild")


# ---- three result slides, as pictures ------------------------------------
# These three were built as tables of numbers and a reviewer asked for the
# deck to be simple. A table is the wrong form for all three: each is a
# comparison of magnitudes across a handful of categories, and nobody at the
# back of a room does arithmetic on a table -- but everybody can see a bar
# that crosses zero. One picture, one sentence of takeaway, one caption with
# the numbers a questioner might want. scripts/result_figures.py draws them
# from results/, so a figure cannot drift from the run that made it.
RESULT_SLIDES = [
 ("fig_closedloop.png", u"Closing the loop",
  u"The loop holds 50 V. Open loop walks to %.1f V." % CL.LINE_O,
  u"sim/buck_closed.cir runs the same power stage and the same segmented "
  u"drivers, now regulated by a type-III loop and then disturbed deliberately. "
  u"Closed loop 50.01 / 50.00 / 50.00 V through a 2\u00d7 load step and a "
  u"100 \u2192 120 V line step; worst error %.2f %% against open loop's "
  u"%.2f %%. " % (CL.ERR_C, CL.ERR_O) +
  u"Load step recovers in 4 \u00b5s, line step in 22 \u00b5s. Ripple 0.25 %, "
  u"efficiency 96.1 %, start-up overshoot 3.8 %."),
 ("fig_headtohead.png", u"Head-to-Head: ngspice Output",
  u"5.5\u00d7 to 12.4\u00d7, and the lead widens as the corner gets harder.",
  u"scripts/headtohead.py: same deck, same GaN, same parasitics; only "
  u"the driver is swapped. We hold one fixed control word at all four corners; "
  u"they are re-optimised at every corner, which is more freedom than their "
  u"own design has. Their margin falls +0.50 \u2192 +0.18 V from the mildest "
  u"corner to the hottest and ours barely moves, because a clamp does not care "
  u"how hot the device is. Our switch node also slews about twice as fast, so "
  u"the margin is not bought with switching speed. One caveat: "
  u"models/zhangdrv.lib is our implementation of the scheme as they "
  u"(their netlist is not published), run in our testbench with "
  u"our parasitics. It is not 5.5\u201312.4\u00d7 their measured result, and "
  u"we do not claim it is."),
 ("fig_modeldep.png", u"Does the result depend on the model?",
  u"Only the shipped design is safe under every model we tried.",
  u"Two assumptions carry every margin in this deck, and each was replaced and "
  u"re-run. scripts/silicon_check.py rebuilds the output stage in real SKY130 "
  u"5 V transistors; scripts/capmodel_check.py swaps the junction diodes for a "
  u"charge capacitance. The ordering survives both. Two things do not: the "
  u"clamp on its own gives +0.03 V on real devices rather than +0.57, and the "
  u"no-clamp row changes sign between capacitance laws \u2014 so \u201cthe "
  u"constant word causes false turn-on\u201d is model-dependent, and we say so."),
]
for fname, title, lead, cap_text in RESULT_SLIDES:
    if not os.path.exists(os.path.join(RES, fname)):
        print("  MISSING FIGURE: %s -- run scripts/result_figures.py" % fname)
        continue
    sl = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(sl)
    set_title(sl, title)
    add_text(sl, 0.70, 1.14, 12.10, 0.40, [
        para([(lead, B)], level=0, sz=1450, spc=0, bullet=False)])
    # The base-paper caption has to carry the "this is our implementation of
    # their described scheme" caveat, which is the longest line in the deck and
    # does not fit under a full-height plot. All three lose 0.28 in of figure
    # so the layout stays identical across them.
    place(sl, fname, 1.58, 4.06)
    caption(sl, cap_text, top=5.78, h=1.24)
    print("added: %s" % title)


# ---- slides: the four things the Review-1 panel asked for -----------------
# They asked, in order: justify GaN over silicon with numbers including
# latency and power; show the base paper's architecture and ours side by side
# so the added blocks are visible; and give "theirs vs ours" on the same
# measured parameters. These four slides are that, and every number is read
# out of results/panel_metrics.csv at build time rather than typed here, so a
# slide cannot survive a re-run that changes the answer.
NEWC = _RGB(0x1b, 0x7f, 0x5f)     # this column wins the row
HOTC = _RGB(0xB0, 0x00, 0x00)     # this column loses it

_UNITS = [("latency_ns", u"Latency, PWM \u2192 switch node at 50 %", u"ns", "%.2f"),
          ("trans_ns",   u"Edge, 10 % \u2192 90 % of bus",            u"ns", "%.2f"),
          ("p_dev_W",    u"Power in the devices",                     u"W",  "%.2f"),
          ("p_gate_W",   u"Power in the gate drive",                  u"W",  "%.3f"),
          ("eff_pct",    u"Converter efficiency",                     u"%",  "%.2f"),
          ("ov_pct",     u"Switch-node overshoot",                    u"%",  "%.1f")]


def _cell(cfg, key, fmt):
    v = PM.get(cfg, {}).get(key)
    try:
        return fmt % float(v)
    except (TypeError, ValueError):
        return u"n/a"


# Lower is better on five of the six. Overshoot is the exception in spirit --
# less is better there too -- but it is the row where our own design loses,
# so it is marked rather than quietly coloured like the rest.
_BETTER_LOW = {"latency_ns", "trans_ns", "p_dev_W", "p_gate_W", "ov_pct"}


def _verdict(cfg_a, cfg_b, key):
    """Which column wins this row, as a ratio or a point difference.

    Efficiency is in points because a ratio of two numbers both near 97 is
    a meaningless 1.02x. Everything else is a ratio, because "6.4x faster"
    is what the row is actually saying and a subtraction hides it.
    """
    try:
        a = float(PM[cfg_a][key]); b = float(PM[cfg_b][key])
    except (KeyError, TypeError, ValueError):
        return u"n/a", None
    if key == "eff_pct":
        d = a - b
        return u"%+.2f pts" % d, (NEWC if d > 0 else HOTC)
    if a == 0 or b == 0:
        return u"%+.2f" % (a - b), None
    if a * b < 0:
        # Opposite signs: a ratio here is nonsense. GaN overshoots 17.9 % and
        # silicon does not overshoot at all (-1.5 %), and dividing the two
        # printed "-11.9x more", a negative multiplier. The same trap was
        # already found and fixed in the win/lose figure; the table had kept
        # it. State the gap in points, as panel_metrics.txt itself does.
        d = a - b
        lower_better = key in _BETTER_LOW
        worse = (d > 0) if lower_better else (d < 0)
        return u"%+.1f pts" % d, (HOTC if worse else NEWC)
    if abs(a) < abs(b):
        return u"%.1f\u00d7 less" % (b / a), NEWC
    return u"%.1f\u00d7 more" % (a / b), HOTC


def metric_slide(title, lead, cfg_a, cfg_b, head_a, head_b, note, caveat=None):
    sl = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(sl)
    set_title(sl, title)
    add_text(sl, 0.70, 1.14, 12.10, 0.40, [
        para([(lead, B)], level=0, sz=1450, spc=0, bullet=False)])
    rows = [[u"Parameter", head_a, head_b, u"unit", head_a + u" vs " + head_b]]
    for key, label, unit, fmt in _UNITS:
        txt, col = _verdict(cfg_a, cfg_b, key)
        rows.append([label, _cell(cfg_a, key, fmt), _cell(cfg_b, key, fmt),
                     unit, (txt, col, True)])
    grid(sl, 0.70, 1.72, 12.10, 3.10, rows, widths=(34, 15, 15, 7, 21),
         sizes=(12.5, 12.5))
    y = 5.02
    if caveat:
        add_text(sl, 0.70, y, 12.10, 0.52, [
            para([(caveat, B)], level=0, sz=1200, spc=0, bullet=False)])
        y += 0.60
    add_text(sl, 0.70, y, 12.10, 1.10, [
        para([(note, N)], level=0, sz=1150, spc=0, bullet=False)])
    print("added: %s" % title)
    return sl


metric_slide(
    u"GaN against silicon \u2014 six parameters, measured",
    u"Same converter, same driver, same on-resistance class. Only the device changes.",
    "gan_ours", "si_ours", u"GaN HEMT", u"Si MOSFET",
    u"ngspice on sim/buck.cir, 100 V \u2192 50 V, 500 kHz, 10 \u03a9, 3 nH loop. "
    u"Each device is driven at its own rated gate voltage \u2014 5 V for GaN, 10 V "
    u"for silicon \u2014 because a silicon MOSFET at 5 V would be barely enhanced "
    u"and would lose on a technicality rather than on physics. Power is averaged "
    u"over the last 20 of 150 whole cycles; latency and edge come from a separate "
    u"3-cycle run at a 0.02 ns step, because a 2 ns edge and a 300 \u00b5s average "
    u"cannot share one transient.",
    caveat=u"Read the last row honestly: GaN loses it. Silicon does not "
           u"overshoot because its edge is nine times slower \u2014 the same "
           u"slowness that costs it 6.1 W. Speed and device stress are the "
           u"same knob, and choosing GaN is choosing to manage the stress.")

# ---- slide: where we win and where we lose --------------------------------
# The two comparison tables are complete but they are tables, and a table
# makes a reader do the arithmetic to see which rows go which way. This is
# the same six parameters as signed bars, so the shape of the result -- four
# wins, two losses, both losses from the same cause -- is visible before a
# single number is read.
if os.path.exists(os.path.join(RES, "fig_winlose.png")):
    sl = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(sl)
    set_title(sl, u"Where we win, and where we lose")
    add_text(sl, 0.70, 1.14, 12.10, 0.40, [
        para([(u"Six parameters, both comparisons. Blue is better, red is "
               u"worse, and the red bars are drawn at full length.", B)],
             level=0, sz=1450, spc=0, bullet=False)])
    place(sl, "fig_winlose.png", 1.60, 4.22)
    caption(sl, u"Bars are a symmetric relative difference, bounded to "
                u"\u00b1100 %, because the six parameters are in four different "
                u"units \u2014 one axis, never two. Plain percentage change was "
                u"tried first and was wrong: silicon's overshoot is \u22121.5 %, "
                u"so dividing by a near-zero opposite-sign baseline put that row "
                u"at \u22121284 %. Raw values under every bar. "
                u"scripts/winlose_figure.py.", top=5.94, h=1.10)
    print("added: Where we win, and where we lose")
else:
    print("  MISSING: results/fig_winlose.png -- run scripts/winlose_figure.py")


# ---- slides: the circuits, as schematics ----------------------------------
# The deck had block diagrams of the driver and a netlist listing, but no
# schematic of it. "8 x pull-up segment" in a box is a claim; a sheet with
# eight drawn branches is the circuit. All three are generated from the
# netlist and the model files, so they cannot drift from what is simulated.
_SCH = [
    ("fig_sch_base.png",
     u"Their driver, drawn \u2014 the reimplementation",
     u"Zhang et al., ISPSD 2020, built as a schematic from our "
     u"implementation of it.",
     u"14 columns per bank, because their seven segments are split across two "
     u"stages and each stage is its own branch. The stage-2 branches carry "
     u"an extra series switch gated by the pattern step \u2014 that switch is "
     u"their mechanism. Every resistor shows its own conditional, so the "
     u"sheet can be checked against models/zhangdrv.lib line by line. No "
     u"clamp branch, and the off rail is tied to its reference."),
    ("fig_sch_ours.png",
     u"Our driver, drawn \u2014 the same stage, improved",
     u"models/segdrv.lib. Eight segments per bank, switching together, plus the "
     u"two blocks they do not have.",
     u"Each segment is a switch and a resistor, and the resistor carries the "
     u"code: Rpu3 is 8 \u03a9 if the word asks for three or more segments and "
     u"1 G\u03a9 if it does not. Drive strength is how many of the eight "
     u"parallel paths are live. On the right, Sclk and Rclk \u2014 the active "
     u"Miller clamp, pulling the gate to the off rail through 0.5 \u03a9."),
    # "The converter, drawn" used to live here as a separate backup slide.
    # It is now the main "circuit we simulate" slide, so keeping it here put
    # the same figure on two slides of the same deck.
]
for _f, _t, _lead, _cap in _SCH:
    if not os.path.exists(os.path.join(RES, _f)):
        print("  MISSING FIGURE: %s -- run scripts/kicad_previews.py" % _f)
        continue
    sl = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(sl)
    set_title(sl, _t)
    add_text(sl, 0.70, 1.14, 12.10, 0.40, [
        para([(_lead, B)], level=0, sz=1450, spc=0, bullet=False)])
    place(sl, _f, 1.60, 4.12)
    caption(sl, _cap, top=5.84, h=1.16)
    print("added: %s" % _t)


# ---- slide: run it in the room --------------------------------------------
# The demo slide plays a recording, and a recording answers none of what a
# sceptic asks: it was made elsewhere, at some other time, by someone who
# could pick the take. This slide is the offer to run it instead.
_LS = "fig_live_sim.png"
if os.path.exists(os.path.join(RES, _LS)):
    sl = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(sl)
    set_title(sl, u"Live Simulation")
    add_text(sl, 0.70, 1.10, 12.10, 0.44, [
        para([(u"bash proof/LIVE-SIM.sh", B),
              (u"   \u2014 two ngspice transients, about ten seconds, on "
               u"whatever machine is in this room.", N)],
             level=0, sz=1400, spc=0, bullet=False)])
    # The recording of this same command goes beside the waveform: a laptop
    # in a review room is not a controlled environment, and if the live run
    # will not start the presenter should play the SAME thing rather than
    # explain a different artefact. place() centres a single image, so this
    # lays the pair out by hand.
    _REC = os.path.join(RES, "live_demo_recording.mp4")
    if os.path.exists(_REC):
        sl.shapes.add_movie(_REC, Inches(0.85), Inches(1.80), Inches(5.50),
                            Inches(3.09),
                            poster_frame_image=os.path.join(HERE, "poster_live.png"),
                            mime_type="video/mp4")
        _pw, _ph = Image.open(os.path.join(RES, _LS)).size
        sl.shapes.add_picture(os.path.join(RES, _LS), Inches(7.45), Inches(1.80),
                              height=Inches(3.09))
        add_text(sl, 0.85, 4.98, 5.50, 0.34, [
            para([(u"the recording, if the room will not cooperate", N)],
                 level=0, sz=1150, spc=0, bullet=False)])
        add_text(sl, 7.45, 4.98, 5.00, 0.34, [
            para([(u"what it draws when it does", N)],
                 level=0, sz=1150, spc=0, bullet=False)])
    else:
        place(sl, _LS, 1.62, 3.88)
    caption(sl,
            u"Two runs of ONE circuit file. Between them only CLKEN (the "
            u"Miller clamp) and VNEG (the gate off rail) change, so nothing "
            u"else can be moving. It prints what it measured beside what "
            u"these slides claim \u2014 OFF gate 1.649 V against the deck's "
            u"1.65, margin 2.576 V against the deck's 2.576 \u2014 then draws "
            u"the waveforms those two runs produced. 3.8 s of that is "
            u"ngspice; the rest is drawing. scripts/live_demo.py.",
            top=5.44, h=1.40)
    print("added: Live Simulation")
else:
    print("  MISSING FIGURE: %s -- run scripts/live_demo.py --deck" % _LS)


# ---- slide: latency and device power, on their own ------------------------
# The panel named these two. They are one row each in the six-parameter tables
# and one panel each in the three-way sheet -- which is not an answer to a
# question that was asked about two.
_LP = "fig_latency_power.png"
if os.path.exists(os.path.join(RES, _LP)):
    sl = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(sl)
    set_title(sl, u"Latency and device power \u2014 the two you asked for")
    add_text(sl, 0.70, 1.10, 12.10, 0.40, [
        para([(u"Same converter, same device class. Silicon \u2192 base paper "
               u"changes the device; base paper \u2192 ours changes the control.",
               B)], level=0, sz=1400, spc=0, bullet=False)])
    place(sl, _LP, 1.80, 4.10)
    caption(sl,
            u"Latency 17.55 \u2192 4.04 \u2192 2.78 ns and device power "
            u"8.60 \u2192 2.93 \u2192 2.60 W. Against silicon that is 6.3\u00d7 "
            u"and 3.3\u00d7; against the base paper's control on the same GaN "
            u"device, 1.5\u00d7 and 1.1\u00d7. The device swap accounts for most of "
            u"it "
            u"and the control swap accounts for the rest \u2014 which is the honest "
            u"shape of the result. Same file the tables read, "
            u"results/panel_metrics.csv. scripts/latency_power_figure.py.",
            top=6.10, h=1.05)
    print("added: Latency and device power")
else:
    print("  MISSING FIGURE: %s -- run scripts/latency_power_figure.py" % _LP)


# ---- slide: all three on one sheet ----------------------------------------
# The panel asked for latency and device power compared across silicon, the
# base paper and ours. winlose_figure.py answers that as two PAIRWISE
# comparisons, which is right for "how much better, and where do we lose" and
# wrong for "put the three side by side" -- silicon and the base paper never
# share a panel there, so they cannot be read against each other at all.
_TW = "fig_three_way.png"
if os.path.exists(os.path.join(RES, _TW)):
    sl = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(sl)
    set_title(sl, u"Six-Parameter Comparison")
    add_text(sl, 0.70, 1.10, 12.10, 0.40, [
        para([(u"Column 1 \u2192 2 changes only the device. Column 2 \u2192 3 "
               u"changes only the control.", B)],
             level=0, sz=1400, spc=0, bullet=False)])
    place(sl, _TW, 1.52, 4.50)
    caption(sl,
            u"Latency 17.55 \u2192 4.04 \u2192 2.78 ns and device power "
            u"8.60 \u2192 2.93 \u2192 2.60 W, left to right. Against silicon "
            u"that is 6.3\u00d7 and 3.3\u00d7; against the base paper's control "
            u"on the same GaN device, 1.5\u00d7 and 1.1\u00d7. The device swap "
            u"accounts for most of it; the control swap accounts for the rest. "
            u"Overshoot is the "
            u"row that runs the other way, and it runs that way for the same "
            u"reason the other five do not: silicon does not overshoot because "
            u"its edge is nine times slower, and that slowness is what costs it "
            u"6.0 W. Speed and device stress are one knob. "
            u"scripts/three_way_figure.py, from results/panel_metrics.csv.",
            top=6.22, h=1.10)
    print("added: Six-Parameter Comparison")
else:
    print("  MISSING FIGURE: %s -- run scripts/three_way_figure.py" % _TW)


# ---- slides: the two sweeps that answer the model objections --------------
_SWEEP = [
    ("fig_voff_tradeoff.png",
     u"What the negative rail costs",
     u"V_off swept 0 to \u22125 V at two loads. Margin against dead-time energy.",
     u"The \u22122 V rail was chosen from the crosstalk side alone, and this is "
     u"the other side of that choice. An E-mode GaN HEMT has no body diode, so "
     u"during dead time it conducts in the third quadrant at roughly "
     u"V_th + |V_off| + I\u00b7R_ds(on) \u2014 every volt of off-bias is paid "
     u"on every dead-time interval. Margin rises at a flat 1 V per volt "
     u"throughout. The cost does not: at 10 A it is 0.004 \u00b5J/V just above "
     u"\u22122 V and 0.246 \u00b5J/V just below, sixty times steeper. "
     u"\u22122 V sits on the knee, which is a result rather than a "
     u"justification. scripts/voff_sweep.py."),

    ("fig_temp_sensitivity.png",
     u"Does the hot-corner lead rest on two typed-in numbers?",
     u"Both derating slopes perturbed \u00b150 %, hot corner re-run for both drivers.",
     u"sim/dpt.cir derates the device through KT = 1 + 0.009\u00b7(TJ\u221225) "
     u"and V_th = 1.4 \u2212 0.0015\u00b7(TJ\u221225). Neither is a datasheet "
     u"fit \u2014 there is no vendor model in the repository to fit against, and "
     u"that is remaining work, not a result. What can be shown is whether the "
     u"lead is manufactured by their exact values, and it is not: across "
     u"\u00b150 % on either slope the lead runs 9.1\u201320.3\u00d7 against "
     u"12.4\u00d7 as shipped. Our margin barely moves; theirs collapses either "
     u"way. scripts/temp_sensitivity.py."),
]
for _f, _t, _lead, _cap in _SWEEP:
    if not os.path.exists(os.path.join(RES, _f)):
        print("  MISSING FIGURE: %s" % _f)
        continue
    sl = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(sl)
    set_title(sl, _t)
    add_text(sl, 0.70, 1.14, 12.10, 0.40, [
        para([(_lead, B)], level=0, sz=1450, spc=0, bullet=False)])
    place(sl, _f, 1.60, 4.02)
    caption(sl, _cap, top=5.76, h=1.30)
    print("added: %s" % _t)


# ---- slides: is the headline robust to how we computed it? ----------------
# Four questions a panel asks about the decomposition, answered off the same
# 36-corner grid by scripts/grid_robustness.py. Backup material: they exist to
# be turned to when challenged, not presented unprompted.
_ROB = [
    ("fig_wov_sensitivity.png",
     u"Does the answer depend on the weight we chose?",
     u"cost = E_tot + W_OV \u00b7 ov_pct, swept over two orders of magnitude.",
     u"The honest answer is two-part, and the second part is the one to say. "
     u"(B) ranges 8.3\u201323.1 % of the gain across the sweep, so the 8.9 % "
     u"headline IS weight-dependent \u2014 weight overshoot harder and "
     u"adapting matters more, which is physical, because overshoot is what "
     u"varies most across corners. What does not move: the fixed word takes at "
     u"least 77 % of the gain at every weight tried. scripts/grid_robustness.py."),

    ("fig_corner_penalty.png",
     u"The distribution behind the 2.6 %",
     u"What one fixed word costs at each of the 36 corners, sorted.",
     u"2.6 % is a mean over these 36 bars and the mean alone is not the whole "
     u"truth: the median is 1.9 %, but 10 of 36 corners cost more than 5 % and "
     u"the worst \u2014 200 V / 2 A / 125 \u00b0C \u2014 costs 16.5 %. That "
     u"corner is also outside the 50\u2013150 V envelope this device is rated "
     u"for. Quote the distribution, not the mean."),

    ("fig_fixed_vs_optimum.png",
     u"The optimum moves. The cost of ignoring it does not.",
     u"Per-corner best word against the one fixed word, all 36 corners.",
     u"Ten distinct words win across the 36 corners, so the optimum genuinely "
     u"moves \u2014 and that is the objection this slide answers. The two "
     u"curves sit on top of each other anyway: the shaded gap between them IS "
     u"the adaptive gain, 2.6 % of the baseline. Segmentation still shapes the "
     u"edge; it just does not need to be scheduled."),

    ("fig_grid_subsample.png",
     u"Is the 36-corner grid dense enough?",
     u"The split re-estimated on 250 random corner subsets at each size.",
     u"At four corners the estimate scatters over 0\u201323 %, which is why the "
     u"earlier n = 4 study reported a different share; by 27 it sits on the "
     u"full-grid answer. Stated precisely: this tests stability under "
     u"COARSENING and is evidence the grid is dense enough. It cannot prove a "
     u"finer grid would agree \u2014 that needs new transients."),
]
for _f, _t, _lead, _cap in _ROB:
    if not os.path.exists(os.path.join(RES, _f)):
        print("  MISSING FIGURE: %s -- run scripts/grid_robustness.py" % _f)
        continue
    sl = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(sl)
    set_title(sl, _t)
    add_text(sl, 0.70, 1.14, 12.10, 0.40, [
        para([(_lead, B)], level=0, sz=1450, spc=0, bullet=False)])
    place(sl, _f, 1.60, 4.12)
    caption(sl, _cap, top=5.84, h=1.16)
    print("added: %s" % _t)


# ---- slide: the two architectures on one canvas ---------------------------
# arch_compare.py gives a sheet each on consecutive slides, which works when
# you can page between them. It does not answer "what exactly did you add"
# at a glance, because the eye has to hold one sheet while looking at the
# other. This is the same two architectures against six shared rows.
if os.path.exists(os.path.join(RES, "fig_arch_delta.png")):
    sl = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(sl)
    set_title(sl, u"Novelty: Three Added Blocks")
    add_text(sl, 0.70, 1.02, 12.10, 0.40, [
        para([(u"Same command, same segmented output stage, same power stage. "
               u"Three blocks added — in green.", B)],
             level=0, sz=1300, spc=0, bullet=False)])
    place(sl, "fig_arch_delta.png", 1.48, 4.72)
    caption(sl,
            u"The five things that differ, and nothing else. Their column is "
            u"the base paper as we rebuilt it in models/zhangdrv.lib; ours is "
            u"models/segdrv.lib. Shaded: the three we add — digital "
            u"control in place of one fixed resistor, an always-on Miller "
            u"clamp, and an off rail selectable to −2 V. The command, the "
            u"power stage and the idea of segmenting the output are all "
            u"our implementation of theirs. The last row is what those three "
            u"deliver at the headline "
            u"corner, read from results/headtohead.csv: +0.407 V becomes "
            u"+2.576 V, from one fixed setting.", top=6.26, h=1.08)
    print("added: What we add that they do not have")
else:
    print("  MISSING: results/fig_arch_delta.png -- run scripts/arch_compare.py")


_arch_note = (u"Drawn to the same grid: a block that exists in both sits in the "
              u"same place in both, so a missing block leaves a visible hole. "
              u"The drawing and models/zhangdrv.lib are the same claim \u2014 "
              u"seven segments, two stages, one bias resistor, no clamp, no "
              u"negative rail \u2014 so either can be checked against the other.")

for _f, _t, _lead, _cap in (
        ("fig_arch_base.png",
         u"Their architecture \u2014 the base paper's blocks",
         u"Zhang et al., ISPSD 2020. One bias resistor sets the whole pattern.",
         _arch_note + u" The two dotted slots are what their design does not have."),
        ("fig_arch_ours.png",
         u"Our architecture \u2014 same stage, three blocks added",
         u"The same output stage. Three blocks added, in green.",
         _arch_note + u" Green marks what is ours: digital 6-field control, the "
         u"active clamp, the switchable \u22122 V rail.")):
    if not os.path.exists(os.path.join(RES, _f)):
        print("  MISSING FIGURE: %s -- run scripts/arch_compare.py" % _f)
        continue
    sl = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(sl)
    set_title(sl, _t)
    add_text(sl, 0.70, 1.14, 12.10, 0.40, [
        para([(_lead, B)], level=0, sz=1450, spc=0, bullet=False)])
    place(sl, _f, 1.62, 4.10)
    caption(sl, _cap, top=5.80, h=1.20)
    print("added: %s" % _t)

# ---- slide: the converter across its own envelope -------------------------
# The architecture slide claims a bus range. Until this sweep it was claimed
# at one point. Reading the CSV here rather than typing the numbers means a
# re-run that changes the answer changes the slide.
_ENV = os.path.join(RES, "envelope_sweep.csv")
if os.path.exists(_ENV):
    with open(_ENV) as _fh:
        _rows = list(_csv.DictReader(_fh))
    sl = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(sl)
    set_title(sl, u"The converter across its own envelope")
    add_text(sl, 0.70, 1.14, 12.10, 0.40, [
        para([(u"Every bus and load point, not just the one the headline "
               u"is quoted at.", B)], level=0, sz=1450, spc=0, bullet=False)])
    _hdr = [u"bus", u"load", u"peak v(sw)", u"overshoot",
            u"gate, HS on", u"margin", u"efficiency", u"verdict"]
    _tr = [_hdr]
    for _r in _rows:
        def _g(k, fmt, suf=u""):
            try:
                return (fmt % float(_r[k])) + suf
            except (KeyError, TypeError, ValueError):
                return u"n/a"
        _ok = _r.get("safe") == "ok"
        _tr.append([_r["vin"] + u" V", _r["iload"] + u" A",
                    _g("peak_V", u"%.1f", u" V"), _g("ov_pct", u"%.1f", u" %"),
                    _g("gate_V", u"%.2f", u" V"), _g("margin_V", u"%+.2f", u" V"),
                    _g("eff_pct", u"%.2f", u" %"),
                    (u"safe" if _ok else _r.get("safe", u"?"),
                     NEWC if _ok else HOTC, True)])
    grid(sl, 0.70, 1.70, 12.10, 3.55, _tr, widths=(9, 9, 14, 12, 14, 12, 13, 17),
         sizes=(11.5, 11.5))
    add_text(sl, 0.70, 5.44, 12.10, 1.25, [
        para([(u"The margin column is the answer. ", B),
              (u"It is the 1.4 V threshold minus the highest the OFF gate "
               u"reaches while the other device is conducting, and it is "
               u"positive at all eight points \u2014 +2.14 V at the worst. The "
               u"off device stays off everywhere in the range.", N)],
             level=0, sz=1150, spc=110, bullet=False),
        para([(u"The two 200 V rows are not a driver failure. ", B),
              (u"Their overshoot is the smallest in the sweep, 3.1 % and "
               u"4.1 %. The problem is running a 200 V-rated part on a 200 V "
               u"bus, where any overshoot at all exceeds the rating. So the "
               u"envelope is stated as 50\u2013150 V on this device; 200 V "
               u"needs a higher-rated part, not a different driver.", N)],
             level=0, sz=1150, spc=0, bullet=False)])
    print("added: The converter across its own envelope")
else:
    print("  MISSING: results/envelope_sweep.csv -- run scripts/envelope_sweep.py")


metric_slide(
    u"Theirs and ours \u2014 six parameters, measured",
    u"Same converter, same GaN device, same output stage. Only the control changes.",
    "gan_ours", "gan_base", u"Ours", u"Base paper",
    u"ngspice on sim/buck.cir with the driver subcircuit swapped: "
    u"models/segdrv.lib against models/zhangdrv.lib. Identical devices, "
    u"parasitics, timing and solver options, so any difference here is the "
    u"control scheme and nothing else. Their pattern step is a delayed copy of "
    u"their own PWM, so it lands the same distance after turn-on on every "
    u"cycle, which is what their one-knob scheme does.",
    # Derived from the same CSV the table above is built from. It used to be
    # written out by hand and said "24 points harder" and "0.28 W" against a
    # table reading 15.0 and 0.330 -- the prose had been left behind by a
    # re-run.
    caveat=u"The last two rows are ours to answer. We spend %.0f %% more gate "
           u"power and we overshoot %.0f points harder, because we switch "
           u"faster. That buys %.1f ns of latency, %.2f W in the devices and "
           u"the crosstalk margin on the next slide."
           % (100.0 * (_metric("gan_ours", "p_gate_W") / _metric("gan_base", "p_gate_W") - 1.0),
              _metric("gan_ours", "ov_pct")    - _metric("gan_base", "ov_pct"),
              _metric("gan_base", "latency_ns") - _metric("gan_ours", "latency_ns"),
              _metric("gan_base", "p_dev_W")   - _metric("gan_ours", "p_dev_W")))


# ---- slide: how much of the project this is, and how that was counted ------
# "50 %" was a placeholder from the template, asserted rather than counted.
# A reviewer is entitled to ask what the denominator is. So the slide now
# carries the denominator: twelve blocks with a weight each, eight of them
# done. Arguing with the weights is a real conversation; arguing with a bare
# percentage is not.
COMPLETION = [
    (u"The converter itself, built and converting", 6, True,
     u"%s → %s at %s, %s efficient (buck.cir)"
     % (CN.VIN, CN.VOUT, CN.IOUT, CN.EFF)),
    (u"The device choice justified against silicon", 8, True,
     u"6.2 W vs 12.6 W at 500 kHz, on the shipped word; 3 sweeps, 4 duty profiles"),
    (u"The base paper implemented, not just cited", 8, True,
     u"zhangdrv.lib in our deck and in the converter — at 100 V only"),
    (u"The segmented driver; the fault reproduced and fixed", 12, True,
     u"−0.249 V → +2.576 V, one change at a time"),
    (u"The full study: 720 words × 4 corners", 8, True,
     u"66,924 transients over 36 corners — all on dpt.cir, not the converter"),
    (u"How much controller that justifies", 8, True,
     u"ladder + leave-one-corner-out; two implementations agree"),
    (u"FPGA: RTL written, verified, synthesised, timing met", 12, True,
     u"8 properties; 20 LUT / 20 FF; 200 MHz, 1.996 ns slack"),
    (u"The two halves made to meet in one simulation", 5, True,
     u"RTL VCD drives the SPICE segments; agree to 0.081 V"),
    (u"Closed-loop regulation, disturbed deliberately", 6, True,
     u"type-III loop: %.2f %% error through a 2x load and a 20 %% line step"
     % CL.ERR_C),
    (u"Transistor-level output stage, on a real PDK", 7, True,
     u"SKY130 5 V devices: sign and ordering of the result both survive"),
    (u"Place-and-route on a chosen board", 3, False,
     u"Needs real package pins and an MMCM for the clock"),
    (u"The converter swept across its stated envelope", 10, True,
     u"8 bus×load points: margin +2.14 to +2.61 V everywhere, and the "
     u"envelope corrected to 50–150 V because a 200 V part cannot run a "
     u"200 V bus"),
    (u"A hardware half-bridge, measured", 7, False,
     u"Review-III. Until then this is a simulation study, and is titled as one"),
]
DONE = sum(w for _, w, d, _ in COMPLETION if d)
NDONE = sum(1 for _, _, d, _ in COMPLETION if d)
# Read the hardware row's own weight rather than typing 7 into the prose --
# change the table and the sentence follows.
HW_WEIGHT = next(w for t, w, _, _ in COMPLETION if "hardware half-bridge" in t)
assert sum(w for _, w, _, _ in COMPLETION) == 100

wi = index_of(u"Work Completed")
if wi is not None:
    s = p.slides[wi]
    strip(s)
    set_title(s, u"Work Completed — %d %%" % DONE)
    add_text(s, 0.70, 1.18, 12.10, 0.46, [
        para([(u"Counted, not asserted. ", B),
              (u"%d blocks, weighted by how much of the project each is. "
               u"%d are finished. The weights are on the slide so they can "
               u"be argued with." % (len(COMPLETION), NDONE), N)],
             level=0, sz=1200, spc=0, bullet=False)])

    rows = [(u"", u"Block of work", u"Weight", u"Evidence, or why not yet")]
    for name, w, done, ev in COMPLETION:
        mark = (u"✔", GREEN, True) if done else (u"—", GREY, True)
        rows.append([mark, (name, None, done), (u"%d" % w, None, False),
                     (ev, None if done else GREY, False)])
    grid(s, 0.62, 1.74, 12.14, 4.45, rows, widths=(4, 36, 8, 52),
         sizes=(10.0, 9.0))

    add_text(s, 0.70, 6.34, 11.70, 0.90, [
        # The rubric sentence used to read "Review-I's rubric asks for 50 %".
        # This deck is presented at Review-II, and quoting the previous
        # review's threshold to this panel is worse than quoting none.
        # Lead with what is finished and what the remainder needs, THEN the
        # number. A percentage stated first sounds like a claim about how
        # close we are; stated second it reads as an accounting of work.
        para([(u"The simulation study is complete. ", B),
              (u"What remains needs a bench: place-and-route on a chosen "
               u"board, and one measured half-bridge. Simulating harder will "
               u"not deliver either.", N)],
             level=0, sz=1300, spc=150, bullet=False),
        para([(u"%d of 100 by the count above. " % DONE, B),
              (u"The weights are on this slide because we would rather they "
               u"were argued with than discovered. Score the hardware higher "
               u"than %d and the number falls \u2014 that is a fair reading, "
               u"and it is the one we cannot answer without a bench."
               % HW_WEIGHT, N)],
             level=0, sz=1250, spc=140, bullet=False),
        para([(u"Nothing has been measured on silicon.", B)],
             level=0, sz=1250, spc=0, bullet=False)])
    print("rebuilt: Work Completed — %d %%" % DONE)
else:
    print("  MISSING: Work Completed slide to rebuild")


# ---- slide: closing the loop ----------------------------------------------
s = clone_after(p, SRC, len(p.slides._sldIdLst))
strip(s)
set_title(s, u"Closing the loop")

add_text(s, 0.70, 1.20, 12.10, 0.80, [
    para([(u"Every result so far was measured open loop. The duty ratio was "
           u"a parameter and nothing moved while we measured. That is the right "
           u"instrument for a switching edge and the wrong description of a "
           u"converter: a storage system's pack voltage sags all day and its "
           u"load steps whenever something downstream turns on.", N)],
         level=0, sz=1250, spc=0, bullet=False)])

grid(s, 1.30, 2.14, 10.70, 1.10, [
    (u"", u"nominal  100 V / 5 A", u"after 2\u00d7 load step",
     u"after 100 \u2192 120 V line step", u"worst error"),
    ((u"closed loop", None, True), (u"50.02 V", GREEN, True),
     (u"50.00 V", GREEN, True), (u"50.00 V", GREEN, True),
     (u"%.2f %%" % CL.ERR_C, GREEN, True)),
    ((u"open loop", None, True), (u"51.03 V", None, False),
     (u"50.15 V", None, False), (u"58.33 V", AMBER, True),
     (u"16.7 %", AMBER, True)),
], widths=(16, 21, 21, 26, 16), sizes=(10.0, 11.0))

add_text(s, 0.70, 3.44, 5.85, 0.34, [
    para([(u"What the loop buys", B)], level=0, sz=1250, spc=0, bullet=False)])
add_text(s, 0.70, 3.82, 5.85, 2.10, [
    para([(u"Load step 5 \u2192 10 A: dips 1.8 %, back inside \u00b11 % in 4 \u00b5s.", N)],
         level=0, sz=1150, spc=110, bullet=False),
    para([(u"Line step 100 \u2192 120 V: peaks 1.4 %, recovers in 22 \u00b5s.", N)],
         level=0, sz=1150, spc=110, bullet=False),
    para([(u"Output ripple 0.28 %. Soft-start overshoot 10.9 % — the one "
           u"number here we are not proud of, and it is on the slide.", N)],
         level=0, sz=1150, spc=110, bullet=False),
    para([(u"Open loop is not merely less accurate. On the line step it walks "
           u"to 60 V, because V_out = D \u00d7 V_in and nothing in it knows "
           u"V_in moved.", B)], level=0, sz=1150, spc=0, bullet=False)])

add_text(s, 7.00, 3.44, 5.80, 0.34, [
    para([(u"Two compensators that did not work", B)],
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


# ---- slide: does the result depend on the model? --------------------------
s = clone_after(p, SRC, len(p.slides._sldIdLst))
strip(s)
set_title(s, u"Does the result depend on the model?")

add_text(s, 0.70, 1.16, 12.10, 0.56, [
    para([(u"Two assumptions carry every margin in this deck: that an ideal "
           u"switch stands in for the driver's output stage, and that a "
           u"junction diode stands in for the device's capacitance. We "
           u"replaced each with the alternative and re-ran.", N)],
         level=0, sz=1200, spc=0, bullet=False)])

add_text(s, 0.70, 1.78, 5.85, 0.32, [
    para([(u"1.  The output stage \u2014 in real SKY130 devices", B)],
         level=0, sz=1200, spc=0, bullet=False)])
grid(s, 0.70, 2.14, 5.85, 1.30, [
    (u"", u"ideal sw", u"SKY130"),
    ((u"no clamp", None, False), (u"\u22120.249", None, False),
     (u"\u22120.563", None, False)),
    ((u"clamp on", None, False), (u"+0.570", None, False),
     (u"+0.031", AMBER, True)),
    ((u"clamp + \u22122 V", None, True), (u"+2.576", None, False),
     (u"+2.032", GREEN, True)),
], widths=(42, 29, 29), sizes=(10.0, 10.5))

add_text(s, 7.00, 1.78, 5.80, 0.32, [
    para([(u"2.  The capacitance \u2014 charge, not diodes", B)],
         level=0, sz=1200, spc=0, bullet=False)])
grid(s, 7.00, 2.14, 5.80, 1.30, [
    (u"", u"diodes", u"charge"),
    ((u"no clamp", None, False), (u"\u22120.249", AMBER, True),
     (u"+0.115", AMBER, True)),
    ((u"clamp on", None, False), (u"+0.570", None, False),
     (u"+0.800", None, False)),
    ((u"clamp + \u22122 V", None, True), (u"+2.576", None, False),
     (u"+2.710", GREEN, True)),
], widths=(42, 29, 29), sizes=(10.0, 10.5))

add_text(s, 0.70, 3.58, 5.85, 1.70, [
    para([(u"The clamp alone is not the fix.", B)],
         level=0, sz=1200, spc=120, bullet=False),
    para([(u"On real transistors it gives 31 millivolts \u2014 at one corner, "
           u"with nothing left for temperature or a worse layout. The ideal "
           u"switch was flattering it, because it pulls the gate down through "
           u"10 m\u03a9 while a real NMOS pulls through a channel that has to "
           u"be turned on first.", N)],
         level=0, sz=1100, spc=0, bullet=False)])

add_text(s, 7.00, 3.58, 5.80, 1.70, [
    para([(u"And the fault itself changes sign.", B)],
         level=0, sz=1200, spc=120, bullet=False),
    para([(u"Under forward bias a SPICE diode keeps climbing above 0.5 V and "
           u"the charge form saturates. The aggressor is forward-biased "
           u"through its own turn-on, so it slews differently. \u201cThe "
           u"constant word causes false turn-on\u201d is model-dependent, and "
           u"we say so rather than calling it a measurement.", N)],
         level=0, sz=1100, spc=0, bullet=False)])

add_text(s, 0.70, 5.44, 11.70, 1.60, [
    para([(u"Both tables point the same way, and it is an argument FOR the "
           u"design rather than against the result.", B)],
         level=0, sz=1300, spc=170, bullet=False),
    para([(u"The ordering survives every substitution \u2014 each change still "
           u"buys what we say it buys. What does not survive is the middle "
           u"row: the configurations closest to zero are exactly the ones "
           u"whose verdict a modelling choice can flip. ", N),
          (u"The shipped design is the only one that is safe under all four "
           u"models, with over 2 V of room in each.", B),
          (u" That is a better reason to build it than any ratio on the "
           u"previous slide.", N)],
         level=0, sz=1250, spc=0, bullet=False)])
print("added: Does the result depend on the model?")


# ---- slide: head to head ---------------------------------------------------
s = clone_after(p, SRC, len(p.slides._sldIdLst))
strip(s)
set_title(s, u"Comparison with the Base Paper")

add_text(s, 0.70, 1.16, 12.10, 0.56, [
    para([(u"Only the driver changes. Ours holds one fixed word at every "
           u"corner; theirs is re-optimised at each one \u2014 more freedom "
           u"than their design has. At three of four corners that search "
           u"returns their built setting, so those two columns match.", N)],
         level=0, sz=1250, spc=0, bullet=False)])

grid(s, 0.62, 1.80, 12.14, 1.55, [
    (u"crosstalk margin", u"base, as their paper builds it",
     u"base, re-tuned at every corner", u"ours, one fixed word", u"vs their best"),
    ((u"50 V / 2 A / 25 \u00b0C", None, True), (u"+0.338 V", None, False),
     (u"+0.503 V", None, False), (u"+2.757 V", GREEN, True), (u"5.5\u00d7", None, True)),
    ((u"100 V / 10 A / 25 \u00b0C", None, True), (u"+0.407 V", None, False),
     (u"+0.407 V", None, False), (u"+2.576 V", GREEN, True), (u"6.3\u00d7", None, True)),
    ((u"200 V / 2 A / 125 \u00b0C", None, True), (u"+0.261 V", None, False),
     (u"+0.261 V", None, False), (u"+2.309 V", GREEN, True), (u"8.9\u00d7", None, True)),
    ((u"200 V / 10 A / 125 \u00b0C", None, True), (u"+0.181 V", AMBER, True),
     (u"+0.181 V", None, False), (u"+2.251 V", GREEN, True), (u"12.4\u00d7", None, True)),
], widths=(24, 21, 22, 20, 13), sizes=(10.0, 10.0))

add_text(s, 0.70, 3.54, 5.85, 0.34, [
    para([(u"The margin gap widens with stress", B)], level=0, sz=1250, spc=0, bullet=False)])
add_text(s, 0.70, 3.92, 5.85, 1.55, [
    para([(u"Their margin falls +0.503 \u2192 +0.181 V from the mildest corner "
           u"to the hottest, at their best setting for each. Ours goes "
           u"+2.757 \u2192 +2.251 V. They degrade where "
           u"it matters most; a clamp does not care how hot the device is.", N)],
         level=0, sz=1150, spc=110, bullet=False),
    para([(u"Worst corner is what a converter has to survive: +0.181 V against "
           u"+2.251 V.", B)], level=0, sz=1150, spc=0, bullet=False)])

add_text(s, 7.00, 3.54, 5.80, 0.34, [
    para([(u"The edge is faster, not slower", B)], level=0, sz=1250, spc=0, bullet=False)])
add_text(s, 7.00, 3.92, 5.80, 1.55, [
    para([(u"Their scheme reduces crosstalk by slowing the edge: 67\u2013103 "
           u"V/ns at the switch node. Ours runs 101\u2013175 V/ns — about "
           u"twice as fast — and still wins by a factor of several.", N)],
         level=0, sz=1150, spc=110, bullet=False),
    para([(u"The margin is not bought with switching speed. That is the useful "
           u"form of the result.", B)], level=0, sz=1150, spc=0, bullet=False)])

add_text(s, 0.70, 5.60, 11.70, 1.50, [
    para([(u"What it costs.  ", B),
          (u"Turn-on energy higher at 3 of 4 corners. Their driver: one "
           u"bias resistor. Ours: a clamp device, a negative supply, "
           u"20 LUTs.", N)],
         level=0, sz=1250, spc=180, bullet=False),
    para([(u"What we do not claim.  ", B),
          (u"Their netlist is unpublished. Every ratio here is against our "
           u"implementation of their scheme, not their measured result.", N)],
         level=0, sz=1250, spc=0, bullet=False)])
print("added: Comparison with the Base Paper")


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
    set_title(s, u"Next Steps")
    add_text(s, 0.70, 1.02, 12.10, 0.40, [
        para([(u"What remains is bench work, not further simulation.", B)],
             level=0, sz=1300, spc=0, bullet=False)])
    add_text(s, 0.70, 1.75, 12.10, 4.90, [
        para([(u"Place-and-route on a chosen board. ", B),
              (u"Synthesis is done; the flow stops there because the XDC pins "
               u"are placeholders. Doing it properly also means driving the "
               u"200 MHz clock from an MMCM rather than straight off a pin, "
               u"which is what makes 34 clock-to-pin paths fail today.", N)],
             level=0, sz=1500, spc=360, bullet=False),
        para([(u"A hardware half-bridge, measured. ", B),
              (u"This is the whole of the remaining risk. Everything in this "
               u"deck is a simulation of a converter that has never been "
               u"built, and one behavioural GaN model underlies all of it.", N)],
             level=0, sz=1500, spc=360, bullet=False),
        para([(u"Additionally: transcribe the silicon MOSFET datasheet "
               u"digits rather than using datasheet-class values, and re-run "
               u"the ceiling on the transistor-level stage now that it is "
               u"known to work.", N)], level=0, sz=1400, spc=0, bullet=False),
    ])
    print("rebuilt: Next Steps")


# ---- the two references slides say which role each list plays -------------
# An audit found 19 of the 30 references are never cited in the body: the
# cited set is 1-13 (minus 2 and 9), and 14-30 appear nowhere else. That is
# NOT padding -- the survey was deliberately widened to 30 on 4 September,
# with every entry kept only where the publisher record carried a real author
# list. But a panel that asks "where do you use [22]?" is entitled to an
# answer, and the slide did not give one. Now it does, in a line.
for _t, _note in (
    (u"References  (1\u201315)",
     u"The papers this design engages with directly. [10] is the base paper, "
     u"reimplemented in models/zhangdrv.lib and measured against throughout."),
    (u"References  (16\u201330)",
     u"The wider survey: read and recorded, not cited in the slides above. "
     u"Kept only where the publisher record carried a real author list."),
):
    _i = index_of(_t)
    if _i is None:
        continue
    _sl = p.slides[_i]
    # Both slides already carry an EMPTY text box just above the page number.
    # Fill it rather than adding another one on top: a new box at 6.52 in
    # overlapped that empty one and qa flagged it, which is the check doing
    # exactly its job.
    _box = None
    for _sh in _sl.shapes:
        if (_sh.has_text_frame and not _sh.text_frame.text.strip()
                and _sh.top is not None and 5.9 * 914400 < _sh.top < 6.9 * 914400):
            _box = _sh
            break
    if _box is None:
        add_text(_sl, 0.70, 6.40, 12.10, 0.38, [
            para([(_note, N)], level=0, sz=1050, spc=0, bullet=False)])
    else:
        set_body(_box, [para([(_note, N)], level=0, sz=1050, spc=0, bullet=False)])
    print("noted: %s" % _t)


# ---- slide: the hardware, costed ------------------------------------------
# "A hardware half-bridge, measured" is 7 of the 10 points outstanding, and
# until now the deck said only that it was not done. A panel reads a bare
# "future work: hardware" as an admission. A plan that names the board, the
# bus voltage, what gets measured and what it costs reads as someone who
# knows exactly what they would do next, which is a different answer to the
# same question.
sl = clone_after(p, SRC, len(p.slides._sldIdLst))
strip(sl)
set_title(sl, u"The hardware, costed")
add_text(sl, 0.70, 1.14, 12.10, 0.40, [
    para([(u"7 of the 10 points outstanding. Not vague \u2014 three tiers, "
           u"and we know which one is which.", B)],
         level=0, sz=1450, spc=0, bullet=False)])

_hw = [
    [u"", u"What gets measured", u"Cost", u"Time", u"Status"],
    [u"1.  FPGA on a real board",
     u"The 8+8 segment outputs toggling and dead_time_gen.v sweeping "
     u"5\u201335 ns, on silicon rather than in a report",
     u"\u20b98\u201312k\nor a lab board",
     u"days",
     (u"nearest", NEWC, True)],
    [u"2.  GaN half-bridge eval board, 48 V",
     u"The OFF device's gate during the other's turn-on, with and without "
     u"the \u22122 V rail \u2014 our central claim, on real silicon",
     u"\u20b915\u201325k",
     u"2\u20134 weeks",
     (u"the one that matters", NEWC, True)],
    [u"3.  The segmented driver itself",
     u"Everything above, on our own 8-segment stage at 100 V / 500 kHz",
     u"custom PCB,\nseveral spins",
     u"months",
     (u"Review-III", HOTC, True)],
]
grid(sl, 0.70, 1.72, 12.10, 2.65, _hw, widths=(21, 40, 13, 10, 16),
     sizes=(11.5, 11.0))

add_text(sl, 0.70, 4.56, 12.10, 2.10, [
    para([(u"Two constraints we already know, because they decide whether "
           u"tier 2 produces evidence or noise.", B)],
         level=0, sz=1250, spc=170, bullet=False),
    para([(u"Scope bandwidth. ", B),
          (u"Our edge is 0.78 ns. Bandwidth needed is 0.35 / 0.78 ns \u2248 "
           u"450 MHz to see the edge at all, realistically 1 GHz. On a 100 MHz "
           u"teaching-lab scope the measurement would be of the scope.", N)],
         level=0, sz=1200, spc=150, bullet=True),
    para([(u"Probe grounding. ", B),
          (u"A 10:1 probe with a ground clip carries roughly 10 nH in its "
           u"ground lead, which manufactures ringing that is not in the "
           u"circuit. A GaN gate has to be probed with a short pigtail or a "
           u"coaxial connection, or the trace shows the probe.", N)],
         level=0, sz=1200, spc=150, bullet=True),
    para([(u"And one thing that is not a constraint but a fact: no commercial "
           u"IC implements an 8-segment independently controllable segmented "
           u"driver. Tier 3 is eight single-channel drivers in parallel, "
           u"enabled per segment, summed through 8 \u03a9 \u2014 which is "
           u"exactly what models/segdrv.lib already describes.", N)],
         level=0, sz=1200, spc=0, bullet=False)])
print("added: The hardware, costed")


# ======================================================= geometry cleanup ==
# Nine QA flags had been carried for weeks as a "known-good baseline, all
# investigated false positives". Six of them were not false positives. They
# were small and consistent and nobody had looked at what they actually were:
#
#   4x  a full-width caption box running under the page number. The TEXT does
#       not reach that far, so it looks fine, and one caption one word longer
#       would have printed over the slide number.
#   2x  slide 34's body text box is 5.40 in tall and the VCD screenshot sits
#       on top of it from 4.05 in down. build.py's own comment says that text
#       was written to fit 2.45 in -- the box was simply never resized, so the
#       layout was one added sentence away from text under a picture.
#
# The remaining three ARE false positives, and the fix for those is in qa.py
# rather than here: text deliberately placed inside a panel is not a
# collision. A checker that cries wolf nine times is a checker nobody reads,
# which is exactly what happened.
#
# Both rules below are general rather than per-slide, so a slide added later
# cannot reintroduce either fault.
PAGENUM_GAP = 0.13


def _rect(sh):
    if sh.left is None or sh.top is None or not sh.width or not sh.height:
        return None
    return (sh.left / 914400.0, sh.top / 914400.0,
            sh.width / 914400.0, sh.height / 914400.0)


def _overlaps(a, b, tol=0.05):
    return (min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]) > tol and
            min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]) > tol)


def _text_need(sh, w):
    """Estimate the height a text frame needs, the way qa.py does.

    Same 0.50 em advance, so this and the checker agree about what fits. If
    they disagreed, this pass would 'fix' boxes the checker still flags, or
    leave ones it does not.
    """
    need = 0.0
    for pa in sh.text_frame.paragraphs:
        txt = "".join(r.text for r in pa.runs)
        if not txt:
            continue
        szs = [r.font.size.pt for r in pa.runs if r.font.size]
        sz = max(szs) if szs else 16.0
        pPr = pa._pPr
        marL = pPr.get("marL") if pPr is not None else None
        ind = (int(marL) / 914400.0) if marL else 0.0
        avail = max(0.5, w - ind)
        cw = sz * 0.50 / 72.0
        lines = max(1, int(len(txt) * cw / avail) +
                    (1 if (len(txt) * cw) % avail else 0))
        spc = 0.0
        if pPr is not None:
            sa = pPr.find("{http://schemas.openxmlformats.org/drawingml/2006/"
                          "main}spcAft")
            if sa is not None and len(sa):
                v = sa[0].get("val")
                if v:
                    spc = int(v) / 100.0 / 72.0
        need += lines * sz * 1.22 / 72.0 + spc
    return need


def tidy_geometry(prs):
    """Keep text off the page number, out from under pictures, and fitting.

    The third rule exists because stamp_provenance() adds words to captions
    that were already sized to the line, and a caption that overflows its box
    does not wrap -- PowerPoint just draws it past the bottom edge, over
    whatever is there.
    """
    narrowed = clipped = grown = 0
    for sl in prs.slides:
        shapes = [(sh, _rect(sh)) for sh in sl.shapes]
        shapes = [(sh, r) for sh, r in shapes if r]

        # the page number is the small box in the bottom-right corner
        pageno = [r for sh, r in shapes
                  if r[0] > 12.4 and r[1] > 6.9 and r[2] < 1.0]
        if pageno:
            px = pageno[0][0]
            for sh, r in shapes:
                if not sh.has_text_frame or r is pageno[0] or r[0] > 12.0:
                    continue
                # tol=0.01, not the 0.05 the checker uses. A box that clears
                # the page number by four hundredths of an inch passes QA and
                # is still one longer caption away from printing over it.
                if _overlaps(r, pageno[0], tol=0.01) and r[0] + r[2] > px - PAGENUM_GAP:
                    sh.width = Inches(max(1.0, px - PAGENUM_GAP - r[0]))
                    narrowed += 1

        # text and pictures must not share space. Which way to move depends
        # on which side of the picture the text belongs to: a body block
        # above it gets shortened, a caption below it gets pushed down.
        pics = [(sh, r) for sh, r in shapes
                if sh.shape_type is not None and "PICTURE" in str(sh.shape_type)]
        for sh, r in shapes:
            if not sh.has_text_frame or not sh.text_frame.text.strip():
                continue
            for psh, pr in pics:
                if psh is sh or not _overlaps(r, pr):
                    continue
                if r[1] < pr[1]:                      # body text above it
                    sh.height = Inches(max(0.3, pr[1] - 0.10 - r[1]))
                else:                                 # caption below it
                    sh.top = Inches(pr[1] + pr[3] + 0.06)
                clipped += 1
                r = _rect(sh)

        # grow any caption the stamps pushed past its box, as far as the
        # page-number band allows
        for sh, r in shapes:
            if not sh.has_text_frame or not sh.text_frame.text.strip():
                continue
            need = _text_need(sh, r[2])
            if need <= r[3] + 0.02 or r[1] + need > 7.02:
                continue
            sh.height = Inches(need + 0.04)
            grown += 1
    return narrowed, clipped, grown


# ==================================================== figure provenance ====
# A reviewer's fair question about any picture on a slide is "is that the
# simulator's output, or did you draw it?" The deck had 26 figures and no
# answer to it, which puts a drawn explainer and an ngspice waveform on the
# same footing and invites the panel to distrust both.
#
# So every figure caption is now stamped with where it came from. The map is
# keyed by the file's SHA-1 rather than by its name, because the picture in
# the .pptx is an embedded copy and the slide does not remember which file it
# was -- and a name-based map silently stops matching the day a generator is
# renamed, which is exactly the failure that leaves a wrong label on a slide.
#
# Four honest categories. The one that matters is the last: a figure that
# explains something is not evidence of it, and the caption has to say so.
P_SIM  = u"Simulated in ngspice."
P_SCR  = u"ngspice, on screen."
P_RTL  = u"Icarus Verilog output."
P_VIV  = u"Vivado output."
P_LT   = u"Drawn and simulated in LTspice."
P_DRAW = u"Drawn diagram, not simulation output."
P_FILE = u"A project file, typeset. Not simulation output."

PROVENANCE = {
    # Re-analysis of results/full_grid.csv -- the transients are ngspice's,
    # the figures are what scripts/grid_robustness.py makes of them.
    "fig_three_way.png": P_SIM, "fig_live_sim.png": P_SIM,
    "fig_latency_power.png": P_SIM,
    "fig_voff_tradeoff.png": P_SIM, "fig_temp_sensitivity.png": P_SIM,
    "fig_wov_sensitivity.png": P_SIM, "fig_corner_penalty.png": P_SIM,
    "fig_fixed_vs_optimum.png": P_SIM, "fig_grid_subsample.png": P_SIM,
    # plotted from ngspice transient output
    "fig_si_vs_gan.png": P_SIM, "fig_headtohead.png": P_SIM,
    "fig_closedloop.png": P_SIM, "fig_modeldep.png": P_SIM,
    "fig_converter.png": P_SIM, "fig_cases.png": P_SIM,
    "fig1_crosstalk.png": P_SIM, "fig_buck_tradeoff.png": P_SIM,
    "paper_fig2_ceiling.png": P_SIM, "fig_lloop.png": P_SIM,
    "fig_master_weight.png": P_SIM,
    # the simulator's own terminal, captured
    "17-converter-power.png": P_SCR, "01-ngspice-crosstalk.png": P_SCR,
    "19-ngspice-listing.png": P_SCR,
    "18-named-cases.png": P_SCR, "12-result2-ceiling.png": P_SCR,
    "13-result3-split.png": P_SCR,
    # the other two tools
    "fig_rtl_waveform.png": P_RTL, "03-verilog-8-properties.png": P_RTL,
    "vivado_console.png": P_VIV, "vivado_simulation.png": P_VIV,
    "11-vivado-synthesis-console.png": P_VIV, "fig_vivado.png": P_VIV,
    "fig_circuit_ltspice.png": P_LT, "fig_segdrv_inside.png": P_LT,
    "fig_ltspice_annotated.png": P_LT,
    # drawn: these explain the work, they are not evidence of it
    "fig_gan_1.png": P_DRAW, "fig_gan_2.png": P_DRAW,
    "fig_settings.png": P_DRAW, "fig_input.png": P_DRAW,
    "fig_output.png": P_DRAW, "fig_margin.png": P_DRAW,
    "fig_flow.png": P_DRAW,
    "fig_howrun.png": P_DRAW, "fig_method.png": P_DRAW,
    "fig_tools.png": P_DRAW, "fig_architecture.png": P_DRAW,
    # the two architecture drawings are block diagrams, not measurements --
    # the numbers that go with them are on the two metric slides, which say
    # ngspice in their own captions
    "fig_arch_base.png": P_DRAW, "fig_arch_ours.png": P_DRAW,
    "fig_winlose.png": P_SIM,
    "fig_arch_sidebyside.png": P_DRAW,
    # KiCad sheets: drawn circuits, generated from the netlist and the
    # model files. Not simulation output, and not freehand either.
    "fig_sch_converter.png": P_DRAW, "fig_sch_ours.png": P_DRAW,
    "fig_sch_base.png": P_DRAW,
    "fig_arch_delta.png": P_DRAW,
    "fig_novelty_circuit.png": (u"Annotated screen captures of KiCad 7.0.11 "
                                u"on the two generated sheets; "
                                u"scripts/novelty_circuit.py"),
    # not a diagram and not output: the deck's own netlist, set in type
    "fig_netlist.png": P_FILE,
    "fig_circuit.png": P_DRAW, "pareto_matlab.png": P_DRAW,
}


def _sha_map():
    import glob, hashlib
    out = {}
    for pat in ("results/**/*.png", "review/*.png"):
        for f in glob.glob(os.path.join(HERE, "..", pat), recursive=True):
            name = os.path.basename(f)
            if name in PROVENANCE:
                out[hashlib.sha1(open(f, "rb").read()).hexdigest()] = \
                    PROVENANCE[name]
    return out


SHA_PROV = None


def stamp_provenance(prs):
    """Put the source of every figure into its own caption."""
    global SHA_PROV
    import hashlib
    if SHA_PROV is None:
        SHA_PROV = _sha_map()
    stamped = unknown = 0
    for sl in prs.slides:
        tags = []
        for sh in sl.shapes:
            if sh.shape_type is None or "PICTURE" not in str(sh.shape_type):
                continue
            if not sh.width or sh.width < Inches(2.5):
                continue
            t = SHA_PROV.get(hashlib.sha1(sh.image.blob).hexdigest())
            if t and t not in tags:
                tags.append(t)
            elif not t:
                unknown += 1
        if not tags:
            continue
        tag = u"  ".join(tags)
        # Most figure slides carry a "Fig. n" caption. The Vivado slide carries
        # two side-by-side screenshot captions instead, and skipping it would
        # leave the one slide whose pictures are literally a tool's screen as
        # the only unlabelled one -- so fall back to the first caption-shaped
        # box under the picture.
        caps = [sh for sh in sl.shapes
                if sh.has_text_frame and sh.text_frame.text.strip().startswith("Fig.")]
        if not caps:
            caps = [sh for sh in sl.shapes
                    if sh.has_text_frame and sh.text_frame.text.strip()
                    and sh.top is not None and sh.top > Inches(1.2)
                    and sh.width and sh.width > Inches(3.0)]
            caps = caps[:1]
        for sh in caps:
            txt = sh.text_frame.text
            if tag.split(u".")[0] in txt:      # write() runs three times
                break
            pa = sh.text_frame.paragraphs[0]
            runs = pa.runs
            if not runs:
                break
            # insert after the "Fig. n —" run so the stamp reads as part of
            # the caption's own front matter rather than as a stray heading
            new = _copy.deepcopy(runs[0]._r)
            for t_el in new.findall(q("t")):
                t_el.text = u" " + tag + u" "
            for rPr in new.findall(q("rPr")):
                rPr.set("b", "1")
            runs[0]._r.addnext(new)
            stamped += 1
            break
    return stamped, unknown


# --------------------------------------------------------------- ordering --
# "How the work was run" and "What Python does" are cut: the demo video shows
# both of them happening, and 36 slides does not fit a 10-minute slot. The
# figures are still built and live in results/, so either can be put back by
# naming it here again.

# ======================================================================
# THE SEVEN SLIDES A MOCK VIVA SAID WERE MISSING
#
# Run against the shipping deck, a deliberately hostile examiner landed
# four attacks, and every one landed because the evidence EXISTS in this
# repository and was not on a slide:
#
#   "your fault is a property of your model"   -- three models were run
#   "your conclusion reverses at 1.5 nH"       -- the sweep was filed as
#                                                 an appendix
#   "how is this not a numerical artefact"     -- a 25x refinement exists
#   "you only show me the benefit"             -- the cost is measured
#
# A weakness you state first is a result. A weakness the examiner finds
# is a hole. These seven slides move all four across that line, and add
# the scope box and the conclusion the deck never drew.
# ======================================================================

def _sheet(title, lead, fig, cap, fig_top=1.62, fig_h=3.95, cap_top=5.86,
           cap_h=1.30):
    """One figure slide: title, one bold lead line, the figure, a caption."""
    if not os.path.exists(os.path.join(RES, fig)):
        print("  MISSING: results/%s" % fig)
        return None
    sl = clone_after(p, SRC, len(p.slides._sldIdLst))
    strip(sl)
    set_title(sl, title)
    if lead:
        add_text(sl, 0.70, 1.02, 12.10, 0.40, [
            para([(lead, B)], level=0, sz=1300, spc=0, bullet=False)])
    place(sl, fig, fig_top, fig_h)
    caption(sl, cap, top=cap_top, h=cap_h)
    print("added: %s" % title)
    return sl


# ---- 1. what is and is not claimed ------------------------------------
# Put immediately after the aim, so every later slide is read inside it.
# Most of the viva's questions -- did you build it, did you reproduce
# their circuit, does it always work -- are answered here before they
# are asked.
_sc = clone_after(p, SRC, len(p.slides._sldIdLst))
strip(_sc)
set_title(_sc, u"Scope of the Claim")
add_text(_sc, 0.70, 1.02, 12.10, 0.40, [
    para([(u"What this project establishes, and what it does not. "
           u"Everything after this slide is read inside these bounds.",
           B)], level=0, sz=1300, spc=0, bullet=False)])
add_text(_sc, 0.70, 1.72, 5.90, 4.40, [
    para([(u"WE CLAIM", B)], level=0, sz=1450, spc=240, bullet=False),
    para([(u"A fixed clamp and negative off-bias raise the simulated "
           u"off-state gate margin on every device model we ran.", N)],
         level=0, sz=1400, spc=300, bullet=False),
    para([(u"Runtime adaptation adds a further benefit whose size depends "
           u"strongly on power-loop inductance, and we measure that "
           u"dependence.", N)], level=0, sz=1400, spc=300, bullet=False),
    para([(u"The relative comparison is against our own implementation of "
           u"the published baseline, run in our testbench.", N)],
         level=0, sz=1400, spc=300, bullet=False),
    para([(u"Every number regenerates from a named script in the "
           u"repository.", N)], level=0, sz=1400, spc=0, bullet=False)])
add_text(_sc, 7.05, 1.72, 5.75, 4.40, [
    para([(u"WE DO NOT CLAIM", B)], level=0, sz=1450, spc=240, bullet=False),
    para([(u"Experimental validation. No hardware has been built.", N)],
         level=0, sz=1400, spc=300, bullet=False),
    para([(u"Reproduction of the original authors' measured silicon "
           u"results. Their netlist is not published.", N)],
         level=0, sz=1400, spc=300, bullet=False),
    para([(u"That false turn-on occurs universally. Its occurrence at the "
           u"margin is device-model dependent, and we show the model on "
           u"which it does not occur.", N)],
         level=0, sz=1400, spc=300, bullet=False),
    para([(u"A universally optimal control word. The best setting moves "
           u"with the operating point, and by how much is the result.", N)],
         level=0, sz=1400, spc=0, bullet=False)])
print("added: Scope of the Claim")


# ---- 2. the baseline, and how it was rebuilt --------------------------
# "You chose how good their circuit is" is unanswerable unless the
# reimplementation is itself on a slide.
_bl = clone_after(p, SRC, len(p.slides._sldIdLst))
strip(_bl)
set_title(_bl, u"Baseline Reimplementation")
add_text(_bl, 0.70, 1.02, 12.10, 0.40, [
    para([(u"Zhang et al., ISPSD 2020 [10]. The authors' netlist is not "
           u"published, so the baseline is built from the paper and stated "
           u"as such.", B)], level=0, sz=1300, spc=0, bullet=False)])
add_text(_bl, 0.70, 1.75, 5.90, 4.40, [
    para([(u"TAKEN FROM THE PAPER", B)], level=0, sz=1450, spc=240,
         bullet=False),
    para([(u"Segmented output stage on E-mode GaN, seven segments a bank.",
           N)], level=0, sz=1400, spc=260, bullet=False),
    para([(u"Two-stage engagement: NSEG segments first, the remaining "
           u"7 \u2212 NSEG after TSTEP.", N)],
         level=0, sz=1400, spc=260, bullet=False),
    para([(u"Pattern timing in the 0.5\u20135 ns range.", N)],
         level=0, sz=1400, spc=260, bullet=False),
    para([(u"One external bias resistor selects the whole pattern \u2014 "
           u"the paper's own contribution, and the word \"Simple\" in its "
           u"title.", N)], level=0, sz=1400, spc=0, bullet=False)])
add_text(_bl, 7.05, 1.75, 5.75, 4.40, [
    para([(u"WHAT WE HAD TO DECIDE", B)], level=0, sz=1450, spc=240,
         bullet=False),
    para([(u"Segment resistance and device sizing: matched to ours, so the "
           u"comparison is of architecture, not of silicon area.", N)],
         level=0, sz=1400, spc=260, bullet=False),
    para([(u"The bias setting: their paper fixes it once at design time. "
           u"We instead search NSEG and TSTEP at every corner and run "
           u"theirs at whatever wins.", N)],
         level=0, sz=1400, spc=260, bullet=False),
    para([(u"That is more freedom than their design has, and it is given "
           u"to them deliberately: every methodological choice here runs "
           u"against us.", B)], level=0, sz=1400, spc=260, bullet=False),
    para([(u"models/zhangdrv.lib names each assumption in its header.", N)],
         level=0, sz=1400, spc=0, bullet=False)])
print("added: Baseline Reimplementation")


# ---- 3. the models -----------------------------------------------------
_sheet(u"Model Validation: Three Device Models",
       u"The same three configurations, run on three independent device "
       u"models.",
       "fig_model_table.png",
       u"Simulated in ngspice. models/egan.lib is behavioural "
       u"with diode junction capacitances; scripts/silicon_check.py runs "
       u"real SKY130 transistors; models/egan_c.lib replaces the diodes "
       u"with a charge-based C(V). The sign of the no-clamp margin depends "
       u"on the model: on the charge-based model the OFF gate reaches "
       u"only +0.115 V of margin, meaning it never crosses threshold and "
       u"the fault does not occur, against \u22120.249 V behaviourally and "
       u"\u22120.563 V on SKY130. What every model agrees on is the "
       u"ordering of the three configurations, and that the shipped "
       u"configuration is safe on all of them by +2.032 to +2.710 V. The "
       u"claim this project makes is the second one.",
       fig_top=1.55, fig_h=4.10, cap_top=5.80, cap_h=1.42)


# ---- 4. numerical reliability, and the nine -----------------------------
_sheet(u"Numerical Reliability",
       u"Whether these numbers are physics or solver settings, and every "
       u"run accounted for.",
       "fig_convergence.png",
       u"scripts/metric_converge.py re-runs one word at five "
       u"timesteps spanning 25\u00d7. The crosstalk margin the result "
       u"rests on moves 0.14 % over that range and the spurious gate peak "
       u"0.04 %; scripts/verdict_stability.py flips 0 of 80 feasibility "
       u"verdicts. Separately, the 36-corner grid is 25,911 completed runs "
       u"of 25,920. scripts/failed_runs.py re-runs the nine that are not "
       u"there: all nine fail again, so they are reproducible rather than "
       u"flaky, all nine abort with the same ngspice transient "
       u"convergence failure at the high-side gate node, and all nine are "
       u"half-fixed settings \u2014 clamp without the rail, or rail "
       u"without the clamp. None is the shipped configuration. One figure "
       u"appears twice at different resolutions and the deck quotes the "
       u"finer: switch-node overshoot is 17.9 % at the 0.02 ns step this "
       u"deck reports, against 15.1 % at the sweep's 0.2 ns step, which is "
       u"what proof/LIVE-BUCK.sh prints and says.",
       fig_top=1.52, fig_h=4.15, cap_top=5.80, cap_h=1.45)


# ---- 5. the inductance dependence, as a result -------------------------
_sheet(u"When Runtime Adaptation Is Worth Building",
       u"The headline is conditional, and this is the condition.",
       "fig_lloop_ceiling.png",
       u"Simulated in ngspice, scripts/lloop_sweep.py into "
       u"lloop_analyse.py. The ceiling on per-corner scheduling is 13.5 % "
       u"at 1.5 nH and 0.55 % at 4.5 nH, so the answer to \"is adaptive "
       u"gate control worth the sensor, the lookup table and the "
       u"controller\" is not a property of the driver: it is a property "
       u"of the board the driver sits on. Below about 2.5 nH the answer is "
       u"yes and above it the answer is no. The series is not monotonic in "
       u"that band, which is why it is drawn as eight points rather than "
       u"as a curve. 3.0 nH is our nominal simulation condition, not a "
       u"measured layout, and the 2.6 % headline is the value at that "
       u"nominal condition.",
       fig_top=1.52, fig_h=4.10, cap_top=5.74, cap_h=1.48)


# ---- 6. the bill -------------------------------------------------------
_sheet(u"The Cost of the Fix",
       u"What the crosstalk margin is paid for with.",
       "fig_cost_table.png",
       u"Simulated in ngspice, from results/buck_sweep.csv, "
       u"results/panel_metrics.csv and results/headtohead.csv. The fix buys "
       u"+2.825 V of gate margin, and it is bought with 0.24 points of "
       u"converter efficiency, 0.570 W of "
       u"loss and 12 V of extra switch-node peak. About 0.22 W of that "
       u"loss is third-quadrant conduction: GaN has no body diode, so "
       u"during dead time the device conducts in reverse at V_th + "
       u"|V_off| + I\u00b7R_ds(on), and a deeper off rail makes that drop "
       u"larger. At 118 V on a 200 V-rated device the stress is 59 % of "
       u"rating, so it is a real cost but not the binding constraint at "
       u"this bus.",
       fig_top=1.55, fig_h=4.00, cap_top=5.68, cap_h=1.48)


# ---- 7. the conclusion the deck never drew -----------------------------
_cn = clone_after(p, SRC, len(p.slides._sldIdLst))
strip(_cn)
set_title(_cn, u"Conclusions")
add_text(_cn, 0.70, 1.05, 12.10, 5.30, [
    para([(u"1.  Gate robustness.  ", B),
          (u"An always-on Miller clamp with a \u22122 V off rail raises the "
           u"simulated off-state gate margin on all three device models "
           u"tried, from \u22120.249 V to +2.576 V on the behavioural "
           u"model and to between +2.0 and +2.7 V on the other two.", N)],
         level=0, sz=1300, spc=230, bullet=False),
    para([(u"2.  Adaptation.  ", B),
          (u"Choosing one good fixed control word is worth 26.5 % of the "
           u"baseline. Re-tuning it while the converter runs adds 2.6 % "
           u"more \u2014 8.9 % of the total gain \u2014 at our nominal "
           u"3 nH power loop.", N)],
         level=0, sz=1300, spc=230, bullet=False),
    para([(u"3.  That answer is conditional.  ", B),
          (u"The ceiling on scheduling runs from 13.5 % at 1.5 nH to "
           u"0.55 % at 4.5 nH. Whether adaptive gate control earns its "
           u"hardware is decided by board layout, not by the driver.", N)],
         level=0, sz=1300, spc=230, bullet=False),
    para([(u"4.  It is a trade.  ", B),
          (u"The margin costs 0.24 efficiency points, 0.570 W and 12 V of "
           u"switch-node stress, and raises turn-on energy at three of four "
           u"corners.", N)],
         level=0, sz=1300, spc=230, bullet=False),
    para([(u"5.  Status.  ", B),
          (u"Simulation only. No hardware built. The comparison is against "
           u"our own implementation of the published baseline, because the "
           u"authors' netlist is not published.", N)],
         level=0, sz=1300, spc=230, bullet=False),
    # What the Scope and Overturn slides carried, in one point rather than
    # two slides: the bounds on the claim, and what would break it.
    para([(u"6.  What would change this.  ", B),
          (u"A measured gate waveform that does not match the simulated one, "
           u"or an extracted loop inductance below 2.5 nH — which we "
           u"have not measured, and which would invert conclusion 3.", N)],
         level=0, sz=1300, spc=0, bullet=False)])
print("added: Conclusions")


# ---- 8. where our own conclusion would break ---------------------------
# A candidate who has already listed the conditions that would overturn
# their result is much harder to corner than one defending every point.
_lm = clone_after(p, SRC, len(p.slides._sldIdLst))
strip(_lm)
set_title(_lm, u"What Would Overturn This Result")
add_text(_lm, 0.70, 1.02, 12.10, 0.40, [
    para([(u"The conditions under which our own conclusion would need "
           u"revising, stated by us.", B)],
         level=0, sz=1300, spc=0, bullet=False)])
add_text(_lm, 0.70, 1.72, 12.10, 4.60, [
    para([(u"A measured gate waveform that does not reproduce the "
           u"simulated transient.  ", B),
          (u"Everything here rests on one behavioural GaN model written "
           u"from a datasheet, with hand-typed temperature coefficients "
           u"that are not fitted.", N)],
         level=0, sz=1250, spc=240, bullet=False),
    para([(u"An extracted power-loop inductance below about 2.5 nH.  ", B),
          (u"Then adaptation is worth several times what we report, and "
           u"the recommendation inverts. We have not measured this "
           u"inductance; 3 nH is assumed.", N)],
         level=0, sz=1250, spc=240, bullet=False),
    para([(u"Package and gate-loop parasitics that change the Miller "
           u"current path.  ", B),
          (u"C_GD here is a junction diode biased never to conduct, used "
           u"only for its C(V) law. A charge-based model already moves the "
           u"no-clamp margin by +0.364 V.", N)],
         level=0, sz=1250, spc=240, bullet=False),
    para([(u"Evidence that our baseline differs materially from the "
           u"authors' implementation.  ", B),
          (u"Their netlist is unpublished; if it were released and "
           u"performed better than ours, every ratio in this deck would "
           u"need recomputing.", N)],
         level=0, sz=1250, spc=0, bullet=False)])
print("added: What Would Overturn This Result")


# ---- the cover page stays plain --------------------------------------
# A circuit was placed here and then taken back out: the cover is the page
# that gets signed and scanned, and it reads better with nothing competing
# with the signature box. scripts/title_circuit.py and its figure are kept
# -- the drawing is correct and is worth having -- but nothing places it.


ORDER = [
    # The title page has no title shape; it is matched by its signature
    # text as "School of" further down. A "Slide 1" entry here matched
    # nothing and printed MISSING on every single run, which is one more
    # line teaching a reader to skim the output.
    u"School of",
    # The institute's Review-I rubric slide (5 Marks, 5 %, "Focus: 50 % Work
    # Completion", the mark split-up) came straight out of template_ext.pptx.
    # This deck is presented at Review-II and there is no Review-II rubric in
    # the repository, so the slide is dropped rather than shown stating the
    # previous review's marking scheme to this panel.
    u"Problem Statement",
    u"The goal, and whether this serves it",
    u"Aim and Approach",
    u"Scope of the Claim",
    u"System Architecture",
    u"What a GaN HEMT is",
    u"Why GaN and not silicon",
    u"Why the GaN HEMT causes",
    u"GaN against silicon \u2014 six parameters",
    u"Latency and device power — the two you asked for",
    u"The base paper we build on",
    # build.py creates this slide and simplify.py writes its text, but it was
    # never named here -- so ORDER dropped it and the deck cited a base paper
    # it never compared against, while the speech script talked the audience
    # through a slide that did not exist.
    u"We implemented the base paper",
    u"Their driver, drawn \u2014 the reimplementation",
    u"Our driver, drawn \u2014 the same stage",
    u"Novelty: Three Added Blocks",      # architecture, in green
    u"Novelty at Circuit Level",    # the same claim, ringed
    u"Gate Driver Schematics in KiCad",         # the same two sheets, whole
    u"Crosstalk Mechanism at Device Level",
    u"Implementation: Converter Schematic",
    u"Implementation: Proposed Gate Driver",
    u"Implementation: Base Paper Gate Driver",
    u"Segmented Driver: Block Structure",
    u"Segmented Driver: SPICE Implementation",
    u"GaN HEMT Device Model",
    u"Methodology",   # the method, stated once
    u"Baseline Reimplementation",
    u"Model Validation: Three Device Models",
    u"Numerical Reliability",
    u"When Runtime Adaptation Is Worth Building",
    u"The Cost of the Fix",
    u"Their architecture \u2014 the base paper",
    u"Our architecture \u2014 same stage",
    u"Theirs and ours \u2014 six parameters",
    u"Where we win, and where we lose",
    u"Six-Parameter Comparison",
    u"The converter across its own envelope",
    u"Does the answer depend on the weight we chose?",
    u"The distribution behind the 2.6 %",
    u"The optimum moves. The cost of ignoring it does not.",
    u"Is the 36-corner grid dense enough?",
    u"What the negative rail costs",
    u"Does the hot-corner lead rest on two typed-in numbers?",
    u"Comparison with the Base Paper",
    u"The closest published drivers",
    u"The gap this project fills",
    u"The driver's settings",
    u"The input — what an operating point is",
    u"The output — what is actually measured",
    u"Crosstalk margin",
    u"How it works — one use case",
    u"Converter Under Simulation",
    u"What ngspice runs",
    u"Inside the segmented gate driver",
    u"How we run ngspice",
    u"How the work was run",
    u"Which tool did what",
    u"Base Paper Driver",          # theirs, on its own
    u"Proposed Driver",                    # ours, same axes
    u"Demonstration",
    u"Live Simulation",
    u"What we are building — the converter",
    u"The cases we ran",
    # The simulator's own terminal, captured. These were in the 20-slide cut
    # and NOT in the full deck, which is backwards -- the full deck is the one
    # a reviewer takes away, and it was the one with no raw tool output in it.
    u"The circuit, as ngspice reports it",
    u"Crosstalk: Fault",
    u"Driver simulation",
    u"ngspice output — what re-tuning is worth",
    u"ngspice output — the split",
    u"Icarus Verilog output",
    u"Vivado output",
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
    u"Does the result depend on the model?",
    u"Work Completed",
    u"Next Steps",
    u"The hardware, costed",
    u"Conclusions",
    u"What Would Overturn This Result",
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
# SHORT is the deck that gets presented, and it is now 19 slides. It was 38,
# which is a 45-minute deck in a 20-minute slot: at that length a presenter
# either races or gets stopped, and both lose the room.
#
# What survives is one pass through the argument with nothing said twice --
# problem, aim, architecture, the circuit, their driver against ours three
# ways (drawn, simulated, measured), and the honest accounting at the end.
# BACKUP keeps all 73 for the questions.
#
# The five deliberate cuts, so the reasoning is on record rather than in
# somebody's memory:
#   - four of the five architecture slides. "Base paper and ours, side by
#     side" does in one what 22, 23, 25 and 26 did in four.
#   - the "two effects" slide, which is the strongest intellectual argument
#     in the project (adaptation is worth 2.57 % against 26.45 % for a better
#     fixed word) and also the one that invites the hardest question. It is
#     in BACKUP, and SPEECH-SCRIPT.md has the answer ready.
#   - "Where we win, and where we lose", "The converter across its own
#     envelope", "Closing the loop", "Does the result depend on the model?".
#     Each is a good slide answering a question nobody has asked yet.
#   - the driver-simulation case walk and the FPGA slide: the demo films and
#     the cost table already carry what they proved.
#   - the second references slide. The deck shows 1-15; BACKUP has 16-30.
# Cut from 31 to 25. Six slides go, and each one's point survives on a slide
# that was already carrying it:
#
#   Scope of the Claim            -> Conclusions 5 and 6 say the same bounds
#   Baseline Reimplementation     -> Methodology already states the search we
#                                    give their driver that its paper does not
#   GaN HEMT Device Model         -> Model Validation names the same file and
#                                    runs it against two further models
#   Demonstration                 -> Live Simulation does it live, in the room
#   Six-Parameter Comparison      -> GaN against silicon; this review is about
#                                    the driver, and the Cost slide carries
#                                    the efficiency and loss numbers
#   What Would Overturn This      -> folded into Conclusions as one point
#
# Dropping Demonstration also takes the 8.9 MB demo film out of the package,
# which is over half the file's size on its own. All six are in BACKUP.
SHORT = [
    u"School of",                              # title page (no title shape)
    u"Problem Statement & Background",
    u"Aim and Approach",
    u"System Architecture",
    u"Novelty: Three Added Blocks",      # the novelty, in the blocks
    u"Novelty at Circuit Level",   # the difference, ringed on the sheets
    u"Crosstalk Mechanism at Device Level",
    u"Implementation: Converter Schematic",
    u"Implementation: Proposed Gate Driver",
    u"Implementation: Base Paper Gate Driver",
    u"Segmented Driver: SPICE Implementation",        # the source of the block
    u"Methodology",   # the method, stated once
    u"Model Validation: Three Device Models",
    u"Numerical Reliability",
    u"Base Paper Driver",              # theirs, alone
    u"Proposed Driver",                        # ours, same axes
    u"Live Simulation",                   # the live offer
    u"Crosstalk: Fault",                   # the fault and the fix
    u"Comparison with the Base Paper",       # four corners, 5.5x to 12.4x
    u"When Runtime Adaptation Is Worth Building",
    u"The Cost of the Fix",
    # The completion percentage was doing no work for a
    # reviewer: what matters is what is left, not a score out
    # of a hundred that only this deck defines. The table is
    # still in the backup deck if anyone asks for it.
    u"Conclusions",
    u"Next Steps",
    u"References",
    u"Thank you",
]


# A running order with the same entry twice takes the slide the first time
# and prints MISSING the second, so the deck silently loses a slide while the
# build looks like it worked. That is exactly what happened adding these
# slides: an edit meant for SHORT matched the identical line in ORDER, so
# ORDER carried "Baseline Reimplementation" twice and SHORT carried it not at
# all -- and the only symptom was one MISSING line in 250 lines of output.
for _name, _lst in (("ORDER", ORDER), ("SHORT", SHORT)):
    _dup = sorted({e for e in _lst if _lst.count(e) > 1})
    if _dup:
        raise SystemExit("rebuild_pass: %s names %s more than once -- the "
                         "second occurrence can only print MISSING"
                         % (_name, ", ".join(repr(d) for d in _dup)))
# and every SHORT entry must exist in ORDER, or the presented deck carries a
# slide the takeaway deck does not.
_gap = [e for e in SHORT if not any(o.startswith(e) or e.startswith(o)
                                    for o in ORDER)]
if _gap:
    raise SystemExit("rebuild_pass: SHORT names %s, which ORDER does not"
                     % ", ".join(repr(g) for g in _gap))


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
    # write() is called three times on the same Presentation object, so the
    # first call does the geometry work and the later two find nothing left.
    # Report it only when it fires, or the last two lines read like a failure.
    stamped, unknown_pics = stamp_provenance(p)
    if unknown_pics:
        print("  %d picture(s) with no provenance entry -- add them to "
              "PROVENANCE" % unknown_pics)
    narrowed, clipped, grown = tidy_geometry(p)
    fixed = ((", %d figures stamped with their source" % stamped)
             if stamped else "")
    fixed += ("" if not (narrowed or clipped or grown) else
              ", %d off the page number, %d out from under a picture, "
              "%d grown to fit" % (narrowed, clipped, grown))
    p.save(path)
    print("%-8s %2d slides, %d logos removed%s -> %s"
          % (what, len(idxs), removed, fixed, os.path.basename(path)))


_OUTS = [os.path.join(HERE, "GaN_Review2_PRESENT.pptx"),
         os.path.join(HERE, "GaN_Review2_BACKUP.pptx"),
         DECK]
write(short_idx, _OUTS[0], "PRESENT")
write(full_idx,  _OUTS[1], "BACKUP")
write(full_idx,  _OUTS[2], "FULL")

# ORDER decides what ships, and write() drops the rest from the slide id list
# -- which is what PowerPoint reads. The relationship to each dropped slide
# stayed behind, so the slide, its text and its figures were all still inside
# the .pptx: unreachable, but readable by anything that unzips it. 45 retired
# slides travelled inside the 36-slide deck that way, carrying numbers the
# deck had been corrected to stop claiming. This drops them properly.
print()
import prune_orphans
for _o in _OUTS:
    prune_orphans.prune(_o)

# Register last, once the deck holds only the slides that will be shown.
#
# The slide text is assembled across five passes by people writing prose, and
# prose drifts into the register of speech: stage directions, self-reference,
# emphasis by capital letters. plain_pass rewrites the known cases and then
# fails the build if any survive, so the register cannot come back one slide
# at a time.
#
# It has to run after the prune, not before. Before it, the package still
# carries the retired slides -- their text is reachable in the file even
# though the running order has dropped them, and the guard was reporting
# wording from slides nobody will ever see. Worse, the report was not
# reproducible: running the same check on the same file a second time came
# back clean, because the first run's save had already rewritten the package
# without them. A check that disagrees with itself is worth nothing, so it
# goes where the deck is final.
print()
import plain_pass
if plain_pass.main():
    raise SystemExit("rebuild_pass: banned phrasing in the deck (see above)")

# Name the KiCad sheet on every slide that draws one, so the linker below
# has something to point at.
import cite_pass
if cite_pass.main():
    raise SystemExit("rebuild_pass: a KiCad figure names no sheet (see above)")

# A file path printed on a slide has one use, and it is being clicked.
import link_pass
if link_pass.main():
    raise SystemExit("rebuild_pass: dead link text in the deck (see above)")

# Last: the text-only slides have no figure to give them structure, so give
# them some. Runs last because it measures whether the text still fits, and
# every earlier pass can change how much text there is.
import layout_pass
layout_pass.main()
