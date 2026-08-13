# R2 MASTER PLAN — Research → Proposal → Implementation

**Status:** v2, 2026-08-01. Research phase **closed**; scope, rubric and both gating papers resolved.
**Authority:** supersedes `PLAN.md` for sequencing and proposal selection. `PLAN.md` remains the detailed
method spec for proposal **P-A**. `RESEARCH_LOG.md` is the evidence store — every `[A#] [B#] [C#] [D#] [E#]`
tag resolves there.

> **Deadline: Aug 13 2026, 00:00 GMT+5:30 ⇒ 11 working days (Aug 1–12).**
> **Judged by a human panel against a published rubric. No leaderboard, no metric to optimise.**

---

## 0. The rubric is the specification

| Criterion | Pts | What actually earns it | Where we earn it |
|---|---|---|---|
| Technical Soundness | **25** | index grounded in explainable SAR physics, not arbitrary formulas; R1 crop map correctly applied | P-D (WCM, [E3]), correct calibration [B9], incidence normalisation [B8], water-point referencing [E4] |
| Methodological Creativity | **20** | beyond single-date average; temporal trajectory, spatial/textural, **thoughtful aux integration** | P-C (sub-aperture coherence, K-dist α), P-B (Bi lineage), DEM/TWI + weather as refinement |
| Validity & Plausibility | **20** | internally consistent, agronomically plausible; **uniform canopy scores higher**; village aggregate sensible | I5 validation battery + cross-proposal agreement |
| Village Aggregation & Coverage | **10** | all farms processed; aggregation rule logical and clearly defined | **966/966 farms, one clear rule — near-free, do not drop a farm** |
| Documentation & Reproducibility | **15** | judge can follow *why* each step was taken, not just what ran | commented notebook, this evidence trail |
| Presentation Quality | **10** | writeup + visualisations legible at a glance | ≤4-page writeup, media gallery, required cover image |
| Required Elements | gate | notebook runs clean; CSV has the 5 columns | schema validator |

**Three consequences that drive everything below.**

1. **55 of 100 points are execution, not modelling** (Validity 20 + Docs 15 + Presentation 10 + Aggregation
   10). The last three days are writing. That is not a concession — it is where the points are.
2. **Aggregation's 10 points are nearly free.** One village, full four-date coverage [A4]. All 966 farms
   plus one clearly stated aggregation rule. The degenerate-polygon guard [A2] is now worth real points.
3. ⚠ **Technical Soundness names "polarimetric structure" — impossible at single-pol HH.** Do not fake it.
   State the limitation and show the three substitute axes we *do* exploit: temporal trajectory,
   spatial/textural, interferometric/complex [B3]. "We cannot do polarimetry; here is what we did instead
   and why" reads as soundness, not weakness.

**Correction to `PLAN.md`:** it held Sentinel-2 NDVI back as validation-only. Aux integration is worth
Creativity points *by name* [E1]. Resolution: **DEM/TWI + IMD weather as refinement inputs**
(uncontroversially "complementing" SAR), **S2 NDVI as an independent witness only** — and explain the split
in the writeup. Earns Creativity for the integration *and* Validity for an untainted cross-check.

---

## 1. Where we stand

**Resolved this session:** rubric, deadline, CSV schema, aux-data rules [E1]. Bi TGRS 2017 full energy
function and hyperparameters [E2]. Water Cloud Model with **published X-band HH coefficients** [E3]. The
**water-point normalisation** method [E4]. Compute: local GTX 1650Ti 4 GB + Kaggle GPU.

**The hard problem, unchanged:** crop type, health score and yield for 966 farms with **zero labels and
zero ground truth**, from a **single-polarisation** sensor whose physics rules out the obvious index
[B1, B3].

**Resolved [E6]:** there are **no Round-1 artefacts**. The [A5] hard area constraint is gone. The rules
explicitly permit rebuilding the crop step, so we do — and say so plainly in the writeup. The constraint is
**replaced by public district APY statistics as a soft prior**, which is arguably better founded (R1's areas
were themselves a model output, not ground truth) and which the rubric rewards *by name* as auxiliary open
data. **Nothing is blocking. Plan is final.**

---

## 2. Proposals — final selection

Composed, not competing: P-B and P-D each replace one stage of P-A; P-C supplies features to both.

