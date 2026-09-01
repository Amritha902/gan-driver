FPGA CONTROLLER FOR THE SEGMENTED GaN GATE DRIVER
=================================================

  thermo_decode.v     slice count -> thermometer enables
  dead_time_gen.v     complementary outputs, programmable dead time
  seg_gate_ctrl.v     top level: emits the full 720-point control word
  seg_gate_ctrl_tb.v  self-checking testbench, seven asserted properties

RUN THE TESTS

  iverilog -g2012 -o tb.vvp seg_gate_ctrl_tb.v seg_gate_ctrl.v \
           dead_time_gen.v thermo_decode.v
  vvp tb.vvp

  Expected last line:  ALL CHECKS PASSED

WHY THE DESIGN SPLITS THE WAY IT DOES

  The dead time has a live register the controller may rewrite every cycle.
  The drive-strength fields are strapped once at configuration.

  That is not an arbitrary choice. The 720-word exhaustive search behind this
  project measured what each field is worth to schedule per operating point
  (FINDINGS.md section 17, paper Table IV):

      dead time ............ 5.45 %      <- live register
      gate off-bias ........ 2.55 %
      pull-down strength ... 2.03 %
      high-side pull-down .. 0.97 %
      pull-up strength ..... 0.00 %      <- strapped
      Miller clamp ......... 0.00 %      <- strapped on

  Building fast reload paths for fields worth 0.00 % would be silicon paying
  for nothing. The measurement is built into the hardware.

MAPPING TO THE SPICE MODEL

  Every field here is the same field the ngspice sweep varies, so an FPGA
  driving real hardware and the simulation run the same configuration:

      cfg_npu_ls  <-> .param NPU_LS      cfg_clken <-> .param CLKEN
      cfg_npd_ls  <-> .param NPD_LS      cfg_vneg  <-> .param VNEG (0 / -2 V)
      cfg_npd_hs  <-> .param NPD_HS      dt_cycles <-> .param DT
      cfg_npu_hs  <-> .param NPU_HS

  dt_cycles is in clk cycles, so at 100 MHz a DT of 5 ns is not
  representable - the sweep's 5/10/15/25/35 ns grid needs a 200 MHz clock or
  faster, or a delay line. That is a real constraint on the hardware build and
  is listed as milestone M4 work, not glossed over.

WHAT IS NOT HERE

  No synthesis results, no timing closure, no board. This is verified RTL, not
  a placed-and-routed design. It has been simulated, never synthesised.
