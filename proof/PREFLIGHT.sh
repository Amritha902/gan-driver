#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# PREFLIGHT.sh -- run this the night before, on the machine you will present
# from. Not on any other machine: "it worked in the cloud" is not the claim
# being tested.
#
#     bash proof/PREFLIGHT.sh
#
# Checks everything proof/LIVE-SIM.sh needs, then actually runs it once and
# times it. Exits non-zero if anything would fail in the room.
# ---------------------------------------------------------------------------
set -u
cd "$(dirname "$0")/.."
FAIL=0
ok()   { printf "  \033[32mOK\033[0m    %s\n" "$1"; }
bad()  { printf "  \033[31mFAIL\033[0m  %s\n" "$1"; FAIL=1; }
note() { printf "        %s\n" "$1"; }

echo
echo "  PREFLIGHT -- $(hostname), $(date '+%Y-%m-%d %H:%M')"
echo "  ------------------------------------------------------------"

for t in ngspice python3; do
  if command -v "$t" >/dev/null 2>&1; then ok "$t  -> $(command -v $t)"
  else bad "$t is NOT on PATH"
       [ "$t" = ngspice ] && note "macOS: brew install ngspice"
  fi
done

if command -v ngspice >/dev/null 2>&1; then
  V=$(ngspice -v 2>&1 | grep -m1 -o 'ngspice-[0-9]*' || true)
  [ -n "$V" ] && ok "version $V" || bad "ngspice will not report a version"
fi

if command -v python3 >/dev/null 2>&1; then
  for m in numpy matplotlib; do
    if python3 -c "import $m" 2>/dev/null; then
      ok "python module $m  $(python3 -c "import $m;print($m.__version__)")"
    else
      bad "python module $m missing"; note "pip3 install $m"
    fi
  done
fi

for f in sim/dpt.cir models/egan.lib models/segdrv.lib scripts/gansim.py \
         scripts/live_demo.py; do
  [ -f "$f" ] && ok "$f" || bad "$f is missing from this checkout"
done

if [ "$FAIL" -eq 0 ]; then
  echo
  echo "  running proof/LIVE-SIM.sh once, as a rehearsal ..."
  S=$(date +%s)
  if python3 scripts/live_demo.py --no-plot >/tmp/preflight.out 2>&1; then
    E=$(date +%s)
    grep -E "OFF gate|margin, shipped|wall clock" /tmp/preflight.out | sed 's/^/    /'
    ok "live demo completed in $((E-S)) s"
    [ $((E-S)) -gt 30 ] && note "slower than expected -- run it once more before the review"
  else
    bad "the live demo did not complete"; sed 's/^/    /' /tmp/preflight.out | tail -5
  fi
fi

echo "  ------------------------------------------------------------"
if [ "$FAIL" -eq 0 ]; then
  echo "  READY. proof/LIVE-SIM.sh will run in the room."
else
  echo "  NOT READY. Fix the FAIL lines above, then run this again."
fi
echo
exit $FAIL
