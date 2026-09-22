# -*- coding: utf-8 -*-
"""kicad_schematic.py -- draw the simulated converter as a real KiCad
schematic, generated from the netlist rather than drawn by hand.

    python3 scripts/kicad_schematic.py

WHY GENERATE IT INSTEAD OF DRAWING IT
  A schematic drawn once in a GUI is a picture of what the circuit was on
  the day someone drew it. Component values in this project have moved --
  RDEC went from 20 mOhm to 1 ohm after the 200 V shoot-through, and a
  hand-drawn sheet would still be showing 20 mOhm. This reads the values
  out of sim/buck.cir at build time, so the schematic and the thing that
  was actually simulated cannot disagree.

WHAT IT PRODUCES
  kicad/gan_buck.kicad_sch   a genuine KiCad 7 schematic, openable in
                             eeschema, editable, not an image
  kicad/gan_buck.svg / .pdf  plotted headless with kicad-cli

HOW THE FILE IS BUILT
  A .kicad_sch is an s-expression. Symbols must be embedded in the file's
  own `lib_symbols` block -- a schematic does not reference the system
  libraries at plot time -- so each symbol's definition is lifted verbatim
  out of /usr/share/kicad/symbols/*.kicad_sym and renamed from "R" to
  "Device:R" as the schematic form requires.

COORDINATES, WHICH ARE THE FIDDLY PART
  Symbol libraries use Y-up; schematics use Y-down. A symbol placed at
  (x0, y0) with rotation 0 puts its local pin (px, py) at (x0+px, y0-py).
  For a rotation of 90 degrees the local point becomes (-py, px) first, so
  a resistor at rotation 90 has its pins at (x0-3.81, y0) and (x0+3.81, y0)
  -- horizontal. Every wire endpoint below is computed from that rule
  rather than eyeballed, which is why the wires land on pins instead of
  near them.

THE DEVICE SYMBOL
  KiCad 7 ships no GaN HEMT symbol. Q_NMOS_DGS is used and labelled as the
  eGaN HEMT, which is what EPC's own application schematics do -- an
  enhancement-mode n-channel device with no body diode. The absence of the
  body diode is the physically important part and it is called out on the
  sheet, because a reader who assumes a silicon MOSFET symbol means a
  silicon MOSFET will mis-read the dead-time behaviour.

WHAT IS DELIBERATELY NOT DRAWN
  sim/buck.cir carries three 0 V sources (Vsin, Vshs, Vsls, Vsout) that
  exist only so ngspice can measure current through them. They are not
  circuit elements and drawing them as components would imply hardware
  that does not exist. A note on the sheet says where they are instead.
"""
import os, re, subprocess, uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM  = os.path.join(ROOT, "sim")
OUT  = os.path.join(ROOT, "kicad")
SYMDIR = "/usr/share/kicad/symbols"


# --------------------------------------------------------------- netlist --
def netlist_params(path):
    """Read .param NAME=VALUE out of a SPICE deck. Tolerates the padding
    buck.cir uses ('.param NCYC  = 150'), which a tighter pattern missed
    once already and cost a 50x longer simulation."""
    p = {}
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^\.param\s+(\w+)\s*=\s*([^\s$]+)", line, re.I)
        if m:
            p[m.group(1).upper()] = m.group(2)
    return p


P = netlist_params(os.path.join(SIM, "buck.cir"))


def val(key, default, unit=""):
    v = P.get(key, default)
    v = v.replace("meg", "M")
    return v + unit


# ---------------------------------------------------------- symbol lift --
def lift(lib, name):
    s = open(os.path.join(SYMDIR, lib + ".kicad_sym"), encoding="utf-8").read()
    key = '(symbol "%s"' % name
    i = s.find(key)
    if i < 0:
        raise SystemExit("symbol %s:%s not found" % (lib, name))
    d = 0
    for j in range(i, len(s)):
        if s[j] == "(":
            d += 1
        elif s[j] == ")":
            d -= 1
            if d == 0:
                body = s[i:j + 1]
                return body.replace(key, '(symbol "%s:%s"' % (lib, name), 1)
    raise SystemExit("unterminated symbol %s:%s" % (lib, name))


