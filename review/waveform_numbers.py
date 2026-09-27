"""waveform_numbers.py -- the crosstalk waveform's anatomy, parsed from the run.

scripts/waveform_anatomy.py measures what the trace is doing; this hands those
numbers to the slide so the caption cannot say something the run did not.
"""
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "results", "waveform_anatomy.txt")
_t = open(SRC, encoding="utf-8").read()


def _f(pat):
    m = re.search(pat, _t)
    if not m:
        raise SystemExit("waveform_anatomy.txt: %r missing -- re-run "
                         "scripts/waveform_anatomy.py" % pat)
    return float(m.group(1))


VBUS      = _f(r"starts at\s+([\d.]+) V")
FALL_NS   = _f(r"falls 90% -> 10% in\s+([\d.]+) ns")
SLEW_PK   = _f(r"peak slew \(0\.2 ns window\)\s+([\d.]+) V/ns")
REST_BAD  = _f(r"no clamp, 0 V rail\s+\+?(-?[\d.]+) V")
PEAK_BAD  = _f(r"no clamp, 0 V rail\s+\+?-?[\d.]+ V\s+\+?(-?[\d.]+) V")
LIFT_BAD  = _f(r"no clamp, 0 V rail\s+\+?-?[\d.]+ V\s+\+?-?[\d.]+ V\s+\+?(-?[\d.]+) V")
REST_GOOD = _f(r"clamp on, -2 V rail\s+\+?(-?[\d.]+) V")
PEAK_GOOD = _f(r"clamp on, -2 V rail\s+\+?-?[\d.]+ V\s+\+?(-?[\d.]+) V")
LIFT_GOOD = _f(r"clamp on, -2 V rail\s+\+?-?[\d.]+ V\s+\+?-?[\d.]+ V\s+\+?(-?[\d.]+) V")

if __name__ == "__main__":
    for k, v in sorted(globals().items()):
        if k.isupper() and isinstance(v, float):
            print("  %-10s %9.3f" % (k, v))
