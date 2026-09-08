# Where every number comes from

One line per number on the slides: the command that produces it, and where it
appears. Every command below runs on this laptop in under two minutes. None of
them reads a number from the presentation; the presentation reads from them.

Run them all in order with:

    cd ~/GAN_MAIN/PROOF
    zsh RUN-LIVE.sh

Saved output of each is in `PROOF/logs/`, and a screenshot of each in
`PROOF/screenshots/`.

---

## The converter

| Number | Where it is | Command |
|---|---|---|
| **100 V DC in, 48.6 V DC out** at 4.88 A | "What we are building" slide | `zsh steps/10-converter-power.sh` |
| **242.6 W** drawn, **236.9 W** delivered | same slide | same run |
| **97.6 %** efficiency, 5.8 W lost | same slide | same run |
| Driver setting moves loss **4.5 %** and device stress **50 %** | Result 2 | `python3 scripts/buck_sweep.py` |
| Lowest loss is **4 slices**, not the fastest | Result 2 | same run |
| Crosstalk safety costs **0.53 W** = 0.22 points of efficiency | Result 2 | same run |

`sim/buck.cir` is the converter: the same two GaN devices and the same
segmented gate drivers as the double-pulse bench, now switching continuously
at 500 kHz into an output filter and a 10 Ω load. The double-pulse bench
measures one edge of it precisely; this measures the whole machine.

**Screenshot:** `17-converter-power.png`
**Figures:** `results/fig_converter.png`, `results/fig_buck_tradeoff.png`

---

## The fault, and the fix

| Number | Where it is | Command |
|---|---|---|
| Gate of the OFF device reaches **+1.65 V** | Result 1 slide, demo | `zsh steps/01-ngspice-crosstalk.sh` |
| Threshold is **1.4 V**, so it turns on | Result 1 slide | same run, printed |
| With clamp and −2 V rail: **−1.18 V**, margin **2.58 V** | Result 1 slide | same run |

Two ngspice runs of `sim/dpt.cir`, about 1.6 seconds. The only difference
between them is the clamp enable and the off-bias rail.

**Screenshot:** `01-ngspice-crosstalk.png`
**Waveforms on screen:** `zsh steps/09-show-waveforms.sh` opens a plot window
drawn from the run that just happened — `15-live-waveforms.png`,
`16-ngspice-plot-on-screen.png`.

---

## The named cases

| Case (full load, 100 V / 10 A) | Peak on the OFF gate | Verdict |
|---|---|---|
| 1. Fastest drive, nothing else | **+1.649 V** | false turn-on |
| 2. Turn the Miller clamp on | +0.830 V | safe, +0.570 V margin |
| 3. Add the −2 V off-bias rail | −1.176 V | safe, **+2.576 V** margin |
| 4. Slow the drive right down | −1.674 V | safe, but 7.91 µJ — 2× the loss |
| 5. The setting the search chose | +1.059 V | safe, cheapest at 3.99 µJ |

| Dead-time sweep, same driver | Cheapest dead time |
|---|---|
| full load, 100 V / 10 A | **15 ns** |
| light load, 50 V / 2 A | **5 ns** |

Two different numbers. That gap is the whole case for adapting anything, and
it is why the project exists. 13 ngspice runs, 10 seconds:

    zsh steps/11-named-cases.sh

**Screenshot:** `18-named-cases.png`  ·  **Figure:** `results/fig_cases.png`

---

## Are the stored data files real?

| Check | Command |
|---|---|
| Take row 1 of `results/corners.csv`, re-simulate its settings now, compare | `zsh steps/02-reproduce-stored-row.sh` |

Result: every quantity agrees to within **0.1 %**. The stored sweeps were run
on ngspice 42; this laptop has ngspice 47, and that version difference is the
whole of the disagreement.

**Screenshot:** `02-reproduce-stored-row.png`

---

## The FPGA controller

| Number | Where it is | Command |
|---|---|---|
| **8 properties**, 591 individual assertions, 0 failures | FPGA slide | `zsh steps/03-verilog-testbench.sh` |
| A deliberately broken version is caught **221 times** | FPGA slide | `zsh steps/04-verilog-mutation.sh` |
| **20 LUTs, 20 flip-flops**, 0.10 % of the chip | FPGA slide | `3-FPGA-vivado/build/utilization_synth.rpt` |
| **200 MHz met, 1.996 ns spare** | FPGA slide | `3-FPGA-vivado/build/timing_synth.rpt` |
| **33 LUTs** when every field is left adjustable | Vivado slide | `11-vivado-synthesis-console.png` |

