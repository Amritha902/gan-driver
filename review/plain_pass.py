# -*- coding: utf-8 -*-
"""plain_pass.py -- take the conversational register out of the presented deck.

    python3 review/plain_pass.py

WHY THIS IS A PASS AND NOT AN EDIT
  The slide text is written across two thousand lines of rebuild_pass.py, and
  this session has already broken that file twice with anchored edits. A pass
  over the BUILT deck is safer: it rewrites a table of phrases, then scans for
  the register it was meant to remove and exits non-zero if any survives. The
  guard is the point -- without it the next slide someone adds reintroduces
  the same voice and nobody notices.

WHAT COUNTS AS THE WRONG REGISTER
  Four things, and they are all failures of the same kind -- the deck talking
  about itself or about the room instead of stating the engineering:

    self-reference      "the two you asked for", "click to play"
    stage direction     "if the room will not cooperate", "on whatever
                        machine is in this room"
    editorialising      "which is the honest shape of the result", "the
                        weights are on the slide so they can be argued with"
    shouting            BEST, FOR IT -- emphasis by capital letters

  A review panel reads a slide as a claim. Anything on it that is not a claim
  is noise, and noise on a technical slide reads as padding.
"""
import io
import os
import re
import sys

from pptx import Presentation

HERE = os.path.dirname(os.path.abspath(__file__))

DECKS = ["GaN_Review2_PRESENT.pptx", "GaN_Review2_BACKUP.pptx",
         "Review2_GaN_Segmented_Gate_Driver.pptx"]

# (what it says now, what it should say). Longest first: a shorter pattern
# that is a substring of a longer one would otherwise fire first and leave
# the tail behind.
REWRITE = [
    # ---- titles -------------------------------------------------------
    (u"Latency and device power — the two you asked for",
     u"Latency and device power"),
    (u"Or we can run it now", u"The same simulation, run live"),
    (u"Demo — the driver, built and measured, on this machine",
     u"Demo — the driver, built and measured"),

    # ---- stage direction ----------------------------------------------
    (u"on whatever machine is in this room.", u"on the presentation machine."),
    (u"the recording, if the room will not cooperate",
     u"recorded run of the same command"),
    (u"what it draws when it does", u"the waveforms it produces"),
    (u". Click to play.", u"."),
    (u", click to play,", u","),
    # Cut the whole clause, not just the words: dropping "click to play"
    # alone left "Four sections, 100 s, The circuit as its KiCad sheet".
    (u", click to play. ", u". "),

    # ---- film jargon ---------------------------------------------------
    (u"The same four beats over our driver.",
     u"The same sequence over our driver."),
    (u"Four parts, ", u"Four sections, "),
    (u"the output with what to look at pointed at",
     u"the output with the threshold, the peak and the margin annotated"),

    # ---- self-reference and editorialising -----------------------------
    (u"Here is exactly what is held and exactly what moves.",
     u"The following is held identical; the listed parameter is the only one "
     u"that varies."),
    (u" rather than chosen by us", u""),
    (u"found BEST for their driver", u"found optimal for their driver"),
    (u"best FOR IT", u"optimal for it"),
    (u" — which is the honest shape of the result", u""),
    (u"so the two can be compared by eye", u"so the two are directly comparable"),
    (u"so nothing else can be moving", u"so no other parameter varies"),
    (u"The weights are on the slide so they can be argued with.",
     u"The weights are stated so the total can be checked."),
    (u"The weights are on this slide because we would rather they were "
     u"argued with than discovered.",
     u"The weights are stated so the total can be recomputed."),
    (u"Counted, not asserted. ", u""),
    (u"Simulating harder will not deliver either.",
     u"Neither can be obtained by further simulation."),
    (u"because a clamp does not care how hot the",
     u"because the clamp's action is independent of how hot the"),
    # ---- editorialising in the long decks -------------------------------
    (u"Read the last row honestly: GaN loses it.",
     u"GaN loses the last row."),
    (u"The honest answer is two-part, and the second part is the one to say.",
     u"The answer is two-part."),
    (u"the 8.9 % headline IS weight-dependent",
     u"the 8.9 % headline is weight-dependent"),
    (u"Two runs of ONE circuit file.", u"Two runs of one circuit file."),
    (u"the shaded gap between them IS the adaptive gain",
     u"the shaded gap between them is the adaptive gain"),
    (u"what WE fill", u"what we fill"),
    (u"This is the whole of the remaining honest risk.",
     u"This is the whole of the remaining risk."),
    (u"The honest summary is that the architecture is finished",
     u"In summary: the architecture is finished"),
]