### P-A — Physics-First Phenological Trajectory *(baseline — build first, always)*
`PLAN.md` §1 as written: calibrated γ₀ [B9] → incidence normalisation to 31.5° [B8] → **water-point
referencing** [E4] → June bare-soil referencing [B12] → phenology-template crop assignment under a
**district APY soft prior** [E6] → crop-relative composite health → district baseline × relative
performance × season-completion yield.
**Backing:** [B1–B12]. **Feasibility:** high, numpy/scipy/rasterio/skimage. **Role:** the submittable floor.

### P-B — Unsupervised Discriminative Clustering + MRF *(crop step; the Bi lineage)*
Bi et al. TGRS 2017 [E2], fully specified, physics swapped at initialisation:
```
init      : phenological trajectory agreement [B7] + district APY prior [E6]    (replaces Cloude-Pottier)
subprob 1 : fix Y, solve W  — softmax regression, L-BFGS, α_c = 5e-5
subprob 2 : fix W, solve Y  — MRF over the FARM ADJACENCY GRAPH, BP/ICM, α_s ≈ 1
update    : recompute N_j (class-imbalance weights), iterate 3x
rectify   : entropy/KNN noisy-label rectification post-step [C3-T4]
```
Node = farm polygon, so N = 966 — the optimisation is trivially fast at our scale.
**Backing:** [E2, C3-T1..T4]. **Feasibility:** high — `scipy.sparse` + `sklearn`, no deep learning,
deterministic. **Buys:** replaces the weakest, most hand-wavy stage with a named, published, citable
framework. Reported gains over initialisation were +6.45% and +24.32% overall accuracy.
⚠ **Heed the paper's own warning:** α_s ≤ ~1 and ≤3 iterations, or Maize (6%) and Bajra (9%) get smoothed
out of existence — they measured a 39.76% accuracy collapse on thin classes by iteration 5.

### P-C — Complex-Domain Exploitation *(features + the creativity axis)*
1. **Sub-aperture / zero-baseline coherence** [D1] — split each acquisition into azimuth sub-looks and
   correlate. Zero temporal baseline, available on **all four dates**, measures volume decorrelation:
   canopy decorrelates between sub-looks, bare soil does not. **The one that works.**
2. **K-distribution shape parameter α** per farm per date [D3] — separates speckle from true scene texture,
   which raw spatial CV cannot do at ENL 1.0. Directly serves the rubric's "more uniform canopy structure
   scores higher". Method-of-moments fit, ~2000 samples per median plot [A3].
3. **Repeat-pass coherence** on Jun19–Aug14 (Δθ = 0.076°, [A3]) — expected to fail at 56-day X-band [B4].
   **Run it, report the negative honestly.**

**Backing:** [B4, D1, D3, C3-T5]. **Feasibility:** (1) and (2) high, (3) medium and expected to fail.

### P-D — Water Cloud Model Inversion *(health + yield core; the physical backbone)*
```
σ⁰_tot = σ⁰_veg + T²·σ⁰_sol ;  σ⁰_veg = A·V1·cosθ·(1−T²) ;  T² = exp(−2·B·V2·secθ) ;  σ⁰_sol = C·exp(D·Mv)
```
with **A,B,C,D fixed at the published X-band HH values** [E3] (VWC descriptor: A=0.0438, B=0.1047,
C=0.0324, D=0.03971) and **σ⁰_sol measured directly** from the pre-monsoon, pre-sowing June pair [B12] —
which is exactly what normally makes this inversion under-determined. Output: per-farm **relative
vegetation water content**, a physical biomass quantity driving both health and yield.
**Backing:** [E3, B12, B2, E4]. **Feasibility:** medium.
⚠ **Caveats to state openly:** coefficients fitted on irrigated grassland, not cotton/rice/groundnut; fit R²
0.47–0.52 at HH; incidence must enter via `cosθ`/`secθ`; output is **relative**, not absolute VWC.
D_HH = 0.172 dB/Vol.% also lets us *bound* how much Jun→Aug change is soil moisture rather than
vegetation — the task's biggest confounder, quantified instead of hand-waved.

### P-E — Self-Supervised Representation Learning *(cut to an ablation; first thing dropped)*
n = 966 farms × 4 dates on a 4 GB card. Too small to beat a designed physical feature set, and it would
consume documentation time the rubric actually pays for [D4, E5]. **Run only if I5 finishes early**; report
as an honest comparison. A documented *"we tried it, the physics wins at n=966"* earns points; a
half-trained network loses them.

