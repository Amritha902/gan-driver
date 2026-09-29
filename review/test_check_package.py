# -*- coding: utf-8 -*-
"""test_check_package.py -- can the package check actually see a broken deck?

    python3 review/test_check_package.py

Breaks a copy of the presented deck three ways and confirms each is reported,
then confirms the real deck is reported clean. The first version of the
dangling-reference case rewrote an id that those slides do not contain, so it
mutated nothing, detected nothing, and passed. The mutation now reports the
part it changed, so a case that does not bite is visible.
"""
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_package as cp

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "GaN_Review2_PRESENT.pptx")
DST = "/tmp/test_check_package.pptx"
RID = re.compile(rb'(r:(?:id|embed|link)=")rId\d+(")')
SLIDE = re.compile(r"ppt/slides/slide\d+\.xml$")


def rebuild(mutate):
    if os.path.exists(DST):
        os.remove(DST)
    zin = zipfile.ZipFile(SRC)
    with zipfile.ZipFile(DST, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = mutate(item.filename, zin.read(item.filename))
            if data is not None:
                zout.writestr(item, data)


def dangling():
    hit = {"part": None}

    def mutate(name, data):
        if hit["part"] or not SLIDE.match(name):
            return data
        new, n = RID.subn(rb'\1rId999\2', data, count=1)
        if n:
            hit["part"] = name
        return new
    rebuild(mutate)
    return hit["part"]


def malformed():
    target = {"part": None}

    def mutate(name, data):
        if SLIDE.match(name) and not target["part"]:
            target["part"] = name
            return data.replace(b"</p:sld>", b"</p:sld")
        return data
    rebuild(mutate)
    return target["part"]


def no_rels():
    target = {"part": None}

    def mutate(name, data):
        if name.startswith("ppt/slides/_rels/") and not target["part"]:
            target["part"] = name
            return None
        return data
    rebuild(mutate)
    return target["part"]


def main():
    bad = 0
    for label, break_it in [("dangling r:id", dangling),
                            ("malformed slide XML", malformed),
                            ("a slide's .rels removed", no_rels)]:
        touched = break_it()
        _, problems = cp.check(DST)
        ok = bool(touched) and bool(problems)
        bad += 0 if ok else 1
        print("  %-4s %-26s %s"
              % ("PASS" if ok else "FAIL", label,
                 problems[0][:70] if problems
                 else ("mutation hit nothing" if not touched else "NOT DETECTED")))

    _, problems = cp.check(SRC)
    ok = not problems
    bad += 0 if ok else 1
    print("  %-4s %-26s %s" % ("PASS" if ok else "FAIL", "the real deck",
                               "reported clean" if ok else problems[0][:70]))
    if os.path.exists(DST):
        os.remove(DST)
    print("\n  %s" % ("all checks behaved as expected" if not bad
                      else "%d CHECK(S) FAILED" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
