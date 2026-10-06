# Project closure — segmented GaN gate driver

**Status: closed as a simulation study.** Every question the project set out to
answer has an answer, every number has a script that regenerates it, and every
limit is written down. Nothing here is waiting on a decision. The work that
follows it is a different phase with a different base paper and lives in
`dab/`.

Amritha S (23BEC1368) · Sanjay Kumar (23BEC1447) · Aamir Abdullah (23BPS1197)
Guide: Dr. Bindu, SENSE, VIT Chennai
Repository `Amritha902/gan-driver`, 23 August – 6 October 2026, 240 commits.

This file is the record of what the project is, what it found, what it is
allowed to claim, and what it is not. `DOCS.md` is the map of every other
document; this one is the summary a reader should be able to stop at.

---

## 1. The question

> In a GaN half-bridge, switching one device fast enough to get low loss
> couples charge through the *other* device's Miller capacitance and can turn
> it on when it is supposed to be off. Speed and safety fight each other. How
> much of that conflict is resolved by making the gate driver **programmable**
> rather than fixed — and how much of *that* benefit genuinely needs
> per-operating-point **adaptation**, as opposed to one better fixed setting
> chosen once?

The second half is the part nobody separates. The active-gate-driver
literature reports a single improvement figure over a conventional driver.
That figure bundles two effects with completely different hardware costs: a
better fixed setting needs no sensing at all, while adaptation needs current
sensing, an ADC and a lookup table. Separating them requires searching the
whole control-word space at every operating point, which is why it is usually
argued rather than measured.

## 2. The answer

Measured over **720 control words × 36 operating points**:

| | share of baseline loss | hardware it needs |
|---|---|---|
| **(A)** choosing a better **fixed** word | **26.5 %** | none |
| **(B)** **adapting** it per operating point, on top | **2.6 %** | sensing + ADC + LUT |

Adaptation is **8.9 %** of the total gain. One comparator on load current at
10 A captures **47 %** of (B); two comparators capture **61 %**. What is left
for a full sense-and-lookup chain to justify is **4.7 %** of the total gain
over one comparator, **3.4 %** over two.

**This is a negative result and the project states it as one.** Most of what a
programmable gate driver buys, a single fixed setting already has. That is more
useful than another "we built an adaptive driver" paper, and it is the
contribution.

Three supporting results carry it:

- **The fault is real and reproduced.** Fastest drive, no clamp, 0 V off-bias:
  the off device's gate reaches **1.649 V against a 1.400 V threshold** —
  false turn-on, margin **−0.249 V**.
- **The fix is two blocks, and they are separable.** Miller clamp alone takes
  the margin to **+0.570 V**; clamp plus a −2 V off rail takes it to
  **+2.576 V**. The clamp is worth 9.7–12.2 % on its own, and the whole price
  of crosstalk safety is **≤ 0.04 %** of switching energy.
- **It beats the base paper on the same testbench.** Zhang *et al.*, ISPSD
  2020, rebuilt in `models/zhangdrv.lib` and searched over **its own** stated
  design range so the comparison is against their best setting, not a chosen
  opponent: **+0.407 V** against our **+2.576 V**, a factor of **6.3**. At the
  hottest corner the gap widens — theirs falls to +0.181 V, ours holds at
  +2.251 V — because their scheme suppresses crosstalk by slowing the edge and
  a clamp does not care how hot the device is.

Everything else, with the script that regenerates it, is in
`results/RESULTS-SUMMARY.txt`. **If this file and that one ever disagree, that
one is right**: it is machine-checked against the deck on every build.

## 3. What was actually run

67,116 transient simulations, derived from the result files by
`scripts/count_transients.py` rather than remembered — a stale count is a build
failure here, because it was a wrong slide once.

