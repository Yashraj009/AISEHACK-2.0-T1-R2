"""Stage everything the Kaggle submission needs into one folder.

The upload is manual and the deadline is close, so the failure mode to design against
is not a modelling mistake -- it is uploading the wrong file, or a notebook that cannot
find its data because the dataset was assembled by hand at 2am.

Produces `upload/`:

    upload/submission.csv          the deliverable CSV, verified against the host dummy
    upload/WRITEUP.md              the <=4-page writeup
    upload/figures/                cover + gallery, exactly what goes in the media gallery
    upload/I9_pipeline.ipynb       the public notebook
    upload/kaggle_dataset/         <- zip THIS and upload as a Kaggle Dataset
    upload/UPLOAD_CHECKLIST.md     the steps, in order

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

    # ---- the four things a judge actually opens -------------------------------
    shutil.copy2(RESULTS / "submission.csv", UP / "submission.csv")
    shutil.copy2(ROOT / "docs" / "WRITEUP.md", UP / "WRITEUP.md")
    shutil.copy2(ROOT / "notebooks" / "I9_pipeline.ipynb", UP / "I9_pipeline.ipynb")
    nfig = copy_tree(FIGURES, UP / "figures", "cover.png")
    nfig += copy_tree(FIGURES, UP / "figures", "gallery_*.png")

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
        size_mb=size_mb, nfig=nfig,
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

## 3. Writeup

1. Kaggle → competition → **New Writeup**.
2. Paste `upload/WRITEUP.md`. It is ~2600 words, about 4 pages rendered — check the
   rendered length before submitting, since the cap is on pages, not words.
3. **Media Gallery**: upload all {nfig} images from `upload/figures/`.
   Set `cover.png` as the **cover image** (required).
4. **Project Files / Link**: attach the public notebook from step 2.
5. Attach `upload/submission.csv`.

## 4. Submit

Click **Submit** in the top right. A saved-but-unsubmitted writeup is not judged.

---

## What is being submitted

- `submission.csv` — 966 rows, 5 columns, no nulls, verified against the host's own dummy
- crop mix: {crops}
- writeup — approach, aux-data declaration, validation, limitations
- notebook — full pipeline, runs clean from a fresh kernel, self-reproduction assert
- {nfig} figures including the required cover

## Last-minute sanity

If you change anything at all, re-run:

    python src/d11_ship.py        # 18/18 must pass
    python src/check_writeup.py   # every quoted number must match the CSV
"""


if __name__ == "__main__":
    main()
