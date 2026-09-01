# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lxml import etree
from pptx import Presentation
from pptx.util import Inches, Pt
from fill import para, set_body, find_shape, set_title, q, A, esc, RUN_TPL, PARA_TPL
import content

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
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

# A previous run's output must not survive a crash: qa.py and validate.py
# read OUT by name, and a stale file from the last SUCCESSFUL build looks
# exactly like a passing result. Delete it before doing any work.
if os.path.exists(OUT):
    os.remove(OUT)

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
                          (8, content.SLIDE7,  "Work completed so far"),
                          (9, content.SLIDE7B, "Problem Statement:")):
    sh = find_shape(S[idx], needle)
    set_body(sh, build_paras(spec))
    print("slide %d: %.2f in of %.2f  %s"
          % (idx + 1, fits(spec), BOX_H, "OK" if fits(spec) <= BOX_H else "OVERFLOW"))

rtl_shape = find_shape(S[10], "Problem Statement:")
set_body(rtl_shape, build_paras(content.SLIDE_RTL_SHORT))
set_title(S[10], "FPGA Controller — verified RTL")
print("slide 11 (RTL text block): %.2f in of 2.55  %s"
      % (fits(content.SLIDE_RTL_SHORT),
         "OK" if fits(content.SLIDE_RTL_SHORT) <= 2.55 else "OVERFLOW"))

# The official brief says 10 minutes; the template stub said 8-10.
for sh in S[2].shapes:
    if sh.has_text_frame:
        for pa in sh.text_frame.paragraphs:
            for r in pa.runs:
                if "8\u201310 minutes" in r.text:
                    r.text = r.text.replace("8\u201310 minutes", "10 minutes")

set_title(S[8], "Work Completed — 50 %")
set_title(S[9], "Timeline, Milestones & Tools")

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

def move_note(slide, top_in):
    """A table grows past its declared height when a cell wraps, so the
    footnote has to be placed below where the table ACTUALLY ends, not
    below where python-pptx thinks it does."""
    n = None
    for sh in slide.shapes:
        if sh.has_table or not sh.has_text_frame:
            continue
        # the footnote is the wide low text box, not the title or page number
        if sh.top > Inches(5.0) and sh.width > Inches(6.0):
            n = sh
    if n is not None:
        n.top = Inches(top_in)


def table_of(slide):
    for sh in slide.shapes:
        if sh.has_table: return sh.table
    raise KeyError("no table")

# ---- slide 5: the LANDSCAPE, one slide, grouped by what the work does ----
# The old deck spread eight papers over two identical 4-row tables and made the
# reader do the clustering. Reviewers want the shape of the field on one slide
# and the near neighbours on the next, so that is what these two now are.
CLUSTERS = [
 ("A · Passive / analogue crosstalk fixes",
  "[1] [3] [4] [11] [12]",
  "Negative off-bias, RC-diode rails, three-level drive, Miller clamps. Cheap and effective, "
  "but the setting is chosen once by hand and never revisited."),
 ("B · Closed-loop analogue adaptation",
  "[5] [6] [7]",
  "Sense the operating point, regulate drive strength or timing in the loop. Reports large "
  "gains — 30.5 % less overshoot, 75 % less turn-off loss — against a conventional driver."),
 ("C · Adaptive dead-time control",
  "[8] [13]",
  "Dead time driven to sub-nanosecond across load. The one field our own freeze test finds "
  "actually carries the benefit — and only at light load."),
 ("D · DIGITAL / segmented drive  — where this project sits",
  "[9] BASE   [10]",
  "The gate waveform selected by a multibit CODE rather than a resistor network. [9] is the "
  "BASE PAPER — doi.org/10.1002/cta.3136 — and [10] is the closest GaN implementation. "
  "Digital means FPGA-implementable, and the code space can be searched exhaustively."),
]
sc = S[4]
set_title(sc, "Literature Landscape — four clusters, and where we sit")
note = find_shape(sc, "Minimum 8")
set_body(note, [para([("13 references. Grouped by what the driver DOES, not by date. "
                       "Clusters A\u2013C choose a setting or regulate it in analogue; only "
                       "cluster D makes the setting a digital code \u2014 which is what makes an "
                       "exhaustive search, and this project\u2019s question, possible at all.",
                       False)], level=0, sz=1150, spc=0, bullet=False)])
tbl = table_of(sc)
set_cell(tbl.cell(0, 0), "#");        set_cell(tbl.cell(0, 1), "Cluster")
set_cell(tbl.cell(0, 2), "Refs");     set_cell(tbl.cell(0, 3), "What the cluster does")
set_cell(tbl.cell(0, 4), "")
tbl.cell(0, 3).merge(tbl.cell(0, 4))
for row, (name, refs_, what) in enumerate(CLUSTERS, start=1):
    set_cell(tbl.cell(row, 0), "ABCD"[row - 1])
    set_cell(tbl.cell(row, 1), [(name, True)])
    set_cell(tbl.cell(row, 2), refs_)
    tbl.cell(row, 3).merge(tbl.cell(row, 4))
    set_cell(tbl.cell(row, 3), what)
for row in (6, 5):
    tbl._tbl.remove(tbl.rows[row]._tr)
for row in range(len(tbl.rows)):
    tbl.rows[row].height = Inches(0.90 if row else 0.35)
move_note(sc, 6.45)

