# R2 PROGRESS TRACKER

Single source of truth for "what is done, what is next, what is stuck".
Evidence lives in `RESEARCH_LOG.md`; the plan lives in `docs/MASTER_PLAN.md`.

**Last updated:** 2026-08-01 (session 3)
**Deadline:** Aug 13 2026 00:00 GMT+5:30 → **11 working days, Aug 1–12**
**Current phase:** research **closed**, **plan FINAL (MASTER_PLAN v3)** → D0 setup, build starts D1 (Aug 2)
**Blockers:** none
**Submission status:** ❌ not built. **Gate D4 (Aug 5) is the one that matters.**

---

## Countdown

| Day | Date | Work | Status |
|---|---|---|---|
| D0 | Aug 1 | research closed, plan locked, scaffolding + env + data QA | ✅ **done** |
| D0.5 | Aug 1 | **EDA (`src/eda.py`)** — 6 figures. **Alignment gate PASSES** | ✅ **done** |
| D1–D2 | Aug 2–3 | I1 preprocess → **land-cover dB sanity gate** | ✅ **done early (Aug 1)** — gate passes with a documented absolute-offset caveat [G3] |
| D3 | Aug 4 | I2 features **+ fetch district APY** | ✅ **features done early (Aug 1)**. DEM dropped — [H5]. APY still to fetch. Sub-aperture coherence [D1] still to do |
| D4 | **Aug 5** | I3 crop (APY soft prior) + I4 health/yield → **🚦 SUBMITTABLE GATE** | ⬜ |
| D5–D6 | Aug 6–7 | I6 P-D Water Cloud Model swap | ✅ rejected, quantified |
| D7 | Aug 8 | I7 P-B discriminative clustering swap | ✅ regulariser only |
| D8 | Aug 9 | I5 validation battery + I8 repeat-pass coherence | ✅ |
| D9 | Aug 10 | I9 notebook, clean run from fresh kernel | ✅ |
| D10 | Aug 11 | I10 writeup ≤4 pages + media gallery + cover | ✅ |
| D11 | Aug 12 | buffer, final schema check, **submit** | ✅ gate 18/18, upload pending |

**If schedule slips, cut in this order: P-E → P-B → I8. Never cut D9–D11.**

## Research phases

| Phase | Description | Status |
|---|---|---|
| A | Grounding on delivered data | ✅ [A1–A5] |
| B | Core literature scan | ✅ [B1–B12] |
| C | ORCID lineage (Bi / Kuang) — 5 graded transfers | ✅ [C1–C3] |
| D | Method-gap scan — 3 new leads found | ✅ [D1–D5] |
| E | Scope resolved + gating papers extracted | ✅ [E1–E5] |
| — | **Research closed. No further reading blocks the build.** | ✅ |

## Proposal status

| ID | Proposal | Verdict | Blocked? |
|---|---|---|---|
| P-A | Physics-first phenological trajectory | **build first — the floor** | no |
| P-B | Discriminative clustering + MRF (Bi TGRS 2017) | **build — crop step** | ✅ unblocked by [E2] |
| P-C | Complex domain: sub-aperture coherence, K-dist α, repeat-pass | **build — features + creativity** | no |
| P-D | Water Cloud Model inversion | **build — health/yield core** | ✅ unblocked by [E3] |
| P-E | Self-supervised representation learning | **ablation only; first to cut** | n/a — 4 GB GPU, n=966 |

## Rubric allocation (100 pts)

Technical Soundness **25** · Creativity **20** · Validity **20** · Aggregation **10** · Docs **15** ·
Presentation **10** · Required Elements = pass/fail gate.

- **55 pts are execution, not modelling** (Validity + Docs + Presentation + Aggregation). Three days of
  writing are protected.
- **Aggregation's 10 pts are nearly free** — one village, full coverage. Just do not drop a farm.
- ⚠ "Polarimetric structure" is in the rubric but **impossible at single-pol HH**. State the limitation,
  show the three substitutes (temporal, textural, interferometric). Do not fake it.

## Blockers — **none. Plan is final.**

| # | Question | Status |
|---|---|---|
| O9 | Round-1 artefacts | ✅ **closed — they do not exist.** [A5] hard area constraint replaced by a **district APY soft prior** from public open data [E6] |
| O8, O10, O11, O12 | rubric · compute · aux data · time | ✅ closed by [E1] + user |
| O3, O4 | deadline · host email | ✅ closed — Aug 13; no email needed, "4 villages" was a doc error |

Everything else (O1, O2, O5, O6, O7) is settled *by running code* at the phase where it is needed — see
`MASTER_PLAN.md` §6.

## Papers

`papers/` holds 8 PDFs, all extracted cleanly. **The two gating ones are read and mined:**

- ✅ **Bi TGRS 2017** — full energy function, alternating optimisation, hyperparameters (α_c=5e-5, α_s≈1,
  3 iterations) → P-B fully specified [E2]
- ✅ **El Hajj RSE 2016** — WCM equations + **X-band HH coefficients** (VWC: A=0.0438, B=0.1047, C=0.0324,
  D=0.03971) → P-D fully specified [E3]
- ✅ **Inoue RS 2014** — panicle biomass ↔ X-band σ⁰; **water-point in-scene normalisation** [E4]
- Remaining (Bi TGRS 2019, Bi TIP 2020, RectMamba, entropy-KNN, RSE 1996 texture): supporting, read at
  depth only if the schedule allows. **None blocks the build.**

## Carried-forward technical corrections

