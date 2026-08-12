# Email submission — copy/paste

**To:** Insights@galaxeye.space
**Deadline:** 13 Aug 2026, 12:00 AM (i.e. midnight at the end of 12 Aug — send today)

**Subject** (exact format required by the guidelines; a missing team name may disqualify):

```
ANRF - AISEHack 2.0 Round 2 Submission - GDHTM
```

**Attachments** (all in `upload/`):

| # | file | requirement it satisfies |
|---|---|---|
| 1 | `GDHTM_Sokhda_farm_level_results.csv` | required output CSV, 5 columns, one row per farm |
| 2 | `GDHTM_Sokhda_farm_level_results.xlsx` | "standalone spreadsheet (Excel or CSV)" |
| 3 | `REPORT.pdf` (export `docs/REPORT.md`) | 4-page methodology report |
| 4 | `I9_pipeline.ipynb` | notebook, runs clean, reproduces the CSV |
| 5 | `media_gallery/` (7 + card) | includes both **required** maps — health and yield-to-date |
| 6 | `description_figures/` (6) | the evidence figures embedded in the Kaggle description |

---

## Body

Dear GalaxEye / ANRF AISEHack team,

Please find below our Round 2 submission for the SAR Crop Health & Yield Estimation challenge.

**Team:** GDHTM
**Members:** Yash Sorathiya, Jenish Sorathiya, Yajurshi Velani, Mahi Parmar, Aayush Pandya
**Study area:** Sokhda village (`village_id` 1), Vadodara, Gujarat — 966 farm parcels, kharif 2025

**Kaggle Writeup:** <paste the writeup URL>
**Public Notebook:** <paste the public notebook URL>

**Approach in brief.** Every value in our submission is derived from the four provided Capella
X-band HH SLC acquisitions. Sentinel-1 and Sentinel-2 are used only as independent witnesses to test
the product after it is built; no optical or C-band measurement enters any submitted number. Crop
type carries our Round 1 result onto the new farm boundaries under an area-share constraint; the
health index is a four-family composite whose weights are derived from feature redundancy rather
than hand-tuned, scored within crop; and `yield_estimate_to_date` is a district anchor scaled by two
per-farm SAR-measured terms, reported strictly to the 13 October acquisition and not projected to
final harvest.

**Attached:**

1. Farm-level results — CSV and XLSX, columns `village_id`, `farm_id`, `crop_type`, `health_index`,
   `yield_estimate_to_date`, one row per farm (966 rows, no nulls).
2. Four-page methodology report (PDF).
3. The full pipeline notebook, which runs from a fresh kernel and whose final cell asserts that it
   reproduces the submitted CSV exactly.
4. The media gallery images, including the required farm-level Health Index and Yield Estimate to
   Date maps.

All external datasets used are publicly available and free (Microsoft Planetary Computer for the
Sentinel witnesses, NASA POWER for rainfall, published Gujarat agricultural statistics for the yield
level anchor). No paid or restricted-access data was used.

We would be glad to answer any questions.

Kind regards,
**Team GDHTM**
