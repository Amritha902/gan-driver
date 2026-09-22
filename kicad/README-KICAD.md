# KiCad schematics

Real KiCad 7 schematics, not images. `gan_buck.kicad_sch` opens in eeschema
and is editable.

## Why it is generated, not drawn

Component values in this project move. `RDEC` went from 20 mΩ to 1 Ω after
the 200 V shoot-through investigation, and a sheet drawn by hand in a GUI
would still be showing 20 mΩ. `scripts/kicad_schematic.py` reads the values
out of `sim/buck.cir` at build time, so the schematic and the circuit that
was actually simulated cannot disagree.

Regenerate after any netlist change:

```
python3 scripts/kicad_schematic.py
```

## Files

| file | what it is |
|---|---|
| `gan_buck.kicad_sch` | the schematic — open in eeschema, editable |
| `gan_buck.pdf` | plotted headless by `kicad-cli`, for printing |
| `gan_buck.svg` | same, vector, for the deck |
| `gan_buck.png` | 150 dpi raster preview |

## Two things a reader should know

**The GaN symbol.** KiCad 7 ships no GaN HEMT symbol. `Q_NMOS_DGS` is used
and labelled "eGaN HEMT", which is what EPC's own application schematics do.
The device has **no body diode** — reverse conduction during dead time costs
Vth + |Voff| + I·Rds(on) rather than one diode drop, and that sets the
dead-time trade. The sheet says so, because a reader who takes the MOSFET
symbol literally will mis-read the dead-time behaviour.

**The 0 V sources are not drawn.** `buck.cir` carries `Vsin`, `Vshs`, `Vsls`
and `Vsout` purely so ngspice can measure current through them. They are
measurement points, not components, and drawing them would imply hardware
that does not exist. A note on the sheet says where they are.

## Rendering the PNG

`kicad-cli` exports SVG and PDF. The PNG preview is rasterised separately
with PyMuPDF (`pip install pymupdf`); it is a convenience, not part of the
toolchain.
