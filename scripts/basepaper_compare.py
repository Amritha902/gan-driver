# -*- coding: utf-8 -*-
"""basepaper_compare.py -- implement the BASE PAPER's driver and run it
against ours on the SAME testbench.

    python3 scripts/basepaper_compare.py

METHOD
  sim/dpt.cir is used verbatim for both runs. The ONLY edit is the driver:
  the two SEGDRV instances are replaced by ZHANGDRV plus its pattern-step
  sources. Power stage, device model, timing, options and initial conditions
  are byte-identical, so any difference in the numbers is attributable to the
  control scheme and to nothing else.

  BASE   Zhang, Yu, Leng, Cui, Deng and Ng, "A Segmented Gate Driver for
         E-mode GaN HEMTs with Simple Driving Strength Pattern Control,"
         Proc. IEEE ISPSD, 2020, pp. 102-105. Xplore 9170108. Seven slices
         on E-mode GaN, engaged as a timed pattern across the edge, the
         pattern selected by ONE external bias resistor. No Miller clamp,
         no negative off-bias rail.
  OURS   Eight-slice output stage, every field programmable from an FPGA,
         plus the active Miller clamp and the selectable negative off-bias.

  Same device (E-mode GaN), same architecture (segmented output stage) --
  which is exactly why this is the base paper. The comparison is therefore
  about CONTROL, not about the power stage or the transistor.
"""
import os, re, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM  = os.path.join(ROOT, "sim")
BASE_SRC = open(os.path.join(SIM, "dpt.cir")).read()

# Pattern step timing. The paper gives 0.5-5 ns; 3 ns sits mid-range and is
# not tuned to favour either side. NSEG=2 of 7 slices engage first.
TSTEP, NSEG = "3n", 2


def make(clken, vneg, base_paper=False):
    t = BASE_SRC
    t = re.sub(r"^\.param CLKEN=.*$", ".param CLKEN=%d" % clken, t, flags=re.M)
    t = re.sub(r"^\.param VNEG=.*$",  ".param VNEG=%d"  % vneg,  t, flags=re.M)
    if base_paper:
        t = t.replace(".include ../models/segdrv.lib",
                      ".include ../models/zhangdrv.lib")
        # Low side: swap SEGDRV for ZHANGDRV. The pattern step replaces the
        # clamp input -- their driver has no clamp, so the pin carries the
        # one control their driver does have.
        t = t.replace(
            "Xdrvls lspu lspd lsclk lsg lsvp lsvn 0 SEGDRV\n"
            "+      params: npu={NPU_LS} npd={NPD_LS} runit={RUNIT} rclamp=0.5",
            "Vsegls lsseg 0 PWL(0 0 {T4+TSTEP} 0 {T4+TSTEP+TR} 1)\n"
            "Xdrvls lspu lspd lsseg lsg lsvp lsvn 0 ZHANGDRV\n"
            "+      params: nseg={NSEG} runit={RUNIT}")
        t = t.replace(
            "Xdrvhs hspu hspd hsclkl hsg hsvp hsvn sw SEGDRV\n"
            "+      params: npu={NPU_HS} npd={NPD_HS} runit={RUNIT} rclamp=0.5",
            "Vseghs segh 0 PWL(0 0 {T2+TSTEP} 0 {T2+TSTEP+TR} 1)\n"
            "Bseghs hsseg sw V = {v(segh)}\n"
            "Xdrvhs hspu hspd hsseg hsg hsvp hsvn sw ZHANGDRV\n"
            "+      params: nseg={NSEG} runit={RUNIT}")
        t = t.replace(".param VBUS=100",
                      ".param TSTEP=%s NSEG=%d\n.param VBUS=100" % (TSTEP, NSEG))
    # dpt.cir already carries a .control block that runs the transient and
    # writes out.dat. Append the measurement INSIDE it rather than adding a
    # second block, which ngspice ignores.
    t = t.replace("\nquit",
                  "\nlet vgs = v(hsg) - v(sw)\n"
                  "meas tran vspur MAX vgs from=2.015u to=2.10u\nquit", 1)
    return t


def run(tag, deck):
    p = os.path.join("/tmp", tag + ".cir")
    open(p, "w").write(deck)
    r = subprocess.run(["ngspice", "-b", p], capture_output=True, text=True,
                       timeout=900, cwd=SIM)
    m = re.search(r"^vspur\s*=\s*([-\d.e+]+)", r.stdout, re.M)
    err = [l for l in (r.stdout + r.stderr).splitlines()
           if re.search(r"error|singular|aborted", l, re.I)][:2]
    return (float(m.group(1)) if m else None), err


def main():
    VTH = 1.4
    cases = [
        ("BASE PAPER   7-slice pattern, no clamp, 0 V", make(0, 0, base_paper=True)),
        ("OURS         clamp OFF, 0 V  (their control)", make(0, 0)),
        ("OURS         clamp ON,  0 V", make(1, 0)),
        ("OURS         clamp ON, -2 V  (shipped)", make(1, -2)),
    ]
    print("\n  BASE PAPER vs THIS WORK")
    print("  Zhang et al., ISPSD 2020 -- same device (E-mode GaN), same")
    print("  architecture (segmented). Identical testbench (sim/dpt.cir);")
    print("  only the driver differs.")
    print("  " + "-" * 74)
    print("  %-44s %10s %10s" % ("", "V_spur", "margin"))
    for label, deck in cases:
        v, err = run(label.split()[0].lower() + str(abs(hash(label)) % 999), deck)
        if v is None:
            print("  %-44s   FAILED  %s" % (label, err[0][:28] if err else ""))
            continue
        marg = VTH - v
        print("  %-44s %9.3f V %+9.3f V   %s"
              % (label, v, marg, "FALSE TURN-ON" if marg < 0 else "safe"))
    print("\n  Threshold %.1f V. Margin = Vth - max(V_GS,HS) at the hard turn-on (T4).\n" % VTH)


if __name__ == "__main__":
    main()
