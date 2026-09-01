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
