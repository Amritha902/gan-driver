# -*- coding: utf-8 -*-
"""kicad_common.py -- the bits both generated schematics need.

Factored out when the driver sheet was added, so the coordinate maths and
the symbol lifting exist once rather than twice. The two rendering bugs in
the power-stage sheet were both in this code; having two copies would have
meant fixing them twice and, realistically, fixing one.
"""
import os, uuid

SYMDIR = "/usr/share/kicad/symbols"

# Pin offsets in symbol-local coordinates (Y up), read out of the library
# definitions rather than guessed.
PINS = {
    "Device:R":          {"1": (0, 3.81),  "2": (0, -3.81)},
    "Device:R_Small":    {"1": (0, 2.54),  "2": (0, -2.54)},
    "Device:L":          {"1": (0, 3.81),  "2": (0, -3.81)},
    "Device:C":          {"1": (0, 3.81),  "2": (0, -3.81)},
    "Device:C_Small":    {"1": (0, 2.54),  "2": (0, -2.54)},
    "Device:Q_NMOS_DGS": {"D": (2.54, 5.08), "G": (-5.08, 0), "S": (2.54, -5.08)},
    "Switch:SW_SPST":    {"1": (-5.08, 0), "2": (5.08, 0)},
    "power:GND":         {"1": (0, 0)},
}


def lift(lib, name):
    """Pull a symbol's definition out of a system library.

    A .kicad_sch must embed the symbols it uses in its own lib_symbols
    block -- it does not reference the system libraries at plot time -- so
    the definition is copied in verbatim and renamed from "R" to the
    "Device:R" form a schematic expects.
    """
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
                return s[i:j + 1].replace(key, '(symbol "%s:%s"' % (lib, name), 1)
    raise SystemExit("unterminated symbol %s:%s" % (lib, name))


def pin(lib_id, x0, y0, rot, which):
    """Where a pin actually lands on the sheet.

    Symbol libraries are Y-up and schematics are Y-down, so a symbol placed
    at (x0,y0) puts its local pin (px,py) at (x0+px, y0-py). A rotation of
    90 degrees maps the local point to (-py, px) first. Computing this is
    the difference between wires that connect and wires that merely look
    like they do.
    """
    px, py = PINS[lib_id][which]
    if rot == 90:
        px, py = -py, px
    elif rot == 180:
        px, py = -px, -py
    elif rot == 270:
        px, py = py, -px
    return (round(x0 + px, 3), round(y0 - py, 3))


U = lambda: str(uuid.uuid4())


