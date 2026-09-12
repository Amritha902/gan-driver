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
- Decomposition **25.1 % fixed, 3.9 % adaptive, 13.4 % share**. Of the adaptive
  part, **46 % is reachable with ONE comparator** (bus voltage at 75 V),
  leaving **7.2 %** for a full sense + ADC + LUT. Two comparators reach 72 %,
  leaving 3.7 % (`novelty.py`).
  QUOTE THE ONE-COMPARATOR NUMBER. The corner worth isolating shares its bus
  voltage, load and temperature with other corners, so no single threshold
  selects it -- 72 % needs two comparators, and calling it one is wrong.
- Weight independence: over 106 overshoot weights, (A) stays 23.4–29.0 % and
  (B) 1.3–6.4 %, and **(A) exceeds (B) at every weight out to 5.0**
  (`weight_sensitivity.py`) — the strongest form of the headline claim
- 34,622 transients, matching the row counts of every result CSV

**Closed loop, and real transistors** (12 Sep)
- `sim/buck_closed.cir` + `scripts/closedloop.py`: type-III loop around the
  same power stage and the same drivers. **50.02 / 50.00 / 50.01 V** through a
  2x load step and a 100 -> 120 V line step; worst error **0.05 %** against
  open loop's 16.7 %. Load step recovers in 4 us, line step in 19 us, ripple
  0.28 %, soft-start overshoot 10.9 % (stated, not good).
  DO NOT QUOTE A PHASE MARGIN. None is measured; the 59 deg in the design
  notes is from an averaged model the measurement shows is 4x out on gain.
- `scripts/silicon_check.py`: the same output stage in real SKY130 5 V
  devices. Sign and ordering both survive -- **and the clamp ALONE gives
  +0.031 V, not +0.570**. Quote it that way: the -2 V off-bias is the fix and
  the clamp is what makes it hold. The ideal-switch model was flattering the
  clamp.
- `scripts/headtohead.py`: four corners, four metrics, base paper re-optimised
  at every corner against our one fixed word. **5.5x / 6.3x / 8.9x / 12.4x** --
  the lead WIDENS with stress. And our switch node slews about 2x faster than
  theirs, so the margin is not bought with switching speed. Costs: our turn-on
  energy is higher at 3 of 4 corners (the -2 V rail).
- Bug fixed: `gansim.py` did not rewrite the SKY130 decks' relative `.lib`
  path, so every transistor-level run through it silently measured nothing.
  Fails safe (returns None, never a wrong number), but it made the whole
  transistor-level stage unreachable through the standard interface.

**Base paper, implemented — not just cited**
`models/zhangdrv.lib` implements Zhang et al.'s segmented driver (ISPSD 2020,
Xplore 9170108): seven slices brought in as a timed pattern across the edge,
the pattern selected by one bias resistor; no clamp, no negative rail.
`scripts/basepaper_compare.py` runs it inside `sim/dpt.cir` verbatim, swapping
only the driver:

    base paper, at its best       +0.407 V   safe
    ours, constant code, no clamp -0.249 V   FALSE TURN-ON
    ours, clamp on                +0.570 V   safe
    ours, clamp + -2 V            +2.576 V   safe

Their pattern works and beats a constant code. Our margin comes from the
negative off-bias, 6.3x theirs. Report it that way.

**Quote them at their BEST — this matters.** Their driver has two controls:
how many of the seven slices engage first, and the pattern timing, which the
paper puts at 0.5–5 ns. Across that range their margin runs from **+0.407 V
down to −0.278 V**, so whichever setting you hand them decides how far ahead
we look. `basepaper_compare.py` searches their range and quotes their best
point. Do not quote them anywhere worse — that is choosing the opponent, and
a reviewer who checks will say so.

NOTE: the earlier Takayama (SiC) reproduction in `models/basedrv.lib` is
**not** the base paper any more. Ref [9] cites it as prior art for the
mechanism only; the base paper is now [10], Zhang, on the same device.

**RTL**
- 8 properties T1–T8 pass under Icarus; `mutate.sh` catches an injected
  shoot-through 221 times
