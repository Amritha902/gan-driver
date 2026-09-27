#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# LIVE-SIM.sh -- simulate the circuit in front of the panel, right now.
#
#     bash proof/LIVE-SIM.sh
#
# Two ngspice transients of sim/dpt.cir, about ten seconds, then the waveform
# they produced. Nothing is read from a saved result: the numbers on screen
# are measured while the panel watches, and printed beside the numbers on the
# slide so the two can be compared without taking anyone's word for it.
#
# Why bash and not zsh: proof/RUN-LIVE.sh is zsh, hardcodes ~/gan-driver, and
# includes an Octave step this project no longer uses. This runs anywhere
# ngspice and python3 do, from wherever it is checked out.
# ---------------------------------------------------------------------------
set -u
cd "$(dirname "$0")/.."

for t in ngspice python3; do
  command -v "$t" >/dev/null 2>&1 || { echo "  $t not found on PATH."; exit 1; }
done

python3 scripts/live_demo.py "$@" || exit 1

PNG="results/live_run.png"
if [ -f "$PNG" ]; then
  if   command -v open     >/dev/null 2>&1; then open "$PNG"
  elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$PNG" >/dev/null 2>&1 &
  else echo "  (open $PNG to see the waveforms)"
  fi
fi
