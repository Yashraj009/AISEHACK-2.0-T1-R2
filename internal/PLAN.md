# R2 PLAN — Method Design and Execution Schedule

Derived from `00_BRIEF.md` (requirements) and `RESEARCH_LOG.md` (evidence). Every design choice below
carries the evidence tag that justifies it, so the notebook and writeup can cite it inline.

---

## 0. Design principles for this round

1. **Optimise for the rubric, not for an imaginary accuracy.** 55 of 100 points are plausibility,
   completeness, documentation and presentation. Ship the whole thing early, then deepen.
2. **Every number has a physical reason printed next to it.** If we cannot justify a parameter in one
   sentence, it does not go in.
3. **Capella is primary.** Aux data refines or validates. Sentinel-2 NDVI is held back as an *independent
   check*, not an input — that converts it from a threat to the "SAR-primary" claim into evidence for the
   "Validity" score.
4. **Crop-relative everything.** "Healthy" for cotton standing in October and "healthy" for harvested rice
   are different physical states. All scoring happens within crop class.
5. **Honest negatives are assets.** A documented failed coherence experiment scores better than silence.
6. **Round-1 reproducibility discipline applies unchanged:** version every intermediate, never overwrite,
   log every run, no hand-computed parameters, deterministic rebuild.

---

## 1. The method

### Stage 0 — Preprocessing (the foundation; get this exactly right)

```
SLC (complex)
  → β₀ = scale_factor · |z|²                      [B9 — ESA EDAP; FIXES the R1 scale² bug]
  → multilook (speckle ↓, ENL ↑) at two scales:
        FINE  ~2 m   → texture, within-field uniformity   [A3: 1.2 m res, ~2000 looks/plot]
        BASE  ~5 m   → farm-level means, temporal trends
  → σ₀ = β₀·sin(θ_local),  γ₀ = σ₀/cos(θ_local)   using DEM local incidence  [O6]
  → geocode: GCPs + Copernicus GLO-30 DEM → EPSG:32643
  → incidence normalization to θ_ref = 31.5° (Oct anchor), cosine-N law,
    N fitted empirically from stable targets                                  [B8]
  → dB
```
Guards: `os.environ.pop("PROJ_LIB", None)` first line; match SLC files by **basename date**, never folder
(Jun-19 folder holds a stray Jun-06 tif, [A3]); crop to the village bbox + buffer immediately (the full
strips are 27k × 4k — cropping is what makes Kaggle runtime feasible, [O7]).

**Validation gate before proceeding:** land-cover sanity check on σ₀ — water near NESZ, built-up strongly
positive, cropland ≈ −5…−12 dB. This settles [O1] empirically. If the numbers are wrong, everything
downstream is wrong, so this gate is mandatory.

### Stage 1 — Farm-level feature extraction

Per farm × per date, over the plot interior (**negatively buffered ~3–5 m to kill edge/mixed pixels** —
critical when 37% of plots are <0.2 ha, [A2]):

| Family | Features | Physical meaning |
|---|---|---|
| Level | mean/median γ₀ per date | canopy + soil scattering strength |
| Temporal | Δ(Aug−Jun), Δ(Oct−Aug), Δ(Oct−Jun), season integral (trapezoidal) | growth, senescence, accumulated growth [B10] |
| Uniformity | **spatial CV within plot** per date, IQR, p10/p90 spread | canopy uniformity — the rubric's own wording [B6] |
| Dynamism | **temporal CV** across 4 dates | cropped vs fallow; near-zero = nothing ever grew [B6] |
| Texture | GLCM **entropy** (primary), contrast, variance — on **unfiltered** fine data | within-field structural heterogeneity [B5; R1: entropy best] |
| Coherence | γ(Jun19, Aug14) if the pair proves usable | vegetation decorrelation [B4, O2] |
| Context | DEM elevation, slope, TWI (waterlogging proxy); plot area, shape | drainage — matters given the wet Aug/Sep [B12] |

Bare-soil referencing: **June scenes are pre-monsoon, pre-sowing** [B12] → treat mean(Jun06, Jun19) as each
farm's **bare-soil baseline** and use `Δ = γ₀(Aug or Oct) − γ₀(Jun_baseline)` as the vegetation-attributable
component. This removes the static per-plot soil-roughness and terrain contribution — one of the strongest
and most defensible ideas available to us, and it turns two apparently useless pre-season dates into the
calibration reference.

### Stage 2 — Crop type per farm (means to an end; do it well but do not over-invest)

Not a free-running 5-class classifier — Round 1 proved HH-only X-band cannot cleanly separate five crops
(hard fusion scored 5× worse than a flat prior). Instead: **area-constrained assignment.**

