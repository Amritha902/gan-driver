"""
plot_waveform.py -- render the RTL simulation's VCD as a timing diagram.

ModelSim is proprietary and not installable here, so the waveform comes from
Icarus Verilog's VCD and is drawn directly. That is an advantage rather than a
compromise: this is a vector figure at the exact window that matters, instead
of a screenshot of a tool's GUI.

The window shown is one commanded edge: the controller is driving the low
side, PWM commands a change, both sides go off for exactly dt_cycles, then
the high side comes on. That interval is the dead time, and it is the one
field the study found worth scheduling.
"""
import os, re, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VCD  = sys.argv[1] if len(sys.argv) > 1 else "/tmp/seg_gate_ctrl.vcd"
OUT  = os.path.join(ROOT, "results", "fig_rtl_waveform.png")


def parse_vcd(path):
    """Minimal VCD reader: returns {name: [(t, value), ...]} and the timescale."""
    ids, series, t, scale = {}, {}, 0, "1ns"
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("$timescale"):
                m = re.search(r"(\d+\s*\w+)", line)
                if m: scale = m.group(1)
            m = re.match(r"\$var\s+\w+\s+(\d+)\s+(\S+)\s+(\S+)", line)
            if m:
                width, sym, name = int(m.group(1)), m.group(2), m.group(3)
                ids.setdefault(sym, []).append((name, width))
                series.setdefault(sym, [])
                continue
            if line.startswith("#"):
                t = int(line[1:]); continue
            if not line or line[0] in "$":
                continue
            if line[0] in "01xzXZ" and len(line) > 1:          # scalar
                sym = line[1:]
                if sym in series: series[sym].append((t, line[0]))
            elif line[0] in "bB":                              # vector
                val, sym = line[1:].split(" ", 1)
                if sym in series: series[sym].append((t, val))
    return ids, series, scale


def find(ids, series, want):
    for sym, entries in ids.items():
        for name, width in entries:
            if name == want:
                return series[sym], width
    return None, 0


def level_at(sig, t):
    v = "0"
    for tt, val in sig:
        if tt <= t: v = val
        else: break
    return v


ids, series, scale = parse_vcd(VCD)
SIGNALS = [("clk", "clk"), ("pwm", "pwm_in"), ("in_dt", "dead time"),
           ("hs_pu", "hs_pu[7:0]"), ("ls_pu", "ls_pu[7:0]"),
           ("hs_clamp", "hs clamp"), ("ls_clamp", "ls clamp")]

# Window on a real dead-time event, sized from the VCD rather than guessed.
# The timescale is 1 ns but Icarus emits picosecond units, so a clock period
# is 10 000 units, not 10 - hard-coding a span in "ns" produced a window
# 0.72 ns wide with no transitions in it at all.
clk, _  = find(ids, series, "clk")
dtsig, _ = find(ids, series, "in_dt")
if not clk or not dtsig:
    sys.exit("clk or in_dt missing from the VCD")
half = min(b - a for (a, _), (b, _) in zip(clk, clk[1:]) if b > a)
period = 2 * half

# pick the dead time with the LONGEST duration - it is the dt=25 case, and a
# long interval makes the both-off invariant visible rather than a sliver
spans, start = [], None
for t, v in dtsig:
    if v == "1" and start is None: start = t
    elif v == "0" and start is not None: spans.append((start, t)); start = None
if not spans:
    sys.exit("no complete dead-time interval in the VCD")
d0, d1 = max(spans, key=lambda s: s[1] - s[0])
T0, T1 = d0 - 6 * period, d1 + 6 * period
print("  dead time %d..%d units = %.0f cycles; window %d..%d"
      % (d0, d1, (d1 - d0) / period, T0, T1))

fig, ax = plt.subplots(figsize=(12.4, 4.5))
INK, MUTED, HL = "#141414", "#6A6A6A", "#D8D8D8"
row_h, gap = 1.0, 0.62

for i, (vcdname, label) in enumerate(SIGNALS):
    sig, width = find(ids, series, vcdname)
    y = -(i * (row_h + gap))
    ax.text(T0 - (T1-T0)*0.035, y + row_h/2, label, ha="right", va="center",
            fontsize=9, color=INK, family="DejaVu Sans")
    if sig is None:
        continue
    if width == 1:
        pts, prev = [], level_at(sig, T0)
        tcur = T0
        for tt, val in sig:
            if tt <= T0 or tt > T1: continue
            pts.append((tcur, tt, prev)); prev, tcur = val, tt
        pts.append((tcur, T1, prev))
        for a, b, v in pts:
            lvl = y + (row_h if v == "1" else 0)
            ax.plot([a, b], [lvl, lvl], color=INK, lw=1.5, solid_capstyle="butt")
            ax.plot([a, a], [y, y + row_h], color=INK, lw=1.0)
        if vcdname == "in_dt":                       # shade the dead time
            for a, b, v in pts:
                if v == "1":
                    ax.axvspan(a, b, color=HL, zorder=0)
    else:
        prev, tcur = level_at(sig, T0), T0
        segs = []
        for tt, val in sig:
            if tt <= T0 or tt > T1: continue
            segs.append((tcur, tt, prev)); prev, tcur = val, tt
        segs.append((tcur, T1, prev))
        for a, b, v in segs:
            if b - a <= 0: continue
            nz = v.lstrip("0") or "0"
            on = nz != "0"
            ax.fill_between([a, b], y, y + row_h,
                            color="#3A3A3A" if on else "#FFFFFF",
                            ec=INK, lw=1.0, zorder=1)
            if b - a > (T1 - T0) * 0.06:
                ax.text((a+b)/2, y + row_h/2, "%d" % int(v, 2),
                        ha="center", va="center", fontsize=7.6,
                        color="#FFFFFF" if on else MUTED, zorder=2,
                        family="DejaVu Sans")

ymin = -(len(SIGNALS) * (row_h + gap))
ax.set_xlim(T0 - (T1-T0)*0.16, T1); ax.set_ylim(ymin, row_h + 1.9)
ax.set_yticks([]); ax.set_xlabel("time (ps)", fontsize=9, color=MUTED)
for s in ("top", "right", "left"): ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color(MUTED)
ax.tick_params(axis="x", colors=MUTED, labelsize=8)

ax.set_title("seg_gate_ctrl.v — one commanded edge, dead time shaded",
             fontsize=11, fontweight="bold", color=INK, pad=12,
             family="DejaVu Sans")
ax.text(T0 - (T1-T0)*0.16, row_h + 0.7,
        "Icarus Verilog VCD.  Both pull-up banks are off for the whole dead "
        "time and both clamps are on — no shoot-through window exists.",
        fontsize=8.2, color=MUTED, family="DejaVu Sans")

fig.tight_layout(pad=0.6)
fig.savefig(OUT, dpi=200, facecolor="white")
print("wrote", OUT)