- **RTL-in-the-loop, verified end to end** (`scripts/rtl_cosim.py`). The
  thermometer encoding matches the SPICE abstraction on every bank, 0
  mismatches. And `sim/dpt.cir` is now run twice — once with `segdrv.lib`'s
  integer slice count, once with the low-side slices driven by sixteen PWL
  sources built from the RTL's own VCD into `models/segdrv_bus.lib`. Margins:
  **-0.242 V clamp off, +0.651 V clamp on** from the RTL bus, against
  -0.249 / +0.570 V from the parameters. Worst disagreement **0.081 V**, and
  that is 2.5 ns of dead-time timing, not encoding. The bench that made this
  possible is `rtl/seg_gate_ctrl_dpt_tb.v`.
- **Dead time is (dt_cycles + 1) x 5 ns**, measured. `dpt.cir`'s DT = 15 ns is
  `dt_cycles = 2`, NOT 15/5 = 3 — `dead_time_gen` counts down through zero.
  Mapping the swept DT grid to hardware by dividing by the clock period makes
  the driver one cycle slow at every operating point.
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
- **Cost of programmability, in Vivado**: seg_gate_ctrl fully programmable
  is **33 LUTs / 30 FFs**; seg_gate_ctrl_top strapped is **20 / 20**. Strapping
  saves 13 LUTs, 39 % of the logic. This supersedes the yosys estimate
  (53 -> 27) that scripts/synth_cost.sh still prints -- same direction, but
  the honest figure is 39 %, not 49 %. Quote the Vivado pair.

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

**Deck** — 45 slides, `review/Review1_GaN_Segmented_Gate_Driver.pptx`
(the 20-slide `GaN_Review1_PRESENT.pptx` is the one to actually present).
Rebuild `cd review && python3 build.py`; geometry check `python3 qa.py`
(9 flags is the known-good baseline, all investigated false positives;
the three slides added on 12 Sep add none).
Speech script in `review/SPEECH-SCRIPT.md`; the 10-minute cut is
`review/SPEECH-10-MINUTES.md`. Run `python3 check_consistency.py` after any
edit — it fails the build if the deck and the scripts stop agreeing.

**Three slides answer the examiner directly** (added 12 Sep, after the
reviewer asked what the goal actually is):
- *The goal, and whether this serves it* — GaN buck converter for storage;
  why GaN, what GaN costs, what we build about it, and the statement that the
  test of purpose is the architecture, not "does the converter run".
- *Does the architecture close the gaps?* — six literature gaps, what the
  architecture does about each, the evidence and the owning script. Five
  CLOSED, one ANSWERED NEGATIVE, one OPEN (hardware).
- *The architecture, end to end* — the RTL-in-the-loop co-simulation.

**Completion is counted, not asserted: 90 %.** Twelve weighted blocks on the
Work Completed slide, ten done. The remaining 10 % is place-and-route on a
chosen board (3) and a hardware half-bridge on a bench (7) — neither of which
more simulating can deliver.

**`review/JUDGE.md` is the examiner's report**: the project reviewed
adversarially and then answered, every finding marked FIXED, STATED or OPEN.
Read it before the viva; the questions a reviewer will ask are in it, with the
answers.
Demo video `results/demo_crosstalk_explained.mp4`, embedded on slide 23.

## Open work, in priority order

Items 1-4 of the previous list are DONE (5 Sep 2026): every slide has been
looked at, all 30 references are verified against the publisher record, Vivado
has been run, and the LTspice port has been run in LTspice. What is left:

**1. Guide's signature.** Print slide 2, get it signed and dated, scan it, and
replace the slide-1 placeholder with the scan. Mandatory for every review, and
the only item that cannot be done from this repository.

**2. DONE (5 Sep).** Both designs are synthesised in Vivado: 33 LUTs
programmable against 20 strapped. Reproduce with rtl/vivado/synth_both_STEVEN.tcl.

**3. Place-and-route, if a board is chosen.** synth_only.tcl stops at
synthesis. build.tcl runs the full flow but needs real package pins, and the
XDC pins are placeholders. Doing this properly also means driving clk_200 from
a Clocking Wizard MMCM rather than straight from a pin -- that alone removes
2.917 ns of clock insertion delay from every output path and is why the 34
clock-to-pin endpoints fail today.

**4. Optional: draw the clamp into a .asc schematic.** The three .asc sheets
are simplified teaching drawings and say so on their face; the real clamp lives
in the .cir files, which have been run in both ngspice and LTspice. Node names
are `bus`, `sw`, `hsg`, `lsg`, `lss`, `0`.

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
builds to 45 slides with the usual 9 QA lines. Paths survived the move
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
