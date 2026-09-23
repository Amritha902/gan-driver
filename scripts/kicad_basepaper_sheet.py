# -*- coding: utf-8 -*-
"""kicad_basepaper_sheet.py -- the BASE PAPER's driver, drawn as a schematic
from our reimplementation of it.

    python3 scripts/kicad_basepaper_sheet.py

THE POINT OF DRAWING THEIRS AT ALL
  A comparison is only worth something if both sides are built. This is
  their circuit, on its own sheet, in the same drawing language as ours --
  so the two sheets can be laid next to each other and the difference is a
  difference in the drawing, not in how it was drawn.

  Reimplement, then improve, then compare. Their sheet is the "before".

WHAT THEIR DRIVER IS
  Zhang, Yu, Leng, Cui, Deng and Ng, ISPSD 2020, pp. 102-105. A segmented
  output stage on E-mode GaN with SEVEN slices per bank, engaged in TWO
  STAGES across the switching edge. The split between stages -- nseg now,
  7-nseg after the pattern step -- is set by ONE external bias resistor,
  chosen at design time. "Simple driving strength pattern control" is the
  paper's title and that single knob is its contribution.

HOW THAT LOOKS ON THE SHEET
  Fourteen columns per bank, not seven, because the two stages are separate
  branches in the netlist:

    first stage    Spu_i  then  Rpu_i  {runit + (i<=nseg ? 0 : 1e9)}
    second stage   Spu_ib then Sgu_ib then Rpu_ib {runit + (i>nseg ? 0 : 1e9)}

  The second-stage branches carry an EXTRA switch in series, gated by the
  pattern step rather than by the drive command. That extra switch is the
  paper's mechanism and it is why their sheet is wider than ours.

  Each resistor carries its own conditional as its value, so the drawing
  can be checked against models/zhangdrv.lib line by line.

WHAT IS NOT ON THIS SHEET, AND THAT IS THE COMPARISON
  No clamp branch. No negative off rail -- vn is tied to the local
  reference by the testbench. models/zhangdrv.lib says so in its own
  comments: "there is deliberately no clamp branch here".

  Put this sheet beside kicad/gan_segdrv.kicad_sch and the two additions
  are the whole of the difference.

WHAT IS INFERRED
  The ISPSD paper is four pages and does not give slice sizing. That the
  slices are equal-sized and that the stage splits nseg / (7-nseg) is our
  reading, stated here and in the model file rather than hidden. Neither
  assumption favours our result: equal slices and a two-stage split are the
  most generous simple reading of "pattern control".
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicad_common import Sheet, pin, plot

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "kicad")
LIB  = os.path.join(ROOT, "models", "zhangdrv.lib")
NEEDED = [("Device", "R_Small"), ("Switch", "SW_SPST"), ("power", "GND")]

src = open(LIB, encoding="utf-8").read()

# first-stage and second-stage slice resistors, with their conditionals
first = {}
second = {}
for m in re.finditer(r"^R(pu|pd)(\d+)(b?)\s+\S+\s+\S+\s+\{([^}]*)\}", src, re.M | re.I):
    bank, n, b, expr = m.group(1).lower(), int(m.group(2)), m.group(3), m.group(4)
    (second if b else first)[(bank, n)] = expr.strip()

N = max(n for _b, n in first)
par = dict(kv.split("=", 1) for kv in
           re.search(r"params:\s*(.*)$", src, re.M).group(1).split() if "=" in kv)
NSEG, RUNIT = par.get("nseg", "2"), par.get("runit", "8")
HAS_CLAMP = bool(re.search(r"^Sclk\b", src, re.M | re.I))

s = Sheet("BASE PAPER driver - Zhang et al., ISPSD 2020 (our reimplementation)",
          "Generated from models/zhangdrv.lib by scripts/kicad_basepaper_sheet.py",
          paper="A2")

VPY, OUTY, VNY = 60.0, 200.0, 340.0
X0, DX = 50.0, 34.0
RIGHT = X0 + DX * (2 * N - 1) + 20

s.label("VP  (drive rail)", X0 - 34, VPY - 3)
s.label("OUT  (to HEMT gate)", X0 - 34, OUTY - 3)
s.label("VN  (tied to ref — NO negative rail)", X0 - 34, VNY - 3)
for yy in (VPY, OUTY, VNY):
    s.hop((X0 - 36, yy), (RIGHT, yy))


def column(i, stage2, bank, x):
    """One slice branch. Second-stage branches get the extra `seg` switch."""
    expr = (second if stage2 else first)[(bank, i)]
    tag = "%s%d%s" % (bank, i, "b" if stage2 else "")
    up = (bank == "pu")
    y0, y1 = (VPY, OUTY) if up else (OUTY, VNY)

    ys = y0 + 26
    s.hop((x, y0), pin("Switch:SW_SPST", x, ys, 90, "2"))
    s.place("Switch:SW_SPST", "S%s" % tag, bank, x, ys, 90, vx=x + 3.2, vy=ys)
    prev = pin("Switch:SW_SPST", x, ys, 90, "1")

    if stage2:
        yg = y0 + 60
        s.hop(prev, pin("Switch:SW_SPST", x, yg, 90, "2"))
        s.place("Switch:SW_SPST", "Sg%s" % tag, "seg", x, yg, 90, vx=x + 3.2, vy=yg)
        prev = pin("Switch:SW_SPST", x, yg, 90, "1")

    yr = y1 - 30
    s.hop(prev, pin("Device:R_Small", x, yr, 0, "1"))
    # One line, no embedded newline: a literal newline inside an
    # s-expression string makes the file unparseable, and kicad-cli's only
    # complaint is "Failed to load schematic file".
    s.place("Device:R_Small", "R%s" % tag,
            "%s Ω if %s" % (RUNIT, "i>%s" % NSEG if stage2 else "i<=%s" % NSEG),
            x, yr, 0, vx=x + 3.2, vy=yr)
    s.hop(pin("Device:R_Small", x, yr, 0, "2"), (x, y1))
    s.junction(x, y0)
    s.junction(x, y1)


for i in range(1, N + 1):
    column(i, False, "pu", X0 + DX * (i - 1))
    column(i, True,  "pu", X0 + DX * (N + i - 1))
    column(i, False, "pd", X0 + DX * (i - 1))
    column(i, True,  "pd", X0 + DX * (N + i - 1))

s.text("BASE PAPER — segmented gate driver, our reimplementation", 44, 20, 3.2)
s.text("Zhang, Yu, Leng, Cui, Deng, Ng.  ISPSD 2020, pp. 102-105.  "
       "%d slices per bank, engaged in TWO stages." % N, 44, 27, 2.1)
s.text("STAGE 1  —  engaged immediately", X0 + DX * (N / 2.0) - 40, VPY - 16, 2.4)
s.text("STAGE 2  —  joins at the pattern step", X0 + DX * (N + N / 2.0) - 44,
       VPY - 16, 2.4)

y = VNY + 24
for line in [
    "HOW THEIR CONTROL WORKS, AND WHY THIS SHEET IS WIDER THAN OURS.",
    "The two stages are separate branches in the netlist, so %d slices per bank means %d"
    % (N, 2 * N),
    "columns. A stage-2 branch carries an EXTRA switch in series, gated by the pattern",
    "step (seg) rather than by the drive command. That extra switch is the paper's",
    "mechanism: nseg slices engage at the edge and the remaining %d join TSTEP later."
    % (N - int(NSEG)),
    "",
    "The split, and therefore the whole pattern, is set by ONE external bias resistor",
    "chosen at design time. That single knob is the paper's contribution and is what",
    "'Simple Driving Strength Pattern Control' in its title refers to.",
    "",
    "WHAT IS ABSENT HERE, WHICH IS THE COMPARISON.  There is no clamp branch and no",
    "negative off rail: VN is tied to the local reference. Put this sheet beside",
    "kicad/gan_segdrv.kicad_sch and those two additions are the whole difference.",
    "",
    "INFERRED, NOT STATED BY THE PAPER.  The ISPSD paper is four pages and gives no",
    "slice sizing. Equal-sized slices and an nseg/(%d-nseg) split are our reading."
    % N,
    "Both are the most generous simple reading of 'pattern control', so neither",
    "assumption favours our result.",
]:
    s.text(line, 44, y, 2.1)
    y += 5.6

path = os.path.join(OUT, "gan_zhangdrv.kicad_sch")
n = s.save(path, NEEDED)
print("  written: kicad/gan_zhangdrv.kicad_sch  (%d components)" % n)
print("  %d slices per bank, 2 stages, nseg=%s, clamp present: %s"
      % (N, NSEG, HAS_CLAMP))
for fmt, ok, msg in plot(path, OUT):
    print("  %s: %s" % (fmt.upper(), "ok" if ok else msg))