# What must not survive. Each is a regex; a match fails the build.
#
# Two lists, because case matters for one kind and not the other. "best
# setting" is ordinary English and must pass; BEST as emphasis must not. A
# single case-insensitive list cannot tell them apart -- the first version of
# this file had one, and it failed the build on nine correct slides.
BANNED_ANY_CASE = [
    (r"you asked for", "self-reference to a previous review"),
    (r"click to play", "stage direction"),
    (r"in this room", "stage direction"),
    (r"will not cooperate", "stage direction"),
    (r"argued with", "editorialising"),
    (r"we would rather", "editorialising"),
    (r"\bhonest(ly)?\b", "editorialising"),
    (r"\bbeats\b", "film jargon"),
    (r"by eye", "informal"),
    (r"\bbro\b|\byeah\b|\bokay\b|\buk\b|\bstuff\b", "conversational"),
]

# Emphasis by capital letters -- "the headline IS weight-dependent", "what
# WE fill". A technical deck is full of capitals that are not shouting, so
# only a word that has no meaning in capitals counts. Everything else is
# excluded by construction:
#
#   an acronym       FPGA, HEMT, IEEE, LUT, FF     -- not in the list
#   a signal or node  HSG, LSG, CLKEN, VNEG        -- not in the list
#   a file or path    LIVE-SIM.sh, RESULTS-SUMMARY -- identifier characters
#                                                     on either side
#   a number          23BEC1447                    -- a digit alongside
#   a table header    THE ONE THING THAT MOVES     -- the whole run is caps
#   a quotation       "tied to ref - NO negative   -- inside quote marks;
#                     rail" (their sheet label)       their capitals, not ours
#
# An earlier version tried to infer this instead -- flag any capitalised word
# the deck also uses in lower case -- and returned 28 findings of which 4 were
# real. Inference that wrong is worse than a list, because a check that cries
# wolf gets switched off.
SHOUT_WORDS = set("""
IS ARE WAS WERE BE NOT NO NONE ALL ANY EVERY EACH BOTH NEVER ALWAYS ONLY JUST
MUST SHOULD CAN CANNOT WILL WOULD DOES DID DO
WE OUR US THEY THEIR THEM YOU YOUR MY
BEST WORST BETTER WORSE MORE LESS MOST LEAST SAME REAL TRUE FALSE
ONE TWO FIRST LAST NOW THEN HERE THERE THIS THAT THESE THOSE
VERY MUCH MANY FEW BIG HUGE TINY WHOLE ENTIRE ACTUALLY REALLY
""".split())

# Identifier characters either side disqualify a match, so FOO_BAR, a-b and
# path/NAME.ext never register.
# Two letters minimum: a lone capital is physics notation (I, V, R, Q), not
# emphasis.
SHOUT = re.compile(r"(?<![A-Za-z0-9_\-/.])([A-Z]{2,9})(?![A-Za-z0-9_\-/.])")

# Straight and curly quotes, and anything between them.
QUOTED = re.compile(u"[\"\u201c\u2018'][^\"\u201d\u2019']{0,200}[\"\u201d\u2019']")


def shouted(run_text, _unused=None):
    """The words in one run that read as emphasis by capital letters."""
    letters = [c for c in run_text if c.isalpha()]
    if letters and all(c.isupper() for c in letters):
        return []                       # a label or a table header
    masked = QUOTED.sub(lambda m: " " * len(m.group(0)), run_text)
    return [m.group(1) for m in SHOUT.finditer(masked)
            if m.group(1) in SHOUT_WORDS]


