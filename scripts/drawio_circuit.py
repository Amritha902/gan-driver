# -*- coding: utf-8 -*-
"""drawio_circuit.py -- the converter and the driver as an editable
draw.io file.

    python3 scripts/drawio_circuit.py

WHY A .drawio AND NOT ANOTHER IMAGE
  Every other figure in this project is something you can only look at. A
  .drawio you can open at app.diagrams.net, drag a component, change a
  value and export. If somebody asks whether the diagram is yours, opening
  it and editing it in front of them settles the question in about four
  seconds. That is the whole point of this file.

  It uses draw.io's own electrical shape library (mxgraph.electrical.*),
  so the symbols are the standard ones, not drawn rectangles pretending to
  be components.

TWO PAGES
  1. Power stage -- sim/buck.cir: supply, loop parasitics, damped bus
     decoupling, the GaN half-bridge, output filter, load.
  2. Segmented driver -- models/segdrv.lib: the eight pull-up and eight
     pull-down slices, the Miller clamp, the selectable off rail.

  Values are read from the netlist and the model file at build time, the
  same as the KiCad sheets, so all three representations agree by
  construction rather than by somebody remembering to update them.

NOTE ON VERIFICATION
  There is no draw.io CLI in this environment, so this file is generated
  and its XML is validated, but it has not been rendered here. Open it to
  check the layout.
"""
import os, re
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "kicad", "gan_driver.drawio")

# ---------------------------------------------------------------- inputs --
def params(path):
    p = {}
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^\.param\s+(\w+)\s*=\s*([^\s$]+)", line, re.I)
        if m:
            p[m.group(1).upper()] = m.group(2)
    return p


P = params(os.path.join(ROOT, "sim", "buck.cir"))
SEG = open(os.path.join(ROOT, "models", "segdrv.lib"), encoding="utf-8").read()
NPU = max(int(n) for n in re.findall(r"^Rpu(\d+)", SEG, re.M | re.I))
NPD = max(int(n) for n in re.findall(r"^Rpd(\d+)", SEG, re.M | re.I))
RUNIT = (re.search(r"runit=(\S+)", SEG) or [None, "8"])[1]
RCLAMP = (re.search(r"rclamp=(\S+)", SEG) or [None, "0.5"])[1]


def V(k, d):
    return P.get(k, d)


# ---------------------------------------------------------------- emitter --
class Page(object):
    def __init__(self, name):
        self.name, self.cells, self.n = name, [], 0

    def _id(self):
        self.n += 1
        return "%s-%d" % (self.name[:3].lower(), self.n)

    def node(self, style, label, x, y, w, h):
        i = self._id()
        self.cells.append(
            '        <mxCell id="%s" value="%s" style="%s" vertex="1" parent="1">\n'
            '          <mxGeometry x="%s" y="%s" width="%s" height="%s" as="geometry"/>\n'
            '        </mxCell>' % (i, escape(label), style, x, y, w, h))
        return i

    def edge(self, x1, y1, x2, y2, style="edgeStyle=orthogonalEdgeStyle;"
                                        "rounded=0;html=1;endArrow=none;"
                                        "strokeWidth=2;strokeColor=#1F6F3F;"):
        i = self._id()
        self.cells.append(
            '        <mxCell id="%s" style="%s" edge="1" parent="1">\n'
            '          <mxGeometry relative="1" as="geometry">\n'
            '            <mxPoint x="%s" y="%s" as="sourcePoint"/>\n'
            '            <mxPoint x="%s" y="%s" as="targetPoint"/>\n'
            '          </mxGeometry>\n'
            '        </mxCell>' % (i, style, x1, y1, x2, y2))
        return i

    def text(self, label, x, y, w=560, h=22, size=12, bold=False):
        st = ("text;html=1;align=left;verticalAlign=top;fontSize=%d;"
              "fontColor=#1A1A1A;%s" % (size, "fontStyle=1;" if bold else ""))
        return self.node(st, label, x, y, w, h)

    def xml(self):
        return ('    <diagram name="%s" id="%s">\n'
                '      <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" '
                'guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" '
                'pageScale="1" pageWidth="1600" pageHeight="1200" math="0" shadow="0">\n'
                '        <root>\n'
                '          <mxCell id="%s-0"/>\n'
                '          <mxCell id="%s-1" parent="%s-0"/>\n'
                % (escape(self.name), self.name[:3].lower(),
                   self.name[:3].lower(), self.name[:3].lower(),
                   self.name[:3].lower())
                + "\n".join(c.replace('parent="1"',
                                      'parent="%s-1"' % self.name[:3].lower())
                            for c in self.cells)
                + '\n        </root>\n      </mxGraphModel>\n    </diagram>')


# draw.io's own electrical shapes, so these are standard symbols
R_V = ("shape=mxgraph.electrical.resistors.resistor_2;html=1;direction=north;"
       "strokeWidth=2;strokeColor=#8B0000;fillColor=none;verticalLabelPosition=middle;"
       "verticalAlign=middle;labelPosition=right;align=left;spacingLeft=6;fontSize=11;")
