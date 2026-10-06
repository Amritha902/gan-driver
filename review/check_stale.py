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
# Documents outside review/, relative to the repository root. The provenance
# walkthrough carried 5.2 / 25.1 / 3.9 / 13.4 unattributed for a month after
# the 36-corner study replaced them -- in the one document whose entire job is
# to say where a number comes from, and the one place nothing was scanning.
ROOT_DOCS = ["proof/WHERE-EVERY-NUMBER-COMES-FROM.md",
             "results/README-MATLAB.txt", "GUIDE.md", "HANDOFF.md",
             "README.md", "PROJECT-CLOSURE.md", "DOCS.md",
             "review/BINDU-QUESTIONS.md"]   # METHODOLOGY.md is in DOCS above

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
# The trailing class allows markdown emphasis and ordinary punctuation between
# the cue and the number:
# "the four-corner study said **25.1 %**" is an attributed figure, and a `\s*$`
# anchor missed it because of the two asterisks.
_CUE = (r"four[- ]corner study said|n=4 said|earlier study said|previously|"
        r"superseded|used to (?:say|be)|quoted|was ")
CITED = re.compile(r"(%s)[\s*_,:;\u2014\u2013-]*$" % _CUE, re.I)
# The same cue matched anywhere in the preceding window rather than against
# its end, plus the only thing allowed to sit between it and the number: a
# cue can attribute a LIST. "the four-corner study said 25.1 / 3.9 / 13.4 %"
# is one attributed sentence, and requiring the cue to touch every figure
# flagged the third while accepting the first two. Nothing but further
# numbers and the punctuation joining them may intervene, so a cue cannot
# reach across a sentence boundary and launder an unattributed figure.
CITED_ANY = re.compile(r"(%s)" % _CUE, re.I)
LIST_ONLY = re.compile(r"[\s*_,:;/%.\u2014\u2013-]*"
                       r"(?:\d[\d.]*\s*%?[\s*_,:;/\u2014\u2013-]*(?:and\s*)?)*")


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
            cue = CITED_ANY.search(before)
            if cue and LIST_ONLY.fullmatch(before[cue.end():]):
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
    # A file whose opening lines say SUPERSEDED is skipped, which is the rule
    # check_consistency.py already applies to the speech scripts. The one
    # legitimate place a retired number appears is the banner that retires it:
    # SPEECH-10-MINUTES.md opens by saying it quotes 3.9 % and that 3.9 % was
    # replaced by 2.6 %. Flagging that sentence failed BUILD-DECK.sh at its
    # last step on every run, which trains a reader to ignore the check --
    # worse than not having it.
    for name in DOCS:
        p = os.path.join(HERE, name)
        if not os.path.exists(p):
            continue
        txt = open(p).read()
        if "SUPERSEDED" in txt[:600]:
            print("  skipped %-34s its own banner says SUPERSEDED" % name)
            continue
        bad += scan(name, txt, olds)
    for rel in ROOT_DOCS:
        p = os.path.join(ROOT, rel)
        if os.path.exists(p):
            bad += scan(rel, open(p).read(), olds)

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
