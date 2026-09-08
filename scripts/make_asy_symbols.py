"""
make_asy_symbols.py -- symbols for the two subcircuits the project actually uses.

The first schematic attempt drew the GaN devices as LTspice's built-in VDMOS and
the gate drive as a resistor, and measured 0.119 V where ngspice measures 1.649.
That is the right answer for a different circuit. A drawing that does not carry
the same models is a picture, not a simulation.

So: give egan.lib's EGAN and segdrv.lib's SEGDRV real symbols, and the schematic
becomes the same netlist ngspice runs, drawn.

    EGAN    d g s
    SEGDRV  pu pd clk out vp vn ref
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LT   = os.path.join(ROOT, "ltspice")


def symbol(name, pins, w, h, lines, label_at=(0, -8)):
    out = ["Version 4", "SymbolType CELL"]
    out += ["LINE Normal %d %d %d %d" % l for l in lines]
    out.append("RECTANGLE Normal 0 0 %d %d" % (w, h))
    out.append("WINDOW 0 %d %d Left 2" % (label_at[0], label_at[1]))
    out.append("WINDOW 3 %d %d Left 2" % (label_at[0], h + 8))
    out.append("SYMATTR Value %s" % name)
    out.append("SYMATTR Prefix X")
    out.append("SYMATTR Description %s" % name)
    for i, (px, py, pname) in enumerate(pins, start=1):
        out.append("PIN %d %d NONE 8" % (px, py))
        out.append("PINATTR PinName %s" % pname)
        out.append("PINATTR SpiceOrder %d" % i)
    return "\n".join(out) + "\n"


# ---- EGAN: d on top, g on the left, s at the bottom -----------------------
egan = symbol(
    "EGAN",
    [(48, -32, "d"), (-32, 48, "g"), (48, 128, "s")],
    96, 96,
    [(48, -32, 48, 0), (-32, 48, 0, 48), (48, 96, 48, 128)],
)

# ---- SEGDRV: inputs left, rails and output right --------------------------
seg = symbol(
    "SEGDRV",
    [(-32, 32, "pu"), (-32, 64, "pd"), (-32, 96, "clk"),
     (160, 64, "out"), (160, 16, "vp"), (160, 112, "vn"), (64, 160, "ref")],
    128, 128,
    [(-32, 32, 0, 32), (-32, 64, 0, 64), (-32, 96, 0, 96),
     (128, 64, 160, 64), (128, 16, 160, 16), (128, 112, 160, 112),
     (64, 128, 64, 160)],
)

for name, body in (("egan.asy", egan), ("segdrv.asy", seg)):
    open(os.path.join(LT, name), "w").write(body)
    print("wrote ltspice/%s" % name)
