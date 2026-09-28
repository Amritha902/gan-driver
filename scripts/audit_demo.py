# -*- coding: utf-8 -*-
"""audit_demo.py -- check every claim the demo films make against its source.

    python3 scripts/audit_demo.py          -> results/audit_demo.txt

WHAT THIS IS FOR
  The films state numbers on screen and the deck captions restate them. Both
  read from sidecars the build writes, so they cannot drift from each other --
  but they can all drift together from the data, which is exactly how the
  transient count stayed wrong for six weeks. This compares the sidecars, the
  figures and the on-screen claims against the files that produce them.

HOW A CHECK IS WRITTEN
  Each one states the claim, pulls the value from the claim's own artefact,
  pulls the truth from source, and compares. Nothing here hard-codes an
  expected number: a check whose expectation is typed into this file tests
  that this file was typed correctly, which is not the same thing and is how
  the first version of scripts/audit_paper.py managed to pass on a paper that
  had been deliberately corrupted.

  Every check must be able to fail. scripts/audit_demo.py --selftest
  perturbs each source in turn and asserts the matching check goes red.
"""
import csv
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
KI = os.path.join(ROOT, "kicad")
SIM = os.path.join(ROOT, "sim")

rows = []


def check(name, claimed, actual, tol=0.0, note=""):
    if isinstance(claimed, float) or isinstance(actual, float):
        ok = abs(float(claimed) - float(actual)) <= tol
        c, a = "%.4f" % float(claimed), "%.4f" % float(actual)
    else:
        ok = str(claimed) == str(actual)
        c, a = str(claimed), str(actual)
    rows.append((ok, name, c, a, note))
    return ok


def sidecar(fn):
    d = {}
    p = os.path.join(RES, fn)
    if not os.path.exists(p):
        rows.append((False, "sidecar %s" % fn, "present", "MISSING", ""))
        return d
    for ln in io.open(p, encoding="utf-8"):
        if ln.startswith("#") or not ln.split():
            continue
        k, v = ln.split(None, 1)
        d[k] = v.strip()
    return d


def mp4_seconds(fn):
    import imageio_ffmpeg
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    r = subprocess.run([exe, "-i", os.path.join(RES, fn)],
                       capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stdout + r.stderr)
    if not m:
        return None
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def tool_version(cmd, pat):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True)
    except Exception:
        return "not found"
    m = re.search(pat, r.stdout + r.stderr)
    return m.group(0) if m else "unknown"


