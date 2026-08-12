"""Render REPORT.md and KAGGLE_WRITEUP.md to DOCX and PDF.

WHY NOT JUST PANDOC. Pandoc handles the DOCX directly, and converts the LaTeX in the
markdown into real OMML equations that Word renders as maths rather than as literal
backslashes. For PDF, pandoc's default engine is pdflatex, which is NOT installed on this
machine -- so PDF goes markdown -> standalone HTML (MathML, images inlined) -> headless
Chrome --print-to-pdf. Chrome renders MathML natively, so the equations survive.

Images are referenced as `figures/NAME.png` relative to docs/, which is where a copy of
each figure lives, so both documents render correctly in place AND after being copied
into upload/ where a figures/ folder sits alongside them.

Run:  python src/build_documents.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, log

DOCS = ROOT / "docs"
OUT = ROOT / "upload"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")

# A4 with sane margins and figures that cannot overflow the page. Kept here rather than in
# a separate .css so the whole conversion is one file with no hidden dependency.
FONT_DIR = DOCS / "fonts"


def _font_face():
    """Literata as base64 @font-face rules, or nothing if the files are absent.

    Falling back silently matters: the build must not break on a machine that has not
    fetched the fonts, it should just render in the stack named after Literata.
    """
    import base64

    faces = []
    for fname, style in (("Literata.ttf", "normal"), ("Literata-Italic.ttf", "italic")):
        p = FONT_DIR / fname
        if not p.exists():
            continue
        b64 = base64.b64encode(p.read_bytes()).decode("ascii")
        faces.append(
            "@font-face { font-family: Literata; font-style: %s; font-weight: 200 900;"
            " src: url(data:font/ttf;base64,%s) format('truetype'); }" % (style, b64))
    return "\n".join(faces)


CSS = """
/* The 4-page cap is a hard requirement and the figures are what push against it, so the
   image height is capped rather than the prose cut. Verified by counting pages in the
   rendered PDF, not by a words-per-page estimate -- the estimate said 2.9 pages while the
   real render came out at 5.

   SCALE is per document (see SCALE below) because the two have different densities: one
   shared value has to satisfy the tighter document, which left the other one's last page
   two-thirds empty. Each is tuned to fill its fourth page without spilling onto a fifth. */
