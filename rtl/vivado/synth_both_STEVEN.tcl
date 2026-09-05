# ---------------------------------------------------------------------------
# synth_both.tcl  --  drop-in replacement for synth_only.tcl
#
# Synthesises BOTH designs in one run and prints the comparison:
#
#   seg_gate_ctrl_top   the STRAPPED controller  (what you already ran)
#   seg_gate_ctrl       the FULLY PROGRAMMABLE controller  (the new one)
#
# The difference between the two LUT counts is the fabric cost of making the
# control word programmable, which is the number we need.
#
# Same project structure as before:
#
#   D:/amritha/PJT1/
#     +-- synth_both.tcl
#     +-- PJT1.srcs/sources_1/new/*.v
#     +-- PJT1.srcs/constrs_1/new/sea_gate_ctrl.xdc
#
# Usage:
#   vivado -mode batch -source synth_both.tcl
#
# WHY THE SECOND DESIGN IS HANDLED DIFFERENTLY
#   seg_gate_ctrl is the inner module. Its clock port is  clk , not clk_200,
#   and it has no light_load port. sea_gate_ctrl.xdc constrains both of those,
#   so reading that XDC against it fails. The second pass therefore applies a
#   plain 200 MHz create_clock on  clk  and no XDC. Utilisation is unaffected;
#   only the I/O constraints are skipped, and those are placeholders anyway.
# ---------------------------------------------------------------------------

set part [expr {$argc > 0 ? [lindex $argv 0] : "xc7a35tcpg236-1"}]

set here       [file dirname [file normalize [info script]]]
set src_dir    [file join $here PJT1.srcs sources_1 new]
set constr_dir [file join $here PJT1.srcs constrs_1 new]
set out        [file join $here build]
set out_prog   [file join $here build_prog]
file mkdir $out
file mkdir $out_prog

set xdc_file [file join $constr_dir sea_gate_ctrl.xdc]

set v_thermo [file join $src_dir thermo_decode.v]
set v_dt     [file join $src_dir dead_time_gen.v]
set v_ctrl   [file join $src_dir seg_gate_ctrl.v]
set v_top    [file join $src_dir seg_gate_ctrl_top.v]

foreach f [list $v_thermo $v_dt $v_ctrl $v_top $xdc_file] {
    if {![file exists $f]} { error "Missing file: $f" }
}

# ===========================================================================
# PASS 1 -- STRAPPED design (seg_gate_ctrl_top), exactly as before
# ===========================================================================
puts "\n======================================================="
puts "  PASS 1 of 2 :  seg_gate_ctrl_top   (STRAPPED)"
puts "======================================================="

read_verilog -sv [list $v_thermo $v_dt $v_ctrl $v_top]
synth_design -top seg_gate_ctrl_top -part $part
read_xdc $xdc_file

report_utilization    -file [file join $out utilization_synth.rpt]
report_timing_summary -file [file join $out timing_synth.rpt]
write_checkpoint -force [file join $out post_synth.dcp]

set lut_top  "?"
set ff_top   "?"
foreach line [split [report_utilization -return_string] "\n"] {
    if {[regexp {\|\s*Slice LUTs\*?\s*\|\s*(\d+)} $line -> m]}      { set lut_top $m }
    if {[regexp {\|\s*Slice Registers\s*\|\s*(\d+)} $line -> m]}    { set ff_top  $m }
}
set wns_top [get_property SLACK [get_timing_paths -max_paths 1 -nworst 1 -setup]]
puts "  seg_gate_ctrl_top : $lut_top LUTs, $ff_top FFs, WNS $wns_top ns"

# ===========================================================================
# PASS 2 -- PROGRAMMABLE design (seg_gate_ctrl), no XDC, clock port is clk
# ===========================================================================
puts "\n======================================================="
puts "  PASS 2 of 2 :  seg_gate_ctrl   (FULLY PROGRAMMABLE)"
puts "======================================================="

close_design
read_verilog -sv [list $v_thermo $v_dt $v_ctrl]
synth_design -top seg_gate_ctrl -part $part
create_clock -period 5.000 -name clk_200 [get_ports clk]

report_utilization    -file [file join $out_prog utilization_prog.rpt]
report_timing_summary -file [file join $out_prog timing_prog.rpt]

set lut_prog "?"
set ff_prog  "?"
foreach line [split [report_utilization -return_string] "\n"] {
    if {[regexp {\|\s*Slice LUTs\*?\s*\|\s*(\d+)} $line -> m]}      { set lut_prog $m }
    if {[regexp {\|\s*Slice Registers\s*\|\s*(\d+)} $line -> m]}    { set ff_prog  $m }
}
puts "  seg_gate_ctrl     : $lut_prog LUTs, $ff_prog FFs"

# ===========================================================================
# THE NUMBER WE NEED
# ===========================================================================
puts "\n======================================================="
puts "         COST OF PROGRAMMABILITY  (send this)"
puts "======================================================="
puts "  part                                : $part"
puts "  seg_gate_ctrl      programmable     : $lut_prog LUTs   $ff_prog FFs"
puts "  seg_gate_ctrl_top  strapped         : $lut_top LUTs   $ff_top FFs"
puts "  strapped 200 MHz worst slack        : $wns_top ns"
puts ""
puts "  reports: $out"
puts "           $out_prog"
puts "======================================================="
