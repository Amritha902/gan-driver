#!/bin/sh
# Run every RTL testbench. Exits non-zero if any fails.
cd "$(dirname "$0")"
python3 scripts/gen_synthetic_table.py >/dev/null
rc=0
for tb in quantiser pareto_table; do
  iverilog -g2012 -o "/tmp/tb_$tb" "rtl/$tb.v" "rtl/tb/tb_$tb.v"
  out=$(vvp "/tmp/tb_$tb")
  echo "$out"
  echo "$out" | grep -q "ALL PASS" || rc=1
done
verilator --lint-only -Wall --top-module pareto_table rtl/pareto_table.v || rc=1
verilator --lint-only -Wall --top-module quantiser    rtl/quantiser.v    || rc=1
[ $rc -eq 0 ] && echo "== ALL TESTBENCHES PASS ==" || echo "== FAILURES =="
exit $rc
