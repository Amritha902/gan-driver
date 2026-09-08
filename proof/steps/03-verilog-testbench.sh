#!/bin/zsh
# STEP 3 -- the FPGA controller, compiled and simulated live.
cd ~/gan-driver/rtl
print -P "%F{cyan}================================================================%f"
print -P "%F{cyan} STEP 3  The Verilog controller, compiled and run live%f"
print -P "%F{cyan}================================================================%f"
echo "files : seg_gate_ctrl.v  thermo_decode.v  dead_time_gen.v"
echo "test  : seg_gate_ctrl_tb.v   (self-checking, 8 asserted properties)"
echo "tool  : $(iverilog -V 2>/dev/null | head -1)"
echo
echo "$ iverilog -g2012 -o /tmp/tb seg_gate_ctrl_tb.v seg_gate_ctrl.v thermo_decode.v dead_time_gen.v"
iverilog -g2012 -o /tmp/tb seg_gate_ctrl_tb.v seg_gate_ctrl.v thermo_decode.v dead_time_gen.v
echo "$ vvp /tmp/tb +report"
vvp /tmp/tb +report
