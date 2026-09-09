# -*- coding: utf-8 -*-
"""simplify.py -- runs after build.py.

Two jobs, both asked for directly: say the same things in words a panel can
follow without a glossary, and carry fewer slides. Nothing here changes a
number; only the sentences around the numbers, and which slides survive.

Slides removed are the ones whose content is already stated somewhere else:
the control-word table (defined in place on the slides that use it), the tool
inventory (the timeline slide lists the same tools), the Vivado report figure
(the on-screen captures next to it show the same numbers), the device/layout
backup (its conclusion is a paragraph on Result 2), the evidence-count slide
(the same counts are on Work Completed), and a section divider standing in
front of a single slide.

Text is replaced in place: the paragraph and run properties already on the
shape are read back and reused, so size, weight and bullet style stay exactly
as build.py set them.
"""
import os, sys, copy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lxml import etree
from pptx import Presentation
from pptx.util import Inches
from fill import q, A, esc, RUN_TPL

HERE = os.path.dirname(os.path.abspath(__file__))
DECK = os.path.join(HERE, "Review1_GaN_Segmented_Gate_Driver.pptx")

p = Presentation(DECK)


def title_of(slide):
    for sh in slide.shapes:
        if sh.has_text_frame and sh.width and abs(sh.width - Inches(10.5)) < Inches(0.3):
            t = sh.text_frame.text.strip()
            if t:
                return t
    return ""


def all_text(slide):
    return "\n".join(sh.text_frame.text for sh in slide.shapes if sh.has_text_frame)


# ------------------------------------------------------------------ cuts ---
DROP = [
    u"What is a “control word”?",
    u"Tools — and what each one produced",
    u"Vivado — the synthesis report itself",
    u"Backup — the device doesn’t move it; layout does",
    u"Why the numbers hold",
    # One tool for the circuit work. This slide re-plotted the same ngspice
    # sweep in a second program as a cross-check; keeping it made the project
    # look like it was spread across four tools when it is not.
]
# Matched on prefix: build.py titles this slide "MATLAB \u2014 the Pareto front
# and the model check" and it is renamed later in this same file, so an exact
# match against either spelling is fragile.
DROP_PREFIX = [u"MATLAB \u2014"]
DROP_DIVIDER = u"Where this goes"


def drop(prs, idx):
    lst = prs.slides._sldIdLst
    ids = list(lst)
    rId = ids[idx].get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
    prs.part.drop_rel(rId)
    lst.remove(ids[idx])


killed = []
while True:
    hit = None
    for i, s in enumerate(p.slides):
        t = title_of(s)
        if t in DROP or any(t.startswith(x) for x in DROP_PREFIX) \
           or (DROP_DIVIDER in all_text(s) and len(all_text(s).split()) < 25):
            hit = (i, t or DROP_DIVIDER)
            break
    if hit is None:
        break
    drop(p, hit[0])
    killed.append(hit[1])

for k in killed:
    print("dropped:", k)


# ------------------------------------------------------------- rewriting ---
def paras_of(shape):
    return shape.text_frame._txBody.findall(q("p"))


def restyle(shape, blocks):
    """blocks: list of list-of-(text, bold). One block -> one paragraph.

    The pPr of the paragraph already in that position is reused, so bullets,
    indent and spacing survive; the rPr of that paragraph's first run gives
    size, colour and typeface. Extra blocks clone the last available style.
    """
    tx = shape.text_frame._txBody
    old = paras_of(shape)
    styles = []
    for op in old:
        pPr = op.find(q("pPr"))
        r = op.find(q("r"))
        rPr = r.find(q("rPr")) if r is not None else None
        styles.append((pPr, rPr))
    if not styles:
        raise RuntimeError("no paragraphs to take style from")
    for op in old:
        tx.remove(op)
    for i, runs in enumerate(blocks):
        pPr, rPr = styles[i] if i < len(styles) else styles[-1]
        np = etree.SubElement(tx, q("p"))
        if pPr is not None:
            np.append(copy.deepcopy(pPr))
        for text, bold in runs:
            nr = etree.SubElement(np, q("r"))
            if rPr is not None:
                nrPr = copy.deepcopy(rPr)
                if bold:
                    nrPr.set("b", "1")
                else:
                    nrPr.attrib.pop("b", None)
                nr.append(nrPr)
            t = etree.SubElement(nr, q("t"))
            t.text = text