# ---- slide 6: the five closest papers, base paper first -----------------
CLOSEST = [R.REFS[8]] + [r for r in R.REFS if r.closest][:4]
sn = S[5]
set_title(sn, "The Five Closest — and the base paper we replicate")
note = find_shape(sn, "Minimum 8")
set_body(note, [para([("[9] is the BASE PAPER: we reproduce its premise \u2014 a gate waveform "
                       "chosen by a multibit code \u2014 on GaN, then extend it. Titles, venues, "
                       "years and DOIs are confirmed; author lists and page ranges sit behind "
                       "IEEE Xplore, which the build environment cannot reach, and are not "
                       "invented.", False)], level=0, sz=1000, spc=0, bullet=False)])
tbl = table_of(sn)
for row, ref in enumerate(CLOSEST, start=1):
    tag = "BASE" if ref.base else str(ref.n)
    set_cell(tbl.cell(row, 0), [(tag, ref.base)])
    set_cell(tbl.cell(row, 1), ref.table_author(), grey=not ref.done)
    set_cell(tbl.cell(row, 2), [(ref.title, False), ("\n" + ref.table_venue(), True)],
             size=Pt(9))
    set_cell(tbl.cell(row, 3), ref.method, size=Pt(9))
    set_cell(tbl.cell(row, 4), ref.finding, size=Pt(9))
tbl._tbl.remove(tbl.rows[6]._tr)
for row in range(len(tbl.rows)):
    tbl.rows[row].height = Inches(0.88 if row else 0.35)
move_note(sn, 6.62)

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
s8 = S[11]
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
s9 = S[12]
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
    para([("It is carried by the dead time — and the dead time by one corner. ", True),
          ("Freezing dead time costs 5.45 % across four corners. Drop the light-load "
           "50 V / 2 A corner and it costs ", False), ("0.00 %", True),
          (": three corners want 5 ns, only that one wants 15 ns. So the adaptive hardware "
           "reduces to a light-load detector picking one of two dead times. Freezing pull-up "
           "drive strength costs ", False), ("0.00 %", True),
          (" — and drive strength is what the active-gate-driver literature actually schedules.",
           False)], level=0, sz=1200, spc=180, bullet=False),
    para([("Robust to the device, conditional on the layout. ", True),
          ("Across 21,600 transients, no device parameter moves the ceiling outside 4.3–7.7 %. "
           "Halving the loop inductance takes it to 13.5 %, and loop inductance is board layout, "
           "not the transistor [3].", False)], level=0, sz=1300, spc=0, bullet=False),
])
p.save(OUT)
print("slides 8 and 9 built")

# ---------------- references slide -----------------------------------------
ref_shape = find_shape(S[19], "A. Author")
# 13 refs no longer fit at 11.5 pt with 3 pt leading; tighten both, and mark
# the base paper so the panel can find it in the list
paras = []
for r in R.REFS:
    head = "[%d]  " % r.n
    runs = [(head, True)]
    if r.base:
        runs.append(("BASE PAPER — ", True))
    runs.append((r.cite(), False))
    if r.url():
        runs.append(("   " + r.url(), True))
    paras.append(para(runs, level=0, sz=900, spc=120, bullet=False))
n_done, n_pend = len(R.DONE), len(R.PENDING)
paras.append(para([
    ("%d of %d verified against the publisher record. " % (n_done, len(R.REFS)), False),
    ("The remaining %d carry title, journal status and Xplore document ID; " % n_pend, False),
    ("volume, issue, pages and authors were not reachable from the build environment and are "
     "left blank rather than guessed.", False)], level=0, sz=850, spc=0, bullet=False))
set_body(ref_shape, paras)

try:
    n2 = find_shape(S[19], "Use IEEE format")
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
s10 = S[16]
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
s11 = S[17]
retitle(s11, "Why the numbers hold")

TILES = [
    ("34,622", "transient simulations",
     "Every sweep, corner study, robustness run, loop-inductance and EMI sweep, start to finish."),
    ("720", "control words, searched in full",
     "At every corner — so each per-corner optimum is a true optimum, not the best of a shortlist."),
    ("25×", "timestep refinement survived",
     "Every reported quantity must be flat across it. Enforced, not assumed."),
    ("10", "wrong numbers caught, and corrected",
     "By that discipline, before any of them reached the report. Every one came from resampling "
     "or re-deriving a figure of our own — none from a reviewer."),
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

# The RTL slide's text box inherited the template's full 5.40 in height, so it
# ran under the waveform figure that now sits at y=4.05.
for sh in S[10].shapes:
    if sh.has_text_frame and sh.text_frame.text.startswith("Three modules emitting"):
        sh.height = Inches(2.45)

# The reference list inherited the template's full-height content box (5.40 in)
# but holds about 4 in of text, so the tail ran under the footnote.
for sh in S[19].shapes:
    if sh.has_text_frame and sh.text_frame.text.startswith("[1]"):
        sh.height = Inches(4.75)

p.save(OUT)
print("geometry fixes applied")


# ================= slide 11 : robustness ==================================
s_rob = S[15]
retitle(s_rob, "Backup — the device doesn\u2019t move it; layout does")

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
    para([("So the claim is narrower and more useful than “robust”: from about 2.5 nH "
           "upward a fixed word is nearly as good; on a tighter loop the question has to be "
           "re-asked, and the answer there is not even monotonic — see slide 19.", False)],
         level=0, sz=1300, spc=0, bullet=True),
])

