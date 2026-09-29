# -*- coding: utf-8 -*-
"""link_pass.py -- every file the deck names, clickable on GitHub.

    python3 review/link_pass.py

The slides cite the thing behind each claim by path: sim/buck.cir for the
converter, models/egan.lib for the GaN HEMT model, rtl/seg_gate_ctrl.v for
the Verilog, scripts/headtohead.py for the comparison that produced the
numbers. That citation is the deck's whole argument -- every figure says
which file made it -- and it was inert text. A reviewer who wants to check a
claim had to retype the path.

Each one is now a hyperlink into the repository at the exact file, along with
the repository address itself and the IEEE references.

TWO GUARDS, AND THE SECOND IS THE USEFUL ONE
  1. A URL or path left unlinked fails the build.
  2. Anything on a slide that reads like a repository path but is not a
     tracked file fails the build. A deck that cites a file which is not in
     the repository is making a claim the panel cannot check -- whether
     because the path is a typo, or because the file was never committed.
     The link target is resolved against `git ls-files`, so a link that
     builds is a link that resolves.
"""
import os
import re
import subprocess
import sys
from copy import deepcopy

from pptx import Presentation
from pptx.oxml.ns import qn
from pptx.text.text import _Run

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

DECKS = ["GaN_Review2_PRESENT.pptx", "GaN_Review2_BACKUP.pptx",
         "Review2_GaN_Segmented_Gate_Driver.pptx"]

# A host with a real TLD, optionally with a path. Deliberately narrow so it
# cannot match "V/ns" or "Fig. 14".
URL = re.compile(
    r"(?:https?://)?(?:www\.)?"
    r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
    r"(?:\.[A-Za-z0-9-]+)*"
    r"\.(?:com|org|net|io|ai|dev|edu|gov|co)"
    r"(?:/[^\s,;]*[^\s,;.])?")

# A candidate path. Membership of the tracked set decides, not the shape, so
# this only has to be permissive enough to catch the token.
TOKEN = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_./\-]*")

# Shaped like a repo path -- a slash and a file extension. Used only to
# decide whether an unrecognised token is a broken citation or ordinary text
# such as "124 V/ns".
PATHLIKE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_./\-]*/[A-Za-z0-9_\-]+"
                      r"\.[A-Za-z0-9]{1,6}$")


def repo_url():
    """The https base for this repository, from the remote rather than typed."""
    out = subprocess.check_output(
        ["git", "remote", "get-url", "origin"], cwd=ROOT).decode("utf-8").strip()
    out = re.sub(r"^git@([^:]+):", r"https://\1/", out)
    return re.sub(r"\.git$", "", out)


def branch():
    return subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=ROOT).decode("utf-8").strip()


def tracked_paths():
    """Every file git tracks, and every directory implied by one."""
    files = set(subprocess.check_output(
        ["git", "ls-files"], cwd=ROOT).decode("utf-8").split("\n")) - {""}
    dirs = set()
    for f in files:
        bits = f.split("/")
        for i in range(1, len(bits)):
            dirs.add("/".join(bits[:i]))
    return files, dirs


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


class Links(object):
    def __init__(self):
        base = repo_url()
        self.blob = "%s/blob/%s/" % (base, branch())
        self.tree = "%s/tree/%s/" % (base, branch())
        self.files, self.dirs = tracked_paths()

    def spans(self, text):
        """[(start, end, href)] for every URL and repository path in `text`."""
        out, taken = [], set()
        for m in URL.finditer(text):
            href = m.group(0)
            out.append((m.start(), m.end(),
                        href if href.startswith("http") else "https://" + href))
            taken.update(range(m.start(), m.end()))

        for m in TOKEN.finditer(text):
            if any(i in taken for i in range(m.start(), m.end())):
                continue
            tok = m.group(0)
            # a path at the end of a sentence carries the full stop
            for cut in (0, 1, 2):
                cand = tok[:len(tok) - cut] if cut else tok
                if "/" not in cand:
                    break
                if cand in self.files:
                    out.append((m.start(), m.start() + len(cand),
                                self.blob + cand))
                    break
                if cand in self.dirs:
                    out.append((m.start(), m.start() + len(cand),
                                self.tree + cand))
                    break
        out.sort()
        return out

    def broken(self, text):
        """Tokens shaped like a repository path that git does not track."""
        bad, taken = [], set()
        for m in URL.finditer(text):
            taken.update(range(m.start(), m.end()))
        for m in TOKEN.finditer(text):
            if any(i in taken for i in range(m.start(), m.end())):
                continue
            tok = m.group(0).rstrip(".,")
            if tok in self.files or tok in self.dirs:
                continue
            if PATHLIKE.match(tok):
                bad.append(tok)
        return bad


