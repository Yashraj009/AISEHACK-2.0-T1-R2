# RESEARCH LOG — Phases T & U (2026-08-06)

Continuation of `../RESEARCH_LOG.md` (Phases A–B). Triggered by the review of `AISEHACK-2.0-T1-R2`.
Conclusions: `GAP_FIXES.md` (technical) and `VALIDATION_SOURCES.md` (ground truth).
Format: `[#] MOVE → FINDING → SO WHAT`.

---

## Phase T — Technical alternatives for the implementation gaps

### [T0] Independent re-measurement of the shipped pipeline (local, no web)
**Move:** re-ran the submission, features and cached rasters directly rather than trusting `PROGRESS.md`.
**Findings:**
- Spearman(health, yield) = **1.000 in all five crops** → the yield column is a monotone image of health.
- `health_index` is `rank(pct=True)` within crop → **uniform 0–100 by construction**; village mean 50.267.
- Rice is **not** darkest on 14 Aug (6.92 dB) — Bajra 6.37 and Groundnut 6.58 are both lower.
- "6.8× rice enrichment" reproduces at 64.2% vs 9.0% base, but `flood_hit` carries weight 2.2 in
  `e["Rice"]`, the largest weight in the evidence function → the check is circular.
- Writeup's "adjacent covered farms" imputation ≠ code's village-wide crop median (`d4_submission.py:295`).
- Offset measured against the S1 witness: ours **+9.64 dB** vs S1 C-VH **−14.66 dB** → gap 24.3 dB →
  **~+17 dB** hot, not the **+28 dB** the writeup quotes. The +28 came from `[J5]`, which measured R1's
  `scale²`-buggy processing and does not describe this pipeline.
- Between-farm spread ours **1.48 dB** vs S1 **1.82 dB** → **contrasts are not compressed**; the
  contrasts-only strategy is empirically justified. Positive result, currently unreported.
- `d_aug_jun06` median **−0.37 dB** — August darker than dry June; the growth term spans 35.24° → 28.69°.
- ρ(health, `glcm_resid`) = **−0.024** at 0.10 weight → texture inert. ρ(level, persist) = **0.742** →
  0.45 of the weight rests on one axis, which inflates the ablation result.

