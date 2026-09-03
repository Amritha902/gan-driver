# Vivado synthesis — what to do, in order

Goal: replace the generic-gate estimate on slide 16 (371→129 cells, from
yowasp-yosys, NOT real LUTs) with real LUT/FF utilization and timing from
actual Vivado synthesis on a real Xilinx part.

## 1. Install

- Download **Vivado ML Edition — WebPACK** (free) from AMD/Xilinx.
  Requires a free Xilinx account. ~30–50 GB. Windows or Linux only —
  not available on macOS.
- WebPACK license is free and auto-activates; no separate license file needed
  for Artix-7 parts.

## 2. Pick a part

Default in `build.tcl` is `xc7a35tcpg236-1` (Artix-7, on Digilent Arty A7-35T
and similar low-cost boards). If you have a specific board, pass its part:

```
vivado -mode batch -source build.tcl -tclargs <your_part_name>
```

If unsure, leave the default — it's a real, small, commonly available part.

## 3. Fix the clock — do this before building, not after

Open `seg_gate_ctrl.xdc`. The design's `dt_cycles` counts clock cycles and the
dead-time grid starts at 5 ns, so it **needs a 200 MHz clock**. A 100 MHz
board oscillator cannot express the fastest dead time the study uses.

- If your board has a 100 MHz (or other) oscillator, add a Clocking Wizard
  MMCM IP core generating `clk_200` (200 MHz) from it, and feed that into the
  design's clock port — not the raw board oscillator.
- Constrain `clk_200` in the XDC at 200 MHz (5 ns period).
- Do not skip this and assume it's fine — read `timing.rpt` after the build
  to confirm.

## 4. Set real pin assignments

The pin assignments in `seg_gate_ctrl.xdc` are placeholders, commented out.
Uncomment and set them to your actual board's pins before building. You do
NOT need to wire this to a real gate driver circuit to get synthesis/timing
numbers — placeholder-but-valid pins are enough for utilization + timing.
Only wire to real hardware after the timing report is clean.

## 5. (Optional but recommended) Run the Icarus bench first — no Vivado needed

Confirms the RTL itself is sound before spending a long synthesis run on it:

```
cd rtl
iverilog -g2012 -o /tmp/toptb vivado/seg_gate_ctrl_top_tb.v \
    vivado/seg_gate_ctrl_top.v seg_gate_ctrl.v dead_time_gen.v thermo_decode.v
/tmp/toptb
```

Expect: `ALL CHECKS PASSED`.

## 6. Run the real build

```
cd rtl/vivado
vivado -mode batch -source build.tcl
```

This runs synth → opt → place → route, and writes reports to
`rtl/vivado/build/`:

- `utilization_synth.rpt` — post-synthesis LUT/FF/etc. counts
- `utilization.rpt` — post-route (the real, final numbers — use these)
- `timing.rpt` — post-route timing summary
- `timing_synth.rpt` — post-synthesis timing (less final)
- `drc.rpt` — design rule checks
- `seg_gate_ctrl_top.bit` — bitstream (not needed for the slide, but produced)

The script **fails loudly (exits non-zero, prints "TIMING FAILED") if worst
negative slack is negative** — a gate driver that misses dead-time timing is
a shoot-through, not a warning. If this happens, don't paper over it — send
it to me as-is, it's a real finding, not a bug in the script.

## 7. What to send back

From `utilization.rpt` (post-route):
- LUT count (and LUT % of the part)
- FF (flip-flop) count
- Any other resource lines it reports (BRAM, DSP — likely 0 for this design)

From `timing.rpt`:
- Worst negative slack (WNS) — should be ≥ 0
- Worst hold slack (WHS)
- The line the script itself prints: `== worst negative slack: <value> ns`

That's it — those numbers replace the generic-gate placeholder on slide 16.

## If it fails

- **Timing fails (WNS < 0)**: send the number anyway — real finding, not
  something to hide or re-run with a slower clock without saying so.
- **Synthesis errors on the RTL itself**: send the exact error text.
- **Can't get 200 MHz timing closure**: also a valid, reportable result — the
  RTL's own README already flags this as worth checking, not assuming.
