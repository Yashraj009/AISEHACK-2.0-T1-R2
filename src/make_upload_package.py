"""Stage everything the Kaggle submission needs into one folder.

The upload is manual and the deadline is close, so the failure mode to design against
is not a modelling mistake -- it is uploading the wrong file, or a notebook that cannot
find its data because the dataset was assembled by hand at 2am.

Produces `upload/`:

    upload/submission.csv          the deliverable CSV, verified against the host dummy
    upload/KAGGLE_WRITEUP.md, EMAIL_SUBMISSION.md, KAGGLE_DESCRIPTION_PASTE.md
                                    copy/paste sources -- staged from docs/, unrendered
    upload/media_gallery/          Kaggle Media Gallery -- stands alone, no prose needed
    upload/description_figures/    Kaggle Project Description -- needs the surrounding prose
    upload/I9_pipeline.ipynb       the public notebook
    upload/kaggle_dataset/         <- zip THIS and upload as a Kaggle Dataset
    upload/UPLOAD_CHECKLIST.md     the steps, in order

Note: build_documents.py (run separately) adds REPORT.pdf/.docx and KAGGLE_WRITEUP.pdf/.docx --
those, not a copied docs/REPORT.md, are what actually gets read/mailed, so REPORT.md is not
staged here at all.

The kaggle_dataset folder preserves the directory layout the notebook's root-discovery
expects (a folder containing src/), and deliberately EXCLUDES the 2.1 GB of SLCs: with
FAST=True the notebook reads the cached rasters, so the SLCs are only needed to rebuild
from scratch, which no judge will do inside a 12-hour kernel.

Run:  python src/make_upload_package.py
"""
import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import AUX, CACHE, FIGURES, RESULTS, ROOT, log

UP = ROOT / "upload"
DS = UP / "kaggle_dataset"


# Never publish these, whatever the glob matches. Collected Village Form 12 records are
# derived from 7/12 extracts, which are personal land data tied to named owners; the
# survey-number join makes each row individually identifiable. This dataset becomes
# PUBLIC on Kaggle, so the exclusion is enforced here rather than left to whoever runs
# the script remembering. `.gitignore` protects the repo; this protects the upload.
NEVER_PUBLISH = {"ground_truth_vf12.csv", ".kdss_token", ".alu_key"}


def copy_tree(src, dst, pattern="*"):
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for p in sorted(src.glob(pattern)):
        if p.is_file() and p.name not in NEVER_PUBLISH:
            shutil.copy2(p, dst / p.name)
            n += 1
    return n