| Tool | Version | What it did | State |
|---|---|---|---|
| ngspice | 42 / 47 | every headline number, all sweeps | **ran** |
| LTspice | 26.0.2 (macOS) | independent cross-check of the three named cases and the converter | **ran, 5–9 Sep** |
| Icarus Verilog | 12.0 | RTL testbench, 8 properties / 591 assertions / 0 failures; mutation testing catches a broken build 221 times | **ran** |
| yowasp-yosys | WASM | generic-gate cost of the controller, 371 → 129 cells | **ran** (no ABC techmap in the WASM build) |
| Vivado | 2024.1 | real fabric cost on xc7a35t: **20 LUT, 20 FF**, 0.10 % of the part, 200 MHz met with **+1.996 ns** slack | **synthesis ran; place-and-route did not** |
| Cadence Spectre | — | `cadence/dpt_spectre.scs` is written and has never been executed | **never run** |

### The cross-simulator check, in full

Two independent simulators, two different device-model implementations of the
same netlist, run by hand on a different machine:

| case | ngspice 42 | LTspice 26.0.2 | difference |
|---|---|---|---|
| A — fastest word, no clamp, 0 V | **1.6488 V** | 1.64756 V | 0.08 % |
| B — Miller clamp on | **0.8304 V** | 0.82827 V | 0.26 % |
| C — clamp + −2 V off rail (shipped) | **−1.176 V** | −1.17686 V | 0.07 % |

Logs: `ltspice/*.log`, timestamps 5 and 8 September 2026. The converter's
48.84 V in `ltspice/BUCK_converter.log` is **not** comparable to ngspice's
48.50 V any more: that schematic has since gained the damped decoupling
branch, so the LTspice converter re-run is outstanding and is listed in §6.

## 4. What the result was tested against

A conclusion is only as good as what failed to break it.

- **Joint device variation.** 24 devices with V_th, transconductance, C_GS and
  C_JO sampled together, each a truncated Gaussian whose ±3σ points are the
  bounds the one-at-a-time study already used. On the shipped word, four
  corners, 96 runs: worst margin **+2.225 V**, **0 of 96** false turn-on. The
  nominal device gives +2.576 V, so the whole population costs 0.35 V of
  margin. (A) beat (B) on 23 of 24 devices, and the one exception was shown to
  be an artefact of the 36-word candidate subset, not a property of the
  device — re-run on the full 720-word grid it reverses to A 24.7 % > B 13.9 %.
- **Capacitance law.** Junction-diode `C=` against charge-based `Q=`: the
  ordering survives, and the **sign of the no-clamp row does not**. Stated as a
  limit, not buried.
- **Transistor level.** A real SKY130 output stage in place of the behavioural
  one: sign and ordering survive, but the clamp's own contribution falls to
  +0.03 V there, so the ordering survives and the *attribution* does not.
- **Timestep.** Every reported quantity is flat across 25× refinement: drain
  overshoot drifts 1.14 %, the spurious gate peak 0.04 %, and **0 of 80**
  feasibility verdicts flip.
- **Overshoot weighting.** Swept over 106 weights: the magnitude of the split
  moves, the ordering does not, out to a weight of 5.0.
- **Loop inductance.** 3 nH is **our choice** and the conclusion is sensitive
  to it — adaptive control pays below about 2.5 nH and not above it. Listed as
  a threat to validity, never as a result.

## 5. What this project got wrong, and caught itself

Eleven numbers were wrong or unscoped in a shipping document. Every one was
found by re-deriving a figure from its data, not by a reviewer, and each one is
written up in `results/FINDINGS.md` §24–34. Four automated checks now exist
*because* of them and run on every deck build (`review/BUILD-DECK.sh`):

| Check | What it would have caught |
|---|---|
| `check_consistency.py` | a number the speech script says that no slide carries; a headline that disagrees with the summary; a file the deck cites that does not exist; a claim with no evidence in the repo |
| `check_stale.py` | a superseded figure still shipping anywhere, read from the summary's own "(n=4 said …)" notes |
| `check_package.py` | retired slides still readable inside a `.pptx` that no longer shows them |
| `audit_paper.py` | a number in the paper that no longer matches the CSV it came from |