1. Score each farm × crop by agreement between its measured 4-date trajectory and the crop's expected
   phenology (rice: flood dip then October decline, with the published −22…−17.7 dB SoS → −16.1…−14.2 dB
   peak envelope as the shape reference [B7]; cotton: still standing/high in October; groundnut: drier,
   lighter soils, harvested by October; maize/bajra: early cereals, bare by October). R1's locked blend
   signatures carry over as priors.
2. **Constrain the assignment so per-crop total area matches the R1 Sokhda totals rescaled to the digitized
   447.9 ha** (Cotton 43.0%, Groundnut 31.0%, Rice 10.6%, Bajra 9.4%, Maize 6.0% — from [A5]).
3. Solve as a transportation/assignment problem (`scipy.optimize.linear_sum_assignment`, or a greedy
   quota fill; both deterministic).

This is defensible, directly answers the "Round 1 classification correctly applied" criterion (25-point
band), and is genuinely more creative than a naive classifier — while being *more* accurate, because the
village-level totals it is anchored to are exactly correct.

### Stage 3 — The health index

Crop-relative composite, each component z-scored **within crop**, then combined and mapped to 0–100:

| Component | Rationale |
|---|---|
| **Structure/vigour** — bare-soil-referenced γ₀ at the crop's growth-relevant date | X-band responds to canopy structure; referenced to remove soil [B1, B12] |
| **Trajectory conformity** — agreement of the 4-date curve with the crop's expected phenology | a healthy crop follows its phenological curve; a stressed/failed one does not [B7] |
| **Uniformity** — 1 − normalized spatial CV | *"fields with more uniform canopy structure score higher"* — the rubric's own criterion [B6] |
| **Texture** — inverse GLCM entropy (lower heterogeneity = more even stand) | within-field heterogeneity [B5] |
| **Coherence** (conditional) — low coherence = actively vegetated | [B4] if [O2] passes |

Weights: start equal within family, then justify any deviation. Do **not** tune weights to make the map look
nice — instead run a **sensitivity analysis** showing the ranking is stable across weight choices, and show
that plot. Stability under perturbation is exactly the evidence a judge needs when no ground truth exists.

Explicitly stated in the writeup: **"brighter ≠ healthier" at X-band** — the naive index is physically wrong
because X-band saturates early with biomass [B1]. Saying this, and showing what we did instead, is a
direct play for the Technical Soundness points.

### Stage 4 — Yield to date

```
yield_estimate_to_date[farm] =
      district_yield_baseline[crop]              # t/ha, Vadodara APY stats [O5, B11]
    × relative_performance[farm]                 # from health index, neighbour-relative [B10]
    × season_completion_fraction[crop]           # ← "TO DATE", as of Oct 13
```

- **Neighbour-relative performance** — each farm compared against nearby farms *of the same crop*, which
  removes soil and agro-climatic bias. Published technique, not an invention [B10].
- **Season-completion fraction** is the point most teams will miss. The task says *yield to date as of
  Oct 13, not a final harvest forecast*. On Oct 13: rice, maize and bajra are harvested or at maturity
  (fraction ≈ 0.9–1.0); cotton is mid-picking with the season running to January (≈ 0.4–0.5); groundnut is
  at/just past harvest (≈ 0.85–0.95) [B12]. Making this explicit and crop-specific is a cheap, high-visibility
  demonstration that we read the question carefully.
- Report **both** t/ha and a 0–100 relative index, so the number is interpretable and the relative claim
  stays honest.
- Village aggregate = area-weighted sum → cross-checked against district statistics.

### Stage 5 — Validation without ground truth (this is where the 20 "Validity" points live)

1. **Independent optical cross-check** — correlate the health index against Sentinel-2 October NDVI per
   farm. Positive correlation supports the index; NDVI is *never* an input, only a witness.
2. **Independent sensor cross-check** — same against Sentinel-1 C-band VH. Sensor diversity was Round 1's
   most transferable lesson (a second correlated C-band feature added ~0; a different-frequency X-band
   feature added real signal).
3. **Spatial structure** — Moran's I on the health index. Real agronomic signal is spatially autocorrelated;
   noise is not. A significant positive I is strong evidence.
4. **Ablation/sensitivity** — recompute with each component removed and with perturbed weights; show
   ranking stability (Spearman ρ between variants).
5. **Agronomic plausibility** — distributions by crop, village aggregate production vs district statistics,
   and visual inspection of the highest- and lowest-scoring plots against the imagery.
6. **Report anything that fails.** A documented failure is worth more than a hidden one.

---

## 2. Deliverables

| # | Artifact | Notes |
|---|---|---|
| D1 | `submission.csv` | 966 rows × 5 columns, zero NaN, exact crop spellings |
| D2 | Public Kaggle notebook | full pipeline, runs clean, heavily commented with *why* |
| D3 | Writeup ≤4 pages | R1 application · health method · yield method · findings |
| D4 | Media gallery | cover + farm health map + village summary + temporal/texture plots |
| D5 | Kaggle dataset | preprocessed intermediates so the notebook runs within limits [O7] |

---