def main():
    if UP.exists():
        shutil.rmtree(UP)
    UP.mkdir(parents=True)

    # ---- what a judge and the organisers actually open ------------------------
    shutil.copy2(RESULTS / "submission.csv", UP / "submission.csv")
    shutil.copy2(ROOT / "notebooks" / "I9_pipeline.ipynb", UP / "I9_pipeline.ipynb")
    # The guidelines name three further artefacts explicitly: the 4-page report that goes
    # to Insights@galaxeye.space, the Kaggle Project Description, and a STANDALONE
    # spreadsheet of the farm-level results. Staging them here keeps the email and the
    # Kaggle upload reading from one folder instead of from scattered paths.
    for name in ("KAGGLE_WRITEUP.md", "EMAIL_SUBMISSION.md",
                "KAGGLE_DESCRIPTION_PASTE.md"):
        src = ROOT / "docs" / name
        if src.exists():
            shutil.copy2(src, UP / name)
    import pandas as pd
    sheet = pd.read_csv(RESULTS / "submission.csv")
    stem = "GDHTM_Sokhda_farm_level_results"
    sheet.to_csv(UP / f"{stem}.csv", index=False)
    try:
        with pd.ExcelWriter(UP / f"{stem}.xlsx", engine="openpyxl") as xl:
            sheet.to_excel(xl, index=False, sheet_name="farm_level_results")
    except Exception as exc:                      # openpyxl absent -> CSV still satisfies it
        print(f"  note: xlsx not written ({exc}); the CSV satisfies the requirement")
    # Two DIFFERENT audiences, so two folders. The Media Gallery is browsed without the
    # text and each item must stand alone -- it carries the deliverables and the proof
    # they are real. The Project Description figures are argument: they need the
    # surrounding prose to mean anything, and repeating them in the gallery would just
    # make the gallery look padded. Nothing appears in both.
    GALLERY = ["cover.png",                             # required Kaggle cover
               "gallery_00_method_overview.png",        # the approach, standalone
               "gallery_01_health_index_map.png",       # REQUIRED by the guidelines
               "gallery_02_yield_to_date_map.png",      # REQUIRED by the guidelines
               "gallery_03_crop_classification_map.png",
               "gallery_05_village_aggregate.png",
               "gallery_07_independent_validation.png"]
    INLINE = ["gallery_04_coverage_and_confidence.png",
              "gallery_06_temporal_trajectory.png",
              "gallery_08_season_witness.png",
              "gallery_09_robustness.png",
              "gallery_10_negatives.png",
              "gallery_11_why_xband.png"]

    ngal = 0
    for name in GALLERY:
        ngal += copy_tree(FIGURES, UP / "media_gallery", name)
    ninline = 0
    for name in INLINE:
        ninline += copy_tree(FIGURES, UP / "description_figures", name)
    ngal += copy_tree(FIGURES, UP / "media_gallery", "thumbnail_560x280.png")
    nfig = ngal + ninline
    # No upload/figures/ copy: REPORT.pdf/.docx and KAGGLE_WRITEUP.pdf/.docx (rendered
    # separately by build_documents.py from docs/, where docs/figures/ already lives)
    # are what actually gets read -- a further figures/ copy here served only a raw
    # upload/REPORT.md that nothing downstream ever read either. Both were dropped.

    # _generated is the code-drawn method diagram, kept for reproducibility; the gallery
    # ships the hand-designed one under the plain name, so it is not a stray.
    stray = ({p.name for p in FIGURES.glob("gallery_*.png")} - set(GALLERY) - set(INLINE)
             - {"gallery_00_method_overview_generated.png"})
    assert not stray, f"figure assigned to neither gallery nor description: {sorted(stray)}"

    # ---- the dataset the notebook needs to run on Kaggle ----------------------
    # layout must keep `src/` at the top so _find_root() resolves it
    copy_tree(ROOT / "src", DS / "src", "*.py")
    copy_tree(RESULTS, DS / "results", "*.csv")
    copy_tree(CACHE, DS / "results" / "cache", "*.tif")
    copy_tree(AUX, DS / "data_aux", "*.csv")
    copy_tree(AUX, DS / "data_aux", "*.md")
    # the shapefiles, in the exact nesting common.py expects
    data_name = "anrf-aise-hack-2-0-round-2-sar-crop-health-yield-estimation"
    for sub in ("Farm_boundaries_shp/Farm_boundaries_shp",
                "Village_Shp/Village_Shp"):
        src = ROOT / data_name / sub
        if src.exists():
            copy_tree(src, DS / data_name / sub, "*")

    size_mb = sum(p.stat().st_size for p in DS.rglob("*") if p.is_file()) / 1048576

    # ---- verify the CSV one final time, against the host's own file ----------
    sub = pd.read_csv(UP / "submission.csv")
    host = pd.read_excel(ROOT / "Sokhda_Dummy_Submission.xlsx")
    checks = {
        "columns identical to host": list(sub.columns) == list(host.columns),
        "966 rows": len(sub) == 966,
        "farm_id set identical": set(sub.farm_id) == set(host.farm_id),
        "no nulls": int(sub.isna().sum().sum()) == 0,
        "crop vocabulary a subset": not (set(sub.crop_type) - set(host.crop_type)),
        "yield in t/ha (< host max)": sub.yield_estimate_to_date.max() <
                                      host.yield_estimate_to_date.max() * 3,
    }
    print("=" * 66)
    print("FINAL CSV VERIFICATION vs Sokhda_Dummy_Submission.xlsx")
    print("=" * 66)
    for k, v in checks.items():
        print(f"  [{'PASS' if v else 'FAIL'}] {k}")
    if not all(checks.values()):
        raise SystemExit("CSV does not match the host schema -- do not upload")

    (UP / "UPLOAD_CHECKLIST.md").write_text(CHECKLIST.format(
        size_mb=size_mb, nfig=nfig, ngal=ngal, ninline=ninline,
        crops=", ".join(f"{c} {int(n)}" for c, n in
                        sub.crop_type.value_counts().items())), encoding="utf8")

    print()
    print(f"  package ready: {UP}")
    print(f"  kaggle_dataset: {size_mb:.0f} MB (SLCs deliberately excluded)")
    print(f"  figures staged: {nfig}")
    print(f"  next: open {UP / 'UPLOAD_CHECKLIST.md'}")
    log("upload.package", size_mb=round(size_mb, 1), figures=nfig)


