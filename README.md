# Dasymetric Mapping of Village Crop Statistics to Parcel Level from X-band SAR

**Team GDHTM** — ANRF AISEHack 2.0, Round 2 (SAR Crop Health & Yield Estimation)
Sokhda village, Vadodara district, Gujarat — 966 farm parcels, kharif 2025

Every value in `results/submission.csv` is derived from the four provided Capella X-band
HH SLC acquisitions. Sentinel-1 and Sentinel-2 are used only as independent witnesses to
test the product after it is built — no optical or C-band measurement enters any shipped
number. See `docs/REPORT.md` (or the rendered `upload/REPORT.pdf`) for the full method.

## Layout

```
src/            the pipeline — run stages in order, or python src/d11_ship.py for the gate
notebooks/      I9_pipeline.ipynb, the public Kaggle notebook (mirrors src/ end to end)
data_aux/       small reference tables (rainfall, APY yield anchor, R1 crop shares)
results/        pipeline output — features, submission.csv, figures/, cache/ (gitignored)
docs/           submission documents: REPORT.md, KAGGLE_WRITEUP.md,
                KAGGLE_DESCRIPTION_PASTE.md, EMAIL_SUBMISSION.md, figures/, fonts/
upload/         staged, ready-to-submit package (gitignored, rebuilt by the scripts below)
papers/         reference literature the method draws on
internal/       working docs: PLAN.md, MASTER_PLAN.md, RESEARCH_LOG.md, PROGRESS.md —
                the design rationale and decision log behind src/, not required reading
                to run or judge the submission
```

`Sokhda_Dummy_Submission.xlsx` at the repo root is the host's own schema reference; every
gate below checks the shipped CSV against it directly, not against an assumption of it.

## Reproducing the submission

```
python src/d11_ship.py                # 19-check final gate — run this first
python src/make_upload_package.py     # stage docs/media into upload/
python src/build_documents.py         # render REPORT.pdf/.docx, KAGGLE_WRITEUP.pdf/.docx
python src/check_submission_pack.py   # the organisers' own "before you submit" checklist
python src/check_writeup.py           # every number quoted in the docs matches the CSV
```

Or open `notebooks/I9_pipeline.ipynb` — it runs from a fresh kernel (locally or on
Kaggle, root-discovered automatically either way) and its final cell asserts it
reproduces the shipped `submission.csv` exactly, column for column.

## Where things stand

- `results/submission.csv` — 966 rows, verified against the host schema
- `docs/REPORT.md` / `upload/REPORT.pdf` — 4-page methodology report
- `docs/KAGGLE_WRITEUP.md` — Kaggle writeup copy/paste guide (title, subtitle, gallery
  vs. description split)
- `docs/KAGGLE_DESCRIPTION_PASTE.md` — the Project Description, ready to paste as-is
- `upload/UPLOAD_CHECKLIST.md` — the manual Kaggle steps, generated fresh each run
