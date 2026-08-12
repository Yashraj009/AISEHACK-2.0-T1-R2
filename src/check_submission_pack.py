"""Walk the organisers' "BEFORE YOU SUBMIT" checklist mechanically, line by line.

`d11_ship.py` checks that the PRODUCT is sound. This checks that the SUBMISSION PACKAGE
is complete against the Round 2 Submission Guidelines, which are a different document with
different requirements -- two required maps by name, a standalone spreadsheet, a 4-page
report, a 560x280 card, a team name in the documentation. Missing any of these is a
disqualification risk that no amount of good science recovers.

Run:  python src/check_submission_pack.py
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import RESULTS, ROOT, log

REQUIRED_COLUMNS = ["village_id", "farm_id", "crop_type", "health_index",
                    "yield_estimate_to_date"]
CROPS_ALLOWED = {"Rice", "Cotton", "Maize", "Bajra", "Groundnut"}
TEAM = "GDHTM"
PAGE_WORDS = 650          # same rule the writeup gate uses
FAILED = []


def check(label, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label:52s} {detail}")
    if not ok:
        FAILED.append(label)


def main():
    fig = RESULTS / "figures"
    up = ROOT / "upload"
    docs = ROOT / "docs"

    print("=" * 78)
    print("ROUND 2 SUBMISSION GUIDELINES -- BEFORE YOU SUBMIT")
    print("=" * 78)

    # --- required output format -------------------------------------------------
    sub = pd.read_csv(RESULTS / "submission.csv")
    check("CSV has exactly the required columns, in order",
          list(sub.columns) == REQUIRED_COLUMNS, str(list(sub.columns)))
    check("one row per farm (FID), ids unique",
          len(sub) == 966 and sub.farm_id.is_unique, f"{len(sub)} rows")
    check("no nulls anywhere", bool(sub.notna().all().all()))
    check("crop vocabulary is the five named crops",
          not (set(sub.crop_type) - CROPS_ALLOWED), str(sorted(set(sub.crop_type))))
    check("health_index within 0-100",
          bool(sub.health_index.between(0, 100).all()),
          f"{sub.health_index.min():.2f}-{sub.health_index.max():.2f}")
    check("yield is t/ha and non-negative",
          bool((sub.yield_estimate_to_date >= 0).all()) and
          float(sub.yield_estimate_to_date.max()) < 25,
          f"max {sub.yield_estimate_to_date.max():.3f} t/ha")

    # --- maps and spreadsheet ---------------------------------------------------
    hmap = fig / "gallery_01_health_index_map.png"
    ymap = fig / "gallery_02_yield_to_date_map.png"
    check("REQUIRED farm-level Health Index map present", hmap.exists(), hmap.name)
    check("REQUIRED farm-level Yield-to-Date map present", ymap.exists(), ymap.name)
    check("cover image present", (fig / "cover.png").exists())

    thumb = fig / "thumbnail_560x280.png"
    ok_thumb = thumb.exists()
    if ok_thumb:
        from PIL import Image
        with Image.open(thumb) as im:
            ok_thumb = im.size == (560, 280)
            size = im.size
        check("card/thumbnail is exactly 560x280", ok_thumb, str(size))
    else:
        check("card/thumbnail is exactly 560x280", False, "missing")

    gal = sorted(fig.glob("gallery_*.png"))
    check("supporting maps/plots in gallery", len(gal) >= 6, f"{len(gal)} gallery figures")

    # The Media Gallery and the Project Description hold DIFFERENT figures. A figure in
    # both makes the gallery look padded; a figure in neither is work the judges never see.
    mg = {p.name for p in (up / "media_gallery").glob("*.png")} - {"thumbnail_560x280.png"}
    df = {p.name for p in (up / "description_figures").glob("*.png")}
    if mg or df:
        check("gallery and description share no figure", not (mg & df),
              f"gallery {len(mg)}, inline {len(df)}, overlap {len(mg & df)}")
        every = {p.name for p in fig.glob("gallery_*.png")} | {"cover.png"}
        check("every figure is assigned to one of the two", not (every - mg - df),
              "unassigned: " + (", ".join(sorted(every - mg - df)) or "none"))
        wr_txt = (docs / "KAGGLE_WRITEUP.md").read_text(encoding="utf8")
        inline_named = set(re.findall(r"INSERT `([^`]+)`", wr_txt))
        check("writeup embeds exactly the description figures", inline_named == df,
              f"{len(inline_named)} referenced")

    xls = list(up.glob("*farm_level_results.xlsx")) + list(up.glob("*farm_level_results.csv"))
    check("standalone spreadsheet staged (xlsx and/or csv)", len(xls) >= 1,
          ", ".join(p.name for p in xls) or "missing")
    if xls:
        alt = pd.read_excel(xls[0]) if xls[0].suffix == ".xlsx" else pd.read_csv(xls[0])
        same = (list(alt.columns) == REQUIRED_COLUMNS and len(alt) == len(sub))
        check("spreadsheet matches the submission CSV structure", same,
              f"{len(alt)} rows, {len(alt.columns)} cols")

    # --- written documentation --------------------------------------------------
    rep = docs / "REPORT.md"
    if rep.exists():
        txt = rep.read_text(encoding="utf8")
        words = len(txt.split())
        check("4-page report exists and is under 4 pages", words <= 4 * PAGE_WORDS,
              f"{words} words ~ {words / PAGE_WORDS:.1f} pages")
        check("report names the team (guidelines: required in documentation)",
              TEAM in txt, TEAM)
    else:
        check("4-page report exists and is under 4 pages", False, "docs/REPORT.md missing")
        check("report names the team", False, "missing")

    wr = docs / "KAGGLE_WRITEUP.md"
    if wr.exists():
        t = wr.read_text(encoding="utf8")
        words = len(t.split())
        check("Kaggle writeup exists and is within the page limit",
              words <= 4 * PAGE_WORDS, f"{words} words ~ {words / PAGE_WORDS:.1f} pages")
        # the four topics the submission requirements name explicitly
        topics = {"Round 1": "Round 1", "health index": "health index",
                  "yield": "yield", "findings": "finding"}
        missing = [k for k, v in topics.items() if v.lower() not in t.lower()]
        check("writeup covers all four required topics", not missing,
              "missing: " + ", ".join(missing) if missing else "all present")
        check("writeup names the team", TEAM in t, TEAM)
    else:
        check("Kaggle writeup exists and is within the page limit", False, "missing")

    # --- notebook ---------------------------------------------------------------
    nb = ROOT / "notebooks" / "I9_pipeline.ipynb"
    if nb.exists():
        import json
        doc = json.loads(nb.read_text(encoding="utf8"))
        errs = sum(1 for c in doc["cells"]
                   for o in c.get("outputs", []) if o.get("output_type") == "error")
        check("notebook has no stored errors", errs == 0, f"{len(doc['cells'])} cells")
        src = "\n".join("".join(c["source"]) for c in doc["cells"])
        check("notebook asserts it reproduces the submitted CSV",
              "assert" in src and "submission" in src)
    else:
        check("notebook has no stored errors", False, "missing")

    print()
    print("=" * 78)
    if FAILED:
        print(f"  {len(FAILED)} ITEM(S) NOT READY: " + "; ".join(FAILED))
        log("check_submission_pack", status="FAIL", failed=len(FAILED))
        sys.exit(1)
    print("  SUBMISSION PACKAGE COMPLETE against the Round 2 guidelines.")
    print("=" * 78)
    log("check_submission_pack", status="PASS")


if __name__ == "__main__":
    main()