@page { size: A4; margin: %(mtop)smm 13mm %(mbot)smm 13mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: Literata, Georgia, "Times New Roman", serif; font-size: %(font)spt;
       line-height: %(lh)s; color: #111; max-width: none; margin: 0; }
h1 { font-size: %(h1)spt; margin: 0 0 3pt 0; line-height: 1.2; text-align: center; }
/* the subtitle and the author/study-area block are centred with the title */
h1 + h3 { text-align: center; font-size: 10.6pt; font-weight: 600; color: #334155;
          margin: 0 0 5pt 0; border: 0; }
h1 + h3 + p { text-align: center; color: #334155; margin: 0 0 2pt 0; }
h2 { font-size: %(h2)spt; margin: %(hgap)spt 0 4pt 0; padding: 6.5pt 0 0 0;
     border-top: 0.75pt solid #94a3b8; color: #0f172a; break-after: avoid; }
h2:first-of-type { border-top: 0; }
h3 { font-size: %(h3)spt; margin: 7pt 0 2pt 0; color: #1e293b; break-after: avoid;
     border-bottom: 1px solid #e2e8f0; padding-bottom: 1pt; }
ul, ol { margin: 3pt 0 3pt 0; padding-left: 14pt; }
li { margin: 1.2pt 0; text-align: justify; }
li > strong:first-child { color: #0f172a; }
p  { margin: %(pgap)spt 0; text-align: justify; }
img { max-width: 100%%; max-height: %(imgh)smm; width: auto; height: auto; display: block;
      margin: 5pt auto 1pt auto; break-inside: avoid; }
figure, p:has(img) { break-inside: avoid; }
/* The method diagram is far wider than the map panels, so the shared height cap shrinks it
   until its labels are unreadable. It is selected by ALT TEXT: --embed-resources rewrites
   every src to a base64 data URI, so a src*="name" selector cannot match, and pandoc's gfm
   reader has no link_attributes. Alt text survives into both the HTML and the DOCX. */
img[alt="Figure 1"] { max-height: %(fig1)smm; }
em { color: #333; }
/* Figure and table captions: an all-italic paragraph. Centred under its figure and one
   point smaller than the body, so it reads as a label rather than as more prose. */
p:has(> em:only-child) { text-align: center; font-size: %(cap)spt; color: #475569;
                         margin: 1.5pt 0 4pt 0; }
/* a table is a block, not a paragraph: give it room to read as one */
table { border-collapse: collapse; width: 100%%; font-size: %(tbl)spt;
        margin: 7.5pt 0 8pt 0; break-inside: avoid; }
td { border: 1px solid #cfd6dd; padding: 1.8pt 4pt; }
/* column alignment is set per column in the markdown -- numbers centred, text left --
   but a header is a label, not data, so it is centred and bold in every column. */
th { border: 1px solid #cfd6dd; padding: 1.8pt 4pt; background: #eef2f6;
     text-align: center !important; font-weight: 600; }
code { background: #f2f4f7; padding: 0.5pt 2.5pt; border-radius: 3px;
       font-family: "Cascadia Mono", Consolas, monospace; font-size: 8.0pt; }
table { font-variant-numeric: tabular-nums; }
pre  { background: #f6f8fa; padding: 5pt; overflow-x: auto; font-size: 8.4pt; }
blockquote { margin: 4pt 0; padding: 2.5pt 8pt; border-left: 3px solid #cbd5e1;
             background: #f8fafc; }
math { font-size: 1.02em; }
hr { border: 0; border-top: 1px solid #d8dee4; margin: 9pt 0; }
"""


MAX_PAGES = 4

# Per-document type scale. Tuned against the real render: raise until the PDF turns 5
# pages, then step back one. build() asserts the result is still within MAX_PAGES.
SCALE = {
    "REPORT":         dict(font=8.8, lh=1.30, h1=15.5, h2=11.4, h3=10.0, hgap=8,
                           pgap=3.0, imgh=49, fig1=62, tbl=7.9, mtop=14, mbot=11.5, cap=8.1),
    "KAGGLE_WRITEUP": dict(font=8.9, lh=1.32, h1=15, h2=11, h3=9.6, hgap=8,
                           pgap=2.9, imgh=52, fig1=58, tbl=8.0, mtop=13, mbot=10.5, cap=7.9),
}


def page_count(pdf: Path) -> int:
    """Pages in a PDF.

    Was a regex over /Type /Page. That stopped being true once the header/footer stamp
    rewrote the file: the incremental save leaves the superseded page objects in place,
    so the regex counted 10 for a 4-page document. Ask the parser instead.
    """
    import pymupdf

    with pymupdf.open(pdf) as doc:
        return doc.page_count


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {' '.join(map(str, cmd))}\n{r.stdout}\n{r.stderr}")
    return r


def stamp(pdf: Path, left: str, right: str):
    """Draw the running header and the centred page number onto every page.

    Chrome supports no paged-media margin boxes and no header template via the CLI, so
    this is done after the fact. PyMuPDF is already a dependency of the page-count gate.
    """
    import pymupdf

    doc = pymupdf.open(pdf)
    n = doc.page_count
    for i, page in enumerate(doc, start=1):
        w, h = page.rect.width, page.rect.height
        # 21/26pt against a 14mm (39.7pt) top margin leaves ~14pt of clear space; at
        # 30/36 the rule sat under 4pt above the first line of body text
        y_head, y_rule, y_foot = 21.0, 26.0, h - 22.0
        page.insert_text((37, y_head), left, fontname="Helvetica-Bold", fontsize=7.6,
                         color=(0.20, 0.26, 0.33))
        rw = pymupdf.get_text_length(right, fontname="Helvetica-Bold", fontsize=7.6)
        page.insert_text((w - 37 - rw, y_head), right, fontname="Helvetica-Bold",
                         fontsize=7.6, color=(0.20, 0.26, 0.33))
        page.draw_line(pymupdf.Point(37, y_rule), pymupdf.Point(w - 37, y_rule),
                       color=(0.80, 0.84, 0.88), width=0.6)
        num = f"{i} of {n}"
        nw = pymupdf.get_text_length(num, fontname="Helvetica", fontsize=7.6)
        page.insert_text(((w - nw) / 2, y_foot), num, fontname="Helvetica", fontsize=7.6,
                         color=(0.40, 0.45, 0.50))
    doc.saveIncr() if doc.can_save_incrementally() else doc.save(str(pdf), incremental=False)
    doc.close()
    return n


def build(stem, title):
    md = DOCS / f"{stem}.md"
    assert md.exists(), md
    docx, pdf = OUT / f"{stem}.docx", OUT / f"{stem}.pdf"
    html = OUT / f"_{stem}.html"

    # --- DOCX: pandoc turns the $...$ into native Word equations -------------------
    run(["pandoc", str(md), "-o", str(docx), "--from", "gfm+tex_math_dollars",
         "--resource-path", str(DOCS), "--metadata", f"title={title}"])

    # --- PDF via HTML + headless Chrome -------------------------------------------
    css = OUT / "_print.css"
    css.write_text(_font_face() + "\n" + CSS % SCALE[stem], encoding="utf8")
    # pagetitle, NOT metadata title: --metadata title renders a second <h1> above the
    # document's own heading, so the title appeared twice on page 1. pagetitle sets the
    # browser/PDF title only.
    run(["pandoc", str(md), "-o", str(html), "--from", "gfm+tex_math_dollars",
         "--standalone", "--mathml", "--embed-resources",
         "--resource-path", str(DOCS), "--css", str(css),
         "--variable", f"pagetitle={title}"])
    assert CHROME.exists(), f"Chrome not found at {CHROME}"
    run([str(CHROME), "--headless", "--disable-gpu", "--no-pdf-header-footer",
         f"--print-to-pdf={pdf}", html.resolve().as_uri()])

    stamp(pdf, "ANRF AISEHack 2.0 Round 2", "Team GDHTM")

    html.unlink(missing_ok=True)
    css.unlink(missing_ok=True)
    return docx, pdf


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    made = []
    for stem, title in [("REPORT", "AISEHack 2.0 Round 2 — Methodology Report — Team GDHTM"),
                        ("KAGGLE_WRITEUP", "AISEHack 2.0 Round 2 — Kaggle Writeup — Team GDHTM")]:
        made += list(build(stem, title))
    print()
    bad = []
    for p in made:
        kb = p.stat().st_size / 1024
        pages = page_count(p) if p.suffix == ".pdf" else None
        tag = f"{pages} pages" if pages else "docx"
        print(f"  {p.name:28s} {kb:8.0f} KB   {tag}")
        assert kb > 20, f"{p.name} is suspiciously small -- conversion probably lost content"
        # The organisers cap the written documentation at 4 pages, and the Kaggle writeup
        # carries the same limit. Word count is a bad proxy once figures are embedded --
        # it read 2.9 pages while the render was 5 -- so the gate counts real PDF pages.
        if pages and pages > MAX_PAGES:
            bad.append(f"{p.name}: {pages} pages > {MAX_PAGES}")
    if bad:
        raise SystemExit("PAGE LIMIT EXCEEDED -- " + "; ".join(bad))
    log("build_documents", files=len(made))


if __name__ == "__main__":
    main()
