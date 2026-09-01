#!/bin/sh
# mutate.sh -- reproduces the mutation-test number quoted in the deck.
#
# Injects a real shoot-through bug (the low-side pull-up bank driven
# unconditionally, ignoring both ls_on and the dead time) and shows the bench
# catching it. Run from rtl/:   sh mutate.sh
#
# NOTE on equivalent mutants: deleting only the "&& !in_dt" term from ls_pu or
# hs_pu changes NOTHING, because dead_time_gen already holds ls_on and hs_on
# low for the whole dead time (that is property T7). Those mutants are
# semantically equivalent and are correctly not caught. The mutation below is
# a genuine bug.
set -e
D=$(mktemp -d); cp ./*.v "$D"/; cd "$D"

iverilog -o clean seg_gate_ctrl_tb.v thermo_decode.v dead_time_gen.v seg_gate_ctrl.v
echo "--- unmutated ---"; ./clean 2>&1 | grep -E "PASSED|FAILED"

sed -i 's|^    assign ls_pu = .*|    assign ls_pu = pu_ls_v;   // MUTANT|' seg_gate_ctrl.v
iverilog -o mutant seg_gate_ctrl_tb.v thermo_decode.v dead_time_gen.v seg_gate_ctrl.v
echo "--- with the shoot-through mutant ---"
./mutant 2>&1 | grep -E "PASSED|FAILED"
echo "properties that fired:"
./mutant 2>&1 | grep -oE "T[0-9]+" | sort | uniq -c
cd - >/dev/null; rm -rf "$D"
