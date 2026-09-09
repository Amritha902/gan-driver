"""
make_asc_segdrv.py -- draw what is inside the segmented gate driver.

In BUCK_converter.asc the driver is a yellow SEGDRV box: LTspice draws a
subcircuit as a filled rectangle, so the part this project actually designs is
the one part you cannot see. This opens it up.

It is the contents of models/segdrv.lib drawn out: eight pull-up slices from
the +5 V rail to the gate, eight pull-down slices from the gate to the off
rail, and the Miller clamp beside them on its own 0.5 ohm path. A gate load
and a PWM source are included so the schematic runs -- press Run and the gate
waveform is the driver charging and discharging a real gate capacitance.

Symbol pins (LTspice stock):
    sw   (0,16) (0,96) top/bottom, control (-48,80) (-48,32)
    res  (16,16) (16,96)     cap (16,0) (16,64)     voltage (0,16) (0,96)
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "ltspice", "SEGDRV_inside.asc")

L = []
def w(x1, y1, x2, y2): L.append("WIRE %d %d %d %d" % (x1, y1, x2, y2))
def flag(x, y, n):     L.append("FLAG %d %d %s" % (x, y, n))
def sym(name, x, y, rot="R0", hide_value=False, **a):
    """hide_value: keep the value in the netlist but stop LTspice printing it.

    Every slice resistor is "{runit + (npu>=n ? 0 : 1e9)}". Printed on the
    schematic, sixteen of those land on the same two lines and the drawing is
    unreadable. WINDOW 3 with size 0 hides the text; the netlist is unchanged.
    """
    L.append("SYMBOL %s %d %d %s" % (name, x, y, rot))
    if hide_value:
        L.append("WINDOW 3 0 0 Left 0")
    for k, v in a.items():
        L.append("SYMATTR %s %s" % (k, v))
def txt(x, y, s, size=2):
    L.append("TEXT %d %d Left %d %s" % (x, y, size, s))

L.append("Version 4")
L.append("SHEET 1 2600 1800")

VP_Y, OUT_Y, VN_Y = 176, 704, 1232        # the three horizontal rails
X0, DX = 224, 168                          # first slice, spacing

# ---------------------------------------------------------- pull-up bank --
for i in range(8):
    x = X0 + i * DX
    sym("sw",  x, 240, hide_value=True, InstName="Spu%d" % (i + 1), Value="SWP")
    sym("res", x - 16, 400, hide_value=True, InstName="Rpu%d" % (i + 1),
        Value="{runit + (npu>=%d ? 0 : 1e9)}" % (i + 1))
    w(x, VP_Y, x, 256)                     # +5 V rail down to the switch
    w(x, 336, x, 416)                      # switch to resistor
    w(x, 496, x, OUT_Y)                    # resistor down to the gate node
    w(x - 48, 320, x - 88, 320)            # nc+  (lower pin)
    flag(x - 88, 320, "pu")
    w(x - 48, 272, x - 88, 272)            # nc-  : the driver's own ground
    flag(x - 88, 272, "0")

# -------------------------------------------------------- pull-down bank --
for i in range(8):
    x = X0 + i * DX
    sym("res", x - 16, 768, hide_value=True, InstName="Rpd%d" % (i + 1),
        Value="{runit + (npd>=%d ? 0 : 1e9)}" % (i + 1))
    sym("sw",  x, 928, hide_value=True, InstName="Spd%d" % (i + 1), Value="SWP")
    w(x, OUT_Y, x, 784)
    w(x, 864, x, 944)
    w(x, 1024, x, VN_Y)
    w(x - 48, 1008, x - 88, 1008)          # nc+
    flag(x - 88, 1008, "pd")
    w(x - 48, 960, x - 88, 960)            # nc-
    flag(x - 88, 960, "0")

# ------------------------------------------------------- the Miller clamp --
CX = X0 + 8 * DX + 96
sym("sw",  CX, 768, hide_value=True, InstName="Sclk", Value="SWP")
sym("res", CX - 16, 928, InstName="Rclk", Value="{rclamp}")
w(CX, OUT_Y, CX, 784)
w(CX, 864, CX, 944)
w(CX, 1024, CX, VN_Y)
w(CX - 48, 848, CX - 88, 848)              # nc+
flag(CX - 88, 848, "clk")
w(CX - 48, 800, CX - 88, 800)              # nc-
flag(CX - 88, 800, "0")

# ----------------------------------------------------------- the rails ----
w(X0, VP_Y, CX, VP_Y)
w(X0, OUT_Y, CX, OUT_Y)
w(X0, VN_Y, CX, VN_Y)
flag(X0 - 64, VP_Y, "vp")
w(X0 - 64, VP_Y, X0, VP_Y)
flag(X0 - 64, VN_Y, "vn")
w(X0 - 64, VN_Y, X0, VN_Y)

# ------------------------------------- the gate this driver is charging ---
GX = CX + 240
w(CX, OUT_Y, GX, OUT_Y)
flag(GX, OUT_Y, "out")
sym("cap", GX - 16, OUT_Y + 48, InstName="Cgate", Value="350p")
w(GX, OUT_Y, GX, OUT_Y + 48)
w(GX, OUT_Y + 112, GX, VN_Y)
w(GX, VN_Y, CX, VN_Y)

txt(200, 96, ";+5 V DRIVE RAIL", 1)
txt(200, 640, ";GATE NODE  -  this is what the driver charges", 1)
txt(200, 1288, ";OFF RAIL  -  0 V or -2 V", 1)
txt(200, 40, ";INSIDE THE SEGMENTED GATE DRIVER  -  contents of models/segdrv.lib", 3)
txt(X0, 560, ";EIGHT PULL-UP SLICES  -  each 8 ohm, slice i on when npu >= i.  How hard the device is switched ON.", 2)
txt(X0, 1120, ";EIGHT PULL-DOWN SLICES  -  each 8 ohm, slice i on when npd >= i.  How hard it is switched OFF.", 2)
txt(CX - 120, 1168, ";MILLER CLAMP  -  0.5 ohm", 2)
txt(GX - 90, OUT_Y + 200, ";the GaN gate", 1)

DIRECTIVES = """.model SWP SW(Ron=0.01 Roff=1e9 Vt=0.5 Vh=0.05)
.param npu=8 npd=8 runit=8 rclamp=0.5
.param VDRV=5 VNEG=0
Vvp vp 0 DC {VDRV}
Vvn vn 0 DC {VNEG}
Vpu pu 0 PULSE(0 1 0 1n 1n 200n 500n)
Vpd pd 0 PULSE(1 0 0 1n 1n 200n 500n)
Vclk clk 0 DC 0
.tran 0.1n 1u
.meas TRAN vgate_high MAX V(out)"""
y = 1400
for line in DIRECTIVES.splitlines():
    txt(200, y, "!" + line, 2)
    y += 26
txt(200, y + 20, ";npu and npd are the slice counts the FPGA sets. Press Run to see the gate charge.", 2)

open(OUT, "w").write("\n".join(L) + "\n")
print("wrote", OUT, "(%d lines)" % len(L))
