# run_programmable.tcl -- self-contained. Synthesises the FULLY PROGRAMMABLE
# controller (seg_gate_ctrl), not the strapped wrapper. Pairing its LUT count
# with the wrapper's 20 gives the fabric cost of programmability in Vivado
# numbers instead of yosys estimates.
#
#   vivado -mode batch -source run_programmable.tcl
#
# Nothing is parameterised on purpose: earlier attempts failed because a
# hard-coded top module in a different copy of the script ignored -tclargs.
set here [file dirname [file normalize [info script]]]
set rtl  [file dirname $here]
set out  [file join $here build_prog]
file mkdir $out

read_verilog -sv [list \
    [file join $rtl thermo_decode.v] \
    [file join $rtl dead_time_gen.v] \
    [file join $rtl seg_gate_ctrl.v]]

# seg_gate_ctrl's clock port is clk, NOT clk_200 -- only the wrapper has that.
create_clock -period 5.000 -name clk_200 [get_ports clk]

synth_design -top seg_gate_ctrl -part xc7a35tcpg236-1
report_utilization    -file [file join $out utilization_prog.rpt]
report_timing_summary -file [file join $out timing_prog.rpt]

puts "==================== PROGRAMMABLE DESIGN ===================="
puts "top module : seg_gate_ctrl        <-- must say seg_gate_ctrl"
foreach line [split [report_utilization -return_string] "\n"] {
    if {[regexp {Slice LUTs|Slice Registers|Bonded IOB} $line]} { puts "  $line" }
}
puts "reports    : $out"
puts "============================================================"