def all_paragraphs(prs):
    """Every paragraph in every text frame and table cell of the deck."""
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


def all_runs(prs):
    for para in all_paragraphs(prs):
        for run in para.runs:
            yield run


def para_text(para):
    return "".join(r.text for r in para.runs)


def replace_in_paragraph(para, old, new):
    """Replace `old` with `new` even when it straddles run boundaries.

    PowerPoint splits a sentence into runs wherever the formatting changes,
    and a spell-check pass will split it in the middle of a word for no
    reason at all. A phrase can therefore be plainly visible on the slide and
    invisible to any single run. The first version of this pass worked run by
    run and silently skipped four rewrites because of it -- the guard caught
    that, which is the whole reason the guard exists.

    Only the runs the match actually touches are edited: the replacement goes
    into the first of them and the remainder of the match is cut out of the
    others, so every run the match does not reach keeps its own formatting.
    Bold figures elsewhere in the paragraph survive, which matters because
    check_consistency.py reads them.
    """
    runs = para.runs
    if not runs:
        return 0
    n = 0
    while True:
        texts = [r.text for r in runs]
        at = "".join(texts).find(old)
        if at < 0:
            return n

        # walk the runs to find where the match starts and ends
        spans, pos = [], 0
        for t in texts:
            spans.append((pos, pos + len(t)))
            pos += len(t)
        end = at + len(old)
        first = next(i for i, (a, b) in enumerate(spans) if a <= at < b or
                     (a == b == at))
        last = next(i for i, (a, b) in enumerate(spans) if a < end <= b)

        head = texts[first][:at - spans[first][0]]
        tail = texts[last][end - spans[last][0]:]
        if first == last:
            runs[first].text = head + new + tail
        else:
            runs[first].text = head + new
            for i in range(first + 1, last):
                runs[i].text = ""
            runs[last].text = tail
        n += 1
        if new and old in new:       # would match itself for ever
            return n


def main():
    total, failures = 0, []
    for name in DECKS:
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            continue
        # Normalise the package before reading it. The earlier passes build
        # each deck by editing a zip in place, and that leaves duplicate
        # entries behind -- 16 of them, which is what the "Duplicate name:
        # ppt/slides/slideN.xml.rels" warnings during the build are. A reader
        # resolves a duplicated relationship to one of the two copies, so a
        # slide can be live in the running order while the text this pass
        # sees for it is the shadowed copy: slide 59 of the backup deck read
        # as 73 slides, counted as live, and still hid a sentence that was
        # plainly in slide59.xml. Opening and saving once rewrites every part
        # exactly once, after which the deck reads the way it prints.
        Presentation(path).save(path)

        prs = Presentation(path)
        n = 0
        for para in all_paragraphs(prs):
            before = para_text(para)
            if not before:
                continue
            for a, b in REWRITE:
                if a in para_text(para):
                    n += replace_in_paragraph(para, a, b)
        prs.save(path)
        total += n

        # read back what was actually saved, not what we think we wrote
        prs = Presentation(path)
        text = "\n".join(para_text(p) for p in all_paragraphs(prs))
        for pat, why in BANNED_ANY_CASE:
            for m in re.finditer(pat, text, re.I):
                line = text[max(0, m.start() - 60):m.end() + 40].replace("\n", " ")
                failures.append((name, m.group(0), why, line.strip()))

        for para in all_paragraphs(prs):
            body = para_text(para)
            for word in shouted(body):
                failures.append((name, word, "emphasis by capital letters",
                                 body.strip()))
        print("  %-42s %3d rewrite(s)" % (name, n))

    print("  %d rewrites across %d deck(s)" % (total, len(DECKS)))
    if failures:
        print("\n  BANNED PHRASING SURVIVED:")
        for name, hit, why, line in failures:
            print("    %-28s %-14s %s" % (name, repr(hit), why))
            print("      ...%s..." % line[:110])
        return 1
    print("  no banned phrasing found")
    return 0


if __name__ == "__main__":
    sys.exit(main())
