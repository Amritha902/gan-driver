#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# LIVE-BUCK.sh -- run the CONVERTER in front of the panel, right now.
#
#     bash proof/LIVE-BUCK.sh
#
# proof/LIVE-SIM.sh runs the double-pulse bench: one switching edge, which is
# where the crosstalk result is measured. This runs the converter that bench
# is a measurement of -- 100 V in, 48.5 V out, 236 W into a 10 ohm load at
# 500 kHz -- for 150 switching cycles, twice, about twenty seconds.
#
# Nothing is read from a saved result. The numbers on screen are measured
# while the panel watches, and printed beside the numbers on the slide.
# ---------------------------------------------------------------------------
set -u
cd "$(dirname "$0")/.."

for t in ngspice python3; do
  command -v "$t" >/dev/null 2>&1 || { echo "  $t not found on PATH."; exit 1; }
done

python3 scripts/live_buck.py "$@" || exit 1

PNG="results/buck_run.png"
if [ -f "$PNG" ]; then
  if   command -v open     >/dev/null 2>&1; then open "$PNG"
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$PNG" >/dev/null 2>&1 &
  else echo "  (open $PNG to see the waveforms)"
  fi
fi
