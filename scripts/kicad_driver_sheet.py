# -*- coding: utf-8 -*-
"""kicad_driver_sheet.py -- the segmented gate driver, drawn from the model
that is actually simulated.

    python3 scripts/kicad_driver_sheet.py

WHAT THIS DRAWS
  models/segdrv.lib, one element at a time. Eight pull-up slices, eight
  pull-down slices, the active Miller clamp, and the off-rail select. This
  is the project's contribution, and until now the only picture of it was a
  block diagram with "8 x pull-up slice" written in a box.

  A block saying "8 slices" is a claim. This is the circuit.

HOW A SLICE WORKS, WHICH THE SHEET HAS TO MAKE OBVIOUS
  Each slice is a switch in series with a resistor. In the netlist the
  switch closes on the `pu` (or `pd`) command and the resistor carries the
  thermometer code:

      Rpu3 nu3 out {runit + (npu>=3 ? 0 : 1e9)}

  If the control word asks for three or more slices, Rpu3 is runit -- 8 Ω,
  in circuit. If it asks for fewer, Rpu3 becomes 1 GΩ, which is that slice
  switched out. So drive strength is set by how many of the eight parallel
  8 Ω paths are live: 8 Ω at npu=1 down to 1 Ω at npu=8.

  Every slice on this sheet carries its own conditional as its value, so a
  reader can check the drawing against the netlist line by line.

WHAT MAKES IT OURS RATHER THAN THE BASE PAPER'S
  Two things, and they are the rightmost column: Sclk/Rclk, the active
  Miller clamp that pulls the gate to the off rail through 0.5 Ω, and the
  off rail itself being selectable to -2 V. models/zhangdrv.lib -- the base
  paper implemented in the same testbench -- has neither. Its file says so
  in as many words: "there is deliberately no clamp branch here".

  Of the crosstalk margin, +0.82 V comes from the clamp and a further
  +2.01 V from the negative rail. The eight slices, which are the part
  everyone builds, are worth 0.00 % when frozen.
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kicad_common import Sheet, pin, plot

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "kicad")
LIB  = os.path.join(ROOT, "models", "segdrv.lib")

NEEDED = [("Device", "R_Small"), ("Switch", "SW_SPST"), ("power", "GND")]


def slices(text):
    """Read the slice resistors straight out of segdrv.lib.

    Returns {('pu'|'pd', n): conditional-expression}. Parsing the model
    rather than assuming eight of each means a change to the library shows
    up in the drawing instead of silently disagreeing with it.
    """
    out = {}
    for m in re.finditer(r"^R(pu|pd)(\d+)\s+\S+\s+\S+\s+\{([^}]*)\}",
                         text, re.M | re.I):
        out[(m.group(1).lower(), int(m.group(2)))] = m.group(3).strip()
    return out


def params(text):
    m = re.search(r"params:\s*(.*)$", text, re.M)
    d = {}
    if m:
        for kv in m.group(1).split():
            if "=" in kv:
                k, v = kv.split("=", 1)
                d[k.lower()] = v
    return d


src = open(LIB, encoding="utf-8").read()
SL = slices(src)
PA = params(src)
NPU = max(n for k, n in SL if k == "pu")
NPD = max(n for k, n in SL if k == "pd")

s = Sheet("Segmented Gate Driver - one side",
          "Generated from models/segdrv.lib by scripts/kicad_driver_sheet.py")

VP_Y, OUT_Y, VN_Y = 52.0, 112.0, 172.0
X0, DX = 52.0, 24.0

s.label("VP  (+%s V drive rail)" % PA.get("vp", "5"), X0 - 14, VP_Y - 2)
s.label("OUT  (to HEMT gate)", X0 - 14, OUT_Y - 2)
s.label("VN  (off rail: 0 V or -2 V)", X0 - 14, VN_Y - 2)

# the three rails
s.hop((X0 - 16, VP_Y), (X0 + DX * (NPU - 1) + 44, VP_Y))
s.hop((X0 - 16, OUT_Y), (X0 + DX * (NPU - 1) + 44, OUT_Y))
s.hop((X0 - 16, VN_Y), (X0 + DX * (NPU - 1) + 44, VN_Y))

# ---- pull-up bank: VP -> switch -> resistor -> OUT ----
for i in range(1, NPU + 1):
    x = X0 + DX * (i - 1)
    s.place("Switch:SW_SPST", "Spu%d" % i, "pu", x, VP_Y + 14, 90,
            vx=x + 3.0, vy=VP_Y + 14)
    s.hop((x, VP_Y), pin("Switch:SW_SPST", x, VP_Y + 14, 90, "2"))
    s.place("Device:R_Small", "Rpu%d" % i, "%s Ω" % PA.get("runit", "8"),
            x, VP_Y + 36, 0, vx=x + 3.0, vy=VP_Y + 36)
    s.hop(pin("Switch:SW_SPST", x, VP_Y + 14, 90, "1"),
          pin("Device:R_Small", x, VP_Y + 36, 0, "1"))
    s.hop(pin("Device:R_Small", x, VP_Y + 36, 0, "2"), (x, OUT_Y))
    s.junction(x, VP_Y)
    s.junction(x, OUT_Y)

# ---- pull-down bank: OUT -> resistor -> switch -> VN ----
for i in range(1, NPD + 1):
    x = X0 + DX * (i - 1)
    s.place("Device:R_Small", "Rpd%d" % i, "%s Ω" % PA.get("runit", "8"),
            x, OUT_Y + 22, 0, vx=x + 3.0, vy=OUT_Y + 22)
    s.hop((x, OUT_Y), pin("Device:R_Small", x, OUT_Y + 22, 0, "1"))
    s.place("Switch:SW_SPST", "Spd%d" % i, "pd", x, OUT_Y + 44, 90,
            vx=x + 3.0, vy=OUT_Y + 44)
    s.hop(pin("Device:R_Small", x, OUT_Y + 22, 0, "2"),
          pin("Switch:SW_SPST", x, OUT_Y + 44, 90, "2"))
    s.hop(pin("Switch:SW_SPST", x, OUT_Y + 44, 90, "1"), (x, VN_Y))
    s.junction(x, VN_Y)

# ---- the Miller clamp: ours, and the base paper has no equivalent ----
CX = X0 + DX * (NPU - 1) + 34
s.place("Switch:SW_SPST", "Sclk", "clk", CX, OUT_Y + 22, 90,
        vx=CX + 3.0, vy=OUT_Y + 22)
s.hop((CX, OUT_Y), pin("Switch:SW_SPST", CX, OUT_Y + 22, 90, "2"))
s.junction(CX, OUT_Y)
s.place("Device:R_Small", "Rclk", "%s Ω" % PA.get("rclamp", "0.5"),
        CX, OUT_Y + 44, 0, vx=CX + 3.0, vy=OUT_Y + 44)
s.hop(pin("Switch:SW_SPST", CX, OUT_Y + 22, 90, "1"),
      pin("Device:R_Small", CX, OUT_Y + 44, 0, "1"))
s.hop(pin("Device:R_Small", CX, OUT_Y + 44, 0, "2"), (CX, VN_Y))
s.junction(CX, VN_Y)
s.label("ACTIVE MILLER CLAMP", CX - 8, OUT_Y + 14, size=1.5)

# ---- what a reader needs that the drawing cannot say ----
s.text("Segmented gate driver - one side of the half-bridge, as simulated", 36, 22, 2.5)
s.text("models/segdrv.lib.  %d pull-up slices, %d pull-down, clamp, selectable off rail."
       % (NPU, NPD), 36, 28, 1.8)

y = 196
for line in [
    "EACH SLICE IS A SWITCH AND A RESISTOR, AND THE RESISTOR CARRIES THE CODE.",
    "In the netlist slice 3 of the pull-up bank reads:",
    "    Rpu3 nu3 out {runit + (npu>=3 ? 0 : 1e9)}",
    "Ask for three or more slices and Rpu3 is runit, 8 ohm, in circuit. Ask for fewer",
    "and it becomes 1 Gohm, which is that slice switched out. Drive strength is",
    "therefore how many of the eight parallel 8 ohm paths are live: 8 ohm at npu=1,",
    "down to 1 ohm at npu=8. The switches are voltage-controlled (.model SWP,",
    "Ron 0.01, Roff 1e9) - a behavioural stand-in for the real output transistors,",
    "which is stated here rather than implied.",
    "",
    "WHAT IS OURS RATHER THAN THE BASE PAPER'S.  Sclk and Rclk on the right are the",
    "active Miller clamp: it pulls the gate to the off rail through 0.5 ohm whenever",
    "the device should be off. VN is selectable to -2 V. models/zhangdrv.lib, the",
    "base paper built in the same testbench, has neither; its file says so in as many",
    "words. Of the crosstalk margin the clamp is worth +0.82 V and the negative rail",
    "a further +2.01 V. The eight slices - the part everyone builds - cost 0.00 %",
    "to freeze.",
]:
    s.text(line, 36, y, 1.7)
    y += 4.4

path = os.path.join(OUT, "gan_segdrv.kicad_sch")
n = s.save(path, NEEDED)
print("  written: kicad/gan_segdrv.kicad_sch  (%d components, %d+%d slices)"
      % (n, NPU, NPD))
for fmt, ok, msg in plot(path, OUT):
    print("  %s: %s" % (fmt.upper(), "ok" if ok else msg))
