# ---------------------------------------------------------------------------
# build.tcl -- non-project-mode synthesis + implementation.
#
#   vivado -mode batch -source build.tcl
#   vivado -mode batch -source build.tcl -tclargs xc7a100tcsg324-1
#
# Non-project mode is used deliberately: it leaves no .xpr state in the repo,
# so the build is reproducible from a clean checkout.
# ---------------------------------------------------------------------------
set part [expr {$argc > 0 ? [lindex $argv 0] : "xc7a35tcpg236-1"}]
set here [file dirname [file normalize [info script]]]
set rtl  [file dirname $here]
set out  [file join $here build]
file mkdir $out

puts "== part: $part"
read_verilog -sv [list \
    [file join $rtl thermo_decode.v] \
    [file join $rtl dead_time_gen.v] \
    [file join $rtl seg_gate_ctrl.v] \
    [file join $here seg_gate_ctrl_top.v]]
read_xdc [file join $here seg_gate_ctrl.xdc]

synth_design -top seg_gate_ctrl_top -part $part
write_checkpoint -force [file join $out post_synth.dcp]
report_utilization -file [file join $out utilization_synth.rpt]
report_timing_summary -file [file join $out timing_synth.rpt]

opt_design
place_design
route_design
write_checkpoint -force [file join $out post_route.dcp]
report_utilization  -file [file join $out utilization.rpt]
report_timing_summary -file [file join $out timing.rpt]
report_drc -file [file join $out drc.rpt]
write_bitstream -force [file join $out seg_gate_ctrl_top.bit]

# Fail loudly on a timing miss -- a gate driver that misses its dead-time
# timing is a shoot-through, not a warning.
set wns [get_property SLACK [get_timing_paths -max_paths 1 -nworst 1 -setup]]
puts "== worst negative slack: $wns ns"
if {$wns < 0} { puts "== TIMING FAILED"; exit 1 }
puts "== build OK -> $out"
