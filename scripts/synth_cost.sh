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
#   brew install yosys      (or apt install yosys)
#   sh scripts/synth_cost.sh
#
# WHAT THESE NUMBERS ARE. synth_xilinx maps to real Artix-7 primitives -- LUT2
# through LUT6, FDCE/FDPE, CARRY4 -- so these are genuine LUT and flip-flop
# counts, not technology-independent gates. They are NOT Vivado's numbers:
# there is no place-and-route and no timing closure here, and Vivado's mapper
# will differ somewhat. For utilisation and timing on a real part, run
# rtl/vivado/build.tcl in Vivado on Windows or Linux.
#
# -flatten matters. Without it synth_xilinx keeps seg_gate_ctrl as a submodule
# of the wrapper, constants cannot propagate across the boundary, and the
# strapped design comes out no smaller -- 79 LUTs for both. Flattened, the
# strapping actually optimises away.
set -e
cd "$(dirname "$0")/../rtl"

run() {
  yosys -p "read_verilog -sv thermo_decode.v dead_time_gen.v seg_gate_ctrl.v \
            vivado/seg_gate_ctrl_top.v; synth_xilinx -family xc7 -flatten -top $1; stat" 2>&1 \
  | awk '
      /Printing statistics/ {inblk=1; lut=0; ff=0; carry=0}
      inblk && $2 ~ /^LUT[0-9]$/ {lut+=$1}
      inblk && $2 ~ /^FD/        {ff+=$1}
      inblk && $2 == "CARRY4"    {carry+=$1}
      END {printf "  %-34s LUTs %3d   FFs %3d   CARRY4 %d\n", D, lut, ff, carry}
    ' D="$1"
}

echo "Fabric cost of programmability (Artix-7 primitives, yosys synth_xilinx):"
run seg_gate_ctrl
run seg_gate_ctrl_top
