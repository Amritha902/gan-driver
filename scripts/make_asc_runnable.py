"""
make_asc_runnable.py -- emit .asc files LTspice will open and run.

The .cir netlists are correct and LTspice-compatible, but macOS will not hand
a .cir to LTspice: the wrapper answers "unable to open ... not in the default
bottle", because only .asc is registered to the application. Opening one means
File > Open with the type filter changed to All Files, which is exactly the
kind of instruction that does not survive being handed to somebody else.

So the netlist goes inside a .asc instead. LTspice appends any SPICE directive
placed on a schematic to the netlist it simulates, and a schematic that is
nothing BUT directives simulates exactly the same circuit. Double-click, press
Run, read the error log. Nothing to configure.

    python3 scripts/make_asc_runnable.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LT   = os.path.join(ROOT, "ltspice")

FILES = [
    ("A_baseline_FALSE_TURN_ON.cir", "RUN_A_no_clamp_FAILS.asc",
     "A -- no clamp, 0 V off-bias.  EXPECT vspur = +1.649 V, above the "
     "1.4 V threshold: FALSE TURN-ON."),
    ("B_miller_clamp_ON.cir", "RUN_B_clamp_on.asc",
     "B -- Miller clamp on, 0 V off-bias.  EXPECT vspur = +0.830 V: safe, "
     "margin +0.570 V."),
    ("C_clamp_and_negative_bias.cir", "RUN_C_clamp_and_negative_bias.asc",
     "C -- clamp on and -2 V off-bias.  EXPECT vspur = -1.176 V: safe, "
     "margin +2.576 V."),
]

HOWTO = [
    "HOW TO RUN THIS",
    "  1. Press Run (the running-man button, or Simulate > Run).",
    "  2. View > SPICE Error Log  --  the last line is the measurement:",
    "         vspur: MAX(v(hsg,sw)) ...",
    "  3. vspur is the voltage on the gate of the device that is supposed",
    "     to be OFF. The device turns on above 1.4 V.",
    "",
    "  Keep this file in the same folder as egan.lib and segdrv.lib.",
]


def netlist_lines(path):
    """The circuit, without the title line, the comments, or .end."""
    out = []
    for i, raw in enumerate(open(path)):
        line = raw.rstrip("\n")
        if i == 0:                       # SPICE title line
            continue
        s = line.strip()
        if not s or s.startswith("*"):   # comment-only
            continue
        if s.lower() == ".end":
            continue
        out.append(line.rstrip())
    return out


def esc(lines):
    """LTspice puts a whole multi-line directive in one TEXT record,
    with a literal backslash-n between lines."""
    return "\\n".join(l.replace("\\", "/") for l in lines)


for src, dst, headline in FILES:
    spath = os.path.join(LT, src)
    if not os.path.exists(spath):
        print("missing", src)
        continue
    body = netlist_lines(spath)

    asc = []
    asc.append("Version 4")
    asc.append("SHEET 1 2200 1600")
    asc.append("TEXT 64 48 Left 4 ;GaN half-bridge double-pulse test  --  %s" % headline)
    asc.append("TEXT 64 128 Left 2 ;" + esc(HOWTO))
    asc.append("TEXT 64 400 Left 2 !" + esc(body))

    with open(os.path.join(LT, dst), "w") as f:
        f.write("\n".join(asc) + "\n")
    print("wrote ltspice/%-36s (%d netlist lines)" % (dst, len(body)))