R_H = R_V.replace("direction=north;", "")
L_H = ("shape=mxgraph.electrical.inductors.inductor_3;html=1;strokeWidth=2;"
       "strokeColor=#8B0000;fillColor=none;verticalLabelPosition=top;"
       "verticalAlign=bottom;align=center;fontSize=11;")
L_V = L_H + "direction=north;"
C_V = ("shape=mxgraph.electrical.capacitors.capacitor_1;html=1;direction=north;"
       "strokeWidth=2;strokeColor=#8B0000;fillColor=none;labelPosition=right;"
       "align=left;spacingLeft=6;verticalAlign=middle;fontSize=11;")
FET = ("shape=mxgraph.electrical.transistors.mosfet_2;html=1;strokeWidth=2;"
       "strokeColor=#8B0000;fillColor=none;direction=north;labelPosition=right;"
       "align=left;spacingLeft=10;verticalAlign=middle;fontSize=11;")
GND = ("shape=mxgraph.electrical.signal_sources.signal_ground;html=1;"
       "strokeWidth=2;strokeColor=#8B0000;fillColor=none;fontSize=10;")
SW_V = ("shape=mxgraph.electrical.electro-mechanical.switch_normally_open;"
        "html=1;direction=north;strokeWidth=2;strokeColor=#8B0000;fillColor=none;"
        "labelPosition=right;align=left;spacingLeft=6;verticalAlign=middle;fontSize=10;")

# ============================ page 1: power stage ========================
p1 = Page("Power stage")
p1.text("GaN synchronous buck converter - sim/buck.cir", 60, 30, 900, 30, 20, True)
p1.text("%s V in, %s V out, %s. Values read from the netlist; edit them here and "
        "they are yours to change." % (V("VIN", "100"),
                                       float(V("VIN", "100")) * float(V("D", "0.5")),
                                       V("FSW", "500k") + "Hz"),
        60, 60, 1000, 24, 12)

BUS, SWX, GNDY = 150, 700, 560
p1.text("VIN", 66, BUS - 26, 60, 20, 13, True)
p1.edge(100, BUS, 220, BUS)
p1.node(R_H, "Rloop  %s Ω" % V("RLOOP", "0.3"), 220, BUS - 12, 70, 24)
p1.edge(290, BUS, 360, BUS)
p1.node(L_H, "Lloop  %sH" % V("LLOOP", "3n"), 360, BUS - 14, 70, 28)
p1.edge(430, BUS, SWX, BUS)
p1.text("hstop", 440, BUS - 26, 80, 20, 11)

# damped decoupling
DX = 500
p1.edge(DX, BUS, DX, 210)
p1.node(L_V, "Ldec  %sH" % V("LDEC", "0.5n"), DX - 14, 210, 28, 70)
p1.edge(DX, 280, DX, 320)
p1.node(C_V, "Cdec  %sF" % V("CDEC", "100n"), DX - 20, 320, 40, 50)
p1.edge(DX, 370, DX, 410)
p1.node(R_V, "Rdec  %s Ω  (damping, not parasitic)" % V("RDEC", "1"),
        DX - 12, 410, 24, 70)
p1.edge(DX, 480, DX, GNDY)
p1.node(GND, "", DX - 20, GNDY, 40, 30)

# half-bridge
p1.edge(SWX, BUS, SWX, 250)
p1.node(FET, "Qhs   eGaN HEMT", SWX - 30, 250, 60, 70)
p1.text("HSG", SWX - 130, 275, 60, 20, 12, True)
p1.edge(SWX - 80, 285, SWX - 30, 285)
p1.edge(SWX, 320, SWX, 400)
p1.text("SW", SWX + 16, 372, 60, 20, 13, True)
p1.node(FET, "Qls   eGaN HEMT", SWX - 30, 400, 60, 70)
p1.text("LSG", SWX - 130, 425, 60, 20, 12, True)
p1.edge(SWX - 80, 435, SWX - 30, 435)
p1.edge(SWX, 470, SWX, GNDY)
p1.node(GND, "", SWX - 20, GNDY, 40, 30)

# output filter and load
p1.edge(SWX, 390, 900, 390)
p1.node(L_H, "Lo  %sH" % V("LOUT", "22u"), 900, 376, 80, 28)
p1.edge(980, 390, 1120, 390)
p1.text("OUT", 1010, 362, 60, 20, 13, True)
p1.edge(1120, 390, 1120, 430)
p1.node(R_V, "Resr  0.3 Ω", 1108, 430, 24, 60)
p1.edge(1120, 490, 1120, 520)
p1.node(C_V, "Co  %sF" % V("COUT", "4.7u"), 1100, 520, 40, 40)
p1.edge(1120, GNDY, 1120, GNDY + 10)
p1.node(GND, "", 1100, GNDY + 10, 40, 30)
p1.edge(1120, 390, 1300, 390)
p1.edge(1300, 390, 1300, 440)
p1.node(R_V, "Rload  %s Ω" % V("RLOAD", "10"), 1288, 440, 24, 70)
p1.edge(1300, 510, 1300, GNDY + 10)
p1.node(GND, "", 1280, GNDY + 10, 40, 30)

