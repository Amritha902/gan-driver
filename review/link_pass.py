# -*- coding: utf-8 -*-
"""link_pass.py -- make every URL printed on a slide an actual hyperlink.

    python3 review/link_pass.py

The repository address appears on the closing slide and on the "where the
work lives" slide. It was set as plain bold text, so it read like a link and
did nothing when clicked -- which is worse than not showing it, because the
one thing a reviewer might do with it is click it.

This attaches the real address to the run and then fails if any URL on any
slide is still unlinked, so a new slide cannot reintroduce dead link text.
"""
import os
import re
import sys

from pptx import Presentation

HERE = os.path.dirname(os.path.abspath(__file__))

DECKS = ["GaN_Review2_PRESENT.pptx", "GaN_Review2_BACKUP.pptx",
         "Review2_GaN_Segmented_Gate_Driver.pptx"]

# Deliberately narrow: a host with a real TLD, optionally followed by a path.
# It must not match "scripts/live_demo.py", "sim/buck.cir" or "Fig. 14".
URL = re.compile(
    r"(?:https?://)?(?:www\.)?"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9-]+)*"
    r"\.(?:com|org|net|io|ai|dev|edu|gov|co)"
    r"(?:/[^\s,;]*[^\s,;.])?")


def address(text):
    """The href for link text as printed."""
    text = text.strip()
    return text if text.startswith("http") else "https://" + text


def all_paragraphs(prs):
    for sl in prs.slides:
        for sh in sl.shapes:
            if sh.has_text_frame:
                for para in sh.text_frame.paragraphs:
                    yield para
            if getattr(sh, "has_table", False) and sh.has_table:
                for row in sh.table.rows:
                    for cell in row.cells:
                        for para in cell.text_frame.paragraphs:
                            yield para


def main():
    total, failures = 0, []
    for name in DECKS:
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            continue
        prs = Presentation(path)
        n = 0
        for para in all_paragraphs(prs):
            for run in para.runs:
                m = URL.search(run.text)
                if not m:
                    continue
                # Only a run that is the URL and nothing else can be linked
                # without splitting it. Splitting a run means rebuilding its
                # formatting by hand, and the two URLs in this deck are
                # already their own runs, so the pass refuses instead of
                # guessing -- and the guard below turns that refusal into a
                # failed build rather than a silently dead link.
                if run.text.strip() != m.group(0):
                    failures.append((name, m.group(0),
                                     "URL shares a run with other text",
                                     run.text.strip()))
                    continue
                if run.hyperlink.address:
                    continue
                run.hyperlink.address = address(m.group(0))
                n += 1
        prs.save(path)
        total += n

        # read back: is every URL on every slide now clickable?
        prs = Presentation(path)
        for para in all_paragraphs(prs):
            for run in para.runs:
                m = URL.search(run.text)
                if m and not run.hyperlink.address:
                    failures.append((name, m.group(0), "still not a link",
                                     run.text.strip()))
        print("  %-42s %3d link(s) attached" % (name, n))

    print("  %d link(s) across %d deck(s)" % (total, len(DECKS)))
    if failures:
        print("\n  DEAD LINK TEXT:")
        for name, url, why, line in failures:
            print("    %-28s %-34s %s" % (name, url, why))
            print("      ...%s..." % line[:100])
        return 1
    print("  every URL on a slide is a real hyperlink")
    return 0


if __name__ == "__main__":
    sys.exit(main())