class Sheet(object):
    """One schematic, accumulated then written out."""

    def __init__(self, title, comment, paper="A3"):
        self.uuid, self.title, self.comment, self.paper = U(), title, comment, paper
        self.parts, self.wires, self.labels, self.texts = [], [], [], []
        self.sheets = []
        self.used = set()

    def place(self, lib_id, ref, value, x, y, rot=0, vx=None, vy=None, hide_val=False):
        self.used.add(lib_id)
        # A property's angle in KiCad 7 is RELATIVE to its symbol's rotation,
        # so a property at angle 0 on a symbol rotated 90 renders at 90 --
        # which is how labels ended up running vertically through their own
        # symbols on the first plot. Compensate.
        tang = (360 - rot) % 360
        if vx is None and rot in (90, 270):
            vx, vy = x - 5.0, y - 5.4
        rx = x + 3.2 if vx is None else vx
        ry0 = y - 2.2 if vy is None else vy - 2.2
        ry1 = y + 1.4 if vy is None else vy + 1.4
        vis = "" if not hide_val else " hide"
        self.parts.append('''  (symbol (lib_id "%s") (at %s %s %d) (unit 1)
    (in_bom yes) (on_board yes) (dnp no) (uuid "%s")
    (property "Reference" "%s" (at %s %s %d) (effects (font (size 1.1 1.1)) (justify left)))
    (property "Value" "%s" (at %s %s %d) (effects (font (size 1.1 1.1)) (justify left)%s))
    (instances (project "p" (path "/%s" (reference "%s") (unit 1))))
  )''' % (lib_id, x, y, rot, U(), ref, rx, ry0, tang, value, rx, ry1, tang,
          vis, self.uuid, ref))

    def wire(self, a, b):
        self.wires.append('  (wire (pts (xy %s %s) (xy %s %s)) '
                          '(stroke (width 0) (type default)) (uuid "%s"))'
                          % (a[0], a[1], b[0], b[1], U()))

    def hop(self, *pts):
        for i in range(len(pts) - 1):
            self.wire(pts[i], pts[i + 1])

    def junction(self, x, y):
        self.wires.append('  (junction (at %s %s) (diameter 0) (color 0 0 0 0) '
                          '(uuid "%s"))' % (x, y, U()))

    def label(self, txt, x, y, rot=0, size=1.4):
        self.labels.append('  (label "%s" (at %s %s %d) (effects (font (size %s %s)) '
                           '(justify left bottom)) (uuid "%s"))'
                           % (txt, x, y, rot, size, size, U()))

    def text(self, txt, x, y, size=1.7):
        self.texts.append('  (text "%s" (at %s %s 0) (effects (font (size %s %s)) '
                          '(justify left top)) (uuid "%s"))'
                          % (txt.replace('"', "'"), x, y, size, size, U()))

    def subsheet(self, name, filename, x, y, w, h, pins):
        """A hierarchical sheet instance -- a real sub-schematic, not a box.

        This is what makes the driver part of the converter drawing rather
        than a separate sheet the reader has to wire up mentally. The
        simulation was always integrated (sim/buck.cir includes segdrv.lib
        and instantiates it twice); only the drawing was not.

        `pins` is a list of (name, kind, side, offset) where side is "L" or
        "R" and offset is measured down from the sheet's top edge. KiCad
        wants a pin's angle to point INTO the sheet body, so a pin on the
        left edge is at 180 and one on the right at 0 -- getting that
        backwards puts the stub inside the box where no wire can reach it.
        """
        self.sheets.append(dict(name=name, file=filename, x=x, y=y,
                                w=w, h=h, pins=pins))
        out = {}
        body = ['  (sheet (at %s %s) (size %s %s)' % (x, y, w, h),
                '    (stroke (width 0.1524) (type solid))',
                '    (fill (color 0 0 0 0.0000))',
                '    (uuid "%s")' % U(),
                '    (property "Sheetname" "%s" (at %s %s 0) '
                '(effects (font (size 1.4 1.4)) (justify left bottom)))'
                % (name, x, y - 0.8),
                '    (property "Sheetfile" "%s" (at %s %s 0) '
                '(effects (font (size 1.2 1.2)) (justify left top)))'
                % (filename, x, y + h + 0.8)]
        for nm, kind, side, off in pins:
            px = x if side == "L" else x + w
            py = y + off
            body.append('    (pin "%s" %s (at %s %s %d) '
                        '(effects (font (size 1.2 1.2)) (justify %s)) (uuid "%s"))'
                        % (nm, kind, px, py, 180 if side == "L" else 0,
                           "right" if side == "L" else "left", U()))
            out[nm] = (px, py)
        body.append('    (instances (project "p" (path "/%s" (page "%d"))))'
                    % (self.uuid, len(self.sheets) + 1))
        body.append('  )')
        self.parts.append("\n".join(body))
        return out

    def save(self, path, needed):
        libs = "\n".join("    " + lift(l, n) for l, n in needed)
        sch = '''(kicad_sch (version 20230121) (generator gan_driver_project)
  (uuid "%s")
  (paper "%s")
  (title_block
    (title "%s")
    (company "SENSE, VIT Chennai")
    (comment 1 "%s")
  )
  (lib_symbols
%s
  )
%s
%s
%s
%s
  (sheet_instances (path "/" (page "1"))%s)
)
''' % (self.uuid, self.paper, self.title, self.comment, libs,
       "\n".join(self.wires), "\n".join(self.parts),
       "\n".join(self.labels), "\n".join(self.texts),
       "".join('\n    (path "/%s" (page "%d"))'
               % (self.uuid, i + 2) for i in range(len(self.sheets))))
        d = os.path.dirname(path)
        if d and not os.path.isdir(d):
            os.makedirs(d)
        open(path, "w", encoding="utf-8").write(sch)
        return len(self.parts)


def plot(path, outdir):
    """Export SVG and PDF with kicad-cli. Returns a list of (fmt, ok, msg)."""
    import subprocess
    base = os.path.splitext(os.path.basename(path))[0]
    res = []
    for fmt in ("svg", "pdf"):
        target = outdir if fmt == "svg" else os.path.join(outdir, base + ".pdf")
        r = subprocess.run(["kicad-cli", "sch", "export", fmt, "--output",
                            target, path], capture_output=True, text=True)
        res.append((fmt, r.returncode == 0, (r.stderr or "").strip()[:150]))
    return res
