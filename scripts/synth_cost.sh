#!/bin/sh
# synth_cost.sh -- what does programmability cost in fabric?
#
# Synthesises two designs and compares them:
#   seg_gate_ctrl       every field of the control word live and writable
#   seg_gate_ctrl_top   the studied word strapped, plus ONE light-load
#                       comparator selecting between two dead times
#
# The study says adaptation buys 3.9 % of baseline switching energy. This is
# the other side of that trade: what the adaptive hardware costs.
#
#   pip install yowasp-yosys
#   sh scripts/synth_cost.sh
#
# NOTE ON WHAT THESE NUMBERS ARE. Yosys' ABC technology-mapping pass does not
# complete in the WASM build used here, so these are TECHNOLOGY-INDEPENDENT
# generic gate counts after `techmap`, not Xilinx LUT counts. They are valid
# for comparing the two designs against each other, which is the point. For
# LUT/FF utilisation on a real part, run rtl/vivado/build.tcl in Vivado.
set -e
cd "$(dirname "$0")/../rtl"
run() {
  yowasp-yosys -p "read_verilog -sv thermo_decode.v dead_time_gen.v seg_gate_ctrl.v vivado/seg_gate_ctrl_top.v; hierarchy -top $1; flatten; proc; opt -full; fsm; opt -full; techmap; opt -full; stat" 2>&1 \
  | awk '$2=="cells"{c=$1} $2 ~ /^\$_DFF/{ff+=$1} $2 ~ /^\$_(AND|OR|NOT|MUX|XOR)_$/{g+=$1} END{printf "  %-22s cells %4d   flip-flops %3d   comb gates %4d\n", D, c, ff, g}' D="$1"
}
echo "Hardware cost of programmability (generic gates, not Xilinx LUTs):"
run seg_gate_ctrl
run seg_gate_ctrl_top
