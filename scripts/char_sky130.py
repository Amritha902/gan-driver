"""
char_sky130.py -- drive-strength characterisation of the SKY130 output stage.

Forces the driver output to a small offset from its rail and measures the
current, giving effective on-resistance per thermometer code.  This is the
plot that says the actuator is monotonic and behaves like the ideal-switch
model it replaces.
"""
import os, re, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DECK = """* SKY130 segmented driver DC characterisation
.lib "{root}/pdk/sky130_5v.lib" tt
.include {root}/models/segdrv_sky130.lib
Vp   vp  0 DC 5
Vn   vn  0 DC 0
Vpu  pu  0 DC {pu}
Vpd  pd  0 DC {pd}
Vclk clk 0 DC 0
Vout out 0 DC {vout}
X1 pu pd clk out vp vn 0 SEGDRV_SKY130 npu={npu} npd={npd}
.control
op
print i(Vout)
quit
.endc
.end
"""

def run(npu, npd, pu, pd, vout):
    open('/tmp/ch.cir','w').write(DECK.format(root=ROOT, npu=npu, npd=npd,
                                              pu=pu, pd=pd, vout=vout))
    o = subprocess.run(["ngspice","-b","/tmp/ch.cir"], capture_output=True,
                       text=True, timeout=180).stdout
    m = re.search(r"i\(vout\)\s*=\s*([-\d.eE+]+)", o)
    return abs(float(m.group(1))) if m else None

def main():
    print("SKY130 segmented driver, effective on-resistance per code")
    print("(measured 0.1 V off the rail, V_rail = 5 V)\n")
    print("  code   pull-up(PMOS)      pull-down(NMOS)      ideal 8/N")
    rows=[]
    for n in range(1, 9):
        iu = run(n, 8, 1, 0, 4.9)
        idn = run(8, n, 0, 1, 0.1)
        ru = 0.1/iu if iu else float('nan')
        rd = 0.1/idn if idn else float('nan')
        rows.append((n, ru, rd))
        print("   %d     %8.2f ohm        %8.2f ohm        %5.2f"
              % (n, ru, rd, 8.0/n))
    print("\n  monotonic pull-up  :", all(rows[i][1] > rows[i+1][1] for i in range(7)))
    print("  monotonic pull-down:", all(rows[i][2] > rows[i+1][2] for i in range(7)))
    print("  pull-up  range: %.2f -> %.2f ohm (%.1fx)"
          % (rows[0][1], rows[-1][1], rows[0][1]/rows[-1][1]))
    print("  pull-down range: %.2f -> %.2f ohm (%.1fx)"
          % (rows[0][2], rows[-1][2], rows[0][2]/rows[-1][2]))
    import csv
    with open(os.path.join(ROOT,"results","sky130_drive_strength.csv"),"w",newline="") as f:
        w=csv.writer(f); w.writerow(["code","r_pullup_ohm","r_pulldown_ohm"])
        w.writerows([(n,round(a,4),round(b,4)) for n,a,b in rows])
    return rows

if __name__ == "__main__":
    main()