The failure mode worth naming: **text agreeing with text is not evidence.**
The transient count was wrong in the deck *and* in the summary for six weeks
and every check passed, because they only compared the two strings to each
other. Checks that re-derive from data are the only ones that caught anything.

## 6. What is not done — read this before quoting the project

1. **No hardware exists.** This is a simulation study end to end. No board, no
   measurement, no silicon.
2. **One behavioural model *form*** underlies the headline numbers. The device
   population was varied jointly (§4) and a transistor-level output stage was
   cross-checked, but a different model *formulation* moved the sign of the
   no-clamp row once, and that is on record.
3. **Vivado place-and-route has not run.** The LUT/FF counts and the +1.996 ns
   slack are **post-synthesis**. `rtl/vivado/VIVADO-TODO.md` is the step list;
   the post-route numbers in `utilization.rpt` and `timing.rpt` are the ones to
   quote once they exist.
4. **Cadence/Spectre has never been executed.** The deck must not claim
   cross-simulator agreement involving it — `check_consistency.py` fails the
   build if it tries.
5. **The LTspice converter cross-check is outstanding**, for the reason in §3.
   The three crosstalk cases are checked and current.
6. **Eight reference author lists are still blank**, left blank rather than
   guessed. `review/CITATIONS-STATUS.md` lists the Xplore document IDs; fifteen
   minutes on a campus connection finishes them. No fabricated reference was
   found when every one was checked.
7. **The FPGA route has a resolution ceiling.** 200 MHz fabric gives 5 ns
   dead-time granularity, roughly 25× coarser than the 0.191–0.360 ns a BCD
   process reaches in ref [13]. That is an argument *for* a silicon phase, and
   it is the honest answer if a panel asks.

## 7. Reproducing all of it

```bash
git clone https://github.com/Amritha902/gan-driver.git && cd gan-driver
pip install numpy matplotlib python-pptx pillow lxml
sudo apt-get install -y ngspice iverilog

gunzip -k results/full_grid.csv.gz results/device_mc.csv.gz

python3 scripts/gansim.py                      # the three named cases
python3 scripts/gansim.py CLKEN=1 VNEG=-2      # the shipped word, +2.576 V
python3 scripts/grid_analyse.py                # 26.5 / 2.6 / 8.9 / 3.5 %
python3 scripts/device_mc_shipped.py           # device spread, +2.225 V, ~90 s
python3 scripts/count_transients.py            # 67,116, derived not typed
python3 scripts/audit_paper.py                 # every paper number vs its CSV
bash  review/BUILD-DECK.sh                     # all three decks + all four checks
```

`results/gan_master.m` reproduces the analysis independently in MATLAB or
Octave, from the same CSVs, as a check that the Python is not the result.

## 8. What the next phase inherits

`dab/` is a different project with a different base paper (Shi *et al.*, 2020)
and a different objective. From here it takes the FPGA policy-engine
architecture, `quantiser.v`, and the characterisation-table methodology. It
deliberately drops the segmented output stage, the Cadence track and the
crosstalk objective (`dab/PROPOSAL.md` §5).

Two things in `dab/` are labelled untrustworthy by their own authors and must
stay that way until replaced by real runs: `dab/scripts/gen_synthetic_table.py`
("the numbers are invented, do not quote any of them as a result") and
`dab/sim/gan_behavioural.lib` ("placeholder, not a vendor model"). The blocking
gate `dab/MILESTONES.md` M0 — reproduce Shi's ZVS boundary — specifies Keysight
ADS, which is not available; doing it in ngspice instead is the open decision
at the top of that phase.

---

*Closed 6 October 2026. The checks in `review/BUILD-DECK.sh` all pass on this
commit; if they stop passing, the repository is wrong, not the checks.*
