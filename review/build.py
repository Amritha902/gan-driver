# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lxml import etree
from pptx import Presentation
from pptx.util import Inches, Pt
from fill import para, set_body, find_shape, q, A, esc, RUN_TPL, PARA_TPL
import content

RES = "/home/user/gan-driver/results"
SRC = "template.pptx"
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
                          (5, content.SLIDE6, "Proposed Solution:"),
                          (6, content.SLIDE7, "Work completed so far")):
    sh = find_shape(S[idx], needle)
    set_body(sh, build_paras(spec))
    print("slide %d: %.2f in of %.2f  %s"
          % (idx + 1, fits(spec), BOX_H, "OK" if fits(spec) <= BOX_H else "OVERFLOW"))

p.save(OUT)
print("wrote", OUT)

# ---------------- slide 5 : literature survey table ------------------------
from pptx.dml.color import RGBColor

REFS = [
 ("Zhang, Wang, Tolbert & Blalock (2014)",
  "Active Gate Driver for Crosstalk Suppression of SiC Devices in a Phase-Leg Configuration — IEEE TPEL 29(4), 1986–1997",
  "Two gate-assist circuits on a SiC MOSFET phase leg; suppresses the spurious gate pulse",
  "Up to 17 % less turn-on loss. SiC has a body diode, so the third-quadrant cost of negative off-bias — the GaN-specific trade — never appears."),
 ("Xie, Wang, Tang, Yang & Chen (2017)",
  "An Analytical Model for False Turn-On Evaluation of High-Voltage Enhancement-Mode GaN Transistor in Bridge-Leg Configuration — IEEE TPEL 32(8), 6416–6433",
  "Closed-form model of the crosstalk loop for e-mode GaN; predicts the spurious gate peak",
  "Models the mechanism accurately but does not optimise a driver against it, and does not ask whether settings must adapt per operating point."),
 ("Reusch & Strydom (2014)",
  "Understanding the Effect of PCB Layout on Circuit Performance in a High-Frequency GaN-Based Point of Load Converter — IEEE TPEL 29(4), 2008–2015",
  "Measures GaN converter performance across deliberately varied board layouts",
  "Loop inductance is set by layout, not by the device. Our robustness study finds the scheduling ceiling depends on exactly this parameter (13.5 % at 1.5 nH vs 0.6 % at 4.5 nH)."),
]

def set_cell(cell, text, bold=False, size=Pt(11), grey=False):
    tf = cell.text_frame
    tf.word_wrap = True
    pa = tf.paragraphs[0]
    for r in list(pa.runs):
        r._r.getparent().remove(r._r)
    for extra in list(tf.paragraphs)[1:]:
        extra._p.getparent().remove(extra._p)
    run = pa.add_run(); run.text = text
    run.font.size = size; run.font.bold = bold; run.font.name = "Calibri"
    run.font.color.rgb = RGBColor(0x80, 0x80, 0x80) if grey else RGBColor(0, 0, 0)

tbl = None
for sh in S[4].shapes:
    if sh.has_table: tbl = sh.table
for i, (auth, title, method, find) in enumerate(REFS, start=1):
    for c, txt in enumerate((auth, title, method, find), start=1):
        set_cell(tbl.cell(i, c), txt)
for i in (4, 5, 6):
    set_cell(tbl.cell(i, 1), "— to be added —", grey=True)
    for c in (2, 3, 4):
        set_cell(tbl.cell(i, c), "", grey=True)

note = find_shape(S[4], "Minimum 8")
set_body(note, [para([("3 of the minimum 8–10 references are filled and verified against the "
                       "publisher record (volume, issue, pages, author list). ", False),
                      ("Five more still to add", True),
                      (" — duplicate this slide for rows 7–10.", False)],
                     level=0, sz=1200, spc=0, bullet=False)])
p.save(OUT)
print("slide 5: %d verified refs filled, 3 rows marked to add" % len(REFS))

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
s8 = S[7]
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
s9 = S[8]
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

# ---------------- slide 10 : references -----------------------------------
ref_shape = find_shape(S[9], "A. Author")
set_body(ref_shape, [
 para([("[1]  Z. Zhang, F. Wang, L. M. Tolbert and B. J. Blalock, “Active Gate Driver for "
        "Crosstalk Suppression of SiC Devices in a Phase-Leg Configuration,” ", False),
       ("IEEE Trans. Power Electron.", False),
       (", vol. 29, no. 4, pp. 1986–1997, Apr. 2014.", False)], level=0, sz=1400, spc=500,
      bullet=False),
 para([("[2]  R. Xie, H. Wang, G. Tang, X. Yang and K. J. Chen, “An Analytical Model for False "
        "Turn-On Evaluation of High-Voltage Enhancement-Mode GaN Transistor in Bridge-Leg "
        "Configuration,” ", False), ("IEEE Trans. Power Electron.", False),
       (", vol. 32, no. 8, pp. 6416–6433, Aug. 2017.", False)], level=0, sz=1400, spc=500,
      bullet=False),
 para([("[3]  D. Reusch and J. Strydom, “Understanding the Effect of PCB Layout on Circuit "
        "Performance in a High-Frequency Gallium-Nitride-Based Point of Load Converter,” ", False),
       ("IEEE Trans. Power Electron.", False),
       (", vol. 29, no. 4, pp. 2008–2015, Apr. 2014.", False)], level=0, sz=1400, spc=500,
      bullet=False),
 para([("Each of the three above has been verified against the publisher record. Five more are "
        "needed to meet the 8–10 minimum; they are deliberately not listed until verified, so "
        "that nothing unchecked is cited.", False)], level=0, sz=1200, spc=0, bullet=False),
])

# the template's trailing note under the reference list
try:
    n2 = find_shape(S[9], "Use IEEE format")
    set_body(n2, [para([("Use IEEE format. Every reference listed must be cited in the slides / "
                         "report.", False)], level=0, sz=1200, spc=0, bullet=False)])
except KeyError:
    pass

p.save(OUT)
print("slide 10 references written")

# ---------------- slide 2 : name / guide fields ---------------------------
# The label and its value live in SEPARATE shapes, so a run-follows-run search
# within one shape never finds them.
REPL = {
    "Name — Reg. No.":       "Amritha  —  Reg. No. ________",
    "Dr. Guide Name, School": "Dr. Bindu  —  SENSE",
}
hits = 0
for sh in S[1].shapes:
    if not sh.has_text_frame: continue
    for pa in sh.text_frame.paragraphs:
        for r in pa.runs:
            k = r.text.strip()
            if k in REPL:
                r.text = REPL[k]; hits += 1
p.save(OUT)
print("slide 2: %d of %d fields replaced" % (hits, len(REPL)))

# ---------------- geometry fixes found by qa.py ---------------------------
# The project title is longer than the template's stub, so it wraps to two
# lines at 32 pt and needs a taller box. There is 2.35 in of clear space below
# it before the name fields, so growing it cannot collide with anything.
for sh in S[1].shapes:
    if sh.has_text_frame and sh.text_frame.text.startswith("A Segmented Gate Driver"):
        sh.height = Inches(1.30)

# The reference list inherited the template's full-height content box (5.40 in)
# but holds about 2 in of text, so the empty box ran under the footnote.
for sh in S[9].shapes:
    if sh.has_text_frame and sh.text_frame.text.startswith("[1]"):
        sh.height = Inches(4.60)

p.save(OUT)
print("geometry fixes applied")
