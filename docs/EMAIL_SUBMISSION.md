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
| 3 | `REPORT.pdf` (and `REPORT.docx`) | 4-page methodology report — already rendered |
| 4 | `I9_pipeline.ipynb` | notebook, runs clean, reproduces the CSV |
| 5 | `media_gallery/` (7 + card) | includes both **required** maps — health and yield-to-date |
| 6 | `description_figures/` (6) | the evidence figures embedded in the Kaggle description |

---

## Body

Dear GalaxEye / ANRF AISEHack team,

Please find below our Round 2 submission for the SAR Crop Health & Yield Estimation challenge.

**Team:** GDHTM
**Members:** Yash Sorathiya, Jenish Sorathiya, Yajurshi Velani, Mahi Parmar, Aayush Pandya
**Study area:** Sokhda village (`village_id` 1), Vadodara, Gujarat - 966 farm parcels, kharif 2025

**Kaggle Writeup:** <paste the writeup URL>
**Public Notebook:** <paste the public notebook URL>

**Methodology:**

**Overall approach.** We estimate three per-parcel quantities - crop type, a crop health index and
yield-to-date - for all 966 farm parcels of Sokhda village, Vadodara, Gujarat, for kharif 2025,
without any per-farm ground truth. Everything known about this village's crops is known only in
aggregate: the crop-area shares at village level, the yield anchor at district level. Both
deliverables are therefore built the same way - hold the aggregate, and let the SAR supply only the
variation inside it. Distributing a known total across finer units using an ancillary variable
correlated with the true distribution is dasymetric mapping, and it is applied twice. Every shipped
value is derived from the four provided Capella X-band HH SLC acquisitions; Sentinel-1 and
Sentinel-2 are used only as independent witnesses to test the product after it is built, and no
optical or C-band measurement enters any submitted number.

**Data preprocessing.** SLC pixels are complex, so brightness is formed as beta0 = scale_factor x
|z|^2 following the product's own radiometry field, then converted to the terrain-referenced gamma0
= beta0 x tan(theta) using a per-pixel incidence angle reconstructed from the orbit state vectors,
which agrees with the product metadata to 0.006 degrees. Slant range is geocoded to EPSG:32643 with
the 225 supplied ground control points, resampling by averaging so the multi-look happens in the
same step; a 5 m grid carries the per-farm statistics and a 2 m grid the texture. Each parcel is
eroded before sampling so boundary pixels never mix two fields. Coverage is complete - 966 of 966
farms carry a row: 895 measured directly, 52 filled by spatial nearest-neighbour imputation from
adjacent farms of the same crop, 19 flagged for radio-frequency interference, with the provenance of
every row recorded. Absolute calibration is not claimed: our gamma0 reads about +17 dB above the
physically expected level, consistent with ESA's EDAP finding that Capella's absolute accuracy is
undeclared while its relative accuracy is good, so every downstream quantity is a difference between
dates or a rank within a crop.

**Feature extraction / engineering.** Per farm we compute per-date gamma0, inter-date differences,
the within-farm coefficient of variation, the season integral over all four acquisitions, and GLCM
texture. Four families feed the health index: level (August gamma0, peak canopy volume), growth
(14 Aug minus 19 Jun, the only geometry-matched date pair at 0.076 degrees apart), uniform (negative
within-farm CV, since a patchy stand means gaps, waterlogging or pest damage) and persist (the
season integral, canopy held across the season rather than on one lucky date). Each family is
z-scored across farms and scored within crop, so 50 means typical for that crop rather than typical
overall.

**Model / methodology.** Crop type is a constrained assignment: per-farm soft evidence from X-band
with a physical basis - the 19 June flood/double-bounce response for rice, August volume scattering
for cotton, the August-minus-June difference - is biased until the area-weighted argmax shares match
our Round 1 village shares, with argmax taken only at the end. The health index is the weighted sum
of the four families, where each weight is inversely proportional to that family's total absolute
correlation with the others, w_k proportional to 1 / sum_j |rho(k,j)|; the rule reads only the
feature matrix and is blind to every witness by construction. Yield-to-date is
anchor(district) x completion(farm) x accumulation(farm): the level comes from published district
statistics and both per-farm terms are measured from SAR - completion from each farm's own
August-to-October change, accumulation from the season integral - reported strictly to the 13
October acquisition and never projected to final harvest.

**External datasets.** Sentinel-2 L2A and Sentinel-1 RTC via Microsoft Planetary Computer (witnesses
only, never inputs), NASA POWER for rainfall context, published Vadodara APY agricultural statistics
for the yield level anchor, and the Gujarat DCS parcel registry for survey numbers - all free and
openly licensed. No paid or restricted-access data was used.

**Attached:**

1. Farm-level results - CSV and XLSX, columns `village_id`, `farm_id`, `crop_type`, `health_index`,
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