**Build order: P-A → P-D → P-C → P-B → (P-E if time).**

---

## 3. Schedule — 11 days, gated

| Day | Date | Work | Gate |
|---|---|---|---|
| D0 | **Aug 1** | ✅ research closed, papers extracted, plan locked. Scaffolding, run ledger, env check | ledger works |
| D0.5 | **Aug 1** | ✅ **I0.5 EDA (`src/eda.py`)** — alignment gate, quicklooks, plot geometry, raw SLC stats, land-cover reference candidates, per-farm coverage. Runs on the vendor's geocoded previews, so it needs no preprocessing | ✅ **alignment PASSES** [F3]; coverage measured [F4] |
| D1–D2 | Aug 2–3 | **I1 Preprocess:** `β₀ = sc·\|z\|²` [B9], multilook FINE+BASE, DEM local incidence, GCP geocode, cosine-N normalisation to 31.5° [B8], **water-point referencing** [E4] | 🚦 **land-cover dB sanity gate [O1]** — water ≈ NESZ, built-up ≫ 0, cropland −5…−12 dB. Plus visual farm-overlay alignment check |
| D3 | Aug 4 | **I2 Features:** negative-buffered interiors, level/temporal/CV/GLCM [B5,B6], June bare-soil referencing [B12], **K-dist α** [D3], **sub-aperture coherence** [D1], DEM/TWI. **+ fetch aux: district APY (areas *and* yields) [E6,O5], GLO-30 DEM [O6]** | 966 farms, zero NaN, no farm dropped; APY table on disk |
| D4 | Aug 5 | **I3 crop (P-A heuristic, district APY soft prior)** + **I4 health & yield (P-A)** + `submission.csv` v1 | 🚦 **SUBMITTABLE GATE — schema passes, 966 rows, 5 columns, exact crop spellings.** Nothing below starts until green |
| D5–D6 | Aug 6–7 | **I6 P-D swap:** WCM inversion replaces the vigour component; re-run health & yield | measurable improvement or documented rejection |
| D7 | Aug 8 | **I7 P-B swap:** discriminative clustering + MRF replaces I3; compare against P-A crop map | areas still match constraint; agreement analysis vs P-A |
| D8 | Aug 9 | **I5 Validation battery** (§4) + **I8** repeat-pass coherence attempt [O2] | ≥3 independent checks, all reported including failures |
| D9 | Aug 10 | **I9 Notebook** — clean run from a fresh kernel, heavily commented with *why* | runs top-to-bottom, no errors |
| D10 | Aug 11 | **I10 Writeup ≤4 pages + media gallery + cover image** | all four required writeup topics covered |
| D11 | Aug 12 | Buffer, final schema check, **submit** | submitted, not draft |

**Hard rule:** a complete valid submission exists at the end of **D4 (Aug 5)**. Everything after is
improvement on something already submittable. Round 1's lesson was an unreconstructable champion — secure
first, optimise second. If any phase slips, **cut P-E, then P-B, then I8** — never cut D9–D11.

---

## 4. Validation strategy (no ground truth — this is where 20 points live)

1. **Sentinel-2 October NDVI** correlation — witness only, never an input. Protects the SAR-primary claim.
2. **Sentinel-1 C-band VH** correlation — sensor diversity was R1's most transferable lesson.
3. **Moran's I** on the health index — real agronomic signal is spatially autocorrelated; noise is not.
4. **Ablation + weight perturbation** — Spearman ρ between variants shows ranking stability.
5. **Agronomic plausibility** — per-crop distributions, village aggregate vs Vadodara district statistics.
6. **Cross-proposal agreement** — P-A vs P-B crop maps, P-A vs P-D health rankings. Two independent methods
   agreeing is evidence; disagreeing shows exactly where to look. Only available *because* we built more
   than one proposal.
7. **Visual check** — highest- and lowest-scoring plots against the imagery. Directly tests the rubric's own
   wording: does a "visibly more uniform canopy" actually score higher?
8. **Report everything that fails.** A documented negative outscores a silent omission.

