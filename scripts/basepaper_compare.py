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

# Their driver has two controls: how many of the seven slices engage first
# (NSEG) and how long before the rest join (TSTEP, which the paper puts in the
# 0.5-5 ns range). Both matter a great deal -- across that range their margin
# runs from -0.278 V to +0.407 V -- so picking one setting for them and then
# reporting how far ahead we are is not a comparison, it is a choice of
# opponent. SEARCH below is their own stated range, and main() quotes them at
# their BEST point in it. Beating a strawman is worth nothing.
TSTEP, NSEG = "3n", 2
SEARCH_NSEG  = (1, 2, 3, 4)
SEARCH_TSTEP = ("2n", "3n", "4n", "5n")


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


def search_base(vth):
    """Run their driver across its own stated range; return the best point.

    Reported in full, not just the winner: the spread is the honest context
    for any claim about how far ahead we are.
    """
    global NSEG, TSTEP
    keep = (NSEG, TSTEP)
    best, grid = (None, None, -9.0), []
    for n in SEARCH_NSEG:
        row = []
        for t in SEARCH_TSTEP:
            NSEG, TSTEP = n, t
            v, _ = run("srch%d%s" % (n, t), make(0, 0, base_paper=True))
            m = (vth - v) if v is not None else None
            row.append(m)
            if m is not None and m > best[2]:
                best = (n, t, m)
        grid.append((n, row))
    NSEG, TSTEP = keep
    return best, grid


def main():
    VTH = 1.4
    print("\n  BASE PAPER vs THIS WORK")
    print("  Zhang et al., ISPSD 2020 -- same device (E-mode GaN), same")
    print("  architecture (segmented). Identical testbench (sim/dpt.cir);")
    print("  only the driver differs.")

    # --- their driver, across its own range --------------------------------
    best, grid = search_base(VTH)
    print("\n  Their driver over its own stated range, margin in V:")
    print("      %-8s %s" % ("", "  ".join("%7s" % t for t in SEARCH_TSTEP)))
    for n, row in grid:
        cells = "  ".join(("%+7.3f" % m) if m is not None else "   FAIL" for m in row)
        print("      nseg=%-3d %s" % (n, cells))
    print("  Their best: nseg=%d, TSTEP=%s -> %+.3f V. That is the number we"
          % (best[0], best[1], best[2]))
    print("  compare against -- quoting them anywhere worse would be choosing")
    print("  the opponent rather than measuring against it.")

    global NSEG, TSTEP
    NSEG, TSTEP = best[0], best[1]
    cases = [
        ("BASE PAPER   7-slice pattern at its best, no clamp", make(0, 0, base_paper=True)),
        ("OURS         clamp OFF, 0 V  (their control)", make(0, 0)),
        ("OURS         clamp ON,  0 V", make(1, 0)),
        ("OURS         clamp ON, -2 V  (shipped)", make(1, -2)),
    ]
    print("  " + "-" * 74)
    print("  %-44s %10s %10s" % ("", "V_spur", "margin"))
    ours = None
    for label, deck in cases:
        v, err = run(label.split()[0].lower() + str(abs(hash(label)) % 999), deck)
        if v is None:
            print("  %-44s   FAILED  %s" % (label, err[0][:28] if err else ""))
            continue
        marg = VTH - v
        if label.startswith("OURS") and "shipped" in label:
            ours = marg
        print("  %-44s %9.3f V %+9.3f V   %s"
              % (label, v, marg, "FALSE TURN-ON" if marg < 0 else "safe"))
    print("\n  Threshold %.1f V. Margin = Vth - max(V_GS,HS) at the hard turn-on (T4)." % VTH)
    if ours and best[2] > 0:
        print("  Ours is %.1fx their best (%+.3f V against %+.3f V). Against their"
              % (ours / best[2], ours, best[2]))
        print("  worst in-range setting it would read far higher; that number is not")
        print("  the one to quote.\n")


if __name__ == "__main__":
    main()
