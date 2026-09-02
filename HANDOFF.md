# Handoff — continuing this project on your laptop

Everything below is pushed to `origin/master-orodhc` in `Amritha902/vero`.
Working tree clean at handoff; nothing exists only in the cloud container.

## Setup

```bash
npm install -g @anthropic-ai/claude-code     # or: brew install claude-code

git clone https://github.com/Amritha902/vero.git
cd vero && git checkout master-orodhc
cd gan-driver && claude
```

Paste the prompt at the bottom of this file as your first message.

## Why local is worth it

Every remaining blocker is environmental, not conceptual:

| Blocked in the cloud | Reason | On your laptop |
|---|---|---|
| Looking at the rendered slides | no LibreOffice, apt blocked | open the .pptx |
| LTspice verification | LTspice is Windows/macOS | run it |
| Vivado synthesis | not installable, licensed | free WebPACK covers Artix-7 |
| MATLAB | licence | MATLAB Online, or Octave |
| Author names for 10 refs | Xplore, Crossref, OpenAlex, Wiley, scispace **all** proxy-blocked | campus network, "Cite This" |

## What is done, and verified by running it

Every number below was reproduced by executing the script that owns it, not
copied from notes. `results/RESULTS-SUMMARY.txt` names the owning script for
each one.

**Simulation**
- Crosstalk margins **−0.249 / +0.570 / +2.576 V** (`scripts/gansim.py`)
- Ceiling on scheduling **5.2 %**, per-corner 1.1 / 2.3 / 12.7 / 3.8 (`ceiling.py`)
- Decomposition **25.1 % fixed, 3.9 % adaptive, 13.4 % share**, 72 % from one
  comparator, 3.7 % residual (`novelty.py`)
- Weight independence: over 106 overshoot weights, (A) stays 23.4–29.0 % and
  (B) 1.3–6.4 %, and **(A) exceeds (B) at every weight out to 5.0**
  (`weight_sensitivity.py`) — the strongest form of the headline claim
- 34,622 transients, matching the row counts of every result CSV

**Base paper, implemented — not just cited**
`models/basedrv.lib` implements Takayama, Okuda & Hikihara's DAC-architecture
driver (multibit code changing during the edge; no clamp, no negative rail).
`scripts/basepaper_compare.py` runs it inside `sim/dpt.cir` verbatim, swapping
only the driver:

    base paper, as implemented    +0.533 V   safe
    ours, constant code, no clamp -0.249 V   FALSE TURN-ON
    ours, clamp on                +0.570 V   safe
    ours, clamp + -2 V            +2.576 V   safe

Their sequenced code works and beats a fast fixed code. Our margin comes from
the negative off-bias, 4.8x theirs. Report it that way.

**RTL**
- 8 properties T1–T8 pass under Icarus; `mutate.sh` catches an injected
  shoot-through 221 times
- Vivado export in `rtl/vivado/`: top level, XDC, `build.tcl`, own bench
- Synthesis via `yowasp-yosys`: **371 cells → 129** (−65 %) when the word is
  strapped instead of fully programmable (`scripts/synth_cost.sh`).
  Generic gates, NOT Xilinx LUTs — ABC does not complete in the WASM build

**LTspice** — `ltspice/A_…`, `B_…`, `C_…cir` contain the real Miller clamp and
were verified in ngspice on the shipped files: 1.6488 / 0.8304 / −1.1759 V.
The three `.asc` sheets do NOT have the clamp and their stimulus produces no
event in their own measurement window; their labels say so. Do not present them.

**MATLAB** — `results/gan_master.m`, one entry point for the whole results
section. Independent reimplementation that reproduces the Python exactly.

**Deck** — 27 slides, `review/Review1_GaN_Segmented_Gate_Driver.pptx`.
Rebuild `cd review && python3 build.py`; geometry check `python3 qa.py`
(8 flags is the known-good baseline, all investigated false positives).
Speech script in `review/SPEECH-SCRIPT.md`, aligned to the current 27 slides.
Demo video `results/demo_crosstalk_explained.mp4`, embedded on slide 23.

## Open work, in priority order

**1. Look at the slides.** Nobody has. Everything is verified by text
extraction, XML validation and a height model — never by eye. Open slides
**7, 13 and 23** first; those are the newest.

**2. Finish the references.** 10 of 13 still read "authors: Xplore Cite This".
The papers are real — titles and document IDs resolve — but author lists are
behind Xplore. Base paper is done: H. Takayama, T. Okuda & T. Hikihara,
Int. J. Circuit Theory Appl. 50(1):183–196, 2022 (volume 50 confirmed against
a source that claimed 51). Xplore IDs to look up:

    [4] 9573371  [5] 10553383  [6] 10964227  [7] 10813402
    [10] 9170108 [11] 10286072 [12] 10591431 [13] 11146698

**3. Run Vivado synthesis.** `cd rtl/vivado && vivado -mode batch -source
build.tcl`. Replaces the generic gate counts with real LUT/FF utilisation and
timing. **The clock must be 200 MHz** — `dt_cycles` counts clock cycles and the
dead-time grid starts at 5 ns, so 100 MHz cannot express it. Feed `clk_200`
from a Clocking Wizard MMCM.

**4. Verify the LTspice files in real LTspice.** Open
`ltspice/C_clamp_and_negative_bias.cir` (File → Open, filter "All Files"),
probe `V(hsg,sw)`, confirm −1.176 V. If LTspice disagrees with ngspice, the
port is wrong — say so rather than presenting it.

**5. Optional: draw the clamp into a .asc schematic.** Not done because symbol
pin offsets cannot be checked without opening LTspice. Node names are `bus`,
`sw`, `hsg`, `lsg`, `lss`, `0`.

## Honest limits to keep saying out loud

- Entirely simulation. No silicon, no hardware measurement.
- One behavioural GaN device model underlies every number.
- 13.4 % is weight-dependent; the *ordering* (fixed beats adaptive) is not.
- Synthesis numbers are generic gates, not LUTs.

## Paste this as the first message locally

> I'm continuing a GaN segmented gate-driver project for an academic review.
> Read `gan-driver/HANDOFF.md` and `gan-driver/GUIDE.md` first — they carry the
> full state and every verified number. Priorities: (1) render the deck and
> visually check slides 7, 13 and 23, since nothing in it has ever been seen
> rendered; (2) run `rtl/vivado/build.tcl` in Vivado and put the real LUT/FF
> and timing numbers into slide 16, replacing the generic gate counts;
> (3) open `ltspice/C_clamp_and_negative_bias.cir` in LTspice and confirm it
> gives −1.176 V. Never change a reported number without re-running the script
> that produces it — `results/RESULTS-SUMMARY.txt` says which script owns each.