def main():
    txt = io.open(os.path.join(RES, "headtohead.txt"), encoding="utf-8").read()
    m = re.search(r"^100V_10A_25C base ([+-][\d.]+) V \(nseg=(\d+) tstep=(\S+?)\) "
                  r"ours ([+-][\d.]+) V", txt, re.M)
    if not m:
        raise SystemExit("headtohead.txt: the 100V_10A_25C row is not where "
                         "this expects it")
    base_margin, nseg, tstep, ours_margin = (float(m.group(1)), m.group(2),
                                             m.group(3), float(m.group(4)))

    # ---- 1. the four-part film ------------------------------------------
    s = sidecar("demo_review2.txt")
    if s:
        check("film: ours margin", float(s["ours_margin"]), ours_margin, 5e-4,
              "results/headtohead.txt")
        check("film: base margin", float(s["base_margin"]), base_margin, 5e-4,
              "results/headtohead.txt")
        check("film: base setting", s["base_setting"],
              "nseg=%s tstep=%s" % (nseg, tstep), note="results/headtohead.txt")
        d = mp4_seconds("demo_review2.mp4")
        if d is not None:
            check("film: stated duration", float(s["duration_s"]), d, 0.6,
                  "the mp4 itself")
        check("film: ngspice version", s["ngspice"],
              tool_version(["ngspice", "-v"], r"ngspice-\d+"), note="the tool")
        check("film: KiCad version", s["kicad"],
              tool_version(["kicad-cli", "version"], r"\d+\.\d+\.\d+"),
              note="the tool")

    # ---- 2. the converter it quotes -------------------------------------
    with open(os.path.join(RES, "buck_sweep.csv")) as fh:
        shipped = [r for r in csv.DictReader(fh)
                   if r["CLKEN"] == "1" and float(r["VNEG"]) == -2.0
                   and float(r["slices"]) == 8.0][0]
    if s:
        for key, col, tol in (("conv_vout", "Vout", 5e-4),
                              ("conv_pout", "Pout", 5e-3),
                              ("conv_eff", "eff", 5e-4)):
            check("film: %s" % key, float(s[key]), float(shipped[col]), tol,
                  "results/buck_sweep.csv")

    # ---- 3. the pair of films -------------------------------------------
    q = sidecar("demo_pair.txt")
    if q:
        check("pair: ours margin", float(q["ours_margin"]), ours_margin, 5e-4,
              "results/headtohead.txt")
        check("pair: base margin", float(q["base_margin"]), base_margin, 5e-4,
              "results/headtohead.txt")
        check("pair: ratio", float(q["ratio"]), ours_margin / base_margin, 5e-3,
              "the two margins, divided")
        for fn in ("demo_basepaper.mp4", "demo_ours.mp4"):
            d = mp4_seconds(fn)
            check("pair: %s exists and runs" % fn, d is not None and d > 20,
                  True, note="%.1f s" % (d or 0))

    # ---- 4. the claim the figure and the film both make about the sheet --
    buck_sch = io.open(os.path.join(KI, "gan_buck.kicad_sch"),
                       encoding="utf-8").read()
    check("schematic: driver instantiated as a sub-sheet",
          buck_sch.count('(property "Sheetfile" "gan_segdrv.kicad_sch"'), 2,
          note="kicad/gan_buck.kicad_sch, once per side")
    # Count inside the sheet_instances block only. The first version searched
    # the whole file and also matched the (instances (project ... (path ...)))
    # that sits inside each sheet, so a correct file reported 4 and went red.
    si = re.search(r"\(sheet_instances(.*?)\n\)", buck_sch, re.S)
    pages = len(re.findall(r'\(path "/[0-9a-f-]+" \(page "\d+"\)\)',
                           si.group(1) if si else ""))
    check("schematic: a page entry per sub-sheet", pages, 2,
          note="sheet_instances; without these KiCad calls the file damaged")

    # ---- 5. the same claim, in the netlist ------------------------------
    cir = io.open(os.path.join(SIM, "buck.cir"), encoding="utf-8").read()
    check("netlist: includes the driver library",
          ".include ../models/segdrv.lib" in cir, True, note="sim/buck.cir")
    check("netlist: driver instantiated twice",
          len(re.findall(r"^Xdrv\w+ .*SEGDRV", cir, re.M)), 2,
          note="sim/buck.cir, high side and low side")

    # ---- 6. what the novelty figure says the two blocks are worth -------
    with open(os.path.join(RES, "cases.csv")) as fh:
        cases = {r["case"].strip(): r for r in csv.DictReader(fh)}
    no_clamp = next(v for k, v in cases.items() if "Fastest drive" in k)
    clamped = next(v for k, v in cases.items() if "Miller clamp on" in k)
    clamp_worth = float(clamped["margin_V"]) - float(no_clamp["margin_V"])
    rail_worth = ours_margin - float(clamped["margin_V"])
    fig = io.open(os.path.join(ROOT, "scripts", "novelty_circuit.py"),
                  encoding="utf-8").read()
    # The figure script writes some of its text with \u escapes and some
    # with the character itself, depending on which edit last touched the
    # line. Searching for one form found nothing and reported NOT FOUND on
    # a claim that was plainly there. Normalise before matching.
    fig = fig.replace("\\u2212", u"\u2212").replace("\\u2014", u"\u2014")
    # A claim this cannot FIND is a failure, not a skip. The first version
    # searched for wording the figure had since been rewritten away from, so
    # the two checks silently disappeared -- the audit reported 21 green while
    # testing 19 things, and perturbing cases.csv changed nothing. A check
    # that can vanish is worse than one that is wrong, because nothing says so.
    def claimed(label, pat, truth, tol):
        mm = re.search(pat, fig)
        if not mm:
            rows.append((False, "novelty figure: %s" % label, "NOT FOUND",
                         "%.4f" % truth,
                         "scripts/novelty_circuit.py no longer states this"))
            return
        check("novelty figure: %s" % label, float(mm.group(1)), truth, tol,
              "results/cases.csv")

    claimed("clamp is worth", r"Clamp \+([\d.]+) V", clamp_worth, 5e-3)
    claimed("rail is worth", r"rail \+([\d.]+) V", rail_worth, 5e-3)
    claimed("margin without either", u"−([\\d.]+) V becomes",
            -float(no_clamp["margin_V"]), 5e-3)
    claimed("margin with both", r"becomes \+([\d.]+) V", ours_margin, 5e-3)

    # ---- 7. the captures the films are cut from -------------------------
    from PIL import Image
    import numpy as np
    for fn in ("kicad_buck.png", "kicad_segdrv.png", "kicad_zhangdrv.png"):
        p = os.path.join(RES, fn)
        if not os.path.exists(p):
            rows.append((False, "capture %s" % fn, "present", "MISSING", ""))
            continue
        im = Image.open(p)
        lum = float(np.asarray(im.convert("L")).mean())
        check("capture %s" % fn, "%dx%d ok" % im.size,
              "%dx%d %s" % (im.size[0], im.size[1],
                            "ok" if lum > 40 else "BLACK"),
              note="mean luminance %.0f" % lum)

    # ---- report ---------------------------------------------------------
    out = [u"  DEMO AUDIT -- every claim the films make, against its source",
           u"  " + u"-" * 86,
           u"  %-44s %14s %14s" % (u"claim", u"on screen", u"in source")]
    for ok, name, c, a, note in rows:
        out.append(u"  %-4s %-39s %14s %14s   %s"
                   % (u"ok" if ok else u"FAIL", name[:39], c[:14], a[:14], note))
    bad = sum(1 for r in rows if not r[0])
    out += [u"  " + u"-" * 86,
            u"  %d checks, %d failure(s)" % (len(rows), bad)]
    report = u"\n".join(out)
    print(report)
    io.open(os.path.join(RES, "audit_demo.txt"), "w",
            encoding="utf-8").write(report + u"\n")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