p1.text("Qhs / Qls are enhancement-mode GaN HEMTs - NO BODY DIODE, so reverse "
        "conduction during dead time costs Vth + |Voff| + I*Rds(on), not one diode drop.",
        60, 640, 1300, 24, 12)
p1.text("Rdec is a damping value. At 20 mOhm this branch rings near 22 MHz and drove "
        "the low-side gate to +11.8 V against a 1.4 V threshold at a 200 V bus.",
        60, 668, 1300, 24, 12)
p1.text("Not drawn: Vsin, Vshs, Vsls, Vsout are 0 V sources in the netlist used only "
        "to sense current. They are measurement points, not components.",
        60, 696, 1300, 24, 12)

# ============================ page 2: the driver =========================
p2 = Page("Segmented driver")
p2.text("Segmented gate driver - models/segdrv.lib", 60, 30, 900, 30, 20, True)
p2.text("%d pull-up slices, %d pull-down, active Miller clamp, selectable off rail."
        % (NPU, NPD), 60, 60, 1000, 24, 12)

VPY, OUTY, VNY, X0, DXS = 150, 420, 690, 140, 130
p2.text("VP  (+%s V)" % V("VDRV", "5"), 50, VPY - 28, 120, 20, 13, True)
p2.text("OUT  (to HEMT gate)", 50, OUTY - 28, 200, 20, 13, True)
p2.text("VN  (0 V or -2 V)", 50, VNY + 8, 160, 20, 13, True)
p2.edge(X0 - 40, VPY, X0 + DXS * (NPU - 1) + 200, VPY)
p2.edge(X0 - 40, OUTY, X0 + DXS * (NPU - 1) + 200, OUTY)
p2.edge(X0 - 40, VNY, X0 + DXS * (NPU - 1) + 200, VNY)

for i in range(1, NPU + 1):
    x = X0 + DXS * (i - 1)
    p2.edge(x, VPY, x, VPY + 40)
    p2.node(SW_V, "Spu%d" % i, x - 15, VPY + 40, 30, 60)
    p2.edge(x, VPY + 100, x, VPY + 140)
    p2.node(R_V, "Rpu%d  %s Ω" % (i, RUNIT), x - 12, VPY + 140, 24, 70)
    p2.edge(x, VPY + 210, x, OUTY)

for i in range(1, NPD + 1):
    x = X0 + DXS * (i - 1)
    p2.edge(x, OUTY, x, OUTY + 40)
    p2.node(R_V, "Rpd%d  %s Ω" % (i, RUNIT), x - 12, OUTY + 40, 24, 70)
    p2.edge(x, OUTY + 110, x, OUTY + 150)
    p2.node(SW_V, "Spd%d" % i, x - 15, OUTY + 150, 30, 60)
    p2.edge(x, OUTY + 210, x, VNY)

CXS = X0 + DXS * (NPU - 1) + 150
p2.text("ACTIVE MILLER CLAMP - ours; the base paper has none", CXS - 30, OUTY - 60, 420, 20, 12, True)
p2.edge(CXS, OUTY, CXS, OUTY + 40)
p2.node(SW_V, "Sclk", CXS - 15, OUTY + 40, 30, 60)
p2.edge(CXS, OUTY + 100, CXS, OUTY + 140)
p2.node(R_V, "Rclk  %s Ω" % RCLAMP, CXS - 12, OUTY + 140, 24, 70)
p2.edge(CXS, OUTY + 210, CXS, VNY)

p2.text("Each slice is a switch and a resistor, and the resistor carries the code. "
        "In the netlist: Rpu3 nu3 out {runit + (npu&gt;=3 ? 0 : 1e9)}.",
        60, VNY + 60, 1400, 24, 12)
p2.text("Ask for three or more slices and Rpu3 is %s ohm, in circuit; ask for fewer and "
        "it becomes 1 Gohm - that slice switched out. Drive strength is how many of the "
        "%d parallel paths are live." % (RUNIT, NPU), 60, VNY + 88, 1400, 24, 12)
p2.text("The clamp is worth +0.82 V of crosstalk margin and the -2 V rail a further "
        "+2.01 V. The %d slices - the part everyone builds - cost 0.00 %% to freeze."
        % NPU, 60, VNY + 116, 1400, 24, 12)

doc = ('<mxfile host="app.diagrams.net" agent="gan-driver project" version="21.0.0">\n'
       + p1.xml() + "\n" + p2.xml() + "\n</mxfile>\n")

if not os.path.isdir(os.path.dirname(OUT)):
    os.makedirs(os.path.dirname(OUT))
open(OUT, "w", encoding="utf-8").write(doc)

import xml.etree.ElementTree as ET
ET.fromstring(doc)
print("  written: kicad/gan_driver.drawio  (XML valid, 2 pages)")
print("  page 1: power stage, %d cells" % p1.n)
print("  page 2: segmented driver, %d cells" % p2.n)
