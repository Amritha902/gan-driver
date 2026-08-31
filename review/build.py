# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lxml import etree
from pptx import Presentation
from pptx.util import Inches, Pt
from fill import para, set_body, find_shape, set_title, q, A, esc, RUN_TPL, PARA_TPL
import content

RES = "/home/user/gan-driver/results"
SRC = "template_ext.pptx"
OUT = "Review1_GaN_Segmented_Gate_Driver.pptx"

# ---- text-fit estimate (no renderer available in this environment) ---------
# Calibri average advance is ~0.478 em for mixed-case prose; 0.50 is used here
# so the estimate errs toward predicting overflow rather than hiding it.
CH_EM, LINE_EM, BOX_W, BOX_H = 0.50, 1.22, 11.90, 5.40
INDENT = {0: 0.194, 1: 0.569}

def fits(paras, spc_pt=6.0):
    h = 0.0
    for runs, lvl in paras:
        n = sum(len(t) for t, _ in runs)
        sz = 16 if lvl == 0 else 15
        cw = sz * CH_EM / 72.0
        avail = BOX_W - INDENT[lvl]
        lines = max(1, -(-int(n * cw / avail * 100) // 100) if n else 1)
        lines = max(1, int(n * cw / avail) + (1 if (n * cw) % avail else 0))
        h += lines * sz * LINE_EM / 72.0 + spc_pt / 72.0
    return h

def build_paras(spec):
    out = []
    for runs, lvl in spec:
        out.append(para(runs, level=lvl, sz=(1600 if lvl == 0 else 1500),
                        spc=600, bullet=True))
    return out

p = Presentation(SRC)
S = p.slides

# ---------------- slide 2 : title -----------------------------------------
def set_run_after(slide, label, newtext):
    """Replace the text of the first run that follows a run equal to `label`."""
    for sh in slide.shapes:
        if not sh.has_text_frame: continue
        runs = [r for para_ in sh.text_frame.paragraphs for r in para_.runs]
        for i, r in enumerate(runs):
            if r.text.strip() == label and i + 1 < len(runs):
                runs[i + 1].text = newtext
                return True
    return False

for sh in S[1].shapes:
    if sh.has_text_frame:
        for pa in sh.text_frame.paragraphs:
            for r in pa.runs:
                if r.text.strip() == "Project Title":
                    r.text = ("A Segmented Gate Driver for GaN HEMTs: Measuring What "
                              "Operating-Point Scheduling Is Actually Worth")
set_run_after(S[1], "Student Name(s):", "Amritha  —  Reg. No. ____________")
set_run_after(S[1], "Guide:", "Dr. Bindu, School of Electronics Engineering (SENSE)")

# ---------------- slides 4, 6, 7 : bulleted content ------------------------
for idx, spec, needle in ((3, content.SLIDE4, "Problem Statement:"),
                          (6, content.SLIDE6, "Proposed Solution:"),
                          (7, content.SLIDE7, "Work completed so far")):
    sh = find_shape(S[idx], needle)
    set_body(sh, build_paras(spec))
    print("slide %d: %.2f in of %.2f  %s"
          % (idx + 1, fits(spec), BOX_H, "OK" if fits(spec) <= BOX_H else "OVERFLOW"))

p.save(OUT)
print("wrote", OUT)

# ---------------- slides 5 & 6 : literature survey (4 refs each) -----------
from pptx.dml.color import RGBColor
import refs as R

def set_cell(cell, runs, size=Pt(10.5), grey=False):
    """runs: list of (text, bold) or a plain string.

    A newline inside an <a:t> is not a line break in OOXML - PowerPoint
    swallows it - so "\n" starts a new PARAGRAPH instead."""
    if isinstance(runs, str):
        runs = [(runs, False)]
    tf = cell.text_frame
    tf.word_wrap = True
    pa = tf.paragraphs[0]
    for r in list(pa.runs):
        r._r.getparent().remove(r._r)
    for extra in list(tf.paragraphs)[1:]:
        extra._p.getparent().remove(extra._p)
    col = RGBColor(0x7A, 0x7A, 0x7A) if grey else RGBColor(0, 0, 0)
    for txt, bold in runs:
        for i, line in enumerate(txt.split("\n")):
            if i:
                pa = tf.add_paragraph()
            if not line:
                continue
            run = pa.add_run(); run.text = line
            run.font.size = size; run.font.bold = bold; run.font.name = "Calibri"
            run.font.color.rgb = col

def table_of(slide):
    for sh in slide.shapes:
        if sh.has_table: return sh.table
    raise KeyError("no table")

for page, sidx in ((0, 4), (1, 5)):
    tbl = table_of(S[sidx])
    group = R.REFS[page * 4:(page + 1) * 4]
    for row, (num, auth, title, venue, method, find, xid, ok) in enumerate(group, start=1):
        set_cell(tbl.cell(row, 0), str(num))
        set_cell(tbl.cell(row, 1), [(auth, False)] if ok else
                 [(auth, False), ("\nauthors: complete from Xplore", True)], grey=not ok)
        set_cell(tbl.cell(row, 2), [(title, False), ("\n" + venue, True)])
        set_cell(tbl.cell(row, 3), method)
        set_cell(tbl.cell(row, 4), find)
    # Each table ships with 6 body rows and each slide now carries 4. Delete the
    # spare rows rather than blanking them: an empty row still occupies 0.62 in,
    # and PowerPoint grows rows to fit their text, so leaving two behind would
    # push the table under the footnote.
    for row in (6, 5):
        tbl._tbl.remove(tbl.rows[row]._tr)
    # give the four remaining rows room to breathe
    for row in range(len(tbl.rows)):
        tbl.rows[row].height = Inches(0.95 if row else 0.40)
    if page == 0:
        set_title(S[sidx], "Literature Survey  (1 – 4)")
        note = find_shape(S[sidx], "Minimum 8")
        set_body(note, [para([("References [1]–[3] are verified against the publisher record "
                               "— author list, volume, issue and pages all confirmed.", False)],
                             level=0, sz=1150, spc=0, bullet=False)])
    else:
        set_title(S[sidx], "Literature Survey  (5 – 8)")
        note = find_shape(S[sidx], "Minimum 8")
        set_body(note, [para([("References [4]–[8]: title, journal status and IEEE Xplore document "
                               "ID confirmed. Volume, issue, pages and authors are marked XX — every "
                               "publisher and metadata service was unreachable from the build "
                               "environment, and they are not invented. One click on Xplore's "
                               "\u201cCite This\u201d completes each.", False)],
                             level=0, sz=1150, spc=0, bullet=False)])

# ---------------- slides 8 & 9 : results ----------------------------------
# Both arrive empty from the template (title + logo only). Content area runs
# from y=1.45 to y=6.85, x=0.70 to 12.60.

def add_text(slide, x, y, w, h, paras):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tb.text_frame.word_wrap = True
    bp = tb.text_frame._txBody.find(q("bodyPr"))
    for k in ("lIns", "tIns", "rIns", "bIns"):
        bp.set(k, "0")
    set_body(tb, paras)
    return tb

def stat(slide, x, y, w, big, label, sub):
    """A large number with a caption under it."""
    t = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(1.30))
    tf = t.text_frame; tf.word_wrap = True
    bp = tf._txBody.find(q("bodyPr"))
    for k in ("lIns", "tIns", "rIns", "bIns"): bp.set(k, "0")
    set_body(t, [
        para([(big, True)], level=0, sz=3200, spc=100, bullet=False),
        para([(label, True)], level=0, sz=1300, spc=60, bullet=False),
        para([(sub, False)], level=0, sz=1150, spc=0, bullet=False),
    ])
    return t

# --- slide 8: the problem reproduced, and fixed ---------------------------
s8 = S[8]
s8.shapes.add_picture(RES + "/fig1_crosstalk.png",
                      Inches(0.70), Inches(1.45), width=Inches(7.30))
add_text(s8, 0.70, 6.30, 7.30, 0.45, [
    para([("Fig. 1  Spurious gate voltage on the off-device: the failure, and the actuator that "
           "removes it.", False)], level=0, sz=1100, spc=0, bullet=False)])

add_text(s8, 8.35, 1.45, 4.25, 0.45, [
    para([("The problem is real, and reproduced", True)], level=0, sz=1500, spc=0, bullet=False)])
stat(s8, 8.35, 2.00, 4.25, "1.65 V", "spurious gate peak vs 1.4 V threshold",
     "Fastest drive, no clamp — false turn-on")
stat(s8, 8.35, 3.35, 4.25, "2.58 V", "margin with clamp + −2 V off-bias",
     "The actuator removes it completely")
add_text(s8, 8.35, 4.75, 4.25, 2.00, [
    para([("And safety is nearly free", True)], level=0, sz=1500, spc=200, bullet=False),
    para([("The energy-optimal control word is already crosstalk-safe at three of four corners. "
           "At the fourth, safety costs ", False), ("0.04 % of switching energy", True),
          (" — 3.335 µJ against 3.334 µJ.", False)], level=0, sz=1300, spc=200, bullet=False),
    para([("The clamp itself is worth 9.7–12.2 % of the blended cost, from a static architecture "
           "choice needing no sensing or controller.", False)], level=0, sz=1300, spc=0, bullet=False),
])

# --- slide 9: the headline negative result -------------------------------
s9 = S[9]
s9.shapes.add_picture(RES + "/paper_fig2_ceiling.png",
                      Inches(0.70), Inches(1.55), width=Inches(6.60))
add_text(s9, 0.70, 5.35, 6.60, 0.45, [
    para([("Fig. 2  Cost of one fixed control word vs the true per-corner optimum, four corners.",
           False)], level=0, sz=1100, spc=0, bullet=False)])

add_text(s9, 0.70, 5.95, 6.60, 0.90, [
    para([("Full 720-word search at every corner — 2,880 transients — so each per-corner "
           "optimum is a true optimum, not the best of a shortlist.", False)],
         level=0, sz=1300, spc=0, bullet=False)])

add_text(s9, 7.65, 1.45, 4.95, 0.45, [
    para([("What adaptation is actually worth", True)], level=0, sz=1500, spc=0, bullet=False)])
stat(s9, 7.65, 2.00, 4.95, "5.2 %", "ceiling on operating-point scheduling",
     "vs the best single fixed word. A fixed word is nearly as good.")
add_text(s9, 7.65, 3.45, 4.95, 3.40, [
    para([("The benefit is not spread out. ", True),
          ("Three corners lose 1–4 % from a fixed word; one loses 12.7 %.", False)],
         level=0, sz=1300, spc=180, bullet=False),
    para([("It is carried by the dead time. ", True),
          ("Freezing dead time costs 5.45 %; freezing pull-up drive strength costs ", False),
          ("0.00 %", True),
          (" — and drive strength is what the active-gate-driver literature actually schedules.",
           False)], level=0, sz=1300, spc=180, bullet=False),
    para([("Robust to the device, conditional on the layout. ", True),
          ("Across 21,600 transients, no device parameter moves the ceiling outside 4.3–7.7 %. "
           "Halving the loop inductance takes it to 13.5 %, and loop inductance is board layout, "
           "not the transistor [3].", False)], level=0, sz=1300, spc=0, bullet=False),
])
p.save(OUT)
print("slides 8 and 9 built")

# ---------------- references slide -----------------------------------------
IEEE_FULL = {
 1: "Z. Zhang, F. Wang, L. M. Tolbert and B. J. Blalock, \u201cActive Gate Driver for Crosstalk "
    "Suppression of SiC Devices in a Phase-Leg Configuration,\u201d IEEE Trans. Power Electron., "
    "vol. 29, no. 4, pp. 1986\u20131997, Apr. 2014.",
 2: "R. Xie, H. Wang, G. Tang, X. Yang and K. J. Chen, \u201cAn Analytical Model for False Turn-On "
    "Evaluation of High-Voltage Enhancement-Mode GaN Transistor in Bridge-Leg Configuration,\u201d "
    "IEEE Trans. Power Electron., vol. 32, no. 8, pp. 6416\u20136433, Aug. 2017.",
 3: "D. Reusch and J. Strydom, \u201cUnderstanding the Effect of PCB Layout on Circuit Performance "
    "in a High-Frequency Gallium-Nitride-Based Point of Load Converter,\u201d IEEE Trans. Power "
    "Electron., vol. 29, no. 4, pp. 2008\u20132015, Apr. 2014.",
}
ref_shape = find_shape(S[14], "A. Author")
paras = []
for num, auth, title, venue, method, find, xid, ok in R.REFS:
    if ok:
        paras.append(para([("[%d]  " % num, True), (IEEE_FULL[num], False)],
                          level=0, sz=1150, spc=340, bullet=False))
    else:
        paras.append(para([("[%d]  " % num, True),
                           ("\u201c%s,\u201d " % title, False),
                           ("IEEE journal; Xplore document %s. " % xid, False),
                           ("Authors, vol., no., pp., year to be completed from Xplore.", True)],
                          level=0, sz=1150, spc=340, bullet=False))
paras.append(para([("[1]\u2013[3] verified against the publisher record. [4]\u2013[8]: title, "
                    "journal status and Xplore document ID confirmed; the remaining fields were "
                    "not reachable from the build environment and are deliberately left blank "
                    "rather than guessed.", False)], level=0, sz=1050, spc=0, bullet=False))
set_body(ref_shape, paras)

try:
    n2 = find_shape(S[14], "Use IEEE format")
    set_body(n2, [para([("Use IEEE format. Every reference listed must be cited in the slides / "
                         "report.", False)], level=0, sz=1200, spc=0, bullet=False)])
except KeyError:
    pass

# ================= new slides 10 (demo) and 11 (evidence) ==================
# Both were cloned from the empty "Results (contd.)" slide, so each already
# carries the title box, the VIT logo and a page-number box — all of which
# still hold slide 9's values and must be corrected.

def retitle(slide, text):
    for sh in slide.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip() == "Results (contd.)":
            for pa in sh.text_frame.paragraphs:
                for r in pa.runs:
                    r.text = text; return

def renumber(slide, n):
    for sh in slide.shapes:
        if sh.has_text_frame and sh.left and sh.left > Inches(12.0) \
           and sh.top and sh.top > Inches(6.8):
            for pa in sh.text_frame.paragraphs:
                for r in pa.runs:
                    r.text = str(n); return

# ---- slide 10 : the demo video ------------------------------------------
s10 = S[11]
retitle(s10, "Demo")
# pipeline_demo.mp4 trimmed to 17.5 s. The original's closing caption read
# "the Miller clamp buys 14.7 %", the superseded 36-corner shortlist figure;
# the audit puts it at 9.7-12.2 %. The terminal body is untouched and every
# number in it still reproduces. research_demo.mp4 is not used at all: its
# closing caption says the benefit "collapses to one bit - the off-bias rail",
# which the freeze test corrected to dead time.
VID = "pipeline_demo_review1.mp4"
# 1200x700 source -> 1.714 aspect. 7.60 in wide gives 4.43 in tall.
s10.shapes.add_movie(VID, Inches(0.70), Inches(1.55), Inches(7.60), Inches(4.43),
                     poster_frame_image="poster_pipeline.png", mime_type="video/mp4")
add_text(s10, 0.70, 6.15, 7.60, 0.40, [
    para([("Click to play (17 s). Real captured output — only the pacing is "
           "presentational.", False)], level=0, sz=1100, spc=0, bullet=False)])

add_text(s10, 8.65, 1.55, 3.95, 4.60, [
    para([("What it shows", True)], level=0, sz=1500, spc=240, bullet=False),
    para([("ngspice 42 running the real double-pulse test.", False)],
         level=0, sz=1300, spc=180, bullet=True),
    para([("Fastest drive, no clamp: spurious gate 1.649 V, margin ", False),
          ("−0.249 V", True), (" — false turn-on.", False)],
         level=0, sz=1300, spc=180, bullet=True),
    para([("Miller clamp on: 0.830 V, margin ", False), ("+0.570 V", True),
          (" — safe.", False)], level=0, sz=1300, spc=180, bullet=True),
    para([("The full 720-word search at four corners: 474 feasible, ceiling ", False),
          ("5.2 %", True), (".", False)], level=0, sz=1300, spc=240, bullet=True),
    para([("A second video ships in the project folder: a 20 s interactive waveform "
           "viewer over the same simulation data.", False)],
         level=0, sz=1150, spc=0, bullet=False),
])

# ---- slide 11 : the evidence behind the numbers --------------------------
s11 = S[12]
retitle(s11, "Why the numbers hold")

TILES = [
    ("25,990", "transient simulations",
     "Every sweep, corner study and robustness run, start to finish."),
    ("720", "control words, searched in full",
     "At every corner — so each per-corner optimum is a true optimum, not the best of a shortlist."),
    ("25×", "timestep refinement survived",
     "Every reported quantity must be flat across it. Enforced, not assumed."),
    ("7", "wrong numbers caught, and corrected",
     "By that discipline, before any of them reached the report."),
]
X0, Y0, W, DX, DY = 0.70, 1.70, 5.75, 6.15, 2.35
for i, (big, label, sub) in enumerate(TILES):
    x = X0 + (i % 2) * DX
    y = Y0 + (i // 2) * DY
    t = s11.shapes.add_textbox(Inches(x), Inches(y), Inches(W), Inches(2.00))
    bp = t.text_frame._txBody.find(q("bodyPr"))
    for k in ("lIns", "tIns", "rIns", "bIns"): bp.set(k, "0")
    t.text_frame.word_wrap = True
    set_body(t, [
        para([(big, True)], level=0, sz=4000, spc=120, bullet=False),
        para([(label, True)], level=0, sz=1500, spc=100, bullet=False),
        para([(sub, False)], level=0, sz=1250, spc=0, bullet=False),
    ])

add_text(s11, 0.70, 6.45, 11.90, 0.45, [
    para([("Stated plainly: ", True),
          ("LTspice and Spectre decks are faithful ports re-simulated to the same numbers, but "
           "neither simulator has itself been run — no installation was available.", False)],
         level=0, sz=1150, spc=0, bullet=False)])

# ---- page numbers on every slide from 10 onward --------------------------
for n, sl in enumerate(S, start=1):
    if n >= 5:
        renumber(sl, n)

p.save(OUT)
print("slides 10 (demo, video embedded) and 11 (evidence) built; page numbers fixed")

# ---------------- geometry fixes found by qa.py ---------------------------
# The project title is longer than the template's stub, so it wraps to two
# lines at 32 pt and needs a taller box. There is 2.35 in of clear space below
# it, so growing it cannot collide with anything.
for sh in S[1].shapes:
    if sh.has_text_frame and sh.text_frame.text.startswith("A Segmented Gate Driver"):
        sh.height = Inches(1.30)

# The reference list inherited the template's full-height content box (5.40 in)
# but holds about 4 in of text, so the tail ran under the footnote.
for sh in S[14].shapes:
    if sh.has_text_frame and sh.text_frame.text.startswith("[1]"):
        sh.height = Inches(4.75)

p.save(OUT)
print("geometry fixes applied")


# ================= slide 11 : robustness ==================================
s_rob = S[10]
retitle(s_rob, "Results — robustness of the ceiling")

ROWS = [("Loop inductance −50 %  (1.5 nH)", "13.54 %", "+7.59", True),
        ("Input capacitance +30 %",              "7.71 %", "+1.76", False),
        ("Miller capacitance −50 %",        "6.93 %", "+0.99", False),
        ("nominal",                              "5.95 %",     "—", None),
        ("Threshold −20 %",                 "5.64 %", "−0.31", False),
        ("Transconductance +30 %",               "5.08 %", "−0.87", False),
        ("Threshold +20 %",                      "4.90 %", "−1.05", False),
        ("Input capacitance −30 %",         "4.76 %", "−1.19", False),
        ("Transconductance −30 %",          "4.45 %", "−1.49", False),
        ("Miller capacitance +50 %",             "4.32 %", "−1.63", False),
        ("Loop inductance +50 %  (4.5 nH)",      "0.55 %", "−5.39", True)]

# Three separate boxes per row. Space-padding does not align columns in a
# proportional font, so the numeric columns get their own x positions.
COL_L, COL_C, COL_D = 0.70, 4.55, 5.75
def row(y, label, ceil, delta, bold, sz=1200):
    add_text(s_rob, COL_L, y, 3.80, 0.30,
             [para([(label, bold)], level=0, sz=sz, spc=0, bullet=False)])
    add_text(s_rob, COL_C, y, 1.10, 0.30,
             [para([(ceil, bold)], level=0, sz=sz, spc=0, bullet=False)])
    add_text(s_rob, COL_D, y, 1.20, 0.30,
             [para([(delta, False)], level=0, sz=sz, spc=0, bullet=False)])

row(1.45, "Perturbation", "Ceiling", "vs nom.", True, 1150)
y = 1.88
for label, ceil, delta, big in ROWS:
    row(y, label, ceil, delta, big is True or big is None)
    y += 0.335

add_text(s_rob, 7.55, 1.45, 5.05, 0.60, [
    para([("Robust to the device,", True)], level=0, sz=1500, spc=0, bullet=False),
    para([("conditional on the layout.", True)], level=0, sz=1500, spc=0, bullet=False)])
add_text(s_rob, 7.55, 2.25, 5.05, 4.50, [
    para([("21,600 transients", True), (" — a full 720-word search at two corners under each "
           "of eleven single-parameter perturbations. One failure.", False)],
         level=0, sz=1300, spc=200, bullet=True),
    para([("Every ", False), ("device", True),
          (" parameter leaves the ceiling between 4.3 % and 7.7 % — at most 1.76 points from "
           "nominal. The objection this study was built to answer is not supported.", False)],
         level=0, sz=1300, spc=200, bullet=True),
    para([("The one thing that moves it is ", False), ("loop inductance", True),
          (", which is board layout, not the transistor. A tighter loop commutates faster, so "
           "more charge couples through C", False), ("GD", False),
          (": the median spurious gate voltage goes 0.640 V to 3.522 V and the feasible set "
           "collapses 474 → 158.", False)], level=0, sz=1300, spc=200, bullet=True),
    para([("So the claim is narrower and more useful than “robust”: on a loop of about "
           "3 nH or looser a fixed word is nearly as good; on a substantially tighter loop the "
           "question has to be re-asked.", False)], level=0, sz=1300, spc=0, bullet=True),
])

# ================= slide 14 : conclusion ==================================
s_con = S[13]
set_title(s_con, "Conclusion & next steps")
con_shape = find_shape(s_con, "Problem Statement:")
set_body(con_shape, [
    para([("What the data supports", True)], level=0, sz=1600, spc=200, bullet=False),
    para([("Choosing the control word well matters enormously — it spans roughly fivefold in "
           "switching energy. ", False),
          ("Adapting it to the operating point does not: 5.2 %, and a single fixed word is "
           "nearly as good.", True)], level=0, sz=1450, spc=180, bullet=True),
    para([("The benefit that exists is carried by the ", False), ("dead time", True),
          (", not by the drive-strength segmentation that motivates the hardware. Crosstalk "
           "safety is nearly free once the Miller clamp is present.", False)],
         level=0, sz=1450, spc=180, bullet=True),
    para([("This is a negative result about the ", False), ("adaptive", True),
          (" premise, and it is reported as one rather than hidden.", False)],
         level=0, sz=1450, spc=260, bullet=True),
    para([("What it does not support, and what is next", True)], level=0, sz=1600, spc=200,
         bullet=False),
    para([("The objective prices loss and overshoot only. Pull-up strength is worth 0.00 % to "
           "schedule under it, yet swings turn-on slew rate by 123 % and ringing energy by "
           "128 % — an EMI-bound design could reach the opposite conclusion.", False)],
         level=0, sz=1450, spc=180, bullet=True),
    para([("Review-II: ", True), ("transistor-level output stage in Cadence on a 5 V-capable "
           "PDK; re-run the ceiling on real devices. ", False), ("Review-III: ", True),
          ("measure a hardware half-bridge at one corner — until then this is a simulation "
           "study and is titled as one.", False)], level=0, sz=1450, spc=0, bullet=True),
])

for n, sl in enumerate(S, start=1):
    renumber(sl, n)
p.save(OUT)
print("slides 11 (robustness) and 14 (conclusion) built")

# ---------------- slide 2 : name / guide fields ---------------------------
# The label and its value live in SEPARATE shapes, so a run-follows-run search
# within one shape never finds them. Kept last so nothing can clobber it.
REPL = {
    "Name — Reg. No.":        "Amritha  —  Reg. No. ________",
    "Dr. Guide Name, School": "Dr. Bindu  —  SENSE",
}
hits = 0
for sh in S[1].shapes:
    if not sh.has_text_frame: continue
    for pa in sh.text_frame.paragraphs:
        for r in pa.runs:
            if r.text.strip() in REPL:
                r.text = REPL[r.text.strip()]; hits += 1

# ---------------- informative titles on the two results slides ------------
for sl, txt in ((S[8],  "Results — the problem, and the fix"),
                (S[9],  "Results — what scheduling is actually worth")):
    for sh in sl.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip() in ("Results", "Results (contd.)"):
            for pa in sh.text_frame.paragraphs:
                for r in pa.runs:
                    r.text = txt
            break

p.save(OUT)
print("slide 2: %d of %d fields set; results slides retitled" % (hits, len(REPL)))
