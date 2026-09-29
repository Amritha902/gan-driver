# -*- coding: utf-8 -*-
"""test_plain_pass.py -- does the register guard actually fire?

    python3 review/test_plain_pass.py

A guard nobody has watched fail is not a guard. Two of the checks in
audit_demo.py were silently absent for a while -- they searched for wording
the deck had been rewritten away from, found nothing, and passed. That is why
this file exists and why it tests both directions: eight phrasings that must
be caught, and six legitimate constructions that must NOT be, because a check
that cries wolf on correct slides is a check somebody switches off.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plain_pass as pp

CASES = [
    # (label, text, must the guard fire?)
    ("self-reference", u"Latency and device power, the two you asked for", True),
    ("stage direction", u"Click to play the recording.", True),
    ("room reference", u"It runs on whatever machine is in this room.", True),
    ("editorialising", u"which is the honest shape of the result", True),
    ("film jargon", u"The same four beats over our driver.", True),
    ("conversational", u"yeah all seen and verified uk, this stuff is fine bro", True),
    ("shouting", u"Their driver is run at its BEST setting.", True),
    ("informal", u"so the two can be compared by eye", True),

    ("acronym", u"The FPGA controller drives 20 LUT and 20 FF at 200 MHz.", False),
    ("lower case", u"Their driver is run at its best setting, found by search.", False),
    ("file name", u"Run bash proof/LIVE-SIM.sh and read RESULTS-SUMMARY.md.", False),
    ("quotation", u"their sheet says “tied to ref — NO negative rail”", False),
    ("table header", u"THE ONE THING THAT MOVES", False),
    ("registration no.", u"Sanjay Kumar 23BEC1447 and Amritha S 23BEC1368", False),
    ("physics symbol", u"the cost is V_th + |V_off| + I·R_ds(on)", False),
]


def findings(text):
    out = [why for pat, why in pp.BANNED_ANY_CASE if re.search(pat, text, re.I)]
    out += ["emphasis by capital letters" for _ in pp.shouted(text)]
    return out


def main():
    bad = 0
    for label, text, should in CASES:
        hits = findings(text)
        ok = bool(hits) == should
        bad += 0 if ok else 1
        print("  %-4s %-16s %-28s %s"
              % ("PASS" if ok else "FAIL", label,
                 hits[0] if hits else "no finding", text[:50]))
    print("\n  %d of %d behaved as expected" % (len(CASES) - bad, len(CASES)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
