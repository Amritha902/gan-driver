#!/usr/bin/env bash
# Rebuild the three decks from source, in the one order that works.
#
#   bash review/BUILD-DECK.sh
#
# The passes are not independent and rebuild_pass is not idempotent, so this
# always runs the whole chain from build.py. build.py and simplify.py resolve
# their paths relative to the working directory and must run from review/;
# the rest run from the repository root.
set -euo pipefail
cd "$(dirname "$0")/.."
ROOT=$PWD

# The passes import one another, and these files get rewritten and imported
# within the same second, which is inside the resolution of the mtime stamp
# Python uses to decide whether cached bytecode is stale. It then runs the
# previous version of a pass and reports on a deck it did not produce -- an
# hour was lost to exactly that. Start from source every time.
find review -name '__pycache__' -type d -prune -exec rm -rf {} + 2>/dev/null || true
export PYTHONDONTWRITEBYTECODE=1

echo "== test the guards before trusting them"
python3 review/test_plain_pass.py
python3 review/test_link_pass.py
python3 review/test_check_package.py

for s in build.py simplify.py; do
    echo "== $s"
    ( cd review && python3 "$s" )
done
for s in converter_pass.py captions_pass.py rebuild_pass.py; do
    echo "== $s"
    python3 "review/$s"
done

echo "== consistency"
python3 review/check_consistency.py
echo
echo "== package integrity"
python3 review/check_package.py
echo
echo "Decks written to review/."
