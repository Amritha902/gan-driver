"""
make_ltspice.py -- self-contained LTspice netlists, one file per experiment.

The earlier LTspice export was three files that had to sit in the same
folder.  That is the single most common way this goes wrong for someone
opening it for the first time, so these are FLATTENED: models, driver and
testbench all inlined.  Open one file, press Run, nothing else to place.

    python3 scripts/make_ltspice.py

Dialect handling:
  .control/.endc  removed      (LTspice has no equivalent)
  $ comments      -> ;         (LTspice's inline comment char)
  ternaries       -> baked     (LTspice's evaluator is unreliable here and
                                there is no LTspice in this environment to
                                test a translation against)
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flatten import inline

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "ltspice")

EXPERIMENTS = [
    ("1_baseline_FALSE_TURN_ON", dict(CLKEN="0", VNEG="0"),
     "BASELINE - this one FAILS on purpose.",
     "Peak V(hsg)-V(sw) reaches 1.65 V against a 1.4 V threshold.\n"
     "* That is false turn-on: the off device is switched on by its own\n"
     "* Miller capacitance. This is the problem the project exists to fix."),
    ("2_miller_clamp_on", dict(CLKEN="1", VNEG="0"),
     "FIX 1 - active Miller clamp enabled.",
     "Peak V(hsg)-V(sw) drops to 0.83 V. Margin +0.57 V.\n"
     "* Costs almost nothing: switching energy changes by under 1%."),
    ("3_clamp_and_negative_bias", dict(CLKEN="1", VNEG="-2"),
     "FIX 2 - clamp plus -2 V off-bias.",
     "Peak V(hsg)-V(sw) drops to -1.18 V. Margin +2.58 V.\n"
     "* Much safer, but the negative rail costs dead-time conduction loss\n"
     "* because GaN has no body diode: V_SD = Vth + |V_GS,off| + I*R."),
]

HEADER = """* ==================================================================
* {title}
*
* {desc}
*
* GaN half-bridge double-pulse test with a segmented gate driver.
* SELF-CONTAINED - device model, driver and testbench are all inlined.
* Nothing else needs to be in this folder.
*
* HOW TO RUN
*   LTspice -> File -> Open -> set file type to "All Files" -> this file
*   Press Run (the running man).
*   Right-click the plot pane -> Add Trace, and add:
*        V(sw)              the switch node
*        V(lsg)             low-side gate
*        V(hsg)-V(sw)       HIGH-SIDE GATE  <- the one that matters
*
* WHAT TO LOOK FOR  (verified against ngspice 42)
*   gate on-state at t=0.9us .............  5.00 V
*   peak V(lsd) after t=1us ..............  122.4 V   (bus is 100 V)
*   peak V(hsg)-V(sw) over 2.015-2.10us ..  {expect}
*   threshold Vth ........................  1.40 V
*
* Edit the PARAM BLOCK below to change the experiment.
* ==================================================================
"""


def ltspice_dialect(text, npu=8, npd=8):
    text = re.sub(r"(?is)^\.control\b.*?^\.endc\b[^\n]*\n", "", text, flags=re.M)
    # The first line of a SPICE netlist is the TITLE and is consumed as such.
    # This header is prepended above it, so the original title would land in
    # the middle of the deck and be parsed as a component line -- ngspice
    # reports "could not find a valid modelname".  Comment it out.
    lines = text.splitlines()
    if lines and not lines[0].lstrip().startswith(("*", ".")):
        lines[0] = "* " + lines[0]
    text = "\n".join(lines) + "\n"
    out = []
    for line in text.splitlines():
        m = re.match(r"(R(pu|pd)(\d)\s+\S+\s+\S+\s+)"
                     r"\{runit \+ \((npu|npd)>=\d+ \? 0 : 1e9\)\}\s*$", line)
        if m:
            code = npu if m.group(2) == "pu" else npd
            line = (m.group(1) + "{runit}") if int(m.group(3)) <= code \
                   else (m.group(1) + "1e9   ; slice off at code %d" % code)
        elif "$" in line:
            line = line.replace("$", ";" if not line.lstrip().startswith("*") else "", 1)
        out.append(line)
    return "\n".join(out) + "\n"


def main():
    os.makedirs(OUT, exist_ok=True)
    src = inline(os.path.join(ROOT, "sim", "dpt.cir"))
    for name, params, title, desc in EXPERIMENTS:
        s = src
        for k, v in params.items():
            s = re.sub(r"^\.param %s=.*$" % k, ".param %s=%s" % (k, v), s, flags=re.M)
        s = ltspice_dialect(s)
        expect = {"1_baseline_FALSE_TURN_ON": "1.65 V  <-- ABOVE Vth, FAILS",
                  "2_miller_clamp_on":        "0.83 V  <-- safe",
                  "3_clamp_and_negative_bias":"-1.18 V <-- very safe"}[name]
        s = s.replace(".end", ".save V(sw) V(lsg) V(hsg) V(lsd) V(hsd)\n.end")
        body = HEADER.format(title=title, desc=desc, expect=expect) + s
        p = os.path.join(OUT, name + ".cir")
        open(p, "w").write(body)
        print("  wrote ltspice/%s.cir  (%d lines, self-contained)"
              % (name, body.count("\n")))


if __name__ == "__main__":
    main()