def link_whole_run(run, href):
    if run.hyperlink.address:
        return 0
    run.hyperlink.address = href
    return 1


def split_and_link(para, run, spans):
    """Replace one run with a sequence of runs, linking the cited pieces.

    A path almost always sits inside a sentence, so the run holding it also
    holds ordinary prose and cannot simply be given an address. The run
    element is cloned once per segment, which carries every formatting
    property across unchanged -- size, weight, colour -- and only the text
    and the hyperlink differ between the clones.
    """
    text = run.text
    segs, pos = [], 0
    for start, end, href in spans:
        if start > pos:
            segs.append((text[pos:start], None))
        segs.append((text[start:end], href))
        pos = end
    if pos < len(text):
        segs.append((text[pos:], None))

    r = run._r
    parent = r.getparent()
    idx = list(parent).index(r)

    made, fresh = 0, []
    for seg_text, href in segs:
        nr = deepcopy(r)
        rPr = nr.find(qn("a:rPr"))
        if rPr is not None:
            for h in rPr.findall(qn("a:hlinkClick")):
                rPr.remove(h)      # never inherit the neighbour's address
        nr.find(qn("a:t")).text = seg_text
        fresh.append((nr, href))

    parent.remove(r)
    for off, (nr, _) in enumerate(fresh):
        parent.insert(idx + off, nr)
    for nr, href in fresh:
        if href:
            _Run(nr, para).hyperlink.address = href
            made += 1
    return made


def main():
    links = Links()
    total, failures = 0, []
    print("  linking into %s" % links.blob)

    for name in DECKS:
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            continue
        prs = Presentation(path)
        n = 0
        for para in all_paragraphs(prs):
            # Splitting a run rebuilds it from clones, so the one thing that
            # must never change is the text itself. Checked per paragraph
            # rather than trusted: a character dropped or doubled inside a
            # caption would be invisible in a diff of the .pptx and would
            # reach the panel on the slide.
            was = "".join(r.text for r in para.runs)
            for run in list(para.runs):
                spans = links.spans(run.text)
                if not spans:
                    continue
                if (len(spans) == 1
                        and run.text.strip() == run.text[spans[0][0]:spans[0][1]]):
                    n += link_whole_run(run, spans[0][2])
                else:
                    n += split_and_link(para, run, spans)
            now = "".join(r.text for r in para.runs)
            if now != was:
                failures.append((name, was[:50], "TEXT CHANGED while linking"))
        prs.save(path)
        total += n

        # read back: is every citation on every slide now clickable, and does
        # every one of them point at a file that exists?
        prs = Presentation(path)
        for para in all_paragraphs(prs):
            for run in para.runs:
                if links.spans(run.text) and not run.hyperlink.address:
                    failures.append((name, run.text.strip()[:60],
                                     "citation is not a link"))
            body = "".join(r.text for r in para.runs)
            for tok in links.broken(body):
                failures.append((name, tok, "cited but not tracked by git"))
        print("  %-42s %3d link(s)" % (name, n))

    print("  %d link(s) across %d deck(s)" % (total, len(DECKS)))
    if failures:
        print("\n  BROKEN CITATIONS:")
        for name, what, why in sorted(set(failures)):
            print("    %-28s %-46s %s" % (name, what, why))
        return 1
    print("  every citation on a slide is a hyperlink to a tracked file")
    return 0


if __name__ == "__main__":
    sys.exit(main())