# ================= slide 14 : conclusion ==================================
s_con = S[18]
set_title(s_con, "Conclusion & next steps")
con_shape = find_shape(s_con, "Problem Statement:")
set_body(con_shape, [
    para([("What the data supports", True)], level=0, sz=1600, spc=200, bullet=False),
    para([("Choosing the control word well matters enormously — it spans roughly fivefold in "
           "switching energy. ", False),
          ("Adapting it to the operating point does not: 3.9 %, a seventh of the total gain, "
           "and one comparator takes 72 % of even that.", True)],
         level=0, sz=1450, spc=180, bullet=True),
    para([("The benefit that exists is carried by the ", False), ("dead time", True),
          (" — and the dead time, in turn, by the ", False), ("light-load corner alone", True),
          (": leave it out and freezing dead time costs 0.00 %. Not by the drive-strength "
           "segmentation that motivates the hardware, which stays at 0.00 % even when the "
           "objective prices EMI. Crosstalk safety is nearly free once the clamp is present.",
           False)], level=0, sz=1400, spc=180, bullet=True),
    para([("Stated positively — and this is the deliverable, not the percentage: ", True),
          ("use the recommended fixed word with a light-load comparator, and the full "
           "sense + ADC + lookup table is left justifying 3.7 % of the achievable gain.",
           False)], level=0, sz=1450, spc=260, bullet=True),
    para([("What the data now answers, and what is next", True)], level=0, sz=1600, spc=200,
         bullet=False),
    para([("The EMI objection is now tested rather than conceded.", True),
          (" Re-running the full search under objectives that price turn-on slew rate, and "
           "again under 30–500 MHz band energy, makes scheduling worth ", False),
          ("less", True), (", not more: 5.95 % falls to 0.15 %. Pull-up strength still does "
           "not need scheduling — it needs a different fixed value.", False)],
         level=0, sz=1450, spc=180, bullet=True),
    para([("What it does not support.", True),
          (" Which EMI measure a designer should price is unsettled, and the two disagree: "
           "under band energy freezing pull-up costs 0.00 % at every weight, under slew rate "
           "up to 2.27 % in a narrow transition band. No silicon has been measured, and one "
           "device model underlies everything.", False)],
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
for sl, txt in ((S[11], "Result 1 — crosstalk is real; the clamp fixes it"),
                (S[12], "Result 2 — scheduling is worth only 5.2 %")):
    for sh in sl.shapes:
        if sh.has_text_frame and sh.text_frame.text.strip() in ("Results", "Results (contd.)"):
            for pa in sh.text_frame.paragraphs:
                for r in pa.runs:
                    r.text = txt
            break

p.save(OUT)
print("slide 2: %d of %d fields set; results slides retitled" % (hits, len(REPL)))

# ================= speaker notes + time budget ============================
# 17 slides against an 8-10 minute slot. Without a budget the talk overruns
# and the marker docks presentation quality, so each slide carries its target
# and the two droppable slides say so.
# Official brief: 10 minutes, and the mark split is problem clarity 2,
# literature 1, proposed solution 1, presentation quality 1.
#
# The CORE set below totals 535 s = 8.9 min, leaving ~1 min for transitions
# and the inevitable overrun. Three slides are marked BACKUP: they stay in the
# deck and are strong answers to likely questions, but they are not presented
# unless asked. Presentation quality is a mark, and overrunning a 10-minute
# slot is the easiest way to lose it.
# 20 slides, 10-minute slot. CORE totals 570 s = 9.5 min, leaving 30 s of
# margin. Four slides are BACKUP: in the deck, prepared, not presented.
NOTES = {
 2:  ("15 s", "CORE. Project name and the one-line claim: a segmented GaN gate driver, and a "
               "measurement of what per-operating-point adaptation is actually worth."),
 3:  ("skip", "SKIP. Template slide."),
 4:  ("60 s", "CORE — the 2-mark slide, the biggest block in the review. Land two things: the "
              "failure is real and specific (1.65 V on a 1.40 V threshold), and the gap is "
              "that prior work conflates 'better fixed settings' with 'settings that adapt'."),
 5:  ("30 s", "CORE — literature mark. Do not read the table. Eight references, three verified "
              "to page level; point at [3], layout sets loop inductance, which decides our "
              "answer."),
 6:  ("25 s", "CORE — literature mark. Closest prior work. [8] adapts dead time, the one field "
              "we find worth scheduling — and it does so across a 0.2-2 A range, which is "
              "exactly the light-load corner our leave-one-out test shows carries all of that "
              "benefit. Independent support, not competition."),
 7:  ("30 s", "CORE — proposed-solution mark. The 720-point control word and the method: "
              "exhaustive search at every corner, so each per-corner optimum is a TRUE optimum "
              "and not the best of a shortlist."),
 8:  ("30 s", "CORE. Walk the diagram left to right in one sentence, then stop on the dashed "
              "block: that is the sensing and lookup-table machinery the adaptive premise "
              "needs. The whole project is a measurement of what it buys. Let the picture do "
              "the work — do not narrate every box."),
 9:  ("40 s", "CORE — the 50 %-completion requirement. Five claims, each with a number. If "
              "asked 'is this really 50 %?': the search is complete, stress-tested, and both "
              "objections to it - layout and EMI - have been tested rather than argued. What "
              "remains is silicon and hardware."),
 10: ("30 s", "CORE — the timeline and tools requirement. M1-M6. If asked what could go wrong: "
              "M1, the PDK — a 1.8 V / 3.3 V teaching PDK cannot take a 5 V rail."),
 11: ("BACKUP", "BACKUP — the FPGA. If asked: written AND verified, eight asserted properties, "
                "then mutation-tested. Dead time gets a live register and drive strength is "
                "strapped, because that is what the study found."),
 12: ("40 s", "CORE. The problem reproduced and fixed. Point at the red X below the threshold "
              "line. Then: safety costs 0.04 % — nearly free once the clamp is present."),
 13: ("25 s", "CORE. 5.2 %. Say plainly this is a NEGATIVE result about the adaptive premise "
              "and you are reporting it rather than hiding it. Keep it short — slides 18 and "
              "19 do the real work."),
 14: ("45 s", "CORE — the novelty slide, and the one sentence the panel should leave with: "
              "'a full sense-plus-ADC-plus-lookup-table is left justifying 3.7 % of the gain "
              "over a fixed word and one comparator.' Build it in three steps. (1) Choosing "
              "the fixed word well is worth 25.1 %. (2) Adapting per corner adds only 3.9 % "
              "— a seventh of the total. (3) And 72 % of even THAT is capturable with a "
              "single light-load comparator, not a lookup table. No published work separates "
              "these, because separating them needs the exhaustive search rather than a "
              "shortlist. If asked why nobody found this: they report one number."),
 15: ("40 s", "CORE — the design chart, and the most USEFUL thing in the deck. Do NOT call it "
              "a single crossover: eight points show a BAND. Adaptive control pays from about "
              "2.5 nH down, peaks at 13.5 % at 1.5 nH, then FALLS BACK to 8.1 % at 1.0 nH. Say "
              "why, because it is the interesting part: at 1.0 nH only 165 of 720 words are "
              "still safe, so the fixed word and the per-corner optima are squeezed into the "
              "same narrow region and the gap scheduling exploits shrinks. Below ~2 nH "
              "feasibility binds, not optimisation. We checked it is not the clamp-chatter "
              "artefact — excluding every chatter point leaves all eight ceilings unchanged to "
              "the digit. The literature does not state this trade-off because it never "
              "separates the fixed and adaptive halves."),
 16: ("BACKUP", "BACKUP — the robustness table. Best answer to 'is this just your model?': "
                "every device parameter leaves the ceiling at 4.3-7.7 %; only loop inductance "
                "moves it, and that is board layout, not the transistor."),
 17: ("25 s", "CORE. Play the video. Real captured ngspice output — the failure, the fix, the "
              "search. Let it run; do not talk over it."),
 18: ("BACKUP", "BACKUP — use if the panel probes rigour. TEN wrong numbers caught by our own "
                "checks is a strength; say it that way. The best one to tell: dead time ranked "
                "first at 5.45 % on four corners and dead LAST at 0.00 % on two, and we chased "
                "it to a single light-load corner rather than quoting the flattering number. The "
                "leave-one-out table is in results/FINDINGS.md section 32 if they want it."),
 19: ("35 s", "CORE. Close on what the data supports and what it now answers. Do NOT concede "
              "EMI as a limitation any more - it was tested: pricing it makes scheduling worth "
              "LESS, 5.95 % down to 0.15 %. State the remaining limits yourself instead: the "
              "two EMI measures disagree about drive strength, no silicon has been measured, "
              "and one device model underlies everything."),
 20: ("skip", "Reference list. Leave up during questions."),
 21: ("—",    "Thank you. Expect: 'why is the clamp worth more than scheduling?', 'have you run "
              "real silicon?' (no — Review-II), 'did Cadence actually run?' (no, and the deck "
              "says so), 'is 8 references enough?' (it is the stated minimum). Newer ones: "
              "'your dead-time number depends on which corners you pick' — yes, and we found "
              "that ourselves; it is one light-load corner - leave-one-out table in "
              "FINDINGS.md section 32. "
              "'Doesn't EMI change your answer?' — we ran it; it makes scheduling worth less, "
              "not more."),
}

NOTES_BODY = (
 '<p:sp xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
 '<p:nvSpPr><p:cNvPr id="99" name="Notes Placeholder"/>'
 '<p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>'
 '<p:nvPr><p:ph type="body" idx="1"/></p:nvPr></p:nvSpPr>'
 '<p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>')

def set_note(slide, text):
    """Cloned slides get a notes part with no body placeholder, so
    notes_text_frame is None until one is injected."""
    ns = slide.notes_slide
    if ns.notes_text_frame is None:
        ns.shapes._spTree.append(etree.fromstring(NOTES_BODY))
    ns.notes_text_frame.text = text


for n, (budget, note) in NOTES.items():
    ns = S[n - 1].notes_slide
    if ns.notes_text_frame is None:
        # Slides cloned by add_slide.py inherit a notes part with no body
        # placeholder, so python-pptx has nothing to write into. Add one.
        ns.shapes._spTree.append(etree.fromstring(NOTES_BODY))
    ns.notes_text_frame.text = "[%s]  %s" % (budget, note)

p.save(OUT)
print("speaker notes added to %d slides (budget: ~8 min of talking)" % len(NOTES))

# 2480x900 -> aspect 2.756. At 7.30 in wide the figure is 2.65 in tall.
S[10].shapes.add_picture(RES + "/fig_rtl_waveform.png",
                         Inches(3.00), Inches(4.05), width=Inches(7.30))
add_text(S[10], 3.00, 6.80, 7.30, 0.34, [
    para([("Icarus Verilog VCD. ls_pu falls to 0 before hs_pu rises — the shaded dead time is "
           "the gap, and no shoot-through window exists.", False)],
         level=0, sz=1000, spc=0, bullet=False)])

# ================= slide 8 : architecture =================================
s_arch = S[7]
retitle(s_arch, "System Architecture")
# 2640x1260 -> aspect 2.095. The band from 1.30 in to the caption at 6.55 in
# is 5.25 in tall, so the width that fits is 5.25 * 2.095 = 11.0 in.
s_arch.shapes.add_picture(RES + "/fig_architecture.png",
                          Inches(1.17), Inches(1.32), width=Inches(11.00))
add_text(s_arch, 0.70, 6.66, 11.90, 0.38, [
    para([("Solid blocks are configured once at power-up. The dashed block — sensing, ADC and "
           "lookup table — is the adaptive machinery this project exists to price.", False)],
         level=0, sz=1100, spc=0, bullet=False)])

# ================= slide 13 : the novelty =================================
s_nov = S[13]
retitle(s_nov, "Result 3 — the two halves nobody separates")

add_text(s_nov, 0.70, 1.38, 12.10, 0.80, [
    para([("The base paper [9] ", False), ("(doi.org/10.1002/cta.3136)", True),
          (" shows a gate waveform can be chosen by a digital code. It, and every "
           "active-gate-driver paper after it, then reports ", False), ("one", True),
          (" number — the improvement over a conventional driver. That number bundles two "
           "separable effects, and only the second needs sensing, an ADC and a lookup table. "
           "Separating them needs the exhaustive search, which is why nobody has.", False)],
         level=0, sz=1250, spc=0, bullet=False)])

NOV = [("(A)   Choose a better FIXED word",        "25.1 %", "no sensing · no LUT"),
       ("(B)   ADAPT it per operating point",      "3.9 %",  "needs all of it"),
       ("(B′)  …but ONE comparator captures 72 % of (B)", "2.8 %", "a threshold, not a LUT")]
for i, (label, val, sub) in enumerate(NOV):
    y = 2.42 + i * 1.12
    add_text(s_nov, 0.70, y, 6.55, 0.40,
             [para([(label, True)], level=0, sz=1400, spc=0, bullet=False)])
    add_text(s_nov, 7.45, y - 0.20, 2.15, 0.72,
             [para([(val, True)], level=0, sz=2600, spc=0, bullet=False)])
    add_text(s_nov, 9.85, y + 0.04, 2.95, 0.60,
             [para([(sub, False)], level=0, sz=1100, spc=0, bullet=False)])

add_text(s_nov, 0.70, 5.92, 12.10, 1.10, [
    para([("So the full sense + ADC + lookup table is left justifying ", False),
          ("3.7 % of the total achievable gain", True),
          (" over a fixed word plus one comparator. Adaptation is 13.4 % of the gain; a single "
           "threshold takes 72 % of that.", False)], level=0, sz=1300, spc=130, bullet=False),
    para([("Every figure shares one baseline — the median control word that is safe at all four "
           "corners. Robust across cost weightings: adaptation is 5.5–20.1 % of the gain for "
           "overshoot weights 0 to 1.0. ", False),
          ("scripts/novelty.py", True), (", ", False), ("scripts/howmanywords.py", True),
          (".", False)], level=0, sz=1200, spc=0, bullet=False),
])

for n, sl in enumerate(S, start=1):
    renumber(sl, n)
p.save(OUT)
# ================= slide 15 : the design chart ============================
s_chart = S[14]
retitle(s_chart, "Result 4 — adaptive pays below ~2.5 nH")
# aspect 1.856 (two stacked panels); 1.35 in to the caption at 6.36 in is
# 4.90 in tall, so the width that fits is 4.90 * 1.856 = 9.09 in, centred.
s_chart.shapes.add_picture(RES + "/fig_lloop.png",
                           Inches(2.12), Inches(1.35), width=Inches(9.09))
add_text(s_chart, 0.70, 6.36, 11.90, 0.70, [
    para([("Eight inductances, 7,200 transients. The answer is a ", False), ("band", True),
          (", not a threshold: adaptive control pays only from about 2.5 nH down, peaking at "
           "13.5 % at 1.5 nH, and it falls back to 8.1 % at 1.0 nH because only 165 of 720 "
           "words stay safe there — below ~2 nH feasibility binds, not optimisation. ", False),
          ("A designer measures their loop and reads off the decision", True),
          (" — a trade-off the literature does not state.", False)],
         level=0, sz=1200, spc=0, bullet=False)])

for n, sl in enumerate(S, start=1):
    renumber(sl, n)
p.save(OUT)
print("slides 8 (architecture), 14 (novelty) and 15 (design chart) built")


# ================= slide 9 : what a control word IS =======================
# The deck's central object was never defined anywhere. Slides 13-15 are all
# about "the fixed word" versus "scheduling the word", and a reader had no
# way to know a word is a 6-tuple. Without this slide those results are
# unreadable, which is exactly how they read.
import copy as _copy

def clone_after(prs, src_idx, dest_idx):
    """Duplicate a slide and move the copy to dest_idx.

    Deep-copying the shape XML alone leaves r:embed ids pointing at
    relationships the new slide part does not have, so the logo vanishes;
    the relationships are re-created and the ids remapped below."""
    src = prs.slides[src_idx]
    new = prs.slides.add_slide(src.slide_layout)
    for shp in list(new.shapes):
        shp._element.getparent().remove(shp._element)
    NOTES_RT = ("http://schemas.openxmlformats.org/officeDocument/2006/"
                "relationships/notesSlide")
    idmap = {}
    for rid, rel in src.part.rels.items():
        # NEVER carry the notes relationship across: the clone would SHARE the
        # source slide's notes part, so writing the copy's speaker note
        # silently overwrites the original's.
        if rel.reltype == NOTES_RT:
            continue
        if rel.is_external:
            idmap[rid] = new.part.rels.get_or_add_ext_rel(rel.reltype, rel.target_ref)
        else:
            idmap[rid] = new.part.relate_to(rel.target_part, rel.reltype)
    R_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
    for shp in src.shapes:
        el = _copy.deepcopy(shp._element)
        for node in el.iter():
            for attr in ("embed", "link", "id"):
                key = R_NS + attr
                if key in node.attrib and node.attrib[key] in idmap:
                    node.attrib[key] = idmap[node.attrib[key]]
        new.shapes._spTree.append(el)
    lst = prs.slides._sldIdLst
    items = list(lst)
    lst.remove(items[-1])
    lst.insert(dest_idx, items[-1])
    return prs.slides[dest_idx]

s_def = clone_after(p, 11, 8)          # copy the blank "Results" frame -> slide 9
for sh in list(s_def.shapes):          # strip the architecture content off the copy
    if sh.has_text_frame and sh.text_frame.text.strip() and not sh.has_table:
        if sh.width > Inches(4) and sh.top > Inches(1.0):
            sh._element.getparent().remove(sh._element)
    elif sh.shape_type == 13 and sh.left < Inches(11):
        sh._element.getparent().remove(sh._element)
# retitle() only matches the template's literal "Results (contd.)", and the
# clone's title was already rewritten, so set it directly
for sh in s_def.shapes:
    if sh.has_text_frame and sh.top is not None and sh.top < Inches(1.0) \
       and sh.left is not None and sh.left < Inches(1.0):
        tf = sh.text_frame
        for extra in list(tf.paragraphs)[1:]:
            extra._p.getparent().remove(extra._p)
        pa = tf.paragraphs[0]
        runs = list(pa.runs)
        if runs:
            runs[0].text = "What is a \u201ccontrol word\u201d?"
            for r in runs[1:]:
                r._r.getparent().remove(r._r)
        break

add_text(s_def, 0.70, 1.25, 12.0, 0.45, [
    para([("Everything in this deck is measured over control words, so this is the "
           "definition the rest of the results rest on.", False)],
         level=0, sz=1300, spc=0, bullet=False)])

FIELDS = [("N_PU", "pull-up slices ON", "1 – 8", "how hard the device is turned ON"),
          ("N_PD,LS", "low-side pull-down slices", "1 – 8", "how hard it is turned OFF"),
          ("N_PD,HS", "high-side pull-down slices", "1, 4, 8", "the off device's grip on its gate"),
          ("t_dead", "dead time", "5 / 10 / 15 / 25 ns", "gap before the other device turns on"),
          ("CLK_EN", "active Miller clamp", "off / on", "shorts the gate during the other edge"),
          ("V_neg", "gate off-bias", "0 V / −2 V", "how far below threshold the gate is held")]
YT, DY = 2.05, 0.52
add_text(s_def, 0.70, YT - 0.34, 12.0, 0.30, [
    para([("ONE control word = one setting of these six fields", True)],
         level=0, sz=1250, spc=0, bullet=False)])
for i, (sym, name, vals, why) in enumerate(FIELDS):
    y = YT + i * DY
    add_text(s_def, 0.85, y, 1.60, 0.34,
             [para([(sym, True)], level=0, sz=1150, spc=0, bullet=False)])
    add_text(s_def, 2.50, y, 3.05, 0.34,
             [para([(name, False)], level=0, sz=1150, spc=0, bullet=False)])
    add_text(s_def, 5.60, y, 2.05, 0.34,
             [para([(vals, True)], level=0, sz=1150, spc=0, bullet=False)])
    add_text(s_def, 7.75, y, 4.85, 0.34,
             [para([(why, False)], level=0, sz=1150, spc=0, bullet=False)])

add_text(s_def, 0.70, 5.28, 12.0, 1.30, [
    para([("8 × 8 × 3 × 4 × 2 × 2  =  ", False), ("720 control words", True),
          (".  We simulate every one of them, at every corner — that is what makes this an "
           "exhaustive search rather than a shortlist.", False)],
         level=0, sz=1300, spc=140, bullet=False),
    para([("A FIXED word", True),
          (" is one word chosen once and strapped at power-up — no sensing. ", False),
          ("SCHEDULING", True),
          (" means sensing the operating point and switching to a different word for it, which "
           "is what needs an ADC and a lookup table. The whole project measures the gap between "
           "those two.", False)], level=0, sz=1300, spc=0, bullet=False)])


# the definition slide is created after NOTES is applied, so it gets its own
DEF_NOTE = ("[30 s]  CORE — do NOT skip this and do not rush it. Every number after "
            "this slide is a comparison between control words, and if the panel has not "
            "got the definition, slides 13 to 16 are noise to them. Read the six fields "
            "out loud, land 720, then land the one distinction that matters: a FIXED word "
            "is strapped at power-up and costs nothing; SCHEDULING needs sensing, an ADC "
            "and a lookup table. The whole project measures the gap between those two.")
if s_def.has_notes_slide or True:
    set_note(s_def, DEF_NOTE)

for n, sl in enumerate(S, start=1):
    renumber(sl, n)
p.save(OUT)
print("slide 9 (control-word definition) inserted; deck now %d slides" % len(S))

# ============ slide 10 : base paper vs this work ==========================
# A review wants the delta stated, not inferred. Every row is either a fact
# about the two designs or a number this project measured; nothing here
# claims we beat the base paper on ITS metric, because we have not run it.
s_cmp = clone_after(p, 11, 9)
for sh in list(s_cmp.shapes):
    if sh.has_text_frame and sh.text_frame.text.strip() and not sh.has_table:
        if sh.width > Inches(4) and sh.top > Inches(1.0):
            sh._element.getparent().remove(sh._element)
    elif sh.shape_type == 13 and sh.left < Inches(11):
        sh._element.getparent().remove(sh._element)
for sh in s_cmp.shapes:
    if sh.has_text_frame and sh.top is not None and sh.top < Inches(1.0) \
       and sh.left is not None and sh.left < Inches(1.0):
        tf = sh.text_frame
        for extra in list(tf.paragraphs)[1:]:
            extra._p.getparent().remove(extra._p)
        runs = list(tf.paragraphs[0].runs)
        if runs:
            runs[0].text = "Base paper vs this work — what we improve"
            for r in runs[1:]:
                r._r.getparent().remove(r._r)
        break

add_text(s_cmp, 0.70, 1.22, 12.0, 0.40, [
    para([("Base paper [9]: Takayama & Hikihara, Int. J. Circuit Theory Appl., 50(1):183–196, "
           "2022 — a gate waveform chosen by a multibit digital code.", False)],
         level=0, sz=1150, spc=0, bullet=False)])

CMP = [
 ("Device",            "SiC MOSFET",                     "GaN HEMT (e-mode)  —  no body diode, so off-bias costs third-quadrant drop"),
 ("Control handle",    "multibit gate code, one field",  "6-field, 720-point control word  —  strength, dead time, clamp, off-bias"),
 ("Implementation",    "digital driver",                 "FPGA RTL in Verilog  ·  8 asserted properties, mutation-tested"),
 ("How codes chosen",  "selected codes, measured",       "EXHAUSTIVE  —  all 720 words at every corner, 34,622 transients"),
 ("Crosstalk",         "not addressed",                  "1.65 V spurious gate  →  −1.18 V  (2.58 V margin), clamp + off-bias"),
 ("What is reported",  "one number vs a conventional driver",
                       "the number SPLIT: fixed word 25.1 %, adapting it 3.9 %, one comparator takes 72 % of that"),
 ("Design rule",       "none",                           "adaptive control pays only below ~2.5 nH loop inductance"),
]
X0, X1, X2 = 0.70, 3.45, 7.05
YT, DY = 1.95, 0.60
for lbl, xs, ys in ((("Parameter", True), X0, YT - 0.42),):
    pass
add_text(s_cmp, X0, YT - 0.46, 2.60, 0.30,
         [para([("Parameter", True)], level=0, sz=1150, spc=0, bullet=False)])
add_text(s_cmp, X1, YT - 0.46, 3.45, 0.30,
         [para([("Base paper [9]", True)], level=0, sz=1150, spc=0, bullet=False)])
add_text(s_cmp, X2, YT - 0.46, 5.55, 0.30,
         [para([("This work", True)], level=0, sz=1150, spc=0, bullet=False)])
for i, (par, base, ours) in enumerate(CMP):
    y = YT + i * DY
    add_text(s_cmp, X0, y, 2.65, 0.50,
             [para([(par, True)], level=0, sz=1050, spc=0, bullet=False)])
    add_text(s_cmp, X1, y, 3.50, 0.50,
             [para([(base, False)], level=0, sz=1050, spc=0, bullet=False)])
    add_text(s_cmp, X2, y, 5.60, 0.50,
             [para([(ours, False)], level=0, sz=1050, spc=0, bullet=False)])

add_text(s_cmp, 0.70, 6.28, 12.0, 0.75, [
    para([("The parameter we improve is not a volt or a nanosecond — it is ", False),
          ("what the designer knows before committing silicon", True),
          (". [9] shows a digital code works. We measure what the code is worth, and how much "
           "of that worth needs sensing at all: 3.7 % of the achievable gain, which is what the "
           "sense + ADC + lookup table has to justify.", False)],
         level=0, sz=1200, spc=0, bullet=False)])

set_note(s_cmp, (
    "[35 s]  CORE — the comparison the panel will ask for. Land three rows and move on: "
    "we go from ONE field to six (720 words); from selected codes to an EXHAUSTIVE search; "
    "and from one bundled number to the number SPLIT into fixed versus adaptive. Be honest "
    "if pushed: we have NOT re-run [9]'s SiC experiment, so this is a comparison of method "
    "and scope, not a claim that we beat their result on their metric. That replication is "
    "the next step."))

for n, sl in enumerate(S, start=1):
    renumber(sl, n)
p.save(OUT)
print("slide 10 (base paper vs this work) inserted; deck now %d slides" % len(S))


# ============ slide 9 : the circuit itself =================================
# The architecture slide shows what talks to what. A panel asking "what did
# you actually simulate?" wants the schematic, so it goes right after it and
# before the control-word definition.
s_ckt = clone_after(p, 11, 8)
for sh in list(s_ckt.shapes):
    if sh.has_text_frame and sh.text_frame.text.strip() and not sh.has_table:
        if sh.width > Inches(4) and sh.top > Inches(1.0):
            sh._element.getparent().remove(sh._element)
    elif sh.shape_type == 13 and sh.left < Inches(11):
        sh._element.getparent().remove(sh._element)
for sh in s_ckt.shapes:
    if sh.has_text_frame and sh.top is not None and sh.top < Inches(1.0) \
       and sh.left is not None and sh.left < Inches(1.0):
        tf = sh.text_frame
        for extra in list(tf.paragraphs)[1:]:
            extra._p.getparent().remove(extra._p)
        runs = list(tf.paragraphs[0].runs)
        if runs:
            runs[0].text = "The circuit that is simulated"
            for r in runs[1:]:
                r._r.getparent().remove(r._r)
        break

s_ckt.shapes.add_picture(RES + "/fig_circuit.png",
                         Inches(2.22), Inches(1.22), width=Inches(8.89))
add_text(s_ckt, 0.70, 6.20, 12.10, 0.85, [
    para([("Every element is in ", False), ("sim/dpt.cir", True),
          (", which is the file to open in LTspice — it carries the active Miller clamp "
           "(S", False), ("clk", False), (" through 0.5 \u03a9). The three ", False),
          ("ltspice/*.asc", True),
          (" sheets illustrate the crosstalk mechanism only and do not draw the clamp", False),
          (". C", False), ("GD", False),
          (" on Q2 in red is the crosstalk path; GaN has no body diode, so holding the gate "
           "below threshold is paid for again across the dead time.", False)],
         level=0, sz=1200, spc=0, bullet=False)])
set_note(s_ckt, "[30 s]  CORE — use this the moment anyone asks what was actually simulated. "
                "Trace the red path with a finger: Q1 switches, the SW node moves, charge "
                "couples through C_GD into Q2's gate, and Q2 turns on when it should be off. "
                "Then point at the clamp and the off-bias mux — those are the two things that "
                "fix it. Do not read the component values out.")

for n, sl in enumerate(S, start=1):
    renumber(sl, n)
p.save(OUT)
print("slide 9 (circuit schematic) inserted; deck now %d slides" % len(S))


# ============ slide : MATLAB results ======================================
# The MATLAB work existed as scripts and loose PNGs and appeared nowhere in
# the deck. Both figures were regenerated by running the scripts.
s_mat = clone_after(p, 11, 15)
for sh in list(s_mat.shapes):
    if sh.has_text_frame and sh.text_frame.text.strip() and not sh.has_table:
        if sh.width > Inches(4) and sh.top > Inches(1.0):
            sh._element.getparent().remove(sh._element)
    elif sh.shape_type == 13 and sh.left < Inches(11):
        sh._element.getparent().remove(sh._element)
for sh in s_mat.shapes:
    if sh.has_text_frame and sh.top is not None and sh.top < Inches(1.0) \
       and sh.left is not None and sh.left < Inches(1.0):
        tf = sh.text_frame
        for extra in list(tf.paragraphs)[1:]:
            extra._p.getparent().remove(extra._p)
        runs = list(tf.paragraphs[0].runs)
        if runs:
            runs[0].text = "MATLAB — the Pareto front and the model check"
            for r in runs[1:]:
                r._r.getparent().remove(r._r)
        break

s_mat.shapes.add_picture(RES + "/pareto_matlab.png",
                         Inches(0.60), Inches(1.30), height=Inches(3.65))
s_mat.shapes.add_picture(RES + "/crosstalk_model_matlab.png",
                         Inches(6.95), Inches(1.30), height=Inches(3.65))
add_text(s_mat, 0.60, 5.10, 5.95, 1.05, [
    para([("720 words, 504 feasible (70 %).", True),
          (" A 7-word Pareto front; buying one point of overshoot back costs "
           "0.039 µJ. The green marker is the word the cost function picks.", False)],
         level=0, sz=1150, spc=0, bullet=False)])
add_text(s_mat, 6.95, 5.10, 5.75, 1.05, [
    para([("The two hand calculations disagree by 8.7×.", True),
          (" The peak-C bound says 7.50 V, charge-averaging says 0.86 V, SPICE measures "
           "1.65 V — inside the bracket. That gap is why this is simulated, not "
           "hand-calculated.", False)], level=0, sz=1150, spc=0, bullet=False)])
add_text(s_mat, 0.60, 6.28, 12.10, 0.75, [
    para([("Dead-time margin saturates at about 15 ns", True),
          (": the marginal gain runs 269 → 31.5 → 1.8 → 0.0 mV/ns across 10/15/25/35 ns. "
           "Past 15 ns dead time costs conduction loss and buys nothing. ", False),
          ("results/gan_analysis.m", True), (", ", False),
          ("results/crosstalk_standalone.m", True), (" — both run in MATLAB or Octave.",
           False)], level=0, sz=1200, spc=0, bullet=False)])
set_note(s_mat, "[35 s]  CORE — this is the MATLAB evidence, and it answers 'did you only "
                "use SPICE?'. Land two things. Left: 720 words searched, 504 feasible, and "
                "the Pareto front is only 7 words wide — the choice really is that "
                "constrained. Right: two textbook hand calculations for the same spurious "
                "voltage disagree by 8.7x, and the SPICE number sits between them. That is "
                "the argument for simulating. If you have time, add the dead-time "
                "saturation at 15 ns from the caption.")

for n, sl in enumerate(S, start=1):
    renumber(sl, n)
p.save(OUT)
print("MATLAB results slide inserted; deck now %d slides" % len(S))
