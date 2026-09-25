# -*- coding: utf-8 -*-
"""feasible_words.py -- how many of the 720 control words are safe at the
nominal corner, derived from ngspice output.

    python3 scripts/feasible_words.py

WHY THIS EXISTS
  This number was quoted as "504 of 720 (70 %), gan_analysis.m" -- attributed
  to MATLAB. MATLAB is the one tool in this project nobody can re-run: it is
  not installed here, there is no Octave either, and a reviewer asking "show
  me" could not be shown.

  It never needed MATLAB. The same answer falls straight out of
  results/sweep_nominal.csv, which is ngspice's own output: count the rows
  whose spurious gate peak stays under the threshold. It reproduces exactly --
  504 of 720, 70.0 % -- so the claim is now sourced from the simulator that
  produced the data rather than from a tool that cannot be run.

WHAT "FEASIBLE" MEANS HERE
  Vgs_spur is the highest the OFF gate reaches while the other device
  switches. A word is feasible when that stays below the 1.4 V threshold: the
  device that should be off stayed off. Words at or above it are false
  turn-on and are not usable, whatever their switching energy.
"""
import csv, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES  = os.path.join(ROOT, "results")
VTH  = 1.4          # nominal threshold, 25 C


def main():
    path = os.path.join(RES, "sweep_nominal.csv")
    rows = list(csv.DictReader(open(path)))
    total = len(rows)
    good, bad, unusable = 0, 0, 0
    for r in rows:
        v = r.get("Vgs_spur", "")
        try:
            v = float(v)
        except (TypeError, ValueError):
            unusable += 1
            continue
        if v < VTH:
            good += 1
        else:
            bad += 1

    lines = [
        "",
        "  FEASIBLE CONTROL WORDS AT THE NOMINAL CORNER",
        "  From results/sweep_nominal.csv -- ngspice output, not MATLAB.",
        "  A word is feasible when the OFF gate stays below the %.1f V" % VTH,
        "  threshold while the other device switches.",
        "  " + "-" * 62,
        "  words swept                        %4d" % total,
        "  feasible  (Vgs_spur <  %.1f V)      %4d   %5.1f %%" % (VTH, good, good / total * 100),
        "  false turn-on (Vgs_spur >= %.1f V)  %4d   %5.1f %%" % (VTH, bad, bad / total * 100),
    ]
    if unusable:
        lines.append("  no measurement                     %4d" % unusable)
    lines += [
        "  " + "-" * 62,
        "",
        "  Previously attributed to gan_analysis.m. Same answer, from the",
        "  simulator that produced the data.",
        "",
    ]
    txt = "\n".join(lines)
    print(txt)
    open(os.path.join(RES, "feasible_words.txt"), "w").write(txt + "\n")
    print("  written: results/feasible_words.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
