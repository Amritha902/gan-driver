# -*- coding: utf-8 -*-
"""check_stale.py -- does anything we ship still quote a superseded number?

    python3 review/check_stale.py

Several results in this project were measured twice: first over four corners,
then over all thirty-six. The second measurement moved them -- (B) went from
3.9 % to 2.6 %, its share of the gain from 13.4 % to 8.9 %, the one-comparator
capture from 46 % to 47 % -- and RESULTS-SUMMARY.txt records both, writing the
old value as "(n=4 said 3.9 %)".

Every slide and caption was updated. What was not: a figure that drew "worth
3.9 % of baseline" into its pixels, a line in review/FIGURES-EXPLAINED.md, and
one bullet on backup slide 61. None of them were caught, because
check_consistency.py compares the deck against the summary for the numbers it
knows to look for, and a number nobody thought to look for is invisible to it.

This works the other way round: it reads the superseded values straight out of
the summary's own "(n=4 said ...)" notes and fails if any of them still appears
in a deck or a shipped document. Adding a new supersession to the summary
extends this check automatically.
"""
import os
import re
import sys

from pptx import Presentation

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SUMMARY = os.path.join(ROOT, "results", "RESULTS-SUMMARY.txt")

DECKS = ["GaN_Review2_PRESENT.pptx", "GaN_Review2_BACKUP.pptx",
         "Review2_GaN_Segmented_Gate_Driver.pptx"]
DOCS = ["FIGURES-EXPLAINED.md", "SPEECH-SCRIPT.md", "SPEECH-10-MINUTES.md",
        "METHODOLOGY.md", "JUDGE.md", "VIVA-REHEARSAL.md"]

# Supersessions the summary does not mark in the "(n=4 said ...)" form, with
# the line of the summary that carries the current value.
EXTRA = [
    ("46 %", "47 % of (B)", "one comparator, RESULTS-SUMMARY line 25"),
    ("72 %", "61 % of (B)", "two comparators, RESULTS-SUMMARY line 26"),
]


def superseded():
    """[(old text, why)] -- read from the summary's own notes."""
    txt = open(SUMMARY).read()
    out = []
    for m in re.finditer(r"^\s*(.+?)\s{2,}([\d.]+ ?%?)\s+\(n=4 said "
                         r"([\d.]+ ?%?)\)", txt, re.M):
        label, now, then = m.group(1).strip(), m.group(2), m.group(3)
        out.append((then.strip(), "%s is now %s" % (label, now)))
    for old, now, where in EXTRA:
        out.append((old, "%s (%s)" % (now, where)))
    return out


def deck_text(path):
    prs = Presentation(path)
    parts = []
    for sl in prs.slides:
        for sh in sl.shapes:
            if sh.has_text_frame:
                parts.append(sh.text_frame.text)
            if getattr(sh, "has_table", False) and sh.has_table:
                for row in sh.table.rows:
                    for cell in row.cells:
                        parts.append(cell.text)
    return "\n".join(parts)


# Naming the old value as history is not a fault, it is the honest way to
# report that a measurement moved: "the four-corner study said 5.2 %" is a
# sentence the deck should keep. Only an unattributed number is stale.
CITED = re.compile(
    r"(four[- ]corner study said|n=4 said|earlier study said|previously|"
    r"superseded|used to (?:say|be)|was )\s*$", re.I)


def scan(name, text, olds):
    bad = []
    for old, why in olds:
        # a bare number must stand alone: "3.9 %" must not match "13.9 %",
        # and "46 %" must not match "97.46 %"
        pat = r"(?<![\d.])" + re.escape(old).replace(r"\ ", r"\s?")
        for m in re.finditer(pat, text):
            before = text[max(0, m.start() - 60):m.start()].replace("\n", " ")
            if CITED.search(before):
                continue
            seg = text[max(0, m.start() - 55):m.end() + 35].replace("\n", " ")
            bad.append((name, old, why, seg.strip()[:78]))
    return bad


def main():
    olds = superseded()
    if not olds:
        print("  RESULTS-SUMMARY.txt records no supersessions -- nothing to check")
        return 0
    print("  superseded values, from RESULTS-SUMMARY.txt:")
    for old, why in olds:
        print("     %-8s -> %s" % (old, why))

    bad = []
    for name in DECKS:
        p = os.path.join(HERE, name)
        if os.path.exists(p):
            bad += scan(name, deck_text(p), olds)
    for name in DOCS:
        p = os.path.join(HERE, name)
        if os.path.exists(p):
            bad += scan(name, open(p).read(), olds)

    if bad:
        print("\n  SUPERSEDED NUMBER STILL SHIPPING:")
        for name, old, why, seg in bad:
            print("    %-38s %-8s %s" % (name, old, why))
            print("       ...%s..." % seg)
        return 1
    print("  nothing shipping quotes a superseded number")
    return 0


if __name__ == "__main__":
    sys.exit(main())