def find_by_name(slide, name):
    for sh in slide.shapes:
        if sh.name == name:
            return sh
    raise KeyError("%s not on slide" % name)


def slide_titled(prefix):
    for s in p.slides:
        if title_of(s).startswith(prefix):
            return s
    raise KeyError(prefix)


N = False
Y = True
EM = u"—"
MINUS = u"−"
MU = u"µ"
TIMES = u"×"

EDITS = [
 # ---- the gap -------------------------------------------------------------
 (u"The gap this project fills", "TextBox 5", [
   [(u"Every paper on these drivers reports ONE number: how much better it is than "
     u"a plain driver.", N)],
   [(u"That number hides two separate effects, and they cost very different hardware.", N)],
 ]),
 (u"The gap this project fills", "TextBox 7", [
   [(u"Pick one good setting once, at design time. Costs nothing while running: no "
     u"sensor, no ADC, no lookup table, no controller.", N)],
 ]),
 (u"The gap this project fills", "TextBox 10", [
   [(u"Change the setting as load, voltage and temperature move. This is the part "
     u"that needs the sensing hardware.", N)],
 ]),
 (u"The gap this project fills", "TextBox 12", [
   [(u"THE GAP: ", Y), (u"nobody separates them. No paper says how much of the benefit "
     u"actually needs the re-tuning, because separating the two means running every "
     u"setting at every operating point " + EM + u" and nobody has done that.", N)],
   [(u"WHY IT MATTERS: ", Y), (u"only Effect 2 pays for the sensor, ADC and lookup "
     u"table. If it is small, that hardware is mostly buying something a design-time "
     u"choice already gives you.", N)],
   [(u"WHAT WE DO: ", Y), (u"720 settings " + TIMES + u" 4 operating points, all of "
     u"them, in ngspice " + EM + u" then report the two numbers separately instead of "
     u"adding them together.", N)],
 ]),

 # ---- circuit -------------------------------------------------------------
 (u"The circuit that is simulated", "TextBox 5", [
   [(u"Everything shown is in sim/dpt.cir " + EM + u" the file ngspice runs, and it "
     u"contains the gate clamp. The red C", N),
    (u"GD", N),
    (u" on Q2 is the path the charge takes. GaN has no body diode, so the gate has to "
     u"be held down for the whole dead time.", N)],
 ]),

 # ---- base paper ----------------------------------------------------------
 (u"We implemented the base paper", "TextBox 5", [
   [(u"Citing a base paper is not a comparison, so we built theirs too. ", N),
    (u"models/basedrv.lib", Y),
    (u" is Takayama, Okuda & Hikihara's driver: a multi-bit code that changes DURING "
     u"the switching edge, with no gate clamp and no " + MINUS + u"2 V rail, because "
     u"those two are ours. It runs inside the same sim/dpt.cir, so only the driver "
     u"differs.", N)],
 ]),
 (u"We implemented the base paper", "TextBox 8", [
   [(u"Their changing-in-time code on its own already clears the 1.4 V threshold.", N)],
 ]),
 (u"We implemented the base paper", "TextBox 11", [
   [(u"FALSE TURN-ON. ", Y), (u"A fast fixed code is worse than their timed one " + EM +
     u" their idea is real, and we reproduce it.", N)],
 ]),
 (u"We implemented the base paper", "TextBox 14", [
   [(u"Only just past the base paper. The clamp on its own is not the story.", N)],
 ]),
 (u"We implemented the base paper", "TextBox 17", [
   [(u"4.8" + TIMES + u" the base paper's margin. This is the version we ship.", N)],
 ]),
 (u"We implemented the base paper", "TextBox 18", [
   [(u"What the comparison shows. ", Y),
    (u"The base paper shapes the gate over TIME; we keep the code steady and add two "
     u"things they do not have. Both clear the threshold " + EM + u" theirs works " +
     EM + u" but ours clears it by 4.8" + TIMES + u" more, and ours is the one whose "
     u"settings can then be searched in full.", N)],
   [(u"Command: python3 scripts/basepaper_compare.py " + EM + u" four ngspice runs, "
     u"prints this table.", N)],
 ]),

 # ---- result 1 ------------------------------------------------------------
 (u"Result 1", "TextBox 9", [
   [(u"And safety is nearly free", Y)],
   [(u"The lowest-energy setting is already safe at three of the four operating "
     u"points. At the fourth, safety costs 0.04 % more energy " +
     EM + u" 3.335 " + MU + u"J against 3.334 " + MU + u"J.", N)],
   [(u"The clamp is worth 9.7" + u"–" + u"12.2 % of the blended cost, with no "
     u"sensor and no controller.", N)],
 ]),

 # ---- result 2 ------------------------------------------------------------
 (u"Result 2", "TextBox 6", [
   [(u"All 720 settings run at every operating point " + EM + u" 2,880 runs " + EM +
     u" so the best at each point is the true best, not the best of a short list.", N)],
 ]),
 (u"Result 2", "TextBox 9", [
   [(u"The benefit is not spread out. ", Y),
    (u"Three operating points lose only 1" + u"–" + u"4 % from a fixed setting; "
     u"one loses 12.7 %.", N)],
   [(u"5.2 % is the generous figure " + EM + u" on a finer 36-point grid it is 2.0 %.", N)],
   [(u"It all comes from the dead time, and that from one operating point. Freezing "
     u"the dead time costs 5.45 % across four points. Drop the light-load 50 V / 2 A "
     u"point and it costs 0.00 %: three points want 5 ns, only that one wants 15 ns. "
     u"So the adaptive hardware shrinks to one light-load detector choosing between "
     u"two dead times. Freezing the drive strength costs 0.00 % " + EM + u" and that "
     u"is what these papers actually adjust.", N)],
   [(u"Steady against the device, not the board. ", Y),
    (u"Across 21,600 runs no device parameter moves the answer outside 4.3" +
     u"–" + u"7.7 %. Halving the board inductance takes it to 13.5 %, and that "
     u"is layout, not the transistor [3].", N)],
 ]),

 # ---- result 3 ------------------------------------------------------------
 (u"Result 3", "TextBox 4", [
   [(u"Segmented gate drivers set drive strength by a pattern fixed at design time "
     u"[10]. Papers on active gate drivers report one number " + EM + u" the "
     u"improvement over a conventional driver " + EM + u" and that number adds two "
     u"separate effects together. Only the second needs a sensor, an ADC and a lookup "
     u"table. Separating them means running every setting at every operating point.", N)],
 ]),
 (u"Result 3", "TextBox 5",
  [[(u"(A)   Pick a better FIXED setting", Y)]]),
 (u"Result 3", "TextBox 8",
  [[(u"(B)   CHANGE it per operating point", Y)]]),
 (u"Result 3", "TextBox 11",
  [[(u"(B′)  …but ONE comparator gets 72 % of (B)", Y)]]),
 (u"Result 3", "TextBox 14", [
   [(u"So the full sensor + ADC + lookup table is left justifying 3.7 % of the total "
     u"gain, over a fixed setting plus one comparator. Re-tuning is 13.4 % of the "
     u"gain; a single threshold takes 72 % of that.", N)],
   [(u"Every figure uses the same baseline " + EM + u" the middle setting that is safe "
     u"at all four operating points. The split does not depend on the weighting: "
     u"across 106 weightings, (A) stays 23.4" + u"–" + u"29.0 % and (B) 1.3" +
     u"–" + u"6.4 %, and (A) beats (B) every time. scripts/novelty.py, "
     u"scripts/weight_sensitivity.py.", N)],
 ]),

 # ---- result 4 ------------------------------------------------------------
 (u"Result 4", "TextBox 5", [
   [(u"Eight inductance values, 7,200 runs. The answer is a band, not a single line: "
     u"re-tuning only pays from about 2.5 nH downwards, peaking at 13.5 % at 1.5 nH, "
     u"then falling back to 8.1 % at 1.0 nH because only 165 of the 720 settings are "
     u"still safe there " + EM + u" below about 2 nH the limit is what is safe, not "
     u"what is best. A designer measures their own board and reads the decision off "
     u"this curve.", N)],
 ]),

 # ---- demo ----------------------------------------------------------------
 (u"Demo", "TextBox 5", [
   [(u"Click to play (22 s). ", Y),
    (u"ngspice waveforms from sim/dpt.cir " + EM + u" the same file every number "
     u"in this deck comes from.", N)],
 ]),
 (u"Demo", "TextBox 6", [
   [(u"What it shows", Y)],
   [(u"TOP row: the switch node. ", Y), (u"The low-side device turns on and the "
     u"voltage collapses from 100 V in a few nanoseconds. That fast drop is the "
     u"cause.", N)],
   [(u"BOTTOM row: the gate of the OFF device. ", Y), (u"The fast drop pushes charge "
     u"through C", N), (u"GD", N), (u" and lifts that gate.", N)],
   [(u"LEFT, failing: ", Y), (u"the gate reaches +1.65 V, above the 1.4 V line drawn "
     u"on the plot. The device turns on when it must not.", N)],
   [(u"RIGHT, shipped: ", Y), (u"same circuit, same setting, plus the gate clamp and " +
     MINUS + u"2 V rail. Peak " + MINUS + u"1.18 V, a 2.58 V margin.", N)],
   [(u"Both panels are the same simulation; only the clamp and the off rail differ.", N)],
 ]),

 # ---- conclusion ----------------------------------------------------------
 (u"Conclusion & next steps", "Text 2", [
   [(u"What the data supports", Y)],
   [(u"Picking the setting well: 25.1 %.   Changing it per operating point: 3.9 %.", N)],
   [(u"One comparator gets 72 % of that 3.9 %.", N)],
   [(u"What to build: ", Y), (u"one fixed setting plus a light-load comparator. The "
     u"full sensor + ADC + lookup table is left justifying 3.7 %.", N)],
   [(u"The FPGA half is real: 20 LUTs and 20 flip-flops on an xc7a35t, 200 MHz met "
     u"with 1.996 ns to spare.", N)],
   [(u"What is next", Y)],
   [(u"Review-II " + EM + u" transistor-level output stage in Cadence; re-run the "
     u"answer on real devices.", N)],
   [(u"Review-III " + EM + u" measure a hardware half-bridge. Until then this is a "
     u"simulation study, and is titled as one.", N)],
   [(u"Limits we state ourselves: no silicon measured; one device model underlies "
     u"everything.", N)],
 ]),

 # ---- result 1 wording ----------------------------------------------------
 (u"Result 1", "TextBox 5", [
   [(u"Fig. 1  Voltage on the gate that is supposed to stay OFF: the failure, and the "
     u"fix that removes it.", N)],
 ]),
 (u"Result 1", "TextBox 7", [
   [(u"1.65 V", Y)],
   [(u"peak on the gate that should be OFF", Y)],
   [(u"The threshold is 1.4 V " + EM + u" so it turns on by mistake", N)],
 ]),
 (u"Result 1", "TextBox 8", [
   [(u"2.58 V", Y)],
   [(u"margin with the clamp and the " + MINUS + u"2 V rail", Y)],
   [(u"The fault is removed completely", N)],
 ]),

 # ---- result 2 wording ----------------------------------------------------
 (u"Result 2", "TextBox 5", [
   [(u"Fig. 2  What it costs to use one fixed setting instead of the best setting at "
     u"each operating point.", N)],
 ]),
 (u"Result 2", "TextBox 7", [
   [(u"What re-tuning is actually worth", Y)],
 ]),
 (u"Result 2", "TextBox 8", [
   [(u"5.2 %", Y)],
   [(u"the most that re-tuning can ever gain", Y)],
   [(u"against the best single fixed setting (= 3.9 % of baseline). One fixed setting "
     u"is nearly as good.", N)],
 ]),

]

RETITLE = [
 (u"Result 2 — scheduling", u"Result 2 " + EM + u" re-tuning is worth only 5.2 %"),
 (u"Result 4 — adaptive pays", u"Result 4 " + EM + u" re-tuning only pays below ~2.5 nH"),
]

for prefix, newtitle in RETITLE:
    try:
        s_ = slide_titled(prefix)
    except KeyError:
        print("already retitled:", prefix); continue
    for sh in s_.shapes:
        if sh.has_text_frame and sh.width and abs(sh.width - Inches(10.5)) < Inches(0.3) \
           and sh.text_frame.text.strip():
            restyle(sh, [[(newtitle, False)]])
            print("retitled:", newtitle)
            break

for prefix, name, blocks in EDITS:
    try:
        s = slide_titled(prefix)
    except KeyError:
        # The slide was dropped above. Not an error: the drop list is the
        # authority on what survives, and a stale edit must not take the whole
        # build down with it after the drops have already been applied.
        print("skipped: %-34s (slide not in deck)" % prefix[:34])
        continue
    restyle(find_by_name(s, name), blocks)
    print("rewrote: %-34s %s" % (prefix[:34], name))


# --------------------------------------------------------------- renumber ---
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