The Verilog is in `2-RTL-verilog/`. Step 3 compiles it and runs it in front of
you; step 4 breaks it on purpose and shows the same test failing, which is the
only way to know the test was doing anything.

Vivado has no macOS build, so synthesis was run on a Windows machine by a
project member. The two report files it wrote are in
`3-FPGA-vivado/build/`, unedited, and the two screenshots show the tool that
produced them.

**Screenshots:** `03-verilog-8-properties.png`, `04-verilog-mutation-test.png`,
`10-vivado-simulation.png`, `11-vivado-synthesis-console.png`
**Source code:** `06-code-seg_gate_ctrl-1.png` … `09-code-thermo_decode.png`

---

## The three results

| Number | Where it is | Command |
|---|---|---|
| Re-tuning is worth at most **5.2 %** | Result 2 slide | `zsh steps/06-ceiling-result2.sh` |
| Per operating point: **1.1 / 2.3 / 12.7 / 3.8 %** — the bar chart | Result 2 chart | same run |
| Only **474 of 720** settings are safe at all four points | Result 2 slide | same run |
| Picking a fixed setting well: **25.1 %** | Result 3 slide | `zsh steps/07-split-result3.sh` |
| Re-tuning it live, on top: **3.9 %** | Result 3 slide | same run |
| Re-tuning is **13.4 %** of the total gain; full hardware justifies **3.7 %** | Result 3 slide | same run |
| Holds across 106 weightings: (A) 23.4–29.0 %, (B) 1.3–6.4 % | Result 3 slide | same run |
| Re-tuning pays below about **2.5 nH**; **13.5 %** at 1.5 nH; **0.97 %** at 6 nH | Result 4 slide | `zsh steps/08-loop-inductance-result4.sh` |
| **504 of 720** safe; trade-off curve; the same split in MATLAB | MATLAB slide | `zsh steps/05-octave-analysis.sh` |

**Screenshots:** `12-result2-ceiling.png`, `13-result3-split.png`,
`14-result4-inductance.png`, `05-octave-analysis.png`

---

## Why more than one tool

Not for the sake of it. One tool per job, and each headline number checked in a
second, independent one:

**Two tools for the circuit, and that is the whole list.**

| Tool | Job |
|---|---|
| ngspice | every circuit simulation — the converter, the test bench, every sweep |
| LTspice | the circuit drawn as a schematic, and one independent re-measurement |
| Vivado | the FPGA controller: synthesis and timing |

### What LTspice was used for, exactly

`ltspice/A_design_no_clamp_FAILS.asc`, `B_design_clamp_on.asc` and
`C_design_clamp_and_neg_bias.asc` are drawn schematics carrying the same
`egan.lib` devices and `segdrv.lib` gate drivers that `sim/dpt.cir` uses.
Open one, press Simulate ▸ Run, read View ▸ SPICE Error Log:

| case | LTspice | ngspice | apart |
|---|---|---|---|
| A — no clamp, 0 V | +1.647556 V | +1.6486 V | 1.0 mV |
| B — clamp on, 0 V | +0.828274 V | +0.8302 V | 1.9 mV |
| C — clamp on, −2 V | −1.176857 V | −1.1757 V | 1.2 mV |

`results/fig_ltspice_annotated.png` plots those runs with the meaning marked
on them. It is **not a screenshot** — it is LTspice's data read out of the
`.raw` file it wrote and replotted so it can be labelled, and the figure says
so on its face, quoting the file's own header. The screenshots of LTspice
itself are `19-ltspice-A-false-turn-on.png`, `20-ltspice-C-clamp-safe.png` and
`21-ltspice-schematic.png`.

Icarus Verilog compiles and runs the Verilog during development; Vivado
simulates and synthesises the same files, so it is a checker, not a third
track. Python drives ngspice and plots what comes back — it does no circuit
maths of its own.

Earlier versions of this project also cross-checked in LTspice, MATLAB and
GNU Octave. Those runs agreed, but carrying four tools made the work look
scattered across a toolchain rather than done in one. The circuit work is
ngspice. The FPGA work is Vivado.
