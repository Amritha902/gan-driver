# Headless synthesis for the policy-engine RTL.
#   vivado -mode batch -source cloud/synth.tcl
#
# Produces cloud/utilisation.rpt and cloud/timing.rpt — the two artefacts Review 1
# deliverable 4 asks for. No GUI, no project file, nothing to click.

set part      xc7z020clg400-1        ;# Zynq-7000, PYNQ-Z2 / Zedboard class
set top       pareto_table
set outdir    [file normalize [file dirname [info script]]]
set root      [file dirname $outdir]

puts "== reading RTL =="
read_verilog [glob $root/rtl/*.v]

# $readmemh needs the .mem visible at elaboration
set_property include_dirs $root/data [current_fileset]
file copy -force $root/data/pareto_table.mem [pwd]/pareto_table.mem

puts "== synth_design (top = $top, part = $part) =="
synth_design -top $top -part $part -mode out_of_context

puts "== reports =="
report_utilization        -file $outdir/utilisation.rpt
report_utilization -hierarchical -file $outdir/utilisation_hier.rpt
report_timing_summary     -file $outdir/timing.rpt

puts "== done =="
puts "   utilisation -> $outdir/utilisation.rpt"
puts "   timing      -> $outdir/timing.rpt"
puts ""
puts "   For the report, quote: LUTs, FFs, BRAM tiles, and WNS from timing.rpt."
puts "   BRAM count is the number that matters — it sizes the Pareto table (M3.3)."
