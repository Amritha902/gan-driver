"""closedloop_numbers.py -- the closed-loop slide's figures, read from the run.

Slide 28 quoted "worst error 0.01 % against open loop's 20.0 %" and "open loop
walks to 60 V". results/closedloop.txt, which scripts/closedloop.py writes,
says 0.02 %, 16.65 % and 58.33 V. Three numbers, all rounded the flattering
way, none of them re-derived by anything.

They are parsed out of that file now, so the slide cannot say something the
run did not.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "results", "closedloop.txt")

_t = open(SRC, encoding="utf-8").read()


def _f(pat):
    m = re.search(pat, _t)
    if not m:
        raise SystemExit("closedloop.txt: cannot find %r -- re-run "
                         "scripts/closedloop.py" % pat)
    return float(m.group(1))


NOM_C   = _f(r"closed loop\s+nominal ([\d.]+) V")
LOAD_C  = _f(r"closed loop.*?after load ([\d.]+) V")
LINE_C  = _f(r"closed loop.*?after line ([\d.]+) V")
ERR_C   = _f(r"closed loop.*?worst error ([\d.]+) %")
LINE_O  = _f(r"open loop.*?after line ([\d.]+) V")
ERR_O   = _f(r"open loop.*?worst error ([\d.]+) %")
REC_LD  = _f(r"load step dip [\d.]+ V, recovery (\d+) us")
REC_LN  = _f(r"line step peak [\d.]+ V, recovery (\d+) us")
SOFT_V  = _f(r"soft-start overshoot ([\d.]+) V")
RIPPLE  = _f(r"output ripple ([\d.]+) V pk-pk")
EFF_C   = _f(r"efficiency closed ([\d.]+) %")

SOFT_PCT   = (SOFT_V - NOM_C) / NOM_C * 100.0
RIPPLE_PCT = RIPPLE / NOM_C * 100.0

if __name__ == "__main__":
    for k, v in sorted(globals().items()):
        if k.isupper() and isinstance(v, float):
            print("  %-12s %8.3f" % (k, v))
