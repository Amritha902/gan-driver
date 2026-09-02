# Handoff to a local Claude Code session

Everything below is pushed to `origin/master-orodhc` in `Amritha902/vero`.
Working tree was clean at handoff; nothing is stranded in the remote container.

## Getting set up locally

```bash
# 1. install Claude Code on your laptop
npm install -g @anthropic-ai/claude-code     # or: brew install claude-code

# 2. get the work
git clone https://github.com/Amritha902/vero.git
cd vero
git checkout master-orodhc

# 3. start a session in the project
cd gan-driver
claude
```

Then paste the prompt at the bottom of this file as your first message.

## What a local session can do that the remote one could not

These were the blockers, and all of them are laptop-side problems:

| Blocked remotely | Why | Local |
|---|---|---|
| Rendering slides to look at them | no LibreOffice, apt blocked | install LibreOffice, or just open the .pptx in PowerPoint |
| LTspice `.asc` verification | LTspice is Windows/macOS | open the file in LTspice directly |
| Vivado synthesis | not installable, licensed | install Vivado (free WebPACK covers Artix-7) |
| MATLAB | licence | MATLAB Online in your browser, or Octave |
| Completing the IEEE references | Xplore + Crossref + OpenAlex all blocked by the egress proxy | campus network, "Cite This" |

## State of the work

**Verified by actually running it (numbers reproduce exactly):**
- Crosstalk margins: −0.249 V (fails) / +0.570 V (clamp) / +2.576 V (clamp + −2 V)
- `ceiling.py` → 5.2 %; per-corner 1.1 / 2.3 / 12.7 / 3.8 %
- `novelty.py` → 25.1 % fixed, 3.9 % adaptive, 13.4 % share, 72 % one comparator
- `weight_sensitivity.py` → the split does not depend on the cost weight; (A) 23.4–29.0 %
  and (B) 1.3–6.4 % over weights 0–1, and (A) > (B) at every weight out to 5.0
- RTL: 8 properties T1–T8 pass under Icarus; `mutate.sh` catches the injected
  shoot-through with 221 failures
- Vivado top level + its own bench: pass under Icarus
- Transient count: 34,622, matching the row counts of every result CSV
- Citations: no fabricated reference found; [10] and [13] content-checked

**Deck:** 25 slides, `review/Review1_GaN_Segmented_Gate_Driver.pptx`.
Rebuild with `cd review && python3 build.py`. Geometry QA is `python3 qa.py`.

## The three things still open

### 1. An LTspice .asc that actually contains the Miller clamp
The three sheets in `ltspice/*.asc` illustrate the crosstalk mechanism but do
NOT draw the clamp — their labels now say so. `sim/dpt.cir` is the complete
clamped model and opens in LTspice (File → Open, set file type to All Files).

What is wanted: a real schematic with the clamp drawn, as a voltage-controlled
switch from the off device's gate to its source, Ron = 0.5 Ω, engaged while the
other side turns on. Node names in the existing sheets are `bus`, `sw`, `hsg`,
`lsg`, `lss`, `0`. The safest construction is to add the switch by SPICE
directive on those named nodes rather than by placing a symbol, because symbol
pin offsets cannot be checked without opening LTspice — which you now can.

Validate it by comparing against ngspice: `python3 scripts/gansim.py CLKEN=1
VNEG=-2` must still give margin +2.576 V.

### 2. Synthesis
`rtl/vivado/` has the top level, XDC and `build.tcl`. Nothing has ever been
synthesised — Vivado and Yosys are both unavailable remotely. Run:

```bash
cd rtl/vivado && vivado -mode batch -source build.tcl
```

Reports land in `rtl/vivado/build/`. The script exits non-zero on negative
slack. **The clock must be 200 MHz**: `dt_cycles` counts clock cycles and the
dead-time grid starts at 5 ns, so 100 MHz cannot express it. Feed `clk_200`
from a Clocking Wizard MMCM.

### 3. One comprehensive MATLAB script
`results/gan_analysis.m` (179 lines) runs clean in Octave and does Pareto,
schedule LUT and the analytical crosstalk check. What is wanted is a single
larger script that regenerates *every* figure and table in the deck from the
CSVs, so the whole results section has one MATLAB entry point.

Inputs available in `results/`: `sweep_nominal.csv`, `full_corners.csv`,
`corners.csv`, `robust.csv`, `robust_all.csv`, `robust_fix.csv`,
`lloop_sweep.csv.gz`, `emi_sweep.csv.gz`, `sweep_matlab.csv`.

## Paste this as the first message in the local session

> I'm continuing a GaN segmented gate-driver project. Read `gan-driver/HANDOFF.md`
> and `gan-driver/GUIDE.md` first — they have the full state and the verified
> numbers. Three things are open, in priority order: (1) build an LTspice .asc
> that actually contains the Miller clamp and verify it opens and runs in
> LTspice, cross-checking against `python3 scripts/gansim.py CLKEN=1 VNEG=-2`
> which must give margin +2.576 V; (2) run Vivado synthesis via
> `rtl/vivado/build.tcl` and put the real utilisation and timing numbers into
> the deck; (3) write one comprehensive MATLAB script that regenerates every
> figure and table in the deck from the CSVs in `results/`. Do not change any
> reported number without re-running the script that produces it —
> `results/RESULTS-SUMMARY.txt` lists which script owns each one.
