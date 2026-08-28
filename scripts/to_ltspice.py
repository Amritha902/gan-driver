"""
to_ltspice.py -- convert the ngspice netlists to LTspice dialect.

    python3 scripts/to_ltspice.py            # writes ltspice/*.cir, *.lib

Then in LTspice: File > Open, set the file type filter to "All Files",
open ltspice/dpt.cir, and hit Run.  Probe v(sw), v(lsg), v(hsg).

Differences handled:
  $ comment          ->  ; comment      (LTspice's inline comment char)
  .control/.endc     ->  deleted        (LTspice has no interactive block)
  wrdata             ->  deleted        (use LTspice's own .save / waveform viewer)
  {a ? b : c}        ->  a plain number (see below)

Conditionals are removed rather than translated.  ngspice takes `a ? b : c`
in a component value; LTspice's evaluator is not reliable there and this
environment has no LTspice to test against, so instead the slice enables are
BAKED IN at conversion time:

    python3 scripts/to_ltspice.py --npu 4 --npd 8

writes a netlist whose slice resistors are literal numbers.  Nothing is left
for LTspice to evaluate, so nothing can be mistranslated.  To change the
control word, re-run the converter.
Everything else -- .func, ternaries in component values, .param, the diode
C(V) models, the switch models -- is already common to both simulators.
"""
import os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "ltspice")


def convert(text):
    text = re.sub(r"(?is)^\.control\b.*?^\.endc\b[^\n]*\n", "", text, flags=re.M)
    out = []
    for line in text.splitlines():
        # $ is an ngspice end-of-line comment; LTspice uses ;
        if "$" in line and not line.lstrip().startswith("*"):
            line = line.replace("$", ";", 1)
        elif line.lstrip().startswith("*") and "$" in line:
            line = line.replace("$", "", 1)
        line = line.replace(".include ../models/", ".include ")
        # Bake the slice enables to literals instead of translating the
        # conditional.  ngspice accepts `a ? b : c` in a component value;
        # LTspice's evaluator is not reliable there and there is no LTspice
        # in this environment to test a translation against, so the safe
        # move is to leave LTspice nothing to evaluate.
        m = re.match(r"(R(pu|pd)(\d)\s+\S+\s+\S+\s+)"
                     r"\{runit \+ \((npu|npd)>=\d+ \? 0 : 1e9\)\}\s*$", line)
        if m:
            code = NPU if m.group(2) == "pu" else NPD
            line = (m.group(1) + "{runit}") if int(m.group(3)) <= code else \
                   (m.group(1) + "1e9   ; slice off at code %d" % code)
        out.append(line)
    return "\n".join(out) + "\n"


NPU = NPD = 8


def main():
    os.makedirs(OUT, exist_ok=True)
    jobs = [("models/egan.lib",   "egan.lib"),
            ("models/segdrv.lib", "segdrv.lib"),
            ("sim/dpt.cir",       "dpt.cir")]
    for src, dst in jobs:
        t = convert(open(os.path.join(ROOT, src)).read())
        if dst == "dpt.cir":
            t = t.replace(".end\n",
                          ".save v(sw) v(lsg) v(hsg) v(lsd) v(hsd)\n"
                          "+ i(vsls) i(vshs)\n.end\n")
        open(os.path.join(OUT, dst), "w").write(t)
        print("wrote ltspice/%s" % dst)
    print("\nOpen ltspice/dpt.cir in LTspice (set file filter to 'All Files').")
    print("Edit the PARAM BLOCK to change the control word.")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--npu", type=int, default=8, choices=range(1, 9))
    ap.add_argument("--npd", type=int, default=8, choices=range(1, 9))
    a = ap.parse_args()
    NPU, NPD = a.npu, a.npd
    print("baking control word: npu=%d npd=%d\n" % (NPU, NPD))
    main()
