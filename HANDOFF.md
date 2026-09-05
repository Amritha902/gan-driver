# Handoff — continuing this project on your laptop

This is the `Amritha902/gan-driver` repository, split out of `vero` on 2 Sep.
Working tree clean at handoff; nothing exists only in the cloud container.

## Setup

```bash
npm install -g @anthropic-ai/claude-code     # or: brew install claude-code

git clone https://github.com/Amritha902/gan-driver.git
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

    base paper, as implemented    +0.534 V   safe
    ours, constant code, no clamp -0.249 V   FALSE TURN-ON
    ours, clamp on                +0.570 V   safe
    ours, clamp + -2 V            +2.576 V   safe

Their sequenced code works and beats a fast fixed code. Our margin comes from
the negative off-bias, 4.8x theirs. Report it that way.

**RTL**
- 8 properties T1–T8 pass under Icarus; `mutate.sh` catches an injected
  shoot-through 221 times
- Vivado export in `rtl/vivado/`: top level, XDC, `build.tcl`, own bench
- **Vivado 2024.1.2, xc7a35tcpg236-1, run 5 Sep 2026** (reports committed in
  `rtl/vivado/build/`): **20 LUTs, 20 flip-flops**, 0.10 % of the part; 40
  bonded IOB (37.7 %); 1 BUFG; no BRAM, no DSP.
  **Register-to-register timing at 200 MHz is MET, WNS 1.996 ns**, 0 of 25
  endpoints failing; hold +0.134 ns, pulse width +2.000 ns.
  The report's headline "Timing constraints are not met" refers to 34
  clock-to-output-pin paths in group `**default**`, against the placeholder
  `set_max_delay 4.000` in the XDC. Worst path: 3.49 ns in the LVCMOS33 OBUF
  and 2.92 ns clock insertion (clock driven from a pin with no MMCM); the
  logic is 0.295 ns. Fix is in `rtl/vivado/VIVADO-TODO.md`: MMCM for the
  clock, real output constraint once the board is known.
- Pre-Vivado estimate for comparison, `yosys synth_xilinx -flatten`: 53 LUTs
  fully programmable vs 27 strapped (`scripts/synth_cost.sh`). Vivado gives 20
  for the strapped design — vendor mapping beats yosys. Only the strapped
  design was synthesised in Vivado

**LTspice** — `ltspice/A_…`, `B_…`, `C_…cir` contain the real Miller clamp and
were verified in ngspice on the shipped files: 1.6488 / 0.8304 / −1.1759 V.
The three `.asc` sheets do NOT have the clamp and their stimulus produces no
event in their own measurement window; their labels say so. Do not present them.

**MATLAB** — `results/gan_master.m`, one entry point for the whole results
section. Independent reimplementation that reproduces the Python exactly.
**Run in MATLAB Online on 5 Sep 2026 and in GNU Octave 11.3 the same day:
the two agree to the last printed digit** (`results/matlab_online/RUN-LOG.txt`).
`gan_master.m` is a FUNCTION file, not a script — MATLAB needs local
functions after all code, Octave does not hoist them, and only a function
file satisfies both. Invoke it by typing `gan_master`.

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

## The repository split — DONE

`gan-driver` now lives in its own repository:
**https://github.com/Amritha902/gan-driver** (private, branch `main`).

Done on 2 Sep with `git subtree split --prefix=gan-driver`, so the history
came across rather than a copied working tree: **52 commits**, back to the
original "Add GaN segmented gate driver simulation project". Verified by
cloning it fresh and running the project from the clone —
`scripts/gansim.py CLKEN=1 VNEG=-2` gives margin **+2.576 V** and the deck
builds to 27 slides with the usual 8 QA lines. Paths survived the move
untouched because every script resolves its root from `__file__`.

**This repo is now canonical. Work here, not in `vero`.**

### Still to tidy, after the review

`vero` still contains a copy under `gan-driver/`. Removing it is the
destructive half and there is no hurry — do it on a branch with a PR so the
diff is visible:

```bash
cd vero
git checkout -b remove-gan-driver
git rm -r gan-driver
git commit -m "Move gan-driver to its own repository"
git push -u origin remove-gan-driver
```

Open the PR, confirm this repo really has everything, then merge. Do not
force-push and do not rewrite `vero`'s history — the split already preserved
the history here, so deleting the directory there is enough.

The branch `gan-driver-only` on `vero` was the staging branch for the split.
It can be deleted once you are happy: `git push origin --delete gan-driver-only`.

### Also worth checking

`Amritha902/Amritha902` is your GitHub profile repo. The 3 AM run was asked to
restore its README if earlier automated commits had damaged it. Its last push
predates that run, so nothing landed, but a PR may be open — read the diff
before merging.

## Paste this as the first message locally

> I'm continuing a GaN segmented gate-driver project for an academic review.
> Read `HANDOFF.md` and `GUIDE.md` first — they carry the
> full state and every verified number. Priorities: (1) render the deck and
> visually check slides 7, 13 and 23, since nothing in it has ever been seen
> rendered; (2) run `rtl/vivado/build.tcl` in Vivado and put the real LUT/FF
> and timing numbers into slide 16, replacing the generic gate counts;
> (3) open `ltspice/C_clamp_and_negative_bias.cir` in LTspice and confirm it
> gives −1.176 V. Never change a reported number without re-running the script
> that produces it — `results/RESULTS-SUMMARY.txt` says which script owns each.