## 5. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| ~~Geocoding misalignment on 0.276 ha plots~~ | ~~fatal~~ | ✅ **CLEARED at D0.5** [F3] — boundaries track field edges on the vendor geocoding. Re-run `eda_01` as a regression test after our own GCP geocoding in I1 |
| **42 farms have no SAR data at all; 32 partial** [F4] | coverage is 10 rubric points and needs all 966 rows | crop-conditional village-median imputation with a `qc_flag` column, counted and **reported in the writeup**. Missingness is spatially clustered, not random — say so, and borrow from adjacent *covered* farms |
| Swath-edge bright artefact on Jun 19 / Aug 14 [F7] | biases exactly the fragile edge farms | erode the valid-data mask a few pixels before extraction |
| Slipping past the D4 submittable gate | loses everything | cut P-E → P-B → I8 in that order; never cut D9–D11 |
| WCM coefficients are grassland-fitted, not crop-fitted | overstated absolutes | output **relative** VWC only; cite Attema & Ulaby 1978 for crops; state it |
| P-B smooths away Maize/Bajra (6%/9% of area) | wrong crop map | α_s ≤ 1, ≤3 iterations — the paper's own measured failure mode [E2] |
| No published X-band HH phenology envelopes for cotton/groundnut (74% of area) | weak P-B initialisation | fall back to data-driven relative trajectory shapes; state it |
| District-level APY breakdown for Vadodara unobtainable [E6] | crop prior weakens | fall back to state-level kharif 2025 proportions and state the substitution |
| Crop map is rebuilt, not carried from R1 [E6] | rubric names "R1 classification correctly applied" | rules explicitly permit rebuilding; say so plainly and show the method — do not imply an R1 map existed |
| Over-modelling, under-writing | loses 25 pts of Docs + Presentation | the D4 gate plus three protected days of writing |
| Absolute calibration undeclared [B9] | absolute yields unreliable | index is relative **by design**; water-point referencing [E4] + ESA EDAP citation |

## 6. Remaining open items

| # | Question | Status |
|---|---|---|
| O1 | Does `β₀ = sc·\|z\|²` give sane dB? | settled empirically at the D1–D2 gate |
| O2 | Is repeat-pass coherence recoverable on Jun19–Aug14? | I8, expected negative, report either way |
| O5 | Vadodara district crop **areas and yields** | **fetch at D3** — moved earlier, now load-bearing for the crop step too. data.gov.in Gujarat APY / Gujarat DoA / ICRISAT DLD. **Fallback if no district breakdown: state-level kharif 2025 proportions, stated openly** [E6] |
| O6 | DEM choice | Copernicus GLO-30; terrain is flat, quantify the effect and say so |
| O7 | Kaggle runtime strategy | AOI-crop early; precomputed-intermediates dataset if needed |
| O3, O4, O8, **O9**, O10–O12 | deadline · host email · rubric · **R1 artefacts** · compute · aux rules · time | **all closed** by [E1], [E6] and user input |

**No open item blocks the start of work.** O1, O2, O5, O6, O7 are each settled *by running code* at the
phase where they are needed — none of them is a question to ask.

## 7. Papers — status

**On disk and extracted** (`papers/`): Bi TGRS 2017 discriminative clustering ✅ *(P-B unblocked, [E2])* ·
El Hajj RSE 2016 X-band WCM ✅ *(P-D unblocked, [E3])* · Inoue RS 2014 X-band paddy rice yield ✅ *([E4])* ·
Bi TGRS 2019 graph semi-supervised · Bi TIP 2020 3D-DWT + MRF · RectMamba Neurocomputing 2026 ·
entropy-KNN ASC 2025 · RSE 1996 SAR texture feature selection.

**Nothing further is blocking.** The last five support [C3-T2/T3/T4] and [D3] and get read at depth only if
the schedule allows. Open-access and already usable: ESA EDAP Capella note [B9], coherence↔NDVI [B4], NISAR
cropland CV [B6], dynamic-cosine normalisation [B8].

---

## Change log

- **v3 — 2026-08-01 — PLAN FINAL, no open blockers.** No Round-1 artefacts [E6]; the [A5] hard area
  constraint is replaced by a **district APY soft prior** from public open data (rubric-rewarded as aux
  data). Aux fetch moved D4 → D3. Two risks added. All O-items closed or code-settled.
- **v2 — 2026-08-01** — rubric, deadline and CSV schema resolved [E1]; P-B and P-D unblocked by full-text
  extraction [E2, E3]; water-point normalisation adopted [E4]; P-E cut to an optional ablation; aux-data
  policy corrected; 11-day gated schedule replacing the notional 12-day one.
- **v1 — 2026-08-01** — created. Absorbed `PLAN.md` as P-A; added P-B/P-C/P-D/P-E; recorded blockers.
