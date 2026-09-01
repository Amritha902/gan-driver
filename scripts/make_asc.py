"""
make_asc.py -- write real LTspice SCHEMATIC (.asc) files.

The ltspice/ folder shipped .cir netlists. LTspice opens those as TEXT: you
get a netlist, not a drawing. A .asc is the schematic LTspice actually draws,
so this writes one per experiment.

LTspice symbol pin offsets used here (R0 orientation), which is what the
wire endpoints must land on:
    nmos      drain (x+48, y)    gate (x, y+48)     source (x+48, y+96)
    res       (x+16, y)          (x+16, y+96)
    cap       (x+16, y)          (x+16, y+64)
    ind       (x+16, y)          (x+16, y+80)
    voltage   (x, y)             (x, y+80)
    current   (x, y)             (x, y+80)      arrow points from + to -
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LTS  = os.path.join(ROOT, "ltspice")

def build(name, title, note, clken=0, vneg=0):
    L = ["Version 4", "SHEET 1 1600 1000"]
    W = L.append

    # ---------------- power loop ----------------
    # bus rail
    W("WIRE 320 96 720 96")
    W("WIRE 720 96 720 128")          # to M1 drain
    W("WIRE 320 96 320 128")          # to Vbus +
    # M1 high side at (672,128): D(720,128) G(672,176) S(720,224)
    W("WIRE 720 224 720 256")         # M1 source -> SW
    W("WIRE 720 256 720 288")         # SW -> M2 drain
    W("WIRE 720 256 1040 256")        # SW -> load
    # M2 low side at (672,288): D(720,288) G(672,336) S(720,384)
    W("WIRE 720 384 720 416")         # M2 source -> Lloop
    W("WIRE 720 512 720 560")         # Lloop -> gnd rail
    W("WIRE 320 560 720 560")
    W("WIRE 1040 560 720 560")
    W("WIRE 320 208 320 560")         # Vbus - to gnd
    # load branch
    W("WIRE 1040 256 1040 288")
    W("WIRE 1040 368 1040 400")
    W("WIRE 1040 480 1040 560")

    # ---------------- gate drives ----------------
    # high-side gate: Vhs -> Rg -> gate, referenced to SW
    W("WIRE 448 176 512 176")         # Vhs+ -> Rg_hs top
    W("WIRE 528 272 528 304")
    W("WIRE 448 256 448 304")
    W("WIRE 448 304 528 304")         # Vhs- tied to SW rail
    W("WIRE 528 304 640 304")
    W("WIRE 640 304 640 256")
    W("WIRE 640 256 720 256")         # source reference = SW
    W("WIRE 528 176 528 192")
    W("WIRE 528 272 672 272")
    W("WIRE 672 272 672 176")         # into M1 gate
    # low-side gate
    W("WIRE 448 336 512 336")
    W("WIRE 528 432 528 464")
    W("WIRE 448 416 448 464")
    W("WIRE 448 464 528 464")
    W("WIRE 528 464 720 464")         # low-side source reference = gnd side
    W("WIRE 528 336 528 352")
    W("WIRE 528 432 672 432")
    W("WIRE 672 432 672 336")         # into M2 gate

    # ---------------- flags ----------------
    W("FLAG 720 256 sw")
    W("FLAG 720 560 0")
    W("FLAG 320 96 bus")
    W("FLAG 672 176 hsg")
    W("FLAG 672 336 lsg")
    W("FLAG 720 464 lss")

    # ---------------- symbols ----------------
    W("SYMBOL nmos 672 128 R0"); W("SYMATTR InstName M1"); W("SYMATTR Value EPC2010")
    W("SYMBOL nmos 672 288 R0"); W("SYMATTR InstName M2"); W("SYMATTR Value EPC2010")

    W("SYMBOL voltage 320 112 R0"); W("SYMATTR InstName Vbus"); W("SYMATTR Value 100")
    W("SYMBOL ind 704 416 R0");     W("SYMATTR InstName Lloop"); W("SYMATTR Value 3n")
    W("SYMBOL ind 1024 288 R0");    W("SYMATTR InstName Lload"); W("SYMATTR Value 100u")
    W("SYMBOL current 1040 400 R0");W("SYMATTR InstName Iload"); W("SYMATTR Value 10")

    W("SYMBOL res 512 160 R0"); W("SYMATTR InstName Rg_hs"); W("SYMATTR Value {RG}")
    W("SYMBOL res 512 320 R0"); W("SYMATTR InstName Rg_ls"); W("SYMATTR Value {RG}")
    W("SYMBOL voltage 448 176 R0"); W("SYMATTR InstName Vhs")
    W("SYMATTR Value PULSE(%g 5 1.05u 2n 2n 0.4u 10u)" % vneg)
    W("SYMBOL voltage 448 336 R0"); W("SYMATTR InstName Vls")
    W("SYMATTR Value PULSE(0 5 0 2n 2n 1u 10u)")

    # ---------------- directives ----------------
    W(".model EPC2010 VDMOS(Rg=0.4 Vto=1.4 Kp=5.5 Cgdmax=150p Cgdmin=7p "
      "Cgs=350p Cjo=180p Rd=0.03 Rs=0.01 Rds=1e7)")
    W("TEXT 300 640 Left 2 !.tran 0 3u 0 0.02n")
    W("TEXT 300 672 Left 2 !.param RG=%s" % ("1" if not clken else "0.25"))
    W("TEXT 300 704 Left 2 !.meas TRAN vspur MAX V(hsg,sw) FROM 1.9u TO 2.2u")
    W("TEXT 300 96 Left 3 ;%s" % title)
    W("TEXT 300 768 Left 2 ;%s" % note)

    out = os.path.join(LTS, name)
    open(out, "w").write("\n".join(L) + "\n")
    print("wrote", out)

os.makedirs(LTS, exist_ok=True)
build("1_baseline_FALSE_TURN_ON.asc",
      "BASELINE - fails on purpose: V(hsg,sw) reaches 1.65 V vs a 1.4 V threshold",
      "ngspice on the same circuit measures 1.649 V spurious, margin -0.249 V -> FALSE TURN-ON",
      clken=0, vneg=0)
build("2_miller_clamp_on.asc",
      "WITH ACTIVE MILLER CLAMP - low-impedance gate path during the off edge",
      "ngspice: 0.830 V spurious, margin +0.570 V -> SAFE", clken=1, vneg=0)
build("3_clamp_and_negative_bias.asc",
      "CLAMP + -2 V OFF-BIAS - the shipped configuration",
      "ngspice: -1.176 V spurious, margin +2.576 V -> SAFE, 2.58 V of headroom",
      clken=1, vneg=-2)