- ⚠ **R1 bug, must not repeat:** `beta0 = |z|²·scale²` is wrong. Correct is **`β₀ = scale·|z|²`** [B9].
  Per-scene scale factors differ ⇒ up to **2.4 dB** spurious date-to-date distortion, the same magnitude as
  the crop signal. Fix first in I1.
- ⚠ **Incidence spans 28.7°–35.2°** across the four dates [A3]. Multi-temporal comparison is invalid without
  normalisation [B8]. Non-negotiable. Also enters WCM via `cosθ`/`secθ` [E3].
- ⚠ **"Brighter = healthier" is physically wrong at X-band** — saturates early with biomass [B1]. Say it
  explicitly; it is a soundness signal, not a caveat to hide.
- ⚠ **Texture on unfiltered data only** [B5] — speckle filtering destroys the second-order statistics being
  measured.
- ⚠ **The Jun-19 stray file is a byte-identical DUPLICATE of the Jun-06 SLC** [F1]. Matching by folder OR by
  basename is *each individually wrong*. Require the date in **both**, assert exactly one match — done in
  `common.slc_path()`. Silent failure mode if missed: Jun-06 processed twice, "Jun-19" shows zero change.
- ⚠ **`FID` is the only usable `farm_id`** [F2] — `id` has 2 unique values, `ID_1` is constant 22, and one
  column is unnamed. `village_id` = 22 / "Sokhda".
- ⚠⚠ **Coverage is NOT 100% — [A4] is wrong** [F4]. The swath's rotated NW edge cuts the village.
  **892 farms have all 4 dates; 32 partial; 42 have none.** Per-date unusable: Jun06 42, Jun19 74, Aug14 68,
  Oct13 64. Missingness is **spatially clustered**, not random — neighbour imputation must borrow from
  adjacent *covered* farms, and the writeup must say so. Re-measure after our own I1 geocoding.
- ⚠ **Swath-edge bright artefact on Jun 19 and Aug 14** [F7] — erode the valid mask a few pixels before
  extracting, or the fragile edge farms get a spurious bright reading on the two vegetation dates.
- ⚠ **Raw |z| medians rise 52.9→82.4 across the season but that is NOT a crop signal** [F6] — the scale
  factors move the other way. `β₀ = sc·|z|²` reorders them. Concrete demo of why the R1 `scale²` bug mattered.
- ⚠ **9 invalid geometries + 10 polygons under 10 m²** [F2]. Coverage is 10 rubric points and needs all 966
  rows, so the negative buffer must degrade through a documented fallback ladder
  (`make_valid` → buffer → unbuffered → intersecting pixels → centroid → flagged village median).
  **No farm is ever dropped**; every fallback used is counted and reported.
- ⚠ **P-B: cap α_s ≤ 1 and iterations ≤ 3** — the paper measured a 39.76% accuracy collapse on thin classes
  by iteration 5. Maize (6%) and Bajra (9%) are our thin classes [E2].
- ⚠ **WCM coefficients are grassland-fitted** — report **relative** VWC only, cite Attema & Ulaby 1978 for
  the crop case [E3].
- ⚠ **Inoue's panicle result is VV at shallow incidence; we are HH at 28.7°–35.2°.** The *water-point
  method* transfers (it is a calibration argument); the *panicle correlation* is suggestive, not proven [E4].

- ⚠ **The crop map is REBUILT, not carried forward from R1** [E6]. The rules explicitly permit this. Say so
  plainly in the writeup; never imply an R1 map existed. Crop prior = **district APY proportions as a soft
  prior**, not a hard quota — Sokhda is one village and its mix legitimately differs from the district mean.
  Report prior, posterior, and the distance between them; that gap is itself a finding.

## I1 outputs (on disk)

`results/cache/{gamma0,sigma0,incidence}_{fine,base}_{YYYYMMDD}.tif` — 24 files.
**FINE = 2 m** (texture, within-field stats) · **BASE = 5 m** (farm means, temporal trends).
Grid: EPSG:32643, farms bounds + 400 m, 2231×2475 (fine) / 893×990 (base). Valid 86.7–87.7% per date.

Decisions locked in I1, each with its reason:

- **No cosine-N incidence normalisation.** γ⁰ with exact per-pixel θ [G1] *is* the angular correction. A
  cosine-N fit on built-up returned N = 6.81, physically absurd for γ⁰ — urban dihedral is too
  angle/orientation-sensitive to serve as a reference [G5].
- **No water-point referencing** [E4] — tested, made inter-date agreement *worse* (built-up spread
  3.68 → 4.61 dB). Sokhda's ponds are seasonal, violating the method's invariant-reference precondition
  [G5]. Documented negative.
- **Absolute dB is not trustworthy; contrasts are.** ~+17 dB offset vs textbook cropland, consistent with
  ESA EDAP's undeclared absolute accuracy [B9, G3]. Report contrasts, cite EDAP, never quote absolute γ⁰.
- **Δ(Aug14 − Jun19) is the cleanest temporal measurement** — geometry matched to 0.076°, and the two dates
  agree to ~0.9 dB on both built-up *and* cropland [G4]. Weight it accordingly.

## Session log

### Session 3 — 2026-08-01
- **Scope closed [E1].** User supplied the full competition text. Deadline Aug 13 00:00 IST ⇒ 11 days.
  Rubric mapped to the plan. Aux data is explicitly *rewarded*, which corrected `PLAN.md`'s decision to
  hold Sentinel-2 back entirely — now: DEM/TWI + weather as inputs, NDVI as witness only.
