# ---------------------------------------------------------------------------
# synth_only.tcl -- utilisation + timing, with NO board knowledge required.
#
#   vivado -mode batch -source synth_only.tcl
#   vivado -mode batch -source synth_only.tcl -tclargs xc7a100tcsg324-1
#
# Why this exists separately from build.tcl: build.tcl runs place, route and
# write_bitstream, and those need real package pins. The pins in the XDC are
# deliberate placeholders, so build.tcl cannot complete on someone else's
# machine without their board pinout.
#
# Synthesis alone answers the two questions we actually need: how much fabric
# does the controller use, and does it close timing at 200 MHz. Neither needs
# a pin assignment or a board.
# ---------------------------------------------------------------------------
set part [expr {$argc > 0 ? [lindex $argv 0] : "xc7a35tcpg236-1"}]
# Second optional arg: the top module. Default is the STRAPPED design.
# Pass seg_gate_ctrl to synthesise the fully-programmable one instead --
# the two together give the fabric cost of programmability in Vivado
# numbers rather than yosys estimates.
set top  [expr {$argc > 1 ? [lindex $argv 1] : "seg_gate_ctrl_top"}]
set here [file dirname [file normalize [info script]]]
set out  [file join $here build]
file mkdir $out

# Find each source next to this script FIRST, then one level up. In the repo
# the modules live in rtl/ and this script in rtl/vivado/; when the files are
# sent out as one flat folder they all sit together. Both must work.
proc src {name} {
    global here
    foreach d [list $here [file dirname $here]] {
        set p [file join $d $name]
        if {[file exists $p]} { return $p }
    }
    error "cannot find $name next to $here or in its parent"
}

puts "== part: $part   top: $top"
read_verilog -sv [list \
    [src thermo_decode.v] \
    [src dead_time_gen.v] \
    [src seg_gate_ctrl.v] \
    [src seg_gate_ctrl_top.v]]

# Clock only. The pin-location and IOSTANDARD lines in seg_gate_ctrl.xdc are
# board-specific placeholders and are not needed for synthesis numbers.
create_clock -period 5.000 -name clk_200 [get_ports clk_200]

synth_design -top $top -part $part
report_utilization    -file [file join $out utilization_synth.rpt]
report_timing_summary -file [file join $out timing_synth.rpt]
write_checkpoint -force [file join $out post_synth.dcp]

# ---- print the answer to the console, so it can simply be copied ----------
puts "=================== NUMBERS WE NEED ==================="
puts "part                : $part"
set u [report_utilization -return_string]
foreach line [split $u "\n"] {
    if {[regexp {Slice LUTs|Slice Registers|Bonded IOB|LUT as Logic|Slice$} $line]} {
        puts "  $line"
    }
}
set wns [get_property SLACK [get_timing_paths -max_paths 1 -nworst 1 -setup]]
puts "worst negative slack: $wns ns   (>= 0 means 200 MHz timing is met)"
puts "reports written to  : $out"
puts "======================================================="
