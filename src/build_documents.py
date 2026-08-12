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
CSS = """
/* The 4-page cap is a hard requirement and the figures are what push against it, so the
   image height is capped rather than the prose cut. Verified by counting pages in the
   rendered PDF, not by a words-per-page estimate -- the estimate said 2.9 pages while the
   real render came out at 5.

   SCALE is per document (see SCALE below) because the two have different densities: one
   shared value has to satisfy the tighter document, which left the other one's last page
   two-thirds empty. Each is tuned to fill its fourth page without spilling onto a fifth. */
@page { size: A4; margin: 12mm 13mm 12mm 13mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; font-size: %(font)spt;
       line-height: %(lh)s; color: #111; max-width: none; margin: 0; }
h1 { font-size: %(h1)spt; margin: 0 0 2pt 0; line-height: 1.18; }
h2 { font-size: %(h2)spt; margin: %(hgap)spt 0 4pt 0; border-bottom: 1px solid #d8dee4;
     padding-bottom: 1.5pt; break-after: avoid; }
h3 { font-size: %(h3)spt; margin: 8pt 0 2pt 0; break-after: avoid; }
p  { margin: %(pgap)spt 0; text-align: justify; }
img { max-width: 100%%; max-height: %(imgh)smm; width: auto; height: auto; display: block;
      margin: 5pt auto 1pt auto; break-inside: avoid; }
figure, p:has(img) { break-inside: avoid; }
em { color: #333; }
table { border-collapse: collapse; width: 100%%; font-size: %(tbl)spt; margin: 4pt 0;
        break-inside: avoid; }
th, td { border: 1px solid #cfd6dd; padding: 1.8pt 4pt; text-align: left; }
th { background: #eef2f6; }
code { background: #f2f4f7; padding: 0.5pt 2.5pt; border-radius: 3px; font-size: 8.6pt; }
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
    "REPORT":         dict(font=9.2, lh=1.38, h1=16, h2=11.8, h3=10.3, hgap=11,
                           pgap=3.5, imgh=55, tbl=8.0),
    "KAGGLE_WRITEUP": dict(font=8.9, lh=1.34, h1=15, h2=11, h3=9.6, hgap=9,
                           pgap=3, imgh=55, tbl=8.0),
}


def page_count(pdf: Path) -> int:
    """Pages in a PDF, without pulling in a PDF library for one number."""
    import re
    return len(re.findall(rb"/Type\s*/Page[^s]", pdf.read_bytes()))


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {' '.join(map(str, cmd))}\n{r.stdout}\n{r.stderr}")
    return r


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
    css.write_text(CSS % SCALE[stem], encoding="utf8")
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