NEEDED = [("Device", "R"), ("Device", "L"), ("Device", "C"),
          ("Device", "Q_NMOS_DGS"), ("power", "GND")]

# pin offsets, symbol-local (Y up), from the library definitions
PINS = {
    "Device:R": {"1": (0, 3.81), "2": (0, -3.81)},
    "Device:L": {"1": (0, 3.81), "2": (0, -3.81)},
    "Device:C": {"1": (0, 3.81), "2": (0, -3.81)},
    "Device:Q_NMOS_DGS": {"D": (2.54, 5.08), "G": (-5.08, 0), "S": (2.54, -5.08)},
    "power:GND": {"1": (0, 0)},
}


def pin(lib_id, x0, y0, rot, which):
    """Schematic position of one pin. See the coordinate note above."""
    px, py = PINS[lib_id][which]
    if rot == 90:
        px, py = -py, px
    elif rot == 180:
        px, py = -px, -py
    elif rot == 270:
        px, py = py, -px
    return (round(x0 + px, 3), round(y0 - py, 3))


# ------------------------------------------------------------- emitters --
U = lambda: str(uuid.uuid4())
parts, wires, texts, labels = [], [], [], []


def place(lib_id, ref, value, x, y, rot=0, vx=None, vy=None):
    # A property's angle in KiCad 7 is RELATIVE to its symbol's rotation, so
    # a property written at angle 0 on a symbol rotated 90 degrees renders at
    # 90 degrees -- which is how "Rloop" and "3nH" ended up running vertically
    # through their own symbols. Compensating brings them back to horizontal.
    tang = (360 - rot) % 360
    if vx is None and rot in (90, 270):
        vx, vy = x - 5.0, y - 5.4
    """Reference above, value below, ALWAYS horizontal.

    A component at rotation 90 inherits that rotation for its text fields
    unless they are placed explicitly, which put "Rloop" and "3nH" running
    vertically through their own symbols on the first plot. Horizontal
    parts therefore get their text stacked above and below instead of
    offset to the right."""
    if vx is None and rot in (90, 270):
        vx, vy = x - 4.5, y - 3.0
    parts.append('''  (symbol (lib_id "%s") (at %s %s %d) (unit 1)
    (in_bom yes) (on_board yes) (dnp no) (uuid "%s")
    (property "Reference" "%s" (at %s %s %d) (effects (font (size 1.27 1.27)) (justify left)))
    (property "Value" "%s" (at %s %s %d) (effects (font (size 1.27 1.27)) (justify left)))
    (instances (project "gan_buck" (path "/%s" (reference "%s") (unit 1))))
  )''' % (lib_id, x, y, rot, U(), ref,
          x + 3.2 if vx is None else vx,
          y - 2.2 if vy is None else vy - 2.2, tang,
          value, x + 3.2 if vx is None else vx,
          y + 1.4 if vy is None else vy + 1.4, tang, SHEET_UUID, ref))
    return (x, y, rot)


def wire(a, b):
    wires.append('  (wire (pts (xy %s %s) (xy %s %s)) '
                 '(stroke (width 0) (type default)) (uuid "%s"))'
                 % (a[0], a[1], b[0], b[1], U()))


def hop(*pts):
    for i in range(len(pts) - 1):
        wire(pts[i], pts[i + 1])


def label(txt, x, y, rot=0, size=1.4):
    labels.append('''  (label "%s" (at %s %s %d)
    (effects (font (size %s %s)) (justify left bottom)) (uuid "%s"))'''
                  % (txt, x, y, rot, size, size, U()))


