# -*- coding: utf-8 -*-
"""check_package.py -- is each .pptx a structurally sound package?

    python3 review/check_package.py

The passes in this directory edit slide XML directly: plain_pass rewrites run
text across run boundaries, link_pass takes runs apart and rebuilds them from
clones, prune_orphans deletes parts and relationships. Each of those can
produce a file that python-pptx still opens happily and PowerPoint offers to
repair, which is not something to discover in the review room.

So, for every slide: the XML parses, and every relationship id it references
exists in that slide's .rels.

The one legitimate empty reference is `<a:hlinkClick r:id=""
action="ppaction://media"/>`, which is how a media placeholder says "clicking
me plays this". It has no relationship to point at, by design.
"""
import os
import re
import sys
import zipfile

from lxml import etree

HERE = os.path.dirname(os.path.abspath(__file__))
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
SLIDE = re.compile(r"ppt/slides/slide\d+\.xml$")

DECKS = ["GaN_Review2_PRESENT.pptx", "GaN_Review2_BACKUP.pptx",
         "Review2_GaN_Segmented_Gate_Driver.pptx"]


def refs(el):
    """Relationship ids this element points at, excluding the media idiom."""
    out = []
    for key, val in el.attrib.items():
        if not key.startswith(R):
            continue
        if val == "" and str(el.attrib.get("action", "")).startswith("ppaction://"):
            continue
        out.append(val)
    return out


def check(path):
    z = zipfile.ZipFile(path)
    parts = set(z.namelist())
    problems, slides = [], 0

    for name in z.namelist():
        if not (name.endswith(".xml") or name.endswith(".rels")):
            continue
        try:
            root = etree.fromstring(z.read(name))
        except Exception as exc:
            problems.append("%s does not parse: %s" % (name, exc))
            continue

        if not SLIDE.match(name):
            continue
        slides += 1

        rels_name = name.replace("slides/", "slides/_rels/") + ".rels"
        if rels_name not in parts:
            problems.append("%s has no .rels part" % name)
            continue
        rels = etree.fromstring(z.read(rels_name))
        have = {r.get("Id") for r in rels}

        used = set()
        for el in root.iter():
            used.update(refs(el))
        for rid in sorted(used - have):
            problems.append("%s references %s, which its .rels does not define"
                            % (name, rid or "an empty id"))

        for r in rels:
            if not r.get("Target"):
                problems.append("%s: relationship %s has no target"
                                % (rels_name, r.get("Id")))
    return slides, problems


def main():
    bad = 0
    for name in DECKS:
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            continue
        slides, problems = check(path)
        if problems:
            bad += len(problems)
            print("  %s" % name)
            for p in problems:
                print("     %s" % p)
        else:
            print("  %-42s %2d slides, package sound" % (name, slides))
    if bad:
        print("\n  %d structural problem(s)" % bad)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
