# -*- coding: utf-8 -*-
"""netlist_listing.py -- the circuit as ngspice itself reports it.

    python3 scripts/netlist_listing.py

WHY THIS AND NOT A DRAWING
  ngspice cannot draw a schematic -- it is a simulator, there is no
  topology plotting in it. What it CAN do is tell you what circuit it
  parsed, with `listing`, and for evidence that is worth more than a
  drawing: a drawing is what somebody believes the circuit is, and this is
  what was actually solved.

  It is also the only circuit representation in this project that cannot
  go stale. scripts/circuit_diagram.py hardcodes its geometry and labels
  and does not read the netlist, so when RDEC went from 20 mOhm to 1 ohm
  the drawing could not have known. This is regenerated from the deck
  every time it runs.

WHAT IS SHOWN, AND WHAT IS FILTERED OUT
  `listing` returns 120 lines including .model cards, solver options, the
  .control block and a 579-character comment. None of that is topology.
  What is kept is the element cards -- every V, R, L, C, X and B -- plus
  the .param lines that set the values those cards refer to. That is the
  circuit and nothing else, and it fits on a slide at a readable size.

  `listing expand` would additionally flatten the GaN subcircuits, but the
  transconductance B-source alone runs to several hundred characters and
  is unreadable projected. The expanded form is written to the .txt for
  anyone who wants to check the device model.
"""
import os, re, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIM  = os.path.join(ROOT, "sim")
RES  = os.path.join(ROOT, "results")
OUTP = os.path.join(RES, "toolout", "19-ngspice-listing.png")

# element cards: a SPICE line whose first character names a device type
ELEM = re.compile(r"^[vrlcxbie]\w*\s", re.I)


def listing(deck, expand=False):
    src = open(os.path.join(SIM, deck), encoding="utf-8").read()
    src = re.sub(r"\.control.*?\.endc",
                 ".control\nlisting%s\nquit\n.endc" % (" expand" if expand else ""),
                 src, flags=re.S)
    tmp = "/tmp/_listing_%s.cir" % ("e" if expand else "p")
    open(tmp, "w").write(src)
    r = subprocess.run(["ngspice", "-b", tmp], capture_output=True,
                       text=True, cwd=SIM, timeout=300)
    out = []
    for line in r.stdout.splitlines():
        m = re.match(r"^\s*(\d+) : (.*)$", line.rstrip())
        if m:
            out.append((int(m.group(1)), m.group(2)))
    return out


def topology(rows):
    keep = []
    for _n, txt in rows:
        t = txt.strip()
        if not t or t.startswith("*") or t.startswith("$"):
            continue
        if ELEM.match(t) or re.match(r"^\.param\s", t):
            if len(t) > 116:                      # the one long comment line
                continue
            keep.append(t)
    return keep


def render(lines, path, width=2400, pad=34, lh=30, fs=23):
    from PIL import Image, ImageDraw, ImageFont
    font = None
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf"):
        if os.path.exists(p):
            font = ImageFont.truetype(p, fs)
            break
    if font is None:
        font = ImageFont.load_default()
    bold = font
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"):
        if os.path.exists(p):
            bold = ImageFont.truetype(p, fs)
            break

    hdr = ["$ ngspice -b sim/buck.cir   (control block replaced with: listing)",
           ""]
    body = hdr + lines
    # two columns, because 40 lines stacked is unreadable projected
    half = (len(body) + 1) // 2
    cols = [body[:half], body[half:]]
    h = pad * 2 + lh * half
    im = Image.new("RGB", (width, h), (18, 18, 20))
    d = ImageDraw.Draw(im)
    for ci, col in enumerate(cols):
        x = pad + ci * (width // 2 - pad // 2)
        for i, t in enumerate(col):
            y = pad + i * lh
            if t.startswith("$"):
                d.text((x, y), t, font=bold, fill=(120, 220, 150))
            elif t.startswith(".param"):
                d.text((x, y), t, font=font, fill=(150, 190, 255))
            else:
                d.text((x, y), t, font=font, fill=(226, 226, 226))
    if not os.path.isdir(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    im.save(path)
    return im.size


if __name__ == "__main__":
    rows = listing("buck.cir")
    top = topology(rows)
    print("  ngspice listing: %d lines, %d are topology" % (len(rows), len(top)))

    txt = os.path.join(RES, "ngspice_listing.txt")
    with open(txt, "w") as fh:
        fh.write("ngspice -b sim/buck.cir  with the control block replaced by "
                 "'listing'\nThis is the circuit as ngspice parsed it.\n\n")
        fh.write("\n".join(top))
        fh.write("\n\n\n--- listing expand: subcircuits flattened ---\n\n")
        fh.write("\n".join("%5d : %s" % r for r in listing("buck.cir", True)))
    print("  written: results/ngspice_listing.txt")

    size = render(top, OUTP)
    print("  written: results/toolout/19-ngspice-listing.png  %dx%d" % size)
