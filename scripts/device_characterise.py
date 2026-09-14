# -*- coding: utf-8 -*-
"""device_characterise.py -- what models/egan.lib actually IS.

    python3 scripts/device_characterise.py

THE PROBLEM THIS ADDRESSES, AND THE ONE IT DOES NOT
  Every number in this project rests on one behavioural GaN model. The deck
  says so. scripts/robust.py asks the related question -- how much would the
  parameters have to move to change the conclusion -- and answers it (the
  ceiling stays between 4.3 and 7.7 % across +-50 % C_GD, +-20 % V_th and the
  rest).

  But neither answers the question a device engineer asks first: IS THIS AN
  EPC2010C? The model claims to be "EPC2010C-class". Nobody has ever extracted
  its terminal characteristics and put them next to the manufacturer's curves,
  so the claim has been unfalsifiable -- not wrong, unfalsifiable, which is
  worse in a study that depends on it.

  This does not validate the model. It CANNOT: the datasheet is not in this
  repository and this container has no route to it. What it does is extract
  the model's own characteristics into a table in the form a datasheet states
  them, so that anyone with the datasheet open can check it in five minutes
  instead of reading the netlist. That converts an unfalsifiable assumption
  into a falsifiable one, and it is the honest thing available here.

WHAT IS EXTRACTED, AND WHY EACH ONE
  R_DS(on) vs V_GS      the number the whole loss budget scales with
  R_DS(on) vs T_J       the model's temperature law, which drives every hot
                        corner in the study
  C_iss, C_oss, C_rss   vs V_DS, because C_rss (= C_GD) is the mechanism the
                        entire project is about, and a datasheet states it as
                        a curve rather than a number
  Q_g                   gate charge to the drive rail, which sets driver loss
  V_SD reverse          the third-quadrant drop -- GaN's one real disadvantage
                        and the thing the -2 V rail makes worse
"""
import os, re, subprocess, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "models")
RES = os.path.join(ROOT, "results")
CLAIM = dict(rds=25.0, vth=1.4, vds=200.0)     # what egan.lib's header claims


def ngspice(deck):
    p = "/tmp/devchar.cir"
    open(p, "w").write(deck)
    r = subprocess.run(["ngspice", "-b", p], capture_output=True, text=True,
                       timeout=900)
    return r.stdout


def meas(out, name):
    m = re.search(r"^%s\s*=\s*([-\d.e+]+)" % name, out, re.M)
    return float(m.group(1)) if m else None


HEAD = ".include %s/egan.lib\n" % MODELS


def rds_vs_vgs(tj=25):
    """On-resistance at a small V_DS, swept over gate drive."""
    kt = 1 + 0.009 * (tj - 25)
    rows = []
    for vgs in (3.0, 4.0, 5.0, 6.0):
        d = (HEAD + ".param BH={%g}\n" % (5.55 / kt)
             + ".param VTH={%g}\n" % (1.4 - 0.0015 * (tj - 25))
             + "Vg g 0 DC %g\nVd d 0 DC 0.1\n" % vgs
             + "X1 d g 0 EGAN params: vth={VTH} bh={BH}\n"
             + ".control\nop\nlet r = 0.1/abs(i(vd))\nprint r\nquit\n.endc\n.end\n")
        out = ngspice(d)
        m = re.search(r"^r\s*=\s*([-\d.e+]+)", out, re.M)
        rows.append((vgs, float(m.group(1)) * 1e3 if m else None))
    return rows


def rds_vs_tj():
    return [(tj, rds_vs_vgs(tj)[2][1]) for tj in (25, 75, 125)]


def caps_vs_vds():
    """C_iss, C_oss and C_rss from the model's own C(V) law.

    Read from the diode junction law rather than measured with an AC sweep:
    the capacitances in egan.lib ARE that law (CJO/(1+V/VJ)^M), so evaluating
    it is exact and an AC extraction would only add solver noise to the same
    numbers. The point is to state them the way a datasheet does.
    """
    src = open(os.path.join(MODELS, "egan.lib")).read()
    def p(model, key):
        m = re.search(r"\.model\s+%s\s+D\(([^)]*)\)" % model, src, re.I)
        if not m:
            return None
        mm = re.search(r"%s\s*=\s*([\d.eE+-]+)([pnu]?)" % key, m.group(1))
        if not mm:
            return None
        return float(mm.group(1)) * {"p": 1e-12, "n": 1e-9, "u": 1e-6,
                                     "": 1.0}[mm.group(2)]
    cgd0, vj_gd, m_gd = p("DGD", "CJO"), p("DGD", "VJ"), p("DGD", "M")
    cds0, vj_ds, m_ds = p("DDS", "CJO"), p("DDS", "VJ"), p("DDS", "M")
    mm = re.search(r"cgs\s*=\s*([\d.]+)p", src)
    cgs = float(mm.group(1)) * 1e-12 if mm else None
    rows = []
    for v in (0.0, 10.0, 50.0, 100.0, 150.0):
        crss = cgd0 / (1 + v / vj_gd) ** m_gd
        cds = cds0 / (1 + v / vj_ds) ** m_ds
        rows.append((v, (cgs + crss) * 1e12, (cds + crss) * 1e12, crss * 1e12))
    return rows


