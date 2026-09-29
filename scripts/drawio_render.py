# -*- coding: utf-8 -*-
"""drawio_render.py -- render kicad/gan_driver.drawio without draw.io.

    python3 scripts/drawio_render.py
        -> results/fig_drawio_<page>.png for each page

The .drawio file is uncompressed mxGraph XML: every cell carries its own
geometry and style, so the page can be drawn from the file directly. That
matters here because there is no browser in this container to open
app.diagrams.net with, and exporting by hand would put a step between the
file in the repository and the picture on the slide that nobody could check.
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = os.path.join(ROOT, "results")
SRC = os.path.join(ROOT, "kicad", "gan_driver.drawio")

SCALE = 2.0
MARGIN = 40
INK = "#1A1A1A"
EDGE = "#2E7D32"
BOX = "#FFFFFF"


def font(size, bold=False):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf"
              % ("-Bold" if bold else ""),):
        if os.path.exists(p):
            return ImageFont.truetype(p, max(8, int(size)))
    return ImageFont.load_default()


def style_of(cell):
    out = {}
    for bit in (cell.get("style") or "").split(";"):
        if "=" in bit:
            k, v = bit.split("=", 1)
            out[k] = v
        elif bit:
            out[bit] = "1"
    return out


def geom(cell):
    g = cell.find("mxGeometry")
    if g is None:
        return None
    def f(k, d=0.0):
        try:
            return float(g.get(k, d))
        except (TypeError, ValueError):
            return d
    return f("x"), f("y"), f("width"), f("height")


def endpoint(cell, which):
    """sourcePoint / targetPoint, which is how this file wires everything.

    Not one of the 54 edges in gan_driver.drawio references a cell by id --
    they all carry their own coordinates. The first version of this renderer
    only followed source/target attributes, so it drew every box and not a
    single wire.
    """
    g = cell.find("mxGeometry")
    if g is None:
        return None
    for pt in g.findall("mxPoint"):
        if pt.get("as") == which:
            return float(pt.get("x", 0)), float(pt.get("y", 0))
    return None


def points(cell):
    g = cell.find("mxGeometry")
    if g is None:
        return []
    out = []
    for arr in g.findall("Array"):
        if arr.get("as") == "points":
            for pt in arr.findall("mxPoint"):
                out.append((float(pt.get("x", 0)), float(pt.get("y", 0))))
    return out


def render_page(diagram, out_path):
    cells = diagram.iter("mxCell")
    verts, edges = {}, []
    for c in cells:
        if c.get("vertex") == "1" and geom(c):
            verts[c.get("id")] = c
        elif c.get("edge") == "1":
            edges.append(c)

    xs, ys = [], []
    for c in verts.values():
        x, y, w, h = geom(c)
        xs += [x, x + w]
        ys += [y, y + h]
    if not xs:
        return None
    x0, y0, x1, y1 = min(xs), min(ys), max(xs), max(ys)
    W = int((x1 - x0) * SCALE) + MARGIN * 2
    H = int((y1 - y0) * SCALE) + MARGIN * 2
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)

    def T(px, py):
        return (MARGIN + (px - x0) * SCALE, MARGIN + (py - y0) * SCALE)

    def centre(cid):
        c = verts.get(cid)
        if c is None:
            return None
        x, y, w, h = geom(c)
        return T(x + w / 2.0, y + h / 2.0)

    for e in edges:
        st = style_of(e)
        a = centre(e.get("source"))
        b = centre(e.get("target"))
        sp, tp = endpoint(e, "sourcePoint"), endpoint(e, "targetPoint")
        if a is None and sp:
            a = T(*sp)
        if b is None and tp:
            b = T(*tp)
        if a is None or b is None:
            continue
        path = [T(px, py) for px, py in points(e)]
        pts = [a] + path + [b]
        # orthogonalEdgeStyle with no waypoints means one right-angle turn,
        # which is what a schematic wire looks like; a straight diagonal
        # across a circuit diagram reads as a mistake.
        if not path and st.get("edgeStyle") == "orthogonalEdgeStyle":
            if abs(a[0] - b[0]) > 1 and abs(a[1] - b[1]) > 1:
                pts = [a, (b[0], a[1]), b]
        d.line(pts, fill=st.get("strokeColor", EDGE), width=2)

    for c in verts.values():
        x, y, w, h = geom(c)
        st = style_of(c)
        # drawio stores labels as HTML, so "npu>=3" is on disk as
        # "npu&gt;=3" and was being drawn that way.
        import html as _html
        val = _html.unescape(re.sub(r"<[^>]+>", "", c.get("value") or "")).strip()
        p0, p1 = T(x, y), T(x + w, y + h)
        if "text" not in st and w > 2 and h > 2:
            d.rectangle([p0, p1], fill=BOX,
                        outline=st.get("strokeColor", INK), width=2)
        if not val:
            continue
        fs = float(st.get("fontSize", 12)) * SCALE * 0.92
        f = font(fs, st.get("fontStyle") == "1")
        col = st.get("fontColor", INK)
        if st.get("align") == "left" or "text" in st:
            d.text((p0[0], p0[1]), val, font=f, fill=col)
        else:
            tw = d.textlength(val, font=f)
            d.text(((p0[0] + p1[0]) / 2.0 - tw / 2.0,
                    (p0[1] + p1[1]) / 2.0 - fs / 2.0), val, font=f, fill=col)

    im.save(out_path)
    return im.size


def main():
    if not os.path.exists(SRC):
        raise SystemExit("missing %s" % SRC)
    root = ET.parse(SRC).getroot()
    made = 0
    for dia in root.findall("diagram"):
        name = (dia.get("name") or dia.get("id") or "page")
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        out = os.path.join(RES, "fig_drawio_%s.png" % slug)
        size = render_page(dia, out)
        if size:
            made += 1
            print("  wrote %s  %dx%d  (%s)"
                  % (os.path.relpath(out, ROOT), size[0], size[1], name))
    if not made:
        raise SystemExit("drawio_render: no page had any geometry")
    return 0


if __name__ == "__main__":
    sys.exit(main())
