# -*- coding: utf-8 -*-
"""Render the speech script to a PDF you can read from at the podium.

    python3 scripts/speech_pdf.py review/SPEECH-REVIEW2.md review/SPEECH-REVIEW2.pdf

The .md is the source of truth and what check_consistency.py reads; this is
the printable form of it. A presenter should never be reading Markdown
source off a laptop at 9 a.m.

The Markdown handling below is deliberately small.

It is not a general Markdown engine: it handles exactly what SPEECH-REVIEW2.md
uses -- headings, blockquotes (the spoken lines), fenced code, tables,
checkbox lists, bold and inline code -- and nothing else. A dependency would
have been simpler, but there is no network install in this container and the
script has to be printable tonight.
"""
import html, re, sys, io

src = io.open(sys.argv[1], encoding="utf-8").read().splitlines()
out, in_code, in_quote, in_tbl = [], False, False, False

def inline(t):
    t = html.escape(t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<em>\1</em>", t)
    return t

def close_quote():
    global in_quote
    if in_quote: out.append("</blockquote>"); in_quote = False

def close_tbl():
    global in_tbl
    if in_tbl: out.append("</tbody></table>"); in_tbl = False

for ln in src:
    if ln.startswith("```"):
        close_quote(); close_tbl()
        out.append("</pre>" if in_code else "<pre>"); in_code = not in_code; continue
    if in_code:
        out.append(html.escape(ln)); continue
    if ln.strip() == "---":
        close_quote(); close_tbl(); out.append("<hr>"); continue
    m = re.match(r"^(#{1,3}) (.*)", ln)
    if m:
        close_quote(); close_tbl()
        out.append("<h%d>%s</h%d>" % (len(m.group(1)), inline(m.group(2)), len(m.group(1))))
        continue
    if ln.startswith(">"):
        close_tbl()
        if not in_quote: out.append("<blockquote>"); in_quote = True
        body = ln[1:].strip()
        if body: out.append("<p>%s</p>" % inline(body))
        continue
    close_quote()
    if ln.strip().startswith("|"):
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if set("".join(cells)) <= set("-: "):
            continue                       # the ---|--- separator row
        if not in_tbl:
            out.append("<table><thead><tr>%s</tr></thead><tbody>"
                       % "".join("<th>%s</th>" % inline(c) for c in cells))
            in_tbl = True
        else:
            out.append("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in cells))
        continue
    close_tbl()
    m = re.match(r"^- \[ \] (.*)", ln)
    if m:
        out.append('<p class="box">&#9744;&nbsp; %s</p>' % inline(m.group(1)))
        continue
    if ln.strip():
        out.append("<p>%s</p>" % inline(ln.strip()))

CSS = """
@page { size: A4; margin: 16mm 15mm; }
body { font: 10.5pt/1.45 "DejaVu Sans", Arial, sans-serif; color:#111; }
h1 { font-size: 19pt; color:#1D2F82; margin: 0 0 2mm; }
h2 { font-size: 13pt; color:#1D2F82; margin: 7mm 0 2mm;
     border-top: 1.5pt solid #1D2F82; padding-top: 2mm; page-break-after: avoid; }
h3 { font-size: 11pt; color:#1D2F82; margin: 5mm 0 1.5mm; page-break-after: avoid; }
p { margin: 0 0 2mm; }
blockquote { margin: 2mm 0 3mm 0; padding: 2mm 0 2mm 5mm;
             border-left: 2.5pt solid #1D2F82; background:#F4F6FC;
             page-break-inside: avoid; }
blockquote p { font-size: 11.5pt; line-height: 1.5; margin: 0 0 1.5mm; }
pre { background:#111; color:#EEE; padding: 2.5mm 4mm; font-size: 11pt;
      font-family:"DejaVu Sans Mono", monospace; margin: 2mm 0 3mm; }
code { font-family:"DejaVu Sans Mono", monospace; font-size: 9.5pt;
       background:#EEE; padding: 0 1mm; }
table { border-collapse: collapse; margin: 2mm 0 3mm; width: 100%; }
th { background:#1D2F82; color:#fff; text-align:left; }
th, td { border: 0.5pt solid #BBB; padding: 1.2mm 2.5mm; font-size: 9.5pt; }
hr { border: 0; border-top: 0.5pt solid #CCC; margin: 5mm 0; }
.box { margin: 0 0 1.5mm; }
strong { color:#000; }
"""
page = ("<html><head><meta charset='utf-8'><title>Speech</title>"
        "<style>%s</style></head><body>%s</body></html>"
        % (CSS, "\n".join(out)))

# LibreOffice will not load HTML in this container (no import filter), and
# there is no pandoc, weasyprint or reportlab either. PyMuPDF's Story lays
# out the HTML itself, which is already a dependency here.
import pymupdf

story = pymupdf.Story(html=page, archive=None)
writer = pymupdf.DocumentWriter(sys.argv[2])
rect = pymupdf.Rect(0, 0, *pymupdf.paper_size("a4"))
area = rect + (45, 45, -45, -50)
more, pages = 1, 0
while more:
    dev = writer.begin_page(rect)
    more, _ = story.place(area)
    story.draw(dev)
    writer.end_page()
    pages += 1
    if pages > 80:
        raise SystemExit("%s: runaway layout past 80 pages" % sys.argv[2])
writer.close()

# A Story that lays nothing out still writes a valid, empty PDF, so check.
doc = pymupdf.open(sys.argv[2])
words = sum(len(doc[i].get_text().split()) for i in range(doc.page_count))
src_words = len(io.open(sys.argv[1], encoding="utf-8").read().split())
if words < 0.6 * src_words:
    raise SystemExit("%s: only %d words laid out of %d in the source -- the "
                     "render dropped content" % (sys.argv[2], words, src_words))
print("  wrote %s  (%d pages, %d words)" % (sys.argv[2], pages, words))
