"""
make_asc_design.py -- the half-bridge drawn as an LTspice schematic, using the
project's own models so the drawing simulates the same circuit ngspice does.

An earlier attempt drew the devices as LTspice's built-in VDMOS and the gate
drive as a plain resistor. It ran, and measured 0.119 V where ngspice measures
1.649. That is a correct answer to a different question. A schematic that does
not carry the same models is an illustration, not a simulation, and the whole
point here is that the picture and the number come from one place.

So the two GaN devices are egan.lib's EGAN and the two gate drivers are
segdrv.lib's SEGDRV -- the same subcircuits sim/dpt.cir uses, given symbols by
make_asy_symbols.py.

Connectivity is by net label: every pin gets a short stub and a FLAG. LTspice
joins nets by name, so the netlist is exactly what the labels say and the sheet
stays readable rather than becoming a maze of routed wires.

The stimulus -- the PWM edges, the clamp enables, the two behavioural gate
sources -- stays as SPICE directives, because it is the FPGA's timing rather
than part of the power circuit, and drawing it would bury what matters.

    A   clamp off, 0 V off-bias      expect vspur = +1.649 V   FALSE TURN-ON
    B   clamp on,  0 V off-bias      expect vspur = +0.830 V   safe
    C   clamp on, -2 V off-bias      expect vspur = -1.176 V   safe, margin 2.58 V
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LT   = os.path.join(ROOT, "ltspice")


def build(clken, vneg, title, expect):
    W, F, S, T = [], [], [], []

    def wire(x1, y1, x2, y2):
        W.append("WIRE %d %d %d %d" % (x1, y1, x2, y2))

    def flag(x, y, n):
        F.append("FLAG %d %d %s" % (x, y, n))

    def stub(px, py, name, dx=0, dy=-24):
        wire(px, py, px + dx, py + dy)
        flag(px + dx, py + dy, name)

    def sym(kind, x, y, inst, value=None, extra=None):
        S.append("SYMBOL %s %d %d R0" % (kind, x, y))
        S.append("SYMATTR InstName %s" % inst)
        if value is not None:
            S.append("SYMATTR Value %s" % value)
        if extra:
            S.append("SYMATTR SpiceLine %s" % extra)

    def note(x, y, text, size=2):
        T.append("TEXT %d %d Left %d ;%s" % (x, y, size, text))

    DEV = "vth={VTH_T} bh={BH_T}"
    DRV = "npu=8 npd=8 runit={RUNIT} rclamp=0.5"

    # ---------------- supply, power loop -----------------------------------
    sym("voltage", 96, 128, "Vbus", "{VBUS}")
    stub(96, 144, "bus")
    stub(96, 224, "0", dy=32)

    sym("res", 752, 96, "Rloop", "0.3")
    stub(768, 112, "bus")
    sym("ind", 752, 224, "Lloop", "{LLOOP}")
    wire(768, 192, 768, 240)
    stub(768, 320, "hstop", dy=24)

    # ---------------- high side --------------------------------------------
    sym("egan", 800, 416, "Xhs", "EGAN", DEV)
    stub(848, 384, "hsd")
    stub(768, 464, "hsg", dx=-40, dy=0)
    stub(848, 544, "sw", dy=24)

    sym("segdrv", 336, 384, "Xdrvhs", "SEGDRV", DRV)
    stub(304, 416, "hspu", dx=-40, dy=0)
    stub(304, 448, "hspd", dx=-40, dy=0)
    stub(304, 480, "hsclkl", dx=-40, dy=0)
    stub(496, 448, "hsg", dx=40, dy=0)
    stub(496, 400, "hsvp", dx=40, dy=0)
    stub(496, 496, "hsvn", dx=40, dy=0)
    stub(400, 544, "sw", dy=24)

    sym("voltage", 96, 384, "Vhsvp", "{VDRV}")
    stub(96, 400, "hsvp")
    stub(96, 480, "sw", dy=24)
    sym("voltage", 208, 384, "Vhsvn", "{VNEG}")
    stub(208, 400, "hsvn")
    stub(208, 480, "sw", dy=24)

    # ---------------- low side ---------------------------------------------
    sym("egan", 800, 768, "Xls", "EGAN", DEV)
    stub(848, 736, "lsd")
    stub(768, 816, "lsg", dx=-40, dy=0)
    stub(848, 896, "0", dy=24)

    sym("segdrv", 336, 736, "Xdrvls", "SEGDRV", DRV)
    stub(304, 768, "lspu", dx=-40, dy=0)
    stub(304, 800, "lspd", dx=-40, dy=0)
    stub(304, 832, "lsclk", dx=-40, dy=0)
    stub(496, 800, "lsg", dx=40, dy=0)
    stub(496, 752, "lsvp", dx=40, dy=0)
    stub(496, 848, "lsvn", dx=40, dy=0)
    stub(400, 896, "0", dy=24)

    sym("voltage", 96, 736, "Vlsvp", "{VDRV}")
    stub(96, 752, "lsvp")
    stub(96, 832, "0", dy=24)
    sym("voltage", 208, 736, "Vlsvn", "{VNEG}")
    stub(208, 752, "lsvn")
    stub(208, 832, "0", dy=24)

    # ---------------- load --------------------------------------------------
    # NODE ORDER MATTERS HERE. sim/dpt.cir has "Lload out sw ... IC={ILOAD}",
    # so the initial current flows out -> sw. Drawn the other way round the
    # netlist reads "Lload sw out", the 10 A initial condition starts flowing
    # backwards, and the whole switching sequence inverts: the measured kick
    # falls to 0.148 V instead of 1.649. So pin A (the top) is "out".
    sym("ind", 1136, 416, "Lload", "{LLOAD} IC={ILOAD}")
    stub(1152, 432, "out")
    stub(1152, 512, "sw", dy=24)
    sym("voltage", 1296, 416, "Vout", "{VOUT}")
    stub(1296, 432, "out")
    stub(1296, 512, "0", dy=24)
    stub(1152, 688, "0", dy=24)

    # ---------------- labels on the sheet -----------------------------------
    note(96, 48, title, 3)
    note(96, 80, expect)
    note(760, 368, "hstop")
    note(1088, 380, "load: 100 uH into VBUS/2")

    # ---------------- directives --------------------------------------------
    D = [
        ".include egan.lib",
        ".include segdrv.lib",
        ".param VBUS=100 ILOAD=10 VDRV=5 VNEG=%s" % vneg,
        ".param CLKEN=%d   ; 1 = active Miller clamp enabled" % clken,
        ".param DT=15n CLKDEL=4n RUNIT=8 TJ=25",
        ".param LLOOP=3n LLOAD=100u TR=0.1n",
        ".param KT={1+0.009*(TJ-25)} BH_T={5.55/KT} VTH_T={1.4-0.0015*(TJ-25)}",
        ".param VOUT={VBUS/2}",
        ".param T1=1u T2={T1+DT} T3=2u T4={T3+DT}",
        "Vshs hstop hsd DC 0",
        "Vsls sw lsd DC 0",
        "Vpwmls pwmls 0 PWL(0 1 {T1} 1 {T1+TR} 0 {T4} 0 {T4+TR} 1)",
        "Vpwmhs pwmhs 0 PWL(0 0 {T2} 0 {T2+TR} 1 {T3} 1 {T3+TR} 0)",
        "Vclkls lsclk 0 PWL(0 0 {T1+CLKDEL} 0 {T1+CLKDEL+TR} {CLKEN} {T4} {CLKEN} {T4+TR} 0)",
        "Vclkhs clkhs 0 PWL(0 {CLKEN} {T2} {CLKEN} {T2+TR} 0 {T3+CLKDEL} 0 {T3+CLKDEL+TR} {CLKEN})",
        "Blspu lspu 0 V={v(pwmls)}",
        "Blspd lspd 0 V={1-v(pwmls)}",
        "Bhspu hspu sw V={v(pwmhs)}",
        "Bhspd hspd sw V={1-v(pwmhs)}",
        "Bhsclk hsclkl sw V={v(clkhs)}",
        ".options reltol=1e-3 abstol=1e-10 vntol=1e-6 chgtol=1e-15 gmin=1e-12",
        ".ic v(sw)=0 v(lsg)={VDRV} v(hsg)={VNEG} v(out)={VOUT}",
        ".tran 0.02n 3u 0 0.02n uic",
        ".meas TRAN vspur MAX V(hsg,sw) FROM 2.015u TO 2.1u",
    ]
    y = 960
    for d in D:
        T.append("TEXT 96 %d Left 2 !%s" % (y, d))
        y += 26

    note(96, y + 16, "Press Run, then View > SPICE Error Log for vspur. "
                     "Probe V(hsg,sw): the gate of the device that is OFF.")

    return "\n".join(["Version 4", "SHEET 1 2000 1700"] + W + F + S + T) + "\n"


CASES = [
    ("A_design_no_clamp_FAILS.asc", 0, "0",
     "A  --  no Miller clamp, 0 V off-bias.  Fails on purpose.",
     "Expect vspur = +1.649 V against a 1.4 V threshold: FALSE TURN-ON, margin -0.249 V."),
    ("B_design_clamp_on.asc", 1, "0",
     "B  --  active Miller clamp on, 0 V off-bias.",
     "Expect vspur = +0.830 V: safe, margin +0.570 V."),
    ("C_design_clamp_and_neg_bias.asc", 1, "-2",
     "C  --  Miller clamp on and -2 V off-bias.  The shipped setting.",
     "Expect vspur = -1.176 V: safe, margin +2.576 V."),
]

for name, clken, vneg, title, expect in CASES:
    open(os.path.join(LT, name), "w").write(build(clken, vneg, title, expect))
    print("wrote ltspice/%s" % name)