def qg(ig=10e-3, vbus=100.0, rd=10.0):
    """Gate charge to the drive rail, the way a datasheet's Q_g test does.

    Constant current into the gate with the device switching a real load, and
    the time for V_GS to reach the rail. Q = I * t.

    The first version measured 0.0 nC. Two faults, both mine: the ramp start
    was subtracted from a WHEN time that ngspice reports relative to zero, and
    with `uic` and no .ic the gate node had no defined starting value, so the
    measurement could trigger on the first timepoint. Now the source starts at
    t = 0, the gate is initialised explicitly, and the result is checked
    against C_iss * 5 V for order of magnitude before it is reported.
    """
    d = (HEAD + "Vbus bus 0 DC %g\nRd bus d %g\n" % (vbus, rd)
         + "Ig 0 g DC %g\n" % ig
         + "X1 d g 0 EGAN\n"
         + ".ic v(g)=0 v(d)=%g\n" % vbus
         + ".tran 0.05n 2u uic\n"
         + ".control\nrun\nmeas tran tg WHEN v(g)=5 RISE=1\n"
           "quit\n.endc\n.end\n")
    t = meas(ngspice(d), "tg")
    if t is None or t <= 0:
        return None
    return ig * t * 1e9                                        # nC


def vsd(iload=10.0):
    """Third-quadrant drop at rated current, at both off-bias rails.

    The gate must be referenced to the SOURCE. The first version tied it to
    ground, so as the source floated up the device saw a growing negative
    V_GS, drove itself further off, and the operating point ran away to
    69 V -- a number reported identically for both rails, which is the tell
    that the rail was not in the loop at all. With V_GS referenced properly,
    the two rails differ by |V_off| exactly as the physics says.
    """
    rows = []
    for voff in (0.0, -2.0):
        d = (HEAD + "Vgs g s DC %g\n" % voff
             + "Is 0 s DC %g\n" % iload
             + "X1 0 g s EGAN\n"
             + ".control\nop\nprint v(s)\nquit\n.endc\n.end\n")
        out = ngspice(d)
        m = re.search(r"^v\(s\)\s*=\s*([-\d.e+]+)", out, re.M)
        rows.append((voff, abs(float(m.group(1))) if m else None))
    return rows


def main():
    print("\n  WHAT models/egan.lib ACTUALLY IS")
    print("  Extracted from the model, stated the way a datasheet states it,")
    print("  so it can be checked against one. This is NOT a validation --")
    print("  the datasheet is not in this repository.")
    print("  " + "=" * 66)

    lines = []

    def out(s=""):
        print("  " + s if s else "")
        lines.append(s)

    out("R_DS(on) vs gate drive, at 25 C, V_DS = 0.1 V")
    for vgs, r in rds_vs_vgs():
        out("    V_GS = %.1f V   %s" % (vgs, "%.1f mohm" % r if r else "  -"))
    out("  claimed in the model header: %.0f mohm at 5 V" % CLAIM["rds"])
    out()

    out("R_DS(on) vs junction temperature, at V_GS = 5 V")
    base = None
    for tj, r in rds_vs_tj():
        base = base or r
        out("    T_J = %3d C    %s%s" % (tj, "%.1f mohm" % r if r else "  -",
            "   (x%.2f)" % (r / base) if r and base else ""))
    out("  GaN datasheets put this near x2 from 25 to 125 C")
    out()

    out("Capacitances vs V_DS  (pF)")
    out("    %8s %9s %9s %9s" % ("V_DS", "C_iss", "C_oss", "C_rss"))
    for v, ciss, coss, crss in caps_vs_vds():
        out("    %7.0f V %9.1f %9.1f %9.2f" % (v, ciss, coss, crss))
    out("  C_rss IS the crosstalk mechanism. A datasheet states it as a curve;")
    out("  this is that curve, and it is the first thing to check.")
    out()

    q = qg()
    ciss0 = caps_vs_vds()[0][1] * 1e-12
    sane = q is not None and 0.2 * ciss0 * 5 * 1e9 < q < 20 * ciss0 * 5 * 1e9
    out("Gate charge to the 5 V rail: %s"
        % ("%.1f nC" % q if q is not None else "could not measure"))
    if q is not None:
        out("  sanity: C_iss(0 V) x 5 V = %.1f nC, so a Q_g a few times that "
            % (ciss0 * 5 * 1e9))
        out("  is expected (the Miller plateau is the rest). %s"
            % ("consistent." if sane else
               "NOT consistent -- do not quote this number."))
    out()

    out("Third-quadrant drop at 10 A (GaN has no body diode)")
    vr = vsd()
    for voff, v in vr:
        out("    V_off = %+.0f V   V_SD = %s"
            % (voff, "%.2f V" % v if v else "  -"))
    if all(v for _, v in vr):
        d = vr[1][1] - vr[0][1]
        out("  the -2 V rail costs %+.2f V of extra drop, and the physics says"
            % d)
        out("  it should cost exactly 2.00 V. %s"
            % ("Agrees." if abs(d - 2.0) < 0.05 else
               "It does NOT -- the extraction is wrong, not the model."))
    out("  This is the cost of the -2 V rail, and it is why our turn-on")
    out("  energy is higher than the base paper's at three of four corners.")

    out()
    out("HOW TO CHECK THIS, IN FIVE MINUTES")
    out("  Open the EPC2010C datasheet next to this table. R_DS(on) at 5 V,")
    out("  the C_rss curve at 100 V, and Q_g are the three that matter. If")
    out("  any of them is out by more than about 30 %, scripts/robust.py")
    out("  says which conclusions move -- and the +-50 % C_GD row there is")
    out("  the one to read first.")

    with open(os.path.join(RES, "device_characterisation.txt"), "w") as f:
        f.write("models/egan.lib -- extracted terminal characteristics\n")
        f.write("NOT a validation: the datasheet is not in this repository.\n")
        f.write("=" * 66 + "\n")
        f.write("\n".join(lines) + "\n")
    print("\n  wrote results/device_characterisation.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
