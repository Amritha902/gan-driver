# Implementation

Every picture here is generated. Run `python3 scripts/implementation_shots.py` after changing a netlist or a model and they all follow; nothing in this folder is a one-off export.

The KiCad sheets are rendered from the PDFs KiCad plots, which are vector, at 200 dpi. The 2560x1440 captures in `results/` are screen photographs of eeschema itself and exist to show the application was open; these exist to be read.

| file | source | pixels | what it is |
|---|---|---|---|
| [`01-converter-schematic.png`](01-converter-schematic.png) | `kicad/gan_buck.pdf page 1` | 3307 x 2339 | The synchronous buck converter, root sheet. Drawn from sim/buck.cir by scripts/kicad_schematic.py, so every value on it is the netlist's. |
| [`02-gate-driver-high-side.png`](02-gate-driver-high-side.png) | `kicad/gan_buck.pdf page 2` | 3307 x 2339 | The high-side gate driver, as a hierarchical sub-sheet of the converter. |
| [`03-gate-driver-low-side.png`](03-gate-driver-low-side.png) | `kicad/gan_buck.pdf page 3` | 3307 x 2339 | The low-side gate driver. The same sheet file as the high side, placed twice -- one instance per gate. |
| [`04-driver-proposed.png`](04-driver-proposed.png) | `kicad/gan_segdrv.pdf page 1` | 3307 x 2339 | The proposed segmented gate driver: eight pull-up slices, eight pull-down, an active Miller clamp and an off rail selectable to -2 V. |
| [`05-driver-base-paper.png`](05-driver-base-paper.png) | `kicad/gan_zhangdrv.pdf page 1` | 4678 x 3307 | The base paper's driver as reimplemented here: seven slices a bank in two stages, one bias resistor, no clamp, off rail tied to reference. |
| [`06-driver-block-diagram.png`](06-driver-block-diagram.png) | `results/fig_drawio_segmented_driver.png` | 3160 x 1680 | The segmented driver as a block diagram, rendered from kicad/gan_driver.drawio. |
| [`07-segmented-driver-source.png`](07-segmented-driver-source.png) | `results/fig_code_segdrv.png` | 1860 x 556 | models/segdrv.lib, the SPICE implementation of the driver. |
| [`08-gan-hemt-model-source.png`](08-gan-hemt-model-source.png) | `results/fig_code_egan.png` | 1860 x 376 | models/egan.lib, the behavioural GaN HEMT model written from the EPC2010C datasheet. |
| [`09-novelty-on-the-circuit.png`](09-novelty-on-the-circuit.png) | `results/fig_novelty_circuit.png` | 2000 x 1503 | What the proposed driver has that the base paper's does not, ringed on the sheets themselves. |
| [`10-both-drivers-side-by-side.png`](10-both-drivers-side-by-side.png) | `results/fig_schematics_pair.png` | 4662 x 1509 | Both driver sheets whole, at the same scale, nothing ringed. |