## 3. Schedule (~12 days; front-load a complete end-to-end pass)

| Phase | Days | Output | Gate |
|---|---|---|---|
| **P0 Setup** | 0.5 | R2 `src/`, results ledger, env check, deadline confirmed [O3] | ledger works |
| **P1 Preprocess** | 1.5 | 4-date calibrated, geocoded, incidence-normalized γ₀ stack (2 grids) | **land-cover dB sanity gate [O1]** |
| **P2 Features** | 1.5 | `farm_features.csv` — all 966 farms × all features, no NaN | every farm has values |
| **P3 Crop map** | 1 | `farm_crop.csv`, area-constrained to R1 totals | areas match constraint |
| **P4 Health + Yield** | 2 | `submission.csv` v1 — **complete end-to-end** | CSV passes schema check |
| **P5 Validation** | 1.5 | validation notebook + all plots | ≥3 independent checks done |
| **P6 Depth** | 1.5 | coherence experiment [O2], DEM/TWI, aux refinement | keep only what earns its place |
| **P7 Notebook** | 1.5 | public Kaggle notebook, clean run from fresh kernel | runs top-to-bottom |
| **P8 Writeup + media** | 1.5 | ≤4-page writeup, gallery, cover image | all required elements |

**The rule: a valid, complete submission must exist by end of P4.** Everything after that is improvement on
top of something already submittable. Round 1's lesson — an unreconstructable champion — came from
optimising before securing. We secure first.

---

## 4. Task list

### P0 — Setup
- [ ] `src/`, `results/{submissions,cache,figures}/`, `docs/` scaffolding
- [ ] `log.jsonl` ledger + immutable versioning helper (R1 discipline)
- [ ] Confirm exact deadline [O3]; decide on host email [O4]
- [ ] Env check: `py -3.12`, rasterio/pyproj/shapely/skimage/scipy, `PROJ_LIB` popped

### P1 — Preprocess
- [ ] `prep_r2.py`: β₀ = **sc·|z|²** (fixed), multilook FINE + BASE, DEM local incidence, GCP geocode
- [ ] Fetch Copernicus GLO-30 DEM over AOI [O6]
- [ ] Fit cosine-N incidence normalization empirically; report N and before/after [B8]
- [ ] **Gate:** land-cover dB sanity check [O1]; quicklooks for all 4 dates
- [ ] Self-check: assert on a synthetic complex array that β₀ round-trips

### P2 — Features
- [ ] `farm_stats.py`: negative-buffer plot interiors; guard degenerate polygons (no farm dropped)
- [ ] Level, temporal, spatial-CV, temporal-CV, GLCM entropy (unfiltered), DEM/TWI features
- [ ] Bare-soil referencing from the June pair [B12]
- [ ] Feature QA: NaN counts, distributions, correlation matrix (drop redundant features)

### P3 — Crop map
- [ ] Encode R1 Sokhda proportions [A5]; phenology-agreement scoring [B7]
- [ ] Area-constrained assignment; verify per-crop areas match the constraint
- [ ] Confusion-style diagnostic vs an unconstrained clustering, for the writeup

### P4 — Health + Yield
- [ ] `health_index.py` — crop-relative composite, 0–100
- [ ] `yield_todate.py` — district baseline × neighbour-relative performance × completion fraction
- [ ] Fetch Vadodara district yields [O5]
- [ ] `make_submission.py` + schema validator (966 rows, 5 cols, no NaN, exact spellings)

### P5 — Validation
- [ ] S2 NDVI cross-check · S1 VH cross-check · Moran's I · ablation/sensitivity · district-stats check
- [ ] Write the limitations section honestly

### P6 — Depth
- [ ] Coherence feasibility: baselines, coregistration, γ on the Jun19–Aug14 pair [O2] — report either way
- [ ] Add only what measurably improves internal consistency

### P7/P8 — Delivery
- [ ] Kaggle dataset of intermediates; notebook runs clean from fresh kernel
- [ ] Writeup ≤4 pages; media gallery + cover image
- [ ] Final schema check; submit before deadline

---

## 5. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Geocoding/GCP misalignment on 0.276 ha plots | fatal — features attach to the wrong field | overlay farms on imagery and inspect visually before extracting anything; sub-pixel check against built-up features |
| Kaggle runtime/memory limits | submission gate fails | AOI-crop early; precomputed intermediates dataset [O7] |
| Coherence turns out unusable at 56 days | loses one creativity axis | expected; report as a documented negative and lean on texture + trajectory |
| Health index looks like noise | loses Validity points | Moran's I and the cross-checks catch it early — that is why P5 comes before P6 |
| Over-engineering, under-documenting | loses 25 pts of Docs+Presentation | complete pass by P4; the last 3 days are writing, not modelling |
| Absolute calibration error in Capella [B9] | absolute yields unreliable | index is *relative* by design; cite ESA EDAP as the justification |