### [T1] ★ X-band HH over flooded paddy — the rice mechanism
**Move:** searched TerraSAR-X / X-band rice double-bounce literature.
**Finding:** co-pol X-band at season start is **dominated by double bounce from the stem–water
interaction**; the first backscatter rise runs **up to 46 days after transplanting**; X and K bands show
high early dynamic range with an **early peak**, then decline as volume scattering and canopy attenuation
take over; **HH outperforms VV** for inundated vegetation.
**So what:** Gujarat paddy transplants mid-to-late June, so **19 Jun sits inside the ≤46-day window**. The
mechanism predicts bright-19-Jun → declining-14-Aug → bare-13-Oct, which is the measured shape on all four
dates. The code's comment ("double-bounce off water and bunds") is correct; the writeup's "specular in
August" is both wrong and unnecessary. Fix is prose + figure annotation only.
Sources: [TerraSAR-X rice monitoring](https://www.sciencedirect.com/science/article/abs/pii/S0303243412001547) ·
[Partially inundated fields, polarised backscatter](https://www.tandfonline.com/doi/full/10.1080/22797254.2023.2269305) ·
[Multi-frequency L/C/X full-pol paddy](https://www.researchgate.net/publication/224383689_Radar_Backscattering_Measurement_of_a_Paddy_Rice_Field_using_Multi-frequencyL_C_and_X_and_Full-polarization) ·
[Flood mapping under vegetation](https://www.sciencedirect.com/science/article/abs/pii/S0034425719306029)

### [T2] Incidence-angle correction for multi-angle single-pol series
**Move:** searched dynamic-cosine, land-cover-specific and histogram-matching normalisation.
**Finding:** available methods are cosine-N (static or dynamic), polynomial, mean-grey-value, and histogram
matching; angular dependence **changes with growth stage**, so fixed-N is known-flawed; dynamic-N keyed on
a vegetation descriptor performs best but requires a descriptor unavailable at single-pol.
**So what:** no normalisation open to us is trustworthy — which *strengthens* the fix in `GAP_FIXES.md` §G:
stop trying to correct a 6.55° gap and use the **0.076°-matched pair** instead, removing its wet-soil
common mode by median-centering. The reason Jun 19 was rejected applies to the *level*; every downstream
use is a *between-farm contrast*, in which a village-wide offset cancels identically.
Sources: [Dynamic cosine, C-band agriculture](https://doi.org/10.3390/rs16203838) ·
[Corn phenology dynamic correction](https://www.tandfonline.com/doi/full/10.1080/01431161.2025.2460245) ·
[Acquisition geometry in wheat backscatter series](https://www.sciencedirect.com/science/article/pii/S0303243421003780)

### [T3] Yield formulations that are not a relabelling of health
**Move:** searched growth-curve integration and seasonal accumulation for SAR yield.
**Finding:** established practice is to fit a curve to the SAR series and use its **parameters**;
**accumulate the growth curve across the season** and combine accumulated with current values; compare
**neighbouring fields of the same crop** to remove soil and agro-climatic bias.
**So what:** gives two *measured* terms to replace two per-crop constants — per-farm **completion** from
measured Oct−Aug senescence (village median +2.38 dB) and per-farm **accumulation** from the existing
`season_integral`. Breaks the ρ = 1.000 degeneracy and turns "to date" into a measurement.
Sources: [ORYZA + SAR time-series yield](https://www.researchgate.net/publication/334741937_INTEGRATING_TIME-SERIES_SAR_DATA_AND_ORYZA_CROP_GROWTH_MODEL_IN_RICE_AREA_MAPPING_AND_YIELD_ESTIMATION_FOR_CROP_INSURANCES) ·
[Wheat productivity indicators from S1](https://doi.org/10.3390/rs12152385)

### [T4] ★ Speckle floor in within-field CV — explains two defects at once
**Move:** connected the measured ENL `[G6]` to the observed within-farm CV.
**Finding:** `CV²_obs ≈ CV²_true + 1/ENL`. At the measured ENL ≈ 3.5 (base grid) the pure speckle floor is
CV ≈ 0.53, against a median observed `cv_20250814` of **0.488** — the uniformity feature sits **at or below
the speckle floor**, i.e. it is measuring speckle, not canopy. Effective looks scale with plot pixel count,
so the speckle term is larger for small plots — which is precisely the reported health-vs-area bias
(ρ 0.086), arriving through the front door.
**So what (AS PROPOSED):** ENL-corrected CV should repair the uniformity family and remove the area bias.

⚠ **[T4] IS RETRACTED — refuted by measurement in the bake-off before it was shipped.**
At the *measured* L = 6.5 the corrected CV correlates with raw CV at **ρ +0.9995** — it reorders
nothing, because at fixed L the correction is a monotone transform, exactly as `[H2]` had already
concluded. At L = 3.5 it clips **651 of 966** farms to zero and destroys the feature. The area bias
does not come from CV's speckle floor at all: it came from the **growth term**, and was fixed by
switching to the geometry-matched pair (ρ(health, area) +0.086 → −0.051). The October uniformity
test was likewise fixed by that change, not by this one (−0.049 → −0.161, p = 9.9e-07).
**Lesson:** the bake-off (`src/diagnose_fixes.py`) existed precisely so a plausible-sounding fix
could be killed before it reached the deliverable. It earned its keep on its first run.

---

## Phase U — Ground-truth sources for per-farm crop type

User's question: is there a government or private source giving the actual crop per farm, with that farm's
history? Full ranking and action plan in `VALIDATION_SOURCES.md`.

### [U1] ★★★ Gujarat Village Form 12 via AnyROR — official per-plot crop, with history
**Finding:** the 7/12 "Satbara" extract = Village Form 7 (rights) + **Village Form 12, the register of
cultivation**: crop grown per **survey number**, recorded separately for **kharif / rabi / zaid**, with
**area under each crop** and **irrigation source**, maintained **year on year** by the village Talati.
Free, online, no login at `anyror.gujarat.gov.in` (verified live; captcha per record).
**The missing link:** our shapefile has no survey numbers. **BhuNaksha Gujarat** is the GIS cadastral map
carrying **survey-number boundary polygons**, maintained by the Survey Department and integrated with
AnyROR → spatial join gives farm → survey number → VF-12 → crop.
**Feasibility:** no public REST/GeoJSON API on either; semi-manual. A stratified sample of 60–120 plots is
about a day's work and statistically ample (n=100 at 70% accuracy → ±9 pt CI).
⚠ **Privacy:** 7/12 carries owner names. Crop column only; aggregate accuracy only; nothing
person-identifying in a public notebook.
Sources: [AnyROR portal](https://anyror.gujarat.gov.in/) ·
[7/12 column-by-column guide](https://bhattandjoshiassociates.com/how-to-read-a-7-12-utara-every-column-explained-2026-guide/) ·
[BhuNaksha user guide](https://bhunaksha.nic.in/bhunaksha/userguide.jsp)

### [U2] Digital Crop Survey (AgriStack) Gujarat — authoritative, not open
**Finding:** GPS-enabled plot-level crop survey; 17 states, 492 districts, 421k villages, **253 M plots** in
2024-25; Gujarat runs `gjdcs.agristack.gov.in`. States share **village-level aggregates** with DA&FW via
API; per-plot data is not published.
**So what:** best-in-class data, wrong access model for a 7-day window. Worth one email — even the
village-level kharif-2025 aggregate for Sokhda would validate our crop *mix*.
Sources: [AgriStack DPI overview](https://issca.icrisat.org/scalable-solutions/digital-public-infrastructure-for-agriculture-agristack) ·
[Gujarat Crop Survey](https://gjdcs.agristack.gov.in/crop-survey-gj/)

### [U3] ★★★ Google DeepMind ALU / AnthroKrishi — pan-India farm-level in-season crop ID
**Finding:** *Deshpande et al., arXiv 2507.02972 (Jun 2025)*. Sentinel-1 + Sentinel-2, deep learning,
**farm-level, in-season**, with a **season-detection algorithm estimating per-field sowing and harvest
dates**; billed as the first pan-India farm-level in-season crop product; field boundaries from the ALU
model at 1 m. The ground-truth table covers **all five of our crops** — Rice 4,888 / Cotton 4,365 /
Corn 5,499 / Groundnut 2,509 / Bajra 1,732 samples, 69,723 total across 2,097 S2 level-9 cells. Kharif is
evaluated separately and reliable identification is claimed from ~2 months into the season, so **October
2025 over Sokhda sits inside its operating envelope**. Access via the ALU **Research API** at
`agri.withgoogle.com`, application-based, scoped to researchers and academia.
**So what:** an independent per-farm label for our exact plots in our exact season, from different sensors
and a different method — plus per-field sowing/harvest dates that would independently validate the [T3]
completion term. Apply immediately given the lead time; cite the paper regardless of access.
Sources: [arXiv 2507.02972](https://arxiv.org/pdf/2507.02972) ·
[AnthroKrishi platform](https://agri.withgoogle.com/) ·
[ALU API docs](https://developers.google.com/agricultural-understanding/landscape-understanding)

### [U4] Krishi-DSS — claims parcel-level crop maps over multiple years
**Finding:** `krishi-dss.gov.in`, launched 16 Aug 2024, the GoI national geospatial DSS for agriculture.
Published module list explicitly includes **"parcel-level crop maps over different years"** and field
parcel segmentation. The landing page is a JS application and did not yield its layer catalogue to a fetch.
**So what:** if that layer covers Vadodara it is per-parcel crop *with history*, free, from the government —
potentially answering the entire question. **Unverified; ten minutes of manual browsing settles it. Check
this before investing in the manual VF-12 route.**
Sources: [Krishi-DSS](https://krishi-dss.gov.in/) ·
[PIB launch release](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2045987)

### [U5] ★★★ Self-serve S2 + S1 phenology classifier — no gatekeeper
**Finding:** S1+S2 fusion reaches **80–96% overall accuracy** on smallholder systems in Central and South
Asia; **S1 is especially effective for structurally distinct crops such as cotton**, S2 for the more
diverse classes; monthly temporal aggregation beats coarser binning by 1–3 points and feature selection
adds a further 2–5.
**So what:** Jun–Nov over Sokhda gives roughly 15–20 usable S2 dates plus dense S1 — an order of magnitude
more temporal information than four X-band scenes. Build it as a deliberately **independent second
opinion** and report the confusion matrix against the Capella map. Must be framed as validation and never
as an input, or it costs SAR primacy.
Sources: [S1/S2 fusion, Central & South Asia smallholders](https://www.sciencedirect.com/science/article/pii/S2352938526001400) ·
[S1/S2/Planet smallholder crop type](https://doi.org/10.3390/rs13101870) ·
[Early crop ID from S2 time series](https://pmc.ncbi.nlm.nih.gov/articles/PMC9967001/)

### [U6] Bhuvan / NRSC — OGC services, aggregate scale
**Finding:** Bhuvan exposes WMS / WFS / WCS / CSW / WMTS thematic services including cropping-pattern and
crop-type layers; programmatically accessible.
**So what:** useful for a district or village *mix* cross-check, not per-farm. Second tier.
Sources: [Bhuvan thematic services](https://bhuvan-app1.nrsc.gov.in/thematic/) ·
[Bhuvan WMS guide](https://bhuvan.nrsc.gov.in/wiki/index.php/How_to_use_WMS_services)

### [U7] PMFBY Crop Cutting Experiments — the missing *yield* validator
**Finding:** PMFBY runs Crop Cutting Experiments producing measured yields at insurance-unit
(village/cluster) level, by season and crop, published through the PMFBY / Krishi Rakshak portals.
**So what:** the submission currently has **zero** independent check on the yield column — the district APY
figure is an input, so comparing against it is circular. A CCE yield for Sokhda or its cluster for kharif
2025, on even one or two crops, would be the first external yield check. Twenty minutes to try.


---

## Phase V — Automated extraction attempts (2026-08-06)

User handled Krishi-DSS manually; this phase covers everything reachable without a human.

### [V1] What is NOT automatable — measured, not assumed
| source | probe result |
|---|---|
| Bhuvan WFS | `ows:ExceptionReport` — **"Service WFS is disabled"** |
| Bhuvan WMS (ras1) | HTTP 403 |
| `bhunaksha.gujarat.gov.in` | does not resolve (curl 000); only the NIC national root responds |
| AnyROR | reachable, but captcha-gated per record |
| Krishi-DSS | identical 78 kB SPA shell on `/`, `/api/v1/layers`, `/geoserver/*` |
| data.gov.in catalog API | 404 without a registered key |
| PMFBY | root reachable; no public JSON endpoint found |
| WorldCereal (VITO STAC) | `worldcereal_global_production_classification` exists but its spatial extent is **a Belgium-sized test bbox** (5.32E, 50.63N), temporal 2020-11 → 2021-10. Not global, not usable here |
| Planetary Computer | **no** WorldCereal, **no** CHIRPS collection |

**So what:** per-farm crop-type ground truth genuinely requires a human. This is now a
measured conclusion rather than an assumption, and worth stating in the writeup.

### [V2] ★ Rainfall (NASA POWER, point daily, no key) — settles three assumptions
Monthly 2025 at Sokhda (mm): May 111.0 · **Jun 298.2** · Jul 276.4 · Aug 196.6 · Sep 195.3 ·
Oct 116.4.

| scene | on day | prev 3d | prev 7d |
|---|--:|--:|--:|
| Jun 06 | 0.0 | 10.1 | 24.5 |
| Jun 19 | 21.9 | 109.4 | **137.2** |
| Aug 14 | 1.4 | 3.8 | 4.7 |
| Oct 13 | 0.0 | 0.0 | 11.3 |

- **Jun 06 is genuinely dry** — 0 mm and the start of a 9-day dry spell. Its use as the
  bare-soil reference is justified by measurement.
- **Jun 19 is soaked** — a monsoon burst on 15–19 Jun. This **independently confirms the
  [J5] +7.9 dB wet-soil interpretation**, which the geometry-matched growth term [T2] rests
  on. Previously inferred; now shown.
- **Aug 14 sits in a dry window inside the monsoon** and **Oct 13 is dry** → neither
  vegetation scene is rain-contaminated.
- ⚠ **Corrects our own narrative:** at Sokhda, **June was the wettest month**. The
  state-level "39% deficit by 31 July" story in [B12] does not describe this village.
- ⚠ **Honest cost of [T2]:** the growth pair spans ~132 mm of antecedent rainfall —
  geometrically clean, hydrologically dirty. Median-centring removes the village-wide
  component; between-farm drainage/soil-texture differences do not cancel. It still wins on
  the witness (ρ +0.296 vs +0.143), so the trade is worth it, and is now stated.

### [V3] Multi-year cropland (Impact Observatory 10 m annual LULC, 2017–2023, via PC)
903/966 farms cropland in **all 7 years**; 17 in none; median 7. The 17 are markedly smaller
than average (0.177 vs 0.279 ha) → mixed pixels in a 10 m product, not uncropped land; the
case 1.2 m X-band resolves and a 10 m sensor cannot. Their health does not differ
significantly (p = 0.21), so no confounder. ρ(health, mean cropland fraction) = +0.040.
