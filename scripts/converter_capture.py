# -*- coding: utf-8 -*-
"""converter_capture.py -- the converter result, rendered from the script's
own output rather than screenshotted once and left to rot.

    python3 scripts/converter_capture.py

WHY THIS REPLACED A SCREENSHOT
  results/toolout/17-converter-power.png was a real capture of a terminal,
  taken by hand. That made it good evidence -- and unmaintainable. When
  bucksim.py's default off rail was corrected from 0 V to the -2 V the
  project actually ships, its efficiency moved from 97.70 % to 97.50 %, and
  the screenshot went on showing the old figure beside a caption carrying
  the new one. A panel reads the screen.

  This runs bucksim.py and renders its actual stdout, so the image cannot
  disagree with the script. It is the script's own output, not a desktop
  screenshot, and the deck's description of it says so.
"""
import os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from netlist_listing import render

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "results", "toolout", "17-converter-power.png")

r = subprocess.run([sys.executable, "scripts/bucksim.py"],
                   capture_output=True, text=True, cwd=ROOT, timeout=3600)
if r.returncode != 0:
    print(r.stderr[-800:])
    raise SystemExit("bucksim.py failed")

lines = ["$ python3 scripts/bucksim.py", ""]
lines += [l.rstrip() for l in r.stdout.splitlines() if l.strip()]
lines += ["",
          "# sim/buck.cir, 150 cycles, averaged over the last 10.",
          "# Shipped control word: clamp on, -2 V off rail."]

size = render(lines, OUT, width=2400, lh=42, fs=31, pad=44)
print("  written: results/toolout/17-converter-power.png  %dx%d" % size)
for l in lines:
    print("   " + l)