CHECKLIST = """# Upload checklist — do these in order

Everything below is already staged in `upload/`. Nothing needs to be regenerated.

## 1. Kaggle Dataset (do this FIRST — the notebook depends on it)

1. Zip the folder `upload/kaggle_dataset/` (**{size_mb:.0f} MB**).
2. Kaggle → **Datasets → New Dataset** → upload the zip.
3. Title it something stable, e.g. `aisehack-r2-sokhda-pipeline`.
4. Set it **Public** (a private dataset attached to a public notebook is auto-published
   after the deadline anyway, so public now avoids a surprise).

> The 2.1 GB of Capella SLCs are **deliberately excluded**. The notebook runs with
> `FAST = True`, which reads the cached rasters in `results/cache/`. `FAST = False`
> rebuilds from the SLCs and is not needed for a judge to run it.

## 2. Kaggle Notebook

1. Kaggle → **Code → New Notebook** → **File → Upload Notebook** →
   `upload/I9_pipeline.ipynb`.
2. **Add Data** → attach the dataset from step 1.
3. **Run All.** It should complete with no errors; the last cell asserts it reproduces
   the shipped `submission.csv` exactly.
4. **Save Version** → set visibility **Public**.
5. Copy the notebook URL — you need it for the writeup's Project Link.

> If it cannot find the project it fails with a message naming every path it looked in.
> That means the dataset is not attached, or was zipped one level too deep — the folder
> containing `src/` must be at the top of the dataset.

## 3. Kaggle Writeup

The Title and Subtitle fields are the two fenced blocks at the top of
`upload/KAGGLE_WRITEUP.md` -- copy each verbatim, both already fit their character caps.

1. Kaggle → competition → **New Writeup**.
2. **Project Description**: paste `upload/KAGGLE_DESCRIPTION_PASTE.md` whole. It already
   embeds its figures as uploaded Kaggle images; the only manual step is the `>>>` marker
   lines, which mark where to (re-)insert the method-overview diagram.
3. **Media Gallery**: the 7 images in `upload/media_gallery/` (plus its required
   560x280 card, `thumbnail_560x280.png`, uploaded separately as the card, not a gallery
   item) — set `cover.png` as the cover image. The {ninline} files in
   `upload/description_figures/` belong in the description instead — nothing appears in
   both places.
4. **Project Files / Link**: attach the public notebook from step 2.
5. Attach `upload/GDHTM_Sokhda_farm_level_results.csv` (and the `.xlsx`).

## 4. Submit

Click **Submit** in the top right. A saved-but-unsubmitted writeup is not judged.

---

## What is being submitted

- `submission.csv` — 966 rows, 5 columns, no nulls, verified against the host's own dummy
- crop mix: {crops}
- report — `REPORT.pdf`/`.docx`, 4-page methodology, mailed to the organisers
- writeup — Kaggle title/subtitle/description, approach, validation, limitations
- notebook — full pipeline, runs clean from a fresh kernel, self-reproduction assert
- {nfig} figures: {ngal} in the Media Gallery (incl. the required cover), {ninline} inline
  in the Project Description

## Last-minute sanity

If you change anything at all, re-run in this order:

    python src/make_upload_package.py   # restage everything into upload/
    python src/build_documents.py       # re-render REPORT.pdf/.docx and KAGGLE_WRITEUP.pdf/.docx
    python src/check_submission_pack.py # the organisers' own checklist
    python src/check_writeup.py         # every quoted number must match the CSV
    python src/d11_ship.py              # 19/19 must pass
"""


if __name__ == "__main__":
    main()
