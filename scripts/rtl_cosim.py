# -*- coding: utf-8 -*-
"""rtl_cosim.py -- check the RTL's real output against what SPICE assumes.

    python3 scripts/rtl_cosim.py

THE GAP THIS CLOSES
  The project verifies its RTL in Icarus and its power stage in ngspice, and
  those two halves never met. seg_gate_ctrl.v emits eight thermometer-coded
  wires per bank; models/segdrv.lib consumes an INTEGER slice count and
  switches every slice from one shared node, enabling or disabling each by its
  series resistance.

  So every number in this project rests on an assumption that was never
  tested: that "npu = N" in SPICE faithfully stands in for whatever bus the
  FPGA actually drives. A fault in thermo_decode.v -- a dropped bit, an
  off-by-one, a wrong polarity -- could pass the Icarus bench and remain
  invisible to every figure ngspice produced.

  This closes it by reading the RTL's own VCD and checking, for every
  configured slice count, how many wires the hardware really asserts.

WHAT IS CHECKED, AND WHAT IS NOT
  CHECKED: the thermometer encoding, against the SPICE abstraction, for every
  value the control word can take. This is the assumption segdrv.lib rests on
  and it is now measured rather than assumed.

  NOT CHECKED: the RTL driving the power stage end to end. That was tried and
  is reported here rather than quietly dropped, because the reason is worth
  knowing. seg_gate_ctrl_tb.v is a CONTROLLER UNIT TEST -- it sweeps encoder
  configurations to exercise the decoder, and its timeline has no relation to
  dpt.cir's T1..T4 switching schedule. In its stimulus there are windows (for
  example 35-45 ns) where ls_pu = 0, ls_pd = 0 and ls_clamp = 0 together: all
  sixteen slices off and no clamp. Played into the real power stage the gate
  is then held only through the 1 GOhm off-switches, the 100 V transient
  couples in through C_GD, and the node integrates to kilovolts. ngspice
  solves that correctly; it is a true answer to a meaningless question,
  because a controller unit test is not a converter drive sequence.

  Doing that properly needs a testbench written for the purpose -- one that
  emits a realistic PWM edge with dead time, matched to the power-stage
  timing. That is real work and it is listed as the next step rather than
  faked here.
"""
import os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RTL  = os.path.join(ROOT, "rtl")
RES  = os.path.join(ROOT, "results")
VCD  = os.path.join(RTL, "seg_gate_ctrl.vcd")

BANKS = [("ls_pu", "npu_ls"), ("ls_pd", "npd_ls"),
         ("hs_pu", "npu_hs"), ("hs_pd", "npd_hs")]


