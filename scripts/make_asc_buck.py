"""
make_asc_buck.py -- draw the converter as a real LTspice schematic, with wires.

The earlier .asc files connected everything through net labels, so LTspice drew
a scatter of unconnected boxes. It simulated correctly and looked like nothing.
A schematic whose components are not joined up is not a circuit diagram, and it
is fair for anyone to say so.

This draws the whole converter with actual WIRE segments in the conventional
layout: supply on the left, the half-bridge as a vertical leg, the output
filter and load to the right, and a gate driver beside each device.

Symbol pin offsets (LTspice stock library):
    voltage  (0,16) (0,96)     res  (16,16) (16,96)
    ind      (16,16) (16,96)   cap  (16,0)  (16,64)
    EGAN     d(48,-32) g(-32,48) s(48,128)
    SEGDRV   pu(-32,32) pd(-32,64) clk(-32,96) out(160,64) vp(160,16)
             vn(160,112) ref(64,160)
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "ltspice", "BUCK_converter.asc")

L = []
def w(x1, y1, x2, y2): L.append("WIRE %d %d %d %d" % (x1, y1, x2, y2))
def flag(x, y, n):     L.append("FLAG %d %d %s" % (x, y, n))
def sym(name, x, y, rot="R0", **attrs):
    L.append("SYMBOL %s %d %d %s" % (name, x, y, rot))
    for k, v in attrs.items():
        L.append("SYMATTR %s %s" % (k, v))
def txt(x, y, s, size=2, just="Left"):
    L.append("TEXT %d %d %s %d %s" % (x, y, just, size, s))

L.append("Version 4")
L.append("SHEET 1 2100 1400")

# ----------------------------------------------------- supply and power loop
# Vin: + at (96,208), - at (96,288)
sym("voltage", 96, 192, InstName="Vin", Value="{VIN}")
flag(96, 288, "0")
w(96, 208, 96, 144)                      # up from Vin +
w(96, 144, 288, 144)                     # across to the loop resistance

sym("res", 272, 144, InstName="Rloop", Value="0.3")     # pins (288,160) (288,240)
w(288, 144, 288, 160)
sym("ind", 272, 240, InstName="Lloop", Value="{LLOOP}") # pins (288,256) (288,336)
w(288, 240, 288, 256)
w(288, 336, 288, 384)
flag(288, 352, "bus")

# ------------------------------------------------------------- half-bridge --
# High-side EGAN at (560,416): d(608,384) g(528,464) s(608,544)
sym("egan", 560, 416, InstName="Xhs")
w(288, 384, 608, 384)                    # bus -> HS drain
w(608, 544, 608, 640)                    # HS source -> switch node

# Low-side EGAN at (560,672): d(608,640) g(528,720) s(608,800)
sym("egan", 560, 672, InstName="Xls")
w(608, 640, 608, 640)
flag(608, 800, "0")

# ------------------------------------------------------ output filter, load
w(608, 640, 800, 640)
flag(704, 640, "sw")
sym("ind", 784, 624, InstName="Lo", Value="{LOUT}")     # pins (800,640) (800,720)
w(800, 720, 800, 768)
w(800, 768, 1088, 768)
flag(800, 768, "out")

sym("cap", 928, 768, InstName="Co", Value="{COUT}")     # pins (944,768) (944,832)
flag(944, 832, "0")

sym("res", 1072, 768, InstName="Rload", Value="{RLOAD}")  # pins (1088,784) (1088,864)
w(1088, 768, 1088, 784)
flag(1088, 864, "0")

# --------------------------------------------------------- high-side driver
# SEGDRV at (208,432): pu(176,464) pd(176,496) clk(176,528)
#                      out(368,496) vp(368,448) vn(368,544) ref(272,592)
sym("segdrv", 208, 432, InstName="Xdrvhs",
    Value2="npu={NPU_HS} npd={NPD_HS} runit={RUNIT} rclamp=0.5")
w(368, 496, 528, 496)                    # driver out -> HS gate net
w(528, 496, 528, 464)
flag(176, 464, "hspu")
flag(176, 496, "hspd")
flag(176, 528, "hsclkl")
flag(368, 448, "hsvp")
flag(368, 544, "hsvn")
w(272, 592, 272, 640)
w(272, 640, 608, 640)                    # driver reference sits on the SW node

# ---------------------------------------------------------- low-side driver
sym("segdrv", 208, 688, InstName="Xdrvls",
    Value2="npu={NPU_LS} npd={NPD_LS} runit={RUNIT} rclamp=0.5")
w(368, 752, 528, 752)
w(528, 752, 528, 720)
flag(176, 720, "lspu")
flag(176, 752, "lspd")
flag(176, 784, "lsclk")
flag(368, 704, "lsvp")
flag(368, 800, "lsvn")
w(272, 848, 272, 896)
flag(272, 896, "0")

# ------------------------------------------------------------------ labels --
# ";" is a comment on a schematic; "!" is a SPICE directive. The title
# line went out with "!" and LTspice tried to parse it as a netlist card.
txt(96, 80, ";GaN synchronous buck converter -- 100 V DC in, 48.6 V DC out at 4.88 A", 3)
txt(96, 112, ";100 V DC supply, with the power loop's own R and L", 1)
txt(672, 424, ";HIGH SIDE - control switch", 1)
txt(600, 872, ";LOW SIDE - synchronous rectifier", 1)
txt(776, 592, ";output filter", 1)
txt(1040, 716, ";10 ohm load - 48.6 V, 4.88 A out", 1)
txt(112, 408, ";segmented gate driver", 1)
txt(112, 664, ";segmented gate driver", 1)

DIRECTIVES = """.include egan.lib
.include segdrv.lib
.param VIN=100 D=0.5 FSW=500k
.param LOUT=22u COUT=4.7u RLOAD=10
.param VDRV=5 VNEG=-2 CLKEN=1
.param NPU_LS=8 NPD_LS=8 NPU_HS=8 NPD_HS=8 RUNIT=8
.param DT=15n TJ=25 LLOOP=3n
.param KT={1+0.009*(TJ-25)} BH_T={5.55/KT} VTH_T={1.4-0.0015*(TJ-25)}
.param TSW={1/FSW} TON={D*TSW-DT} TLS={(1-D)*TSW-2*DT} TLSD={D*TSW+DT} TR=0.5n
.param VO={D*VIN} IO={VO/RLOAD}
Vpwmhs pwmhs 0 PULSE(0 1 0 {TR} {TR} {TON} {TSW})
Vpwmls pwmls 0 PULSE(0 1 {TLSD} {TR} {TR} {TLS} {TSW})
Vlsvp lsvp 0 DC {VDRV}
Vlsvn lsvn 0 DC {VNEG}
Blspu lspu 0 V={v(pwmls)}
Blspd lspd 0 V={1-v(pwmls)}
Blsclk lsclk 0 V={CLKEN*(1-v(pwmls))}
Vhsvp hsvp sw DC {VDRV}
Vhsvn hsvn sw DC {VNEG}
Bhspu hspu sw V={v(pwmhs)}
Bhspd hspd sw V={1-v(pwmhs)}
Bhsclk hsclkl sw V={CLKEN*(1-v(pwmhs))}
.ic V(out)=0 I(Lo)=0
.options reltol=1e-3 abstol=1e-10 vntol=1e-6 chgtol=1e-15 gmin=1e-12
.tran 0.2n 300u 0 2n uic
.meas TRAN vout AVG V(out) FROM 280u TO 300u
.meas TRAN iout AVG I(Rload) FROM 280u TO 300u"""

y = 960
for line in DIRECTIVES.splitlines():
    txt(96, y, "!" + line, 2)
    y += 24

txt(96, y + 24, ";Press Run, then View > SPICE Error Log for the measured output.", 2)

open(OUT, "w").write("\n".join(L) + "\n")
print("wrote", OUT, "(%d lines)" % len(L))
