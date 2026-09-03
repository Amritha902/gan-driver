#!/usr/bin/env python3
"""Generate a synthetic Pareto table so the RTL can be developed before M2 delivers.

Real data comes from the sweep (M2) and the Pareto extraction (M3). Until then this
produces a table with the right *shape* and a plausible trade-off, so the arbiter and
the interpolator can be written and tested.

The numbers are invented. Do not quote any of them as a result.

Field packing must match rtl/pareto_table.v exactly.
"""
import argparse
import pathlib

D_W, PHI_W, TD_W, MET_W = 10, 11, 8, 10
REGION_W, PT_W = 5, 3
N_REGIONS = 27          # 3 x 3 x 3 bins, matching quantiser.v
N_POINTS = 1 << PT_W    # 8 points per front
DEPTH = 1 << (REGION_W + PT_W)
WORD_W = 2 * D_W + PHI_W + TD_W + 3 * MET_W   # 69

O_D1 = 0
O_D2 = O_D1 + D_W
O_PHI = O_D2 + D_W
O_TD = O_PHI + PHI_W
O_LOSS = O_TD + TD_W
O_IRMS = O_LOSS + MET_W
O_ZVS = O_IRMS + MET_W


def pack(d1, d2, phi, t_dead, loss, irms, zvs):
    """Pack one entry. phi is signed; store two's complement in PHI_W bits."""
    if not (-(1 << (PHI_W - 1)) <= phi < (1 << (PHI_W - 1))):
        raise ValueError(f"phi {phi} out of range for {PHI_W} bits")
    phi_u = phi & ((1 << PHI_W) - 1)
    for name, val, w in (("d1", d1, D_W), ("d2", d2, D_W), ("t_dead", t_dead, TD_W),
                         ("loss", loss, MET_W), ("irms", irms, MET_W), ("zvs", zvs, MET_W)):
        if not (0 <= val < (1 << w)):
            raise ValueError(f"{name} {val} out of range for {w} bits")
    return ((zvs << O_ZVS) | (irms << O_IRMS) | (loss << O_LOSS) |
            (t_dead << O_TD) | (phi_u << O_PHI) | (d2 << O_D2) | (d1 << O_D1))


def synth_entry(region, pt):
    """One point on a synthetic front.

    Along the front (pt rising) loss rises and RMS current falls — a real trade-off,
    so the arbiter has something meaningful to choose between. Dead-time is deliberately
    made a function of BOTH region and point, because if the RTL only ever sees a
    constant dead-time it will not exercise the path that matters.
    """
    v_bin = region // 9           # 0..2  DC-link / battery voltage
    i_bin = (region // 3) % 3     # 0..2  load current
    t_bin = region % 3            # 0..2  junction temperature

    d1 = 512 + 40 * (v_bin - 1) - 6 * pt
    d2 = 512 - 30 * (v_bin - 1) + 4 * pt
    phi = 60 + 90 * i_bin + 14 * pt          # more load -> more phase shift
    t_dead = 24 + 6 * i_bin + 3 * t_bin + 2 * pt

    loss = 300 + 55 * pt + 30 * i_bin + 12 * t_bin
    irms = 900 - 70 * pt + 40 * i_bin
    zvs = 200 + 65 * pt - 25 * (v_bin - 1) ** 2

    clip = lambda x, w: max(0, min((1 << w) - 1, int(x)))
    return pack(clip(d1, D_W), clip(d2, D_W), int(phi), clip(t_dead, TD_W),
                clip(loss, MET_W), clip(irms, MET_W), clip(zvs, MET_W))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--out", default="data/pareto_table.mem")
    a = ap.parse_args()

    nibbles = (WORD_W + 3) // 4     # 18 hex digits for 69 bits
    lines = []
    for addr in range(DEPTH):
        region, pt = addr >> PT_W, addr & (N_POINTS - 1)
        if region < N_REGIONS:
            w = synth_entry(region, pt)
        elif region == N_REGIONS:
            # Reverse power flow (battery discharging): phi negative. Reserved for the
            # testbench so the signed unpack path is actually exercised.
            w = pack(512, 512, -300 - 10 * pt, 30, 400, 800, 500)
        else:
            w = 0
        lines.append(f"{w:0{nibbles}x}")

    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n")
    print(f"wrote {out}  —  {DEPTH} entries x {WORD_W} bits "
          f"({N_REGIONS} regions used, region {N_REGIONS} = reverse-flow test vectors)")


if __name__ == "__main__":
    main()