def text(txt, x, y, size=1.6):
    texts.append('''  (text "%s" (at %s %s 0)
    (effects (font (size %s %s)) (justify left top)) (uuid "%s"))'''
                 % (txt.replace('"', "'"), x, y, size, size, U()))


def junction(x, y):
    wires.append('  (junction (at %s %s) (diameter 0) (color 0 0 0 0) (uuid "%s"))'
                 % (x, y, U()))


SHEET_UUID = U()

# ============================== THE CIRCUIT ==============================
# Layout mirrors the signal path in sim/buck.cir, left to right: supply,
# loop parasitics, decoupling, half-bridge, output filter, load.

BUS_Y, SWX = 60.0, 162.54

# ---- supply rail and the power-loop parasitics ----
label("VIN  %s" % val("VIN", "100", " V"), 36, BUS_Y - 2)
hop((40, BUS_Y), (66.19, BUS_Y))
rl = place("Device:R", "Rloop", val("RLOOP", "0.3", " Ω"), 70, BUS_Y, 90)
hop(pin("Device:R", 70, BUS_Y, 90, "2"), (91.19, BUS_Y))
ll = place("Device:L", "Lloop", val("LLOOP", "3n", "H"), 95, BUS_Y, 90)
hop(pin("Device:L", 95, BUS_Y, 90, "2"), (120, BUS_Y))
label("hstop", 116, BUS_Y - 2)
junction(120, BUS_Y)
hop((120, BUS_Y), (SWX, BUS_Y))

# ---- damped bus decoupling: the branch that caused the 200 V failure ----
place("Device:L", "Ldec", val("LDEC", "0.5n", "H"), 120, 75)
hop((120, BUS_Y), pin("Device:L", 120, 75, 0, "1"))
place("Device:C", "Cdec", val("CDEC", "100n", "F"), 120, 90)
hop(pin("Device:L", 120, 75, 0, "2"), pin("Device:C", 120, 90, 0, "1"))
place("Device:R", "Rdec", val("RDEC", "1", " Ω"), 120, 105)
hop(pin("Device:C", 120, 90, 0, "2"), pin("Device:R", 120, 105, 0, "1"))
place("power:GND", "#PWR01", "GND", 120, 115)
hop(pin("Device:R", 120, 105, 0, "2"), (120, 115))

# ---- the half-bridge ----
hop((SWX, BUS_Y), pin("Device:Q_NMOS_DGS", 160, 90, 0, "D"))
place("Device:Q_NMOS_DGS", "Qhs", "eGaN HEMT", 160, 90, 0, vx=166, vy=90)
label("HSG", 143, 89)
hop((147, 90), pin("Device:Q_NMOS_DGS", 160, 90, 0, "G"))

SWY = 110.0
hop(pin("Device:Q_NMOS_DGS", 160, 90, 0, "S"), (SWX, SWY))
junction(SWX, SWY)
label("SW", SWX + 2, SWY - 2)

place("Device:Q_NMOS_DGS", "Qls", "eGaN HEMT", 160, 130, 0, vx=166, vy=130)
hop((SWX, SWY), pin("Device:Q_NMOS_DGS", 160, 130, 0, "D"))
label("LSG", 143, 129)
hop((147, 130), pin("Device:Q_NMOS_DGS", 160, 130, 0, "G"))
place("power:GND", "#PWR02", "GND", SWX, 145)
hop(pin("Device:Q_NMOS_DGS", 160, 130, 0, "S"), (SWX, 145))

# ---- output filter and load ----
hop((SWX, SWY), (191.19, SWY))
place("Device:L", "Lo", val("LOUT", "22u", "H"), 195, SWY, 90)
hop(pin("Device:L", 195, SWY, 90, "2"), (225, SWY))
label("OUT", 212, SWY - 2)
junction(225, SWY)

