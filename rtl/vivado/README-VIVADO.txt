XILINX VIVADO EXPORT
====================

FILES
  seg_gate_ctrl_top.v      synthesis top level (wraps rtl/seg_gate_ctrl.v)
  seg_gate_ctrl_top_tb.v   self-check for the wrapper
  seg_gate_ctrl.xdc        timing + I/O constraints
  build.tcl                non-project synth -> impl -> bitstream

RUN THE BENCH FIRST (no Vivado needed)
  cd rtl
  iverilog -g2012 -o /tmp/toptb vivado/seg_gate_ctrl_top_tb.v \
      vivado/seg_gate_ctrl_top.v seg_gate_ctrl.v dead_time_gen.v thermo_decode.v
  /tmp/toptb
  -> ALL CHECKS PASSED

BUILD
  cd rtl/vivado
  vivado -mode batch -source build.tcl
  vivado -mode batch -source build.tcl -tclargs xc7a100tcsg324-1   # other part

  Outputs land in vivado/build/: utilization.rpt, timing.rpt, drc.rpt and
  seg_gate_ctrl_top.bit. The script exits non-zero if worst negative slack is
  negative -- a gate driver that misses dead-time timing is a shoot-through.

TWO THINGS TO SETTLE BEFORE THIS IS REAL HARDWARE
  1. THE CLOCK MUST BE 200 MHz. dt_cycles counts clock cycles and the swept
     dead-time grid starts at 5 ns, so a 100 MHz board clock (10 ns) cannot
     express the fastest dead time the study uses. Feed clk_200 from a
     Clocking Wizard MMCM off the board oscillator. 200 MHz is attainable on
     Artix-7 for logic this small, but read timing.rpt -- do not assume it.

  2. THE PIN ASSIGNMENTS IN THE XDC ARE PLACEHOLDERS, commented out. Set them
     to your board before building, and do not wire the outputs to a real
     gate driver until the timing report is clean.

WHY THE TOP LEVEL LOOKS LIKE THIS
  The study found only one field worth scheduling: dead time, and only at
  light load. Freezing pull-up drive strength costs 0.00 %; the clamp is
  optimal always-on. So the adaptive hardware here is ONE comparator input
  (light_load) selecting between two dead times -- not a sense + ADC + lookup
  table. That is the project's central finding expressed as RTL, and it is
  the cheapest hardware consistent with the measurement.

NOT YET DONE
  Synthesis has never been run -- Vivado is not installed in the environment
  these files were written in. The RTL compiles and its bench passes under
  Icarus Verilog; utilisation and timing are unknown until someone runs
  build.tcl.

RESULTS -- Vivado 2024.1.2, xc7a35tcpg236-1, 5 Sep 2026
=======================================================
Reports are committed in build/.  Behavioural simulation in Vivado's own
simulator also reports ALL CHECKS PASSED.

  UTILISATION
    Slice LUTs          20   of 20800   (0.10 %)   all LUT-as-Logic
    Slice Registers     20   of 41600   (0.05 %)   19 FDCE + 1 FDPE
    Bonded IOB          40   of   106   (37.74 %)
    BUFG                 1;  no BRAM, no DSP, no F7/F8 muxes
    Primitives: LUT6 7, LUT2 6, LUT5 4, LUT1 4, LUT4 3, LUT3 2 (26 before
    LUT combining, 20 after), OBUF 36, IBUF 4

  TIMING -- read this carefully, the headline is misleading
    Intra-clock (register to register), clk_200 at 5.000 ns / 200 MHz:
        WNS  1.996 ns    0 of 25 endpoints failing   -> MET
        WHS  0.134 ns    WPWS 2.000 ns               -> MET
    The design closes 200 MHz with 40 % of the period to spare.

    Path group **default** (register to output PIN):
        WNS -4.755 ns    34 of 34 endpoints failing
    These fail against  set_max_delay 4.000  in seg_gate_ctrl.xdc, which is a
    PLACEHOLDER and is labelled as one in that file. Worst path,
    FSM_sequential_state_reg[0] -> hs_pd[0], arrival 8.755 ns:
        OBUF (LVCMOS33)          3.492 ns
        clock insertion          2.917 ns  (IBUF+BUFG, no MMCM)
        routing                  1.595 ns
        actual logic (LUT3)      0.295 ns
    So the violation is I/O buffer and clock-tree delay, not logic depth.

  WHAT TO DO ABOUT IT
    1. Drive clk_200 from a Clocking Wizard MMCM instead of straight from the
       pin. That removes the 2.9 ns insertion delay from every output path.
    2. Replace set_max_delay 4.000 with a number derived from the real board
       and gate-driver input timing. 4 ns is not achievable through an
       LVCMOS33 OBUF that costs 3.5 ns by itself.
    3. If the outputs must be fast, use a faster I/O standard or ODDR.
    Both 1 and 2 were already written in VIVADO-TODO.md before this run.
