# -*- coding: utf-8 -*-
"""cite_pass.py -- name the KiCad sheet on every slide that shows one.

    python3 review/cite_pass.py

The deck cites the file behind every other claim -- sim/buck.cir for the
netlist, models/egan.lib for the device, scripts/headtohead.py for the
comparison -- and link_pass turns each of those into a link into the
repository. The schematics were the exception: three sheets are drawn across
five slides and not one of them said which file it was, so there was nothing
for a reviewer to open and nothing for the linker to link.

The sheets are kicad/gan_buck.kicad_sch (the converter),
kicad/gan_zhangdrv.kicad_sch (the base paper's driver) and
kicad/gan_segdrv.kicad_sch (ours).

Anchors avoid figure numbers on purpose: the same caption is Fig. 4 in the
presented deck and Fig. 8 in the backup, so anchoring on the number would
silently edit one deck and miss the other.
"""
import os
import re
import sys

from pptx import Presentation

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from plain_pass import all_paragraphs, para_text, replace_in_paragraph

HERE = os.path.dirname(os.path.abspath(__file__))

DECKS = ["GaN_Review2_PRESENT.pptx", "GaN_Review2_BACKUP.pptx",
         "Review2_GaN_Segmented_Gate_Driver.pptx"]

BUCK = u"kicad/gan_buck.kicad_sch"
THEIRS = u"kicad/gan_zhangdrv.kicad_sch"
OURS = u"kicad/gan_segdrv.kicad_sch"

CITE = [
    # the converter schematic
    (u"drawn from sim/buck.cir by scripts/kicad_schematic.py",
     u"drawn from sim/buck.cir by scripts/kicad_schematic.py into " + BUCK),
    # the novelty figure: converter on top, their driver and ours below
    (u"Top: sim/buck.cir, with the two gates of the half-bridge ringed",
     u"Top: " + BUCK + u", with the two gates of the half-bridge ringed"),
    (u"Bottom left, theirs: seven slices a bank in two stages",
     u"Bottom left, theirs (" + THEIRS + u"): seven slices a bank in two stages"),
    (u"Bottom right, ours: the same eight-slice output stage",
     u"Bottom right, ours (" + OURS + u"): the same eight-slice output stage"),
    # the base paper's driver, run and captured
    (u"Their circuit in KiCad, ngspice running it",
     u"Their circuit in KiCad (" + THEIRS + u"), ngspice running it"),
    # the demo film
    (u"The circuit as its KiCad sheet,",
     u"The circuit as its KiCad sheet (" + BUCK + u"),"),
]

# A caption may mention KiCad without showing a sheet. Each exemption says
# why, so the guard below stays meaningful instead of being widened whenever
# it complains.
NO_SHEET_SHOWN = [
    (u"ngspice-42 and KiCad 7.0.11",
     "names the tool and its version, draws nothing"),
    (u"KiCad 7.0.11 (GPL v3)",
     "licence statement, draws nothing"),
    (u"drawn by scripts/kicad_schematic.py",
     "names the generator for a figure whose sheet is cited elsewhere"),
]

SHEET = re.compile(r"kicad/[A-Za-z0-9_\-]+\.kicad_sch")


def main():
    total, failures = 0, []
    for name in DECKS:
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            continue
        prs = Presentation(path)
        n = 0
        for para in all_paragraphs(prs):
            for old, new in CITE:
                if old in para_text(para):
                    n += replace_in_paragraph(para, old, new)
        prs.save(path)
        total += n

        # Every caption that shows a sheet must name it.
        prs = Presentation(path)
        for para in all_paragraphs(prs):
            body = para_text(para)
            if "KiCad" not in body and "kicad" not in body:
                continue
            if SHEET.search(body):
                continue
            if any(x in body for x, _ in NO_SHEET_SHOWN):
                continue
            failures.append((name, body.strip()[:88]))
        print("  %-42s %3d citation(s)" % (name, n))

    print("  %d citation(s) across %d deck(s)" % (total, len(DECKS)))
    if failures:
        print("\n  KICAD FIGURE WITH NO SHEET NAMED:")
        for name, body in sorted(set(failures)):
            print("    %-28s %s" % (name, body))
        return 1
    print("  every KiCad figure names its sheet")
    return 0


if __name__ == "__main__":
    sys.exit(main())
