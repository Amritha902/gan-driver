# -*- coding: utf-8 -*-
"""implementation_shots.py -- the implementation, as separate named files.

    python3 scripts/implementation_shots.py   -> implementation/*.png + README

Everything this project built, one file per thing, at a resolution that holds
up full screen. They are rendered from the sources rather than screenshotted:
the KiCad sheets come out of the PDFs KiCad itself plots, which are vector, so
a 200 dpi render is genuinely sharp rather than an upscaled screen grab. The
2560x1440 eeschema captures elsewhere in this project exist to prove the
application was open; these exist to be read.

Regenerating is the whole point. Change a netlist, run the generators, run
this, and every picture follows -- nothing here is a file somebody exported
once and forgot.
"""
import os
import shutil
import sys

import fitz
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "implementation")
RES = os.path.join(ROOT, "results")
KI = os.path.join(ROOT, "kicad")

DPI = 200

# (output name, source, page, what it is)
SHEETS = [
    ("01-converter-schematic.png", "kicad/gan_buck.pdf", 0,
     "The synchronous buck converter, root sheet. Drawn from sim/buck.cir by "
     "scripts/kicad_schematic.py, so every value on it is the netlist's."),
    ("02-gate-driver-high-side.png", "kicad/gan_buck.pdf", 1,
     "The high-side gate driver, as a hierarchical sub-sheet of the converter."),
    ("03-gate-driver-low-side.png", "kicad/gan_buck.pdf", 2,
     "The low-side gate driver. The same sheet file as the high side, placed "
     "twice -- one instance per gate."),
    ("04-driver-proposed.png", "kicad/gan_segdrv.pdf", 0,
     "The proposed segmented gate driver: eight pull-up slices, eight "
     "pull-down, an active Miller clamp and an off rail selectable to -2 V."),
    ("05-driver-base-paper.png", "kicad/gan_zhangdrv.pdf", 0,
     "The base paper's driver as reimplemented here: seven slices a bank in "
     "two stages, one bias resistor, no clamp, off rail tied to reference."),
]

COPIES = [
    ("06-driver-block-diagram.png", "results/fig_drawio_segmented_driver.png",
     "The segmented driver as a block diagram, rendered from "
     "kicad/gan_driver.drawio."),
    ("07-segmented-driver-source.png", "results/fig_code_segdrv.png",
     "models/segdrv.lib, the SPICE implementation of the driver."),
    ("08-gan-hemt-model-source.png", "results/fig_code_egan.png",
     "models/egan.lib, the behavioural GaN HEMT model written from the "
     "EPC2010C datasheet."),
    ("09-novelty-on-the-circuit.png", "results/fig_novelty_circuit.png",
     "What the proposed driver has that the base paper's does not, ringed on "
     "the sheets themselves."),
    ("10-both-drivers-side-by-side.png", "results/fig_schematics_pair.png",
     "Both driver sheets whole, at the same scale, nothing ringed."),
]


def render(src, page, dest):
    d = fitz.open(os.path.join(ROOT, src))
    if page >= d.page_count:
        raise SystemExit("%s has %d page(s), wanted %d"
                         % (src, d.page_count, page + 1))
    pm = d[page].get_pixmap(dpi=DPI)
    pm.save(dest)
    return pm.width, pm.height


def main():
    if not os.path.isdir(OUT):
        os.makedirs(OUT)
    rows = []

    for name, src, page, what in SHEETS:
        p = os.path.join(ROOT, src)
        if not os.path.exists(p):
            print("  MISSING source: %s" % src)
            continue
        dest = os.path.join(OUT, name)
        w, h = render(src, page, dest)
        rows.append((name, "%s page %d" % (src, page + 1), w, h, what))
        print("  %-36s %5dx%-5d from %s p%d" % (name, w, h, src, page + 1))

    for name, src, what in COPIES:
        p = os.path.join(ROOT, src)
        if not os.path.exists(p):
            print("  MISSING source: %s" % src)
            continue
        dest = os.path.join(OUT, name)
        shutil.copyfile(p, dest)
        w, h = Image.open(dest).size
        rows.append((name, src, w, h, what))
        print("  %-36s %5dx%-5d from %s" % (name, w, h, src))

    with open(os.path.join(OUT, "README.md"), "w") as fh:
        fh.write("# Implementation\n\n")
        fh.write("Every picture here is generated. Run "
                 "`python3 scripts/implementation_shots.py` after changing a "
                 "netlist or a model and they all follow; nothing in this "
                 "folder is a one-off export.\n\n")
        fh.write("The KiCad sheets are rendered from the PDFs KiCad plots, "
                 "which are vector, at %d dpi. The 2560x1440 captures in "
                 "`results/` are screen photographs of eeschema itself and "
                 "exist to show the application was open; these exist to be "
                 "read.\n\n" % DPI)
        fh.write("| file | source | pixels | what it is |\n")
        fh.write("|---|---|---|---|\n")
        for name, src, w, h, what in rows:
            fh.write("| [`%s`](%s) | `%s` | %d x %d | %s |\n"
                     % (name, name, src, w, h, what))
    print("  wrote implementation/README.md  (%d file(s))" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