place("Device:R", "Resr", "0.3 Ω", 240, 120)
hop((225, SWY), (240, SWY), pin("Device:R", 240, 120, 0, "1"))
place("Device:C", "Co", val("COUT", "4.7u", "F"), 240, 135)
hop(pin("Device:R", 240, 120, 0, "2"), pin("Device:C", 240, 135, 0, "1"))
place("power:GND", "#PWR03", "GND", 240, 145)
hop(pin("Device:C", 240, 135, 0, "2"), (240, 145))

place("Device:R", "Rload", val("RLOAD", "10", " Ω"), 275, 120)
hop((225, SWY), (275, SWY), pin("Device:R", 275, 120, 0, "1"))
place("power:GND", "#PWR04", "GND", 275, 145)
hop(pin("Device:R", 275, 120, 0, "2"), (275, 145))

# ---- what the sheet has to say for itself ----
text("GaN synchronous buck converter - the circuit simulated in sim/buck.cir", 36, 26, 2.6)
text("%s V in, %s V out at %s kHz.  Values read from the netlist at build time."
     % (val("VIN", "100"), str(float(val("VIN", "100")) * float(val("D", "0.5"))),
        str(int(float(val("FSW", "500k").replace("k", "")) ))), 36, 32, 1.8)
text("Qhs / Qls are enhancement-mode GaN HEMTs. KiCad has no GaN symbol, so an", 36, 160, 1.7)
text("n-channel enhancement MOSFET symbol is used, as in EPC's own schematics.", 36, 164, 1.7)
text("The device has NO BODY DIODE - reverse conduction during dead time costs", 36, 168, 1.7)
text("Vth + |Voff| + I*Rds(on), not one diode drop. This sets the dead-time trade.", 36, 172, 1.7)
text("Ldec / Cdec / Rdec is the bus decoupling. Rdec = 1 ohm is a damping value,", 36, 180, 1.7)
text("not a parasitic: at 20 mOhm this branch rings at ~22 MHz and drove the", 36, 184, 1.7)
text("low-side gate to +11.8 V against a 1.4 V threshold at a 200 V bus.", 36, 188, 1.7)
text("HSG / LSG come from the segmented gate driver (8 pull-up + 8 pull-down", 36, 196, 1.7)
text("slices, active Miller clamp, -2 V off rail) driven by seg_gate_ctrl.v.", 36, 200, 1.7)
text("Not drawn: Vsin, Vshs, Vsls, Vsout are 0 V sources in the netlist used", 36, 208, 1.7)
text("only to sense current. They are measurement points, not components.", 36, 212, 1.7)

# =========================================================================
libs = "\n".join("    " + lift(l, n) for l, n in NEEDED)
sch = '''(kicad_sch (version 20230121) (generator gan_driver_project)
  (uuid "%s")
  (paper "A3")
  (title_block
    (title "GaN Synchronous Buck Converter - Power Stage")
    (company "SENSE, VIT Chennai")
    (comment 1 "Generated from sim/buck.cir by scripts/kicad_schematic.py")
  )
  (lib_symbols
%s
  )
%s
%s
%s
%s
  (sheet_instances (path "/" (page "1")))
)
''' % (SHEET_UUID, libs, "\n".join(wires), "\n".join(parts),
       "\n".join(labels), "\n".join(texts))

if not os.path.isdir(OUT):
    os.makedirs(OUT)
path = os.path.join(OUT, "gan_buck.kicad_sch")
open(path, "w", encoding="utf-8").write(sch)
print("  written: kicad/gan_buck.kicad_sch  (%d components)" % len(parts))

for fmt in ("svg", "pdf"):
    r = subprocess.run(["kicad-cli", "sch", "export", fmt, "--output",
                        OUT if fmt == "svg" else os.path.join(OUT, "gan_buck.pdf"),
                        path], capture_output=True, text=True)
    ok = r.returncode == 0
    print("  %s: %s" % (fmt.upper(), "ok" if ok else r.stderr.strip()[:160]))