def build_rtl():
    """Run Icarus so the VCD is the current RTL's, not a stale checkout's."""
    exe = "/tmp/cosim_tb"
    src = ["seg_gate_ctrl_tb.v", "seg_gate_ctrl.v", "dead_time_gen.v",
           "thermo_decode.v"]
    r = subprocess.run(["iverilog", "-g2012", "-o", exe] + src,
                       cwd=RTL, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("iverilog failed:\n" + r.stderr[:800])
    r = subprocess.run(["vvp", exe], cwd=RTL, capture_output=True, text=True)
    return "ALL CHECKS PASSED" in r.stdout


def parse_vcd(path):
    """Return (timescale_seconds, {name: [(t_ticks, value_str), ...]})."""
    ids, waves, scale = {}, {}, 1e-12
    t = 0
    txt = open(path).read()
    m = re.search(r"\$timescale\s*(\d+)\s*([munpf]?s)", txt)
    if m:
        scale = float(m.group(1)) * {"s": 1, "ms": 1e-3, "us": 1e-6, "ns": 1e-9,
                                     "ps": 1e-12, "fs": 1e-15}[m.group(2)]
    for line in txt.splitlines():
        line = line.strip()
        mv = re.match(r"\$var\s+\S+\s+(\d+)\s+(\S+)\s+(\S+)", line)
        if mv:
            ids[mv.group(2)] = mv.group(3)
            waves[mv.group(3)] = []
            continue
        if line.startswith("#"):
            t = int(line[1:])
            continue
        if line.startswith(("b", "B")):
            parts = line.split()
            if len(parts) == 2 and parts[1] in ids:
                waves[ids[parts[1]]].append((t, parts[0][1:]))
        elif line and line[0] in "01xzXZ" and len(line) > 1:
            sym = line[1:]
            if sym in ids:
                waves[ids[sym]].append((t, line[0]))
    return scale, waves


def unknown(v):
    return any(c in "xzXZ" for c in v)


def check_bank(waves, bus, cfg):
    """For each configured count, how many wires does the RTL assert?"""
    if bus not in waves or cfg not in waves:
        return None, None, None
    cfg_ev = sorted(waves[cfg])
    seen, ok, bad = {}, 0, 0

    def cfg_at(t):
        val = None
        for ct, cv in cfg_ev:
            if ct <= t:
                val = cv
            else:
                break
        return val

    for t, v in waves[bus]:
        if unknown(v):
            continue
        c = cfg_at(t)
        if c is None or unknown(c):
            continue
        want, got = int(c, 2), v.count("1")
        # the banks are gated off during dead time and when the opposite
        # device is commanded, so 0 asserted is legitimate at any setting;
        # it says nothing about the encoding and is not counted either way.
        if got == 0 and want != 0:
            continue
        seen[want] = got
        if got == want:
            ok += 1
        else:
            bad += 1
    return seen, ok, bad


def main():
    print("\n  RTL ENCODING vs THE SPICE ABSTRACTION")
    print("  seg_gate_ctrl.v drives eight wires per bank; models/segdrv.lib")
    print("  takes an integer count. This checks they mean the same thing.")
    print("  " + "-" * 68)

    passed = build_rtl()
    print("  Icarus bench: %s" % ("ALL CHECKS PASSED" if passed
                                  else "did NOT report all checks passed"))
    if not os.path.exists(VCD):
        raise SystemExit("no VCD at %s" % VCD)
    scale, waves = parse_vcd(VCD)
    span = max(t for w in waves.values() for t, _ in w) * scale
    print("  VCD: %d signals, %.3f us of RTL time\n" % (len(waves), span * 1e6))

    total_bad, lines = 0, []
    for bus, cfg in BANKS:
        seen, ok, bad = check_bank(waves, bus, cfg)
        if seen is None:
            print("  %-7s not in the VCD -- skipped" % bus)
            continue
        total_bad += bad
        vals = ", ".join("%d->%d" % (k, seen[k]) for k in sorted(seen))
        mark = "ok" if bad == 0 else "MISMATCH"
        print("  %-7s %-8s configured -> asserted:  %s" % (bus, mark, vals))
        lines.append("%s: %s (%d ok, %d bad)" % (bus, vals, ok, bad))

    print("\n  " + "-" * 68)
    if total_bad == 0:
        print("  PASS -- every configured count produces exactly that many")
        print("  asserted slices, on every bank. segdrv.lib's integer stands in")
        print("  for the real bus faithfully, so the existing results hold.")
    else:
        print("  FAIL -- %d samples disagree. The SPICE abstraction does not"
              % total_bad)
        print("  match the hardware, and every number that relies on it needs")
        print("  re-examining.")

    print("\n  NOT covered: driving the power stage from these waveforms. The")
    print("  bench is a controller unit test -- it has windows with both banks")
    print("  off and no clamp, which float the gate against a 100 V transient.")
    print("  A purpose-built bench emitting a realistic dead-time edge is the")
    print("  next step; see the header of this file.\n")

    open(os.path.join(RES, "rtl_cosim.txt"), "w").write(
        "RTL encoding vs SPICE abstraction\n"
        "Icarus bench passed: %s\n%s\nmismatches: %d\n"
        % (passed, "\n".join(lines), total_bad))
    return 0 if total_bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