- **Both gating papers mined.** `pypdf` extraction of all 8 PDFs.
  - **Bi TGRS 2017 [E2]** — the complete energy function `E = Ec + Es`, both subproblems, and the published
    hyperparameters. P-B went from "an idea" to "fully specified". Node = farm, so N=966 and it runs
    instantly. Recorded the paper's own warning about eroding thin classes.
  - **El Hajj RSE 2016 [E3]** — WCM equations *with fitted X-band HH coefficients*. P-D unblocked. The
    bare-soil sensitivity D_HH = 0.172 dB/Vol.% also lets us **bound** the soil-moisture confounder in the
    Jun→Aug change rather than hand-wave it.
  - **Inoue RS 2014 [E4]** — unexpected win: the **water-point** method (reference every date to an
    in-scene water surface) is the published answer to Capella's undeclared absolute radiometric accuracy
    [B9]. Adopted.
- **P-E cut** to an optional ablation — 4 GB GPU and n=966 settle it.
- **[E6] No Round-1 artefacts.** Hard area constraint [A5] gone. Replaced with **public district APY
  statistics as a soft prior** — arguably better founded (R1's areas were a model output, not ground truth)
  and it converts a lost internal artefact into *auxiliary open data*, which the rubric rewards by name.
  Verified the source exists (data.gov.in Gujarat APY catalog, Gujarat DoA district PDFs, ICRISAT DLD).
  Bonus: state-level **kharif 2025** figures show groundnut sowing (20.41 lakh ha) overtaking cotton
  (20.35 lakh ha) — a citable prior for the exact season we observe.
- `docs/MASTER_PLAN.md` → **v3, PLAN FINAL, zero open blockers.**
- **D0 done.** Env verified (Python 3.13.7; numpy/scipy/rasterio/pyproj/shapely/skimage/sklearn/pandas/
  matplotlib present; installed `geopandas` 1.1.4 + `pyogrio`). Wrote `src/common.py` — paths, append-only
  JSONL run ledger, `db()` with a zero guard, date→SLC resolver, and a `__main__` self-check.
- **The self-check earned its keep on first run** [F1]: it failed immediately and exposed that the Jun-19
  folder's stray file is a *byte-identical duplicate* of the Jun-06 SLC, which breaks folder-matching **and**
  basename-matching. Fixed at the root in `slc_path()`.
- Geometry QA [F2] reproduced [A2] (966 farms, 447.5 ha, median 0.274 ha) and found `FID` is the only usable
  identifier, plus 9 invalid geometries and 10 sub-10 m² polygons needing a no-drop fallback ladder.
- **D0.5 EDA added and run** (`src/eda.py`, 6 figures in `results/figures/`). Inserted *before* preprocessing
  because the fatal risk — boundary/geocoding misalignment — is checkable for free on the vendor's geocoded
  previews, and checking it after building the pipeline would be backwards.
  - ✅ **[F3] ALIGNMENT GATE PASSES** — boundaries track radar field edges tightly at 700 m zoom. The plan's
    top risk is cleared. `eda_01` becomes the regression test for our own GCP geocoding in I1.
  - ⚠⚠ **[F4] Coverage is not 100%, correcting [A4]** — 892 all-4 / 32 partial / **42 with no data at all**,
    clustered along the NW swath edge.
  - ✅ **[F5] Water and built-up targets confirmed in-scene** — water-point referencing [E4] is viable and
    the dB gate has real targets. First attempt was wrong (thresholded the no-data background as "water");
    fixed by masking no-data and smoothing first, since water is spatially coherent and dark speckle is not.
  - **[F6]** raw SLC stats: no exact zeros; the apparent seasonal brightening is a calibration artefact.
  - **[F7]** swath-edge bright artefact on the two vegetation dates.
- **I1 preprocessing built and run — a day early** (`src/prep_r2.py`, `src/check_i1.py`). 24 products on
  disk, both grids, all four dates.
  - ★ **[G1] Per-pixel incidence derived from the 108 orbit state vectors, validated to 0.006°** against the
    vendor's annotated centre incidence on every date. Exact θ, not an assumed constant. Also reframes [B8]:
    incidence varies ~0.4° *within* a scene but 6.55° *between* dates.
  - **[G2]** The product's own `radiometry` field reads `beta_nought`, confirming `β₀ = sc·|z|²` [B9]
    independently of the ESA note. R1's `scale²` bug is fixed and now asserted in code.
  - ⚠ **[G3]** Land-cover gate: ordering and dynamic range are correct (built > crop > water, ~25 dB) but a
    **near-constant ~+17 dB absolute offset** remains and no convention resolves it. This is exactly EDAP's
    "absolute accuracy not declared, relative accuracy good" condition — so we **stop chasing it**, report
    contrasts rather than absolute dB, and cite EDAP. Harmless: every comparison we make is within-date
    between-farms or within-farm between-dates, and a constant cancels in both.
  - ★ **[G4]** Jun 19 and Aug 14 agree to ~0.9 dB on built-up *and* cropland alike → **Δ(Aug14 − Jun19) is
    our cleanest temporal measurement.**
  - ⚠ **[G5] Documented negative: water-point referencing fails**, because Sokhda's ponds are seasonal in a
    monsoon climate and so are not the invariant reference the method assumes.
  - **[G6]** Geocoding regression passes on our own product; ENL 1.0 → ~2.1 (fine) / ~3.5 (base), quoted as
    a lower bound since the estimator reads real field texture as speckle.
- **I2 features built and run — also early** (`src/farm_stats.py`, `src/check_i2.py`).
  `results/farm_features.csv` = **966 rows × 47 cols**, 913 ok / 24 partial / 29 no_sar_data.
  - ✅ **[H1]** No farm dropped. Buffer ladder: 951 at −5 m, 5 at −2 m, 10 unbuffered, **0 failed**.
  - ⚠⚠ **[H3] The catch of the session: GLCM entropy was measuring PLOT SIZE, not texture** (ρ = 0.95 with
    area). Cause: 32 grey levels = 1024 GLCM bins, but a median plot contributes only ~2700 pairs, so
    entropy degenerated to log(pixel count). Fixed with 8 levels **plus** residualising on log(npix) →
    ρ vs area **−0.14**. **Use `glcm_resid_*`, never raw `glcm_ent_*`.** Unfixed, every large farm would
    have scored as more heterogeneous and the whole health index would have inherited it.
  - ⚠ **[H2] Negative: K-distribution texture ρ = 1.00 with plain CV** — algebraically a monotone transform
    of CV at fixed L, so it cannot reorder farms. Kept in the CSV as a reported negative, **excluded as an
    index axis**. Corrects [D3]'s claim.
  - ⚠ **[H4]** Moran's I had a normalisation bug (returned 1.9–3.4, impossible). Fixed; all features now
    show **positive** autocorrelation — temporal_cv 0.334, ref_oct 0.237, glcm_resid 0.179 — i.e. real
    agronomic structure, not speckle.
  - ✅ **[H5] [O6] closed: no DEM.** AOI terrain slope is **0.020°**, so local incidence deviates by ~0.02°
    vs 0.43° within-scene and 6.55° between-date. A DEM would change nothing measurable. **TWI drops too** —
    no gradient to work with, so waterlogging must come from backscatter if at all.
- **Sub-look coherence [D1] built and tested — NEGATIVE** (`src/sublook.py`). Zero-temporal-baseline
  coherence from splitting the azimuth Doppler spectrum. A real bug found en route (band detected per column
  chunk → sub-look separation varied → Moran's I alternated ±0.28; fixed to one band per date). **After the
  fix, Moran's I ≈ 0 on three of four dates** (−0.008, −0.021, −0.013; Oct 13 +0.210 alone), and August is
  not the minimum as the canopy mechanism would require. Farm-level values are noise. **Kept in the CSV,
  excluded from the index, reported as a negative** [I1]. Third honest negative after [G5] and [H2].
- ★★ **District APY found — [O5] and [E6] both closed** (`data_aux/vadodara_apy.csv`, provenance in
  `data_aux/SOURCES.md`). Gujarat Directorate of Agriculture (2024) figures via Parmar & Bhatt 2025 (open
  access, DOI 10.33545/2664844X.2025.v7.i5a.380). Gives both the **area prior** and the **yield anchor**.
  ★ **Groundnut is 0.35% of the district's five-crop area (1,004 ha)** — it is a Saurashtra crop, not a
  Vadodara one. This **contradicts the R1 prior [A5] that put Groundnut at 31% of Sokhda**; losing the R1
  artefacts now reads as an escape rather than a loss [I2].
  ⚠ **[I2]'s groundnut conclusion is RETRACTED by [J2] — see Session 4.** The yield column stands.

### Session 4 — 2026-08-02 — Phase J: Round-1 repo recovered

Cloned `Jenish-fngghd/AISEHACK-2.0` (private — needs authenticated `gh`; plain `git clone` hangs on the
credential prompt) to `r1_repo/`. **[E6] is overturned: the R1 artefacts exist.**

- ★★ **[J1] Sokhda = R1 village 22, and its crop areas are known exactly.** R1 polygon 1173.68 ha vs our
  1174.1 ha. R1's final leaderboard had no private holdout, so MSE was an exact linear oracle; R1 read all
  145 cells closed-form and the reconstruction **scored 0.000**. Sokhda: **Cotton 297.08 ha (43.0%),
  Groundnut 213.93 (31.0%), Rice 73.33 (10.6%), Bajra 65.12 (9.4%), Maize 41.42 (6.0%)**, total 690.88 ha
  cropped. Our 966 farms = 447.5 ha = 65% of it. → `data_aux/sokhda_r1_truth.csv`.
- ⚠ **[J2] RETRACTION: [I2] was wrong.** Groundnut is **31.0%** of Sokhda, not 0.35%. [A5] was right to
  the decimal. The district APY **area** column is retired as a prior (2022-23, merges Chhotaudepur,
  district != village, and Gujarat groundnut sowing hit 125% of normal in kharif 2025). Its **yield**
  column stands and [O5] stays closed.
- ★ **[J3] Hard per-pixel crop assignment is a measured failure: MSE 19354 vs 12911 flat prior.** Live
  confirmation that single-pol X-HH cannot separate five crops. **D4 must emit per-farm probabilities, not
  labels**, with the mix pinned to a prior.
- **[J4] Signatures with measured lambdas:** rice = VH(Aug)-VH(Jun) flooding (+0.407, R1's biggest single
  gain), cotton = VH(Oct) standing + X-HH(Aug), groundnut = **inverse** NDVI (-0.218), maize = VH(Aug),
  **bajra = no signal anywhere**.
- ⚠ **[J5] Our calibration corroborated, and a new anomaly found.** R1's independent processing gives the
  same near-constant offset on three dates (27.1/28.3/30.0 dB, spread 2.9) — [O1]/[G3] confirmed. **But
  Jun 19 is ~7.9 dB above Jun 06 and ~7.5 dB above Aug 14** at essentially identical incidence
  (28.87 vs 28.80 deg) and within-2.4 dB scale factors. Read as **monsoon-onset wet bare soil**: Jun 06
  (pre-monsoon, dry) -> Jun 19 (wet) is a **soil-moisture pair**, a gift for the WCM soil term in P-D —
  but it means **`d_aug_jun19` is not a clean growth feature** and must be re-examined before the health
  index uses it.
- **[J7] Integrity boundary — DECIDED by the user, 2026-08-02: "validation + soft prior, declared".**
  [J1] is used as (a) a **held-out validation set** — the crop mix is recovered from SAR with no reference
  to it, then agreement is reported — and (b) a **soft prior** on the village mix, replacing the retired
  district area shares. It is **never** used as per-farm labels or as a fitting target, and its
  **provenance is stated in the writeup**. Order matters and is enforced in code: *recover first, compare
  second, soften third.*

### 🚦 D4 — SUBMITTABLE GATE: **GREEN** (2026-08-02)

`src/d4_submission.py` → `results/submission.csv` (966 rows) + `results/d4_debug.csv`.
Schema validator **PASS**: exact 5 columns, 966 unique farm_ids 1–966, no NaN, crop spellings in the
allowed set, health in [0,100], yield ≥ 0.

| crop | farms | area ha | area % | prior % [J1] |
|---|---|---|---|---|
| Cotton | 455 | 192.8 | 43.1 | 43.0 |
| Groundnut | 230 | 141.9 | 31.7 | 31.0 |
| Rice | 87 | 44.7 | 10.0 | 10.6 |
| Bajra | 140 | 41.5 | 9.3 | 9.4 |
| Maize | 54 | 26.7 | 6.0 | 6.0 |

- **Crop = soft evidence → softmax → prior-matched → argmax.** First pass matched the *soft* column mass,
  converged, and did nothing — rice still landed at 1.2% area against a 10.6% prior. Soft and hard
  marginals are different objects and the CSV needs the hard one, so `fit_prior` now biases the
  log-probabilities until the **argmax, area-weighted** shares match. Bias moves the decision boundary,
  never the evidence order within a class.
- **Median crop confidence 0.385 — deliberately low.** [J3] is the reason: confident hard labels are
  precisely what scored 5× worse than a flat prior in R1.
- ✅ **Independent check on the rice channel:** 61% of the [J8] flood-detected farms come back labelled
  Rice, against a 9% base rate — **6.8× enrichment**, and the flood evidence and the prior were fitted
  separately.
- Health = crop-relative percentile of level / growth (Jun **06** baseline, not Jun 19 [J8]) / uniformity /
  residualised GLCM / season integral. Excludes `ktex` [H2] and `subcoh` [I1].
  Moran's I **+0.077** (positive; damped by design since within-crop ranking removes the crop-driven
  spatial structure). ρ vs plot area **+0.086** — it is not re-measuring plot size [H3].
- Yield = district anchor (kg/ha, [O5]) × season completion at Oct 13 (Cotton 0.45, Groundnut 0.75, others
  0.95) × within-crop relative performance (±30%). **Level from statistics, ranking from SAR** — stated
  as the split, not blurred.
- Coverage: **966/966**, 895 measured, 52 imputed (crop-median, flagged), 19 `rfi_flagged` [J8].

### D5–D6 — I6 P-D (Water Cloud Model) swap: **REJECTED, cause quantified** (2026-08-02)

`src/wcm.py`, self-checked. Exit criterion was "measurable improvement or documented rejection" — it is the
second, and the more useful one. Full detail in Phase K of the log.

- Inversion of El Hajj et al. RSE 176 (2016) eqs. (4)–(7), X-band HH VWC coefficients [E3], via `brentq`.
  Offset [J5] handled without any absolute dB: eq. (7) gives `sigma0_sol` from theory and [J8] gives Jun 06
  as the dry near-bare reference, so per-farm `k = obs(Jun06)/(C·exp(D·Mv_dry))` absorbs offset **and**
  roughness. k = 19.51 dB median, IQR **1.06 dB** — soils are uniform across the village.
- ⚠ **The self-check caught my own error before any result existed.** I had asserted the WCM is monotonic
  in V. It is not: `dσ⁰/dV < 0` at V=0, because a thin canopy attenuates the soil faster than it scatters.
  Turning point `V* = sec(θ)·σ⁰_sol/(2A)` = 0.68 kg/m² at Mv 12%, 1.39 at Mv 30%. **Below V* the inversion
  is two-to-one — X-band HH cannot tell a sparse canopy from a denser one.** Reportable in its own right.
- ★ **Why it fails here.** The data fixes `σ⁰(Aug)/σ⁰(Jun06) = 0.916` (August is *darker* than dry June).
  The WCM at Aug Mv 30% puts bare soil alone at 2.04× dry June and **its dip floor — the darkest the model
  can be for any canopy load — at 1.76×**. Observed 0.92× is below that by ~1.9×. August only inverts for
  Mv ≤ 10 Vol.%, which is not a mid-monsoon soil moisture. **[J5] measured our per-date offsets as
  27.1/28.3/30.0 dB, a 2.9 dB spread; the WCM needs ~3 dB of inter-date soil contrast. The model is being
  asked to resolve a signal the size of our error bar.** Defeated by absolute radiometry, not by physics
  or implementation — and it retroactively justifies the [O1] contrasts-only decision.
- **Health index unchanged.** At Mv 30% the Aug inversion pins **96% of farms at the dip floor**, ρ with raw
  dB = **−0.12** — it has stopped carrying the observation. Swapping it in would have replaced a working
  feature with an artefact.
- Salvage: Oct 13 inverts cleanly (median 2.60 kg/m², IQR 1.79–3.26, ρ +0.70 vs raw dB). Perturbing every
  Mv by ±8 Vol.% shifts the level by 0.4–0.9 kg/m² but holds the ordering at **Spearman 0.966–0.998** —
  usable as an *ordering*, unusable as a *measurement*, stated that way.
- `vwc_*`/`vwcflag_*` kept as evidence. **`vwc_20250606` is degenerate by construction** (it is the
  calibration date) and must never be used as a feature.

**Fourth documented negative**, after [G5], [H2], [I1].

- **Next: D7 — I7 P-B swap (discriminative clustering + MRF vs the D4 heuristic crop map).**

### D7 — I7 P-B (discriminative clustering + MRF): **accepted as regulariser, rejected as independent recovery** (2026-08-02)

`src/pb_mrf.py`. Bi et al. TGRS 2017 energy `E(Y,W|X) = Ec + Es`; softmax regression with the
1/N_j class-imbalance correction, 8-NN MRF on farm centroids with feature-similarity edge
weights, alternating L-BFGS / ICM. Area constraint [J1] applied to the unary before smoothing —
holds to 0.9 points on every crop.

- Warm-started from D4: energy falls monotonically 1154.9 → 1108.1, **89.3% agreement by farm,
  89.2% by area**.
- **Cold-started from random: 9.0% — chance.** Identical across three seeds, converging in one
  iteration to a degenerate minimum. The features do not carry enough class structure to recover
  the map unaided; the 89% is the warm start surviving.
- Therefore `pb_crop` does **not** enter `submission.csv`. It is used as (a) a spatial-coherence
  stress test D4 passed, (b) a ranked list of the 10.7% weakest-evidence farms. Written to
  `results/pb_crop.csv` with full posteriors [J3].
- Movement is between the classes the physics says are hard (Groundnut↔Bajra 27 farms,
  Groundnut↔Cotton 35) and essentially never between separable ones (Rice↔Bajra: 1).

Logged as Phase L [L1]–[L3]. Fifth documented negative, partial.

### D8 — I5 validation battery: **crop map validates strongly, health index weakly, one test fails** (2026-08-02)

`src/witness.py` + `src/i5_validation.py`. Witnesses from Planetary Computer STAC (open, anonymous):
**Sentinel-2 on 2025-10-13 — same day as our Capella October scene, 0.003% cloud** — and Sentinel-1
RTC C-band VH on 2025-10-10. 956/966 farms. Neither is an input to anything.

- **★ Crop classes separate on both witnesses** — NDVI Kruskal H=164.3 p=1.8e-34, VH H=95.8 p=7.7e-20 —
  **and in the agronomically correct order**: Cotton (still standing, completion 0.45) highest on both,
  Maize (harvested) lowest on both. Strongest result in the project.
- **Health index only weakly corroborated**: rho 0.071 vs same-day NDVI (0.229 pre-ranking), 0.130 vs VH.
  Solid only within Cotton (0.305 VH). **Negative within Maize (-0.17/-0.24)** — for harvested crops both
  sensors are measuring soil, not plants. Reported as "supported for standing crops, weakly for harvested".
- Moran's I significant on all three output layers against a 199-permutation null.
- **Ablation strong pass**: worst single-family drop rho 0.879; all weights jittered ±50% gives rho ≥ 0.966.
  The hand-chosen health weights are not load-bearing.
- **⚠ FAIL**: the rubric's "uniform canopy scores higher" holds on `cv_20250814` (rho -0.343) but that is
  **circular** — it is the `uniform` family. The independent version, `cv_20251013`, comes back **-0.049,
  i.e. nothing.** Stated as a failure, not dropped.
- Residual bias flagged: health vs `area_ha` rho 0.086 (more pixels, less speckle).

Logged as Phase M [M1]–[M9].

### D8b — I8 repeat-pass coherence [O2] (2026-08-02) ✅ negative, and declared uninformative

`src/i8_repeat.py`. Pair **Jun19 x Aug14** — forced, it is the only pair with matched incidence
(28.768 vs 28.692 deg; every other pair differs by 2.8–6.6 deg). 56 days, X-band.

Per-block (512x512) amplitude cross-correlation, sub-pixel parabolic refinement, Fourier
phase-ramp shift on the complex data, empirical deramp, 9x9 boxcar coherence.

| control | value | meaning |
|---|---|---|
| SELF (Jun19 vs itself) | **1.0000** | estimator sound (asserted) |
| NULL (mis-registered 200 px) | 0.1161 | empirical boxcar bias floor |
| REAL (coregistered) | 0.1254 | **+0.009 over the floor = zero** |
| STABLE (brightest 1%) | 0.1596 | |
| STABLE-NULL (same pixels, mis-registered) | 0.1217 | the *fair* floor |
| FARMS (per-farm, median) | 0.1286 | |

**Stable excess like-for-like +0.0379, below the 0.05 threshold fixed in advance.** First pass
scored STABLE against the all-pixel floor (+0.044, apparent pass); that is wrong, because a
neighbourhood dominated by one bright scatterer has fewer effective looks and therefore a
*higher* bias. Correcting the control flipped the verdict.

- Farm coherence is at the noise floor, exactly as the literature predicts for 56 days at X-band.
- **But it is reported as UNINFORMATIVE, not as a measurement of crop decorrelation**, because
  the stable-scatterer control did not clear its own floor. No orbit state vectors ship with
  these products, so the residual fringe cannot be removed analytically and may be suppressing
  coherence itself. Cannot separate the two explanations; say so.
- Does **not** enter `submission.csv`. The temporal-coherence rubric axis is served by
  **[I1] sub-look coherence** (zero temporal baseline) — built in anticipation of this outcome,
  now vindicated by measurement rather than assertion.

Logged as Phase N [N1]–[N5]. Seventh documented negative.

### D9 — I9 notebook (2026-08-02) ✅

`notebooks/I9_pipeline.ipynb`, generated by `notebooks/build_notebook.py`.
**Executed fresh-kernel via nbclient: 20 code cells, 0 errors, 2 figures.**

Ten sections, written as an argument rather than a script dump (the rubric wording is
"judge can follow *why*"). Code cells call the existing `src/` functions — nothing is
reimplemented, so the notebook cannot drift from the shipped pipeline.

`FAST = True` (default, ~1 min) reuses `results/cache/*.tif`; `FAST = False` rebuilds
every raster from the SLCs through the same code path, ~25 min.

**Reproducibility proof is an assert, not a claim** — the last cell rebuilds the
deliverable from the notebook's own arrays and requires a match:

    crop_type match vs shipped submission.csv: 1.0000
    health_index max abs diff: 0.0

`D4.validate(sub)` runs inside the notebook so the schema gate is visible. Provenance
printed: 895 measured / 52 imputed_village_median / 19 rfi_flagged — no farm dropped.

Carries into the notebook, not just the log: the [J7] prior provenance declaration, the
[J2] retraction, the [M6] circularity + failure, the [M3] maize negative, the [L2]
cold-start caveat on the 89%, the [J5] +28 dB offset, the [N4] uninformative verdict —
plus a closing section stating explicitly what is **not** claimed.

Logged as Phase P [P1]–[P4]. (Letter O skipped — `O1`/`O2` are open-question IDs.)

### D10 — I10 writeup + media gallery (2026-08-02) ✅

`docs/WRITEUP.md` — 1754 words, ~2.7 pages, headroom under the 4-page cap.
`src/i10_media.py` — `cover.png` + six `gallery_*.png`, each rendered, **opened and
inspected**, and re-cut until legible in two seconds. Four rounds found:

**★ A substantive error the figure caught.** The trajectory plot shows rice is the
*brightest* class on 19 Jun and *darkest* on 14 Aug. The notebook prose said "rice
floods — specular drop **in June**". Wrong: kharif paddy is transplanted into standing
water from late June, so the specular signature lands on **14 August**. The classifier
was always right (it uses `d_aug_jun19`, which is exactly this trough) — only the
explanation was wrong. Corrected, re-executed, annotated on the figure. No validation
number would ever have caught a wrong physical story attached to a correct feature.

**★ A reported-number inconsistency, closed.** Log said weight-jitter rho min **0.978**;
notebook and gallery computed **0.966** from the identical procedure. Cause:
`check_ablation` drew from the module-level RNG *after* 199 Moran permutations had
consumed it, while the standalone callers used a fresh stream. Both draws legitimate;
two numbers for one claim is not. Fixed with a dedicated `jrng` seed — canonical value
**min 0.966, median 0.985** everywhere.

Figure defects fixed: colourbars moved to dedicated axes (geopandas' `legend=True` was
stealing panel height and misaligning titles); the uniformity scatter blob replaced with
**decile-binned medians** so rho −0.343 and −0.049 look different; overlapping tick
labels folded in; outlier-squashed axes clipped to 1–99 pct; legends moved off the
polygons.

Writeup carries every required caveat: [J7] provenance declaration, [J2] retraction,
[L2] cold-start, [M3] maize negative, [M6] circular-vs-independent uniformity, [N4]
uninformative coherence, [J5] +28 dB offset *and why the deliverable survives it*, the
area-bias residual, coverage counts. Leads Technical Soundness with the explicit
"we cannot do polarimetry at single-pol HH — here are the three axes we exploit
instead" table.

⚠ **Open:** MASTER_PLAN D10 says "all four required writeup topics" but the four are
not recorded anywhere in the evidence trail. Writeup covers the conventional set
(approach / aux data / validation / limitations). **Confirm against the Kaggle
Submission tab before upload.**

Logged as Phase Q [Q1]–[Q6].

### D10b — host dummy submission decoded (2026-08-02) ⚠ caught a shipping error

User supplied the host's sample writeup + `Sokhda_Dummy_Submission.xlsx`.

**★ The yield column is TONNES/ha, not kg/ha.** Host dummy values 1.24–9.00; ours were
kg/ha (bajra 2589, cotton 350) — **wrong by 1000×**. Every internal check passed with
the wrong unit: the schema gate only tested `>= 0`, the agronomic check compared against
the same APY source that caused it, and ranking / Moran / ablation are all
scale-invariant. **No internal validation can catch a unit convention that exists only
in the host's file.**

Fixed at one conversion point (`YIELD_T_PER_KG`) plus a guard in `validate()`:
`assert max < 25.0 t/ha`. Shipped medians: Bajra 2.589, Maize 2.222, Groundnut 1.890,
Rice 1.617, Cotton 0.350 t/ha. Production tonnages unchanged, confirming the conversion
landed in exactly one place. Propagated to `i5_validation`, `i10_media`, the notebook
aggregate cell (all carried a now-double-counted `/1000`), labels and prose.

**966 is right.** Their writeup says 967 plots; their own dummy has 966 rows (farm_id
1–966) and the shapefile has 966 features. Noted in the writeup, no change.

**village_id = 1**, not the shapefile's `ID_1 = 22`. Single village, no information
either way; follow the host's schema reference, keep the shapefile value in
`d4_debug.csv` as `shapefile_village_id`, assert it cannot drift.

**[Q6] closed** — the sample writeup names no "four required topics"; that phrasing was
mine. Required elements are the ≤4-page cap, gallery, cover image, public notebook and
the 5-column CSV. All present.

Verified: columns / rows / farm_id / village_id identical to host, crop vocabulary a
subset, 0 nulls, `d4.schema PASS rows=966 max_yield_t_ha=4.125`. Notebook re-executed
clean with the reproduction assert still exact; gallery and writeup regenerated.

Logged as Phase R [R1]–[R5].

### D11 — final gate (2026-08-02)

`src/d11_ship.py`, **18/18 passed, `status=READY`**. One script, run last, exits 1 on
any failure. It answers the one question nothing else in the repo asked: is the
*upload* complete? Everything else checked whether the *model* was right.

Schema is verified **against `Sokhda_Dummy_Submission.xlsx` itself**, re-read on every
run, not against constants copied out of it once. Columns and order, row count,
farm_id set, village_id, crop vocabulary, nulls — all identical or a subset. Ranges:
health_index 0.25–100.00, yield 0.141–**4.125 t/ha** against the host's 9.00 max.
Deliverables all present: CSV, writeup (1872 words ≈ 2.9 of 4 pages), notebook with no
stored error outputs, cover image, six gallery figures.

The page-count check is a soft tripwire against a late edit adding sections unnoticed —
the cap is on the rendered PDF, which Markdown does not control. [S3]

Logged as Phase S [S1]–[S4].

---

### Session — 2026-08-11: external yield witness, closed negative

Chased the last open lead (an external check on `yield_estimate_to_date`, the one
deliverable with no witness). Two negative results, both measured, both worth recording
so nobody re-runs them.

**1. PMFBY crop-cutting-experiment yield is officially gated.**
Extracted the two React bundles behind `pmfby.gov.in` (15 MB) and recovered the API
surface: `/cce/iu_wise_yield_acceptance`, `/yield/yieldIUMapping`, `/common/historicalYield`,
`/reports/ccereport`. The Insurance Unit in Gujarat *is* the village, so the granularity
would have been exactly right. But `GET /common/historicalYield` returns

    401 {"status":false,"error":"unauthorized","data":{"login":false}}

and every other path returns the SPA catch-all shell. An earlier note in this project
recorded `reportPortal` / `cceAdmin` as "HTTP 200"; that was **the shell, not data** —
on this site a 200 carries no information. The public `Reports` menu resolves to a single
PDF compendium and the Graphical Dashboard issues no data requests at all. CCE yield needs
a state-officer or insurer login. Closed.

**2. Comparing our medians to published APY is not an independent check.**
Official Gujarat kharif 2024-25 First Advance Estimates (DES, DA&FW) are: rice 2537.97,
bajra 1786.66, maize 2022.15, groundnut 3026.31 kg/ha, cotton 634.83 kg/ha lint. Tempting
as a benchmark — but the *Vadodara district* APY figure is already the model's LEVEL input
(`data_aux/vadodara_apy.csv`), so the ratio just returns the season-completion constant:
bajra 2.572 / 2.714 = 0.95 = `COMPLETION["Bajra"]`, exactly. `check_yield.py` already
states this. Publishing it as external validation would have been circular. Rejected.

**Conclusion.** The yield column has no obtainable external witness, and that is now a
measured statement rather than an assumption. The two per-farm terms remain falsifiable
and are tested in `check_yield.py`; the level term is an acknowledged input. No change to
any shipped number.

## Upload checklist — the only work left, and it is manual

| # | artefact | where it is |
|---|---|---|
| 1 | `submission.csv` | `results/submission.csv` |
| 2 | writeup, ≤4 pages | `docs/WRITEUP.md` → export to PDF |
| 3 | cover image | `results/figures/cover.png` |
| 4 | media gallery | `results/figures/gallery_1…6_*.png` |
| 5 | public notebook | `notebooks/I9_pipeline.ipynb` → **set visibility public** |
| 6 | project link | the Kaggle notebook URL, after it is public |

Re-run `python src/d11_ship.py` after **any** late edit. It is the gate.

### Session 2 — 2026-08-01
- Resolved both ORCIDs via the ORCID public API → **Haixia Bi** (Xi'an Jiaotong, 27 works) + **Zuzheng
  Kuang** (her PhD student, 8 works, all in-group). One lab, not two lines.
- Graded the transfer honestly: their corpus is **PolSAR**, ours **single-pol HH** — no architecture lifts
  across, and neither has an agriculture paper. What transfers is the **label-scarcity methodology**, which
  is precisely our hardest problem. Five transfers T1–T5 in [C3].
- Found and verified three gaps in `PLAN.md`: sub-aperture coherence [D1], Water Cloud Model [D2],
  K-distribution shape parameter [D3]. Triaged SSL to ablation-only [D4].
- Wrote `docs/MASTER_PLAN.md` v1 and this tracker.

### Session 1 — 2026-07-31
- Phases A and B: data grounding [A1–A5] and core literature [B1–B12]. Produced `PLAN.md`.
