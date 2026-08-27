# R2 BRIEF — Requirements, Objectives, and Ground Truth About This Round

> Purpose: the single authoritative statement of *what is being asked*, *what we actually have*, and
> *what we will be scored on*. Read this before any code. Written 2026-07-31.
> Companion docs: `../RESEARCH_LOG.md` (evidence + sources), `../PLAN.md` (how we execute).

---

## 1. The task in one paragraph

Using four Capella X-band HH SLC acquisitions (2025-06-06, 2025-06-19, 2025-08-14, 2025-10-13) over the
village of **Sokhda** near Vadodara, plus farm and village boundary shapefiles, produce for **every one of
966 farm plots**: (a) the dominant crop type carried forward from our Round-1 crop map, (b) an original,
SAR-physics-grounded **crop health index**, and (c) a **yield estimate "to date"** as observed through
October 13. Aggregate to village level. Deliver a public Kaggle notebook, a ≤4-page writeup, a media
gallery, and a CSV with columns `village_id, farm_id, crop_type, health_index, yield_estimate_to_date`.

**No leaderboard. No ground truth. No prescribed formula.** A human judging panel scores against a
published rubric.

---

## 2. THE STRATEGIC FACT — this round is nothing like Round 1

R1 was a closed-form measurement problem: plain MSE + a final leaderboard turned the scoreboard into an
exact oracle, and the optimal play was linear algebra (parabola solve, Gram inner-product leak, all-zeros
cell reads → 0.000). **Every one of those levers is dead here.** There is no MSE channel, no submission
feedback, nothing to solve against.

What replaces it is the rubric. Read the point allocation carefully:

| Criterion | Points | What it actually rewards |
|---|--:|---|
| Technical Soundness | 25 | Real SAR physics; R1 classification correctly applied |
| Methodological Creativity | 20 | Beyond single-date mean: temporal trajectory, texture, coherence, smart aux |
| Validity & Plausibility | 20 | Internally consistent, agronomically sensible, defensible |
| Village Aggregation & Coverage | 10 | All farms processed; aggregation logic clearly defined |
| Documentation & Reproducibility | 15 | Judge can follow *why*, not just *what* |
| Presentation Quality | 10 | Writeup + visuals that land at a glance |
| Required Elements | Y/N | Notebook runs clean; CSV has the 5 columns |

**Only ~45 points (Soundness + Creativity) are about the method itself. 55 points are explanation,
plausibility, completeness, and presentation.** And "Required Elements" is a gate — a notebook that errors
or a CSV missing a column zeroes the whole submission regardless of how good the science is.

Strategic consequence: **a physically-defensible, beautifully-documented, thoroughly-validated moderate
method beats a clever fragile one.** We optimise for explicability and internal consistency, not for a
hypothetical accuracy we can never measure. Every design choice must have a one-sentence physical
justification we can print next to it.

Second consequence: since there is no ground truth, *plausibility IS the metric*. We must manufacture our
own evidence of correctness — independent cross-checks, ablations, spatial-structure tests — and show them.

---

## 3. What we actually have (verified on disk, not from the description)

All figures below were measured directly from the delivered files.

### 3.1 Imagery — 4 × Capella Stripmap SLC, HH

| Date | Folder tag | Rows × Cols | Center incidence | Scale factor | Ground res rg × az |
|---|---|---|--:|--:|---|
| 2025-06-06 | `...20250606072501` | 27192 × 4682 | **35.244°** | 0.00212186 | 1.15 × 1.23 m |
| 2025-06-19 | `...20250619021410` | 27187 × 3910 | **28.768°** | 0.00236205 | 1.38 × 1.23 m |
| 2025-08-14 | `...20250814031124` | 27219 × 3897 | **28.692°** | 0.00198903 | 1.38 × 1.23 m |
| 2025-10-13 | `...20251013022643` | 27241 × 4244 | **31.528°** | 0.00136443 | 1.27 × 1.23 m |

- All **left-looking**, stripmap, HH, ENL = 1 (true SLC, full speckle).
- Pixel spacing ≈ 0.735 m (row) × 1.07–1.28 m (column).
- **All four scenes fully contain the Sokhda village bounding box** — verified against the geocoded
  preview footprints. No coverage trap this round (R1 had 18/29 villages uncovered).
- ⚠ The Jun-19 folder contains a **stray duplicate of the Jun-06 SLC**. Match files by basename date, never
  by folder. (R1 hit this and worked around it — see `prep_stack.py:61`.)
- ~1.2 m resolution on a median 0.276 ha plot ≈ **2000+ independent looks per farm**. Within-field
  statistics (uniformity, texture) are genuinely well-sampled here. This is the round's biggest
  technical opportunity.

### 3.2 Boundaries

- `Sokhda_Farms.shp` — **966 farm polygons**, fields `FID, id, ID_1, VILLAGE`. CRS: geographic WGS84.
  Total area **447.9 ha**. Median plot **0.276 ha**, mean 0.464, max 3.49. **37% of plots are <0.2 ha; 68%
  are <0.5 ha.** Smallholder fragmentation is the defining spatial characteristic.
- `Sokhda_Village.shp` — **1 polygon**, `ID = 22`, `VILLAGE = 'Sokhda'`. Area **1174.1 ha**.

### 3.3 Description-vs-reality mismatches (must be handled, and stated in the writeup)

| Competition text says | Reality on disk | Our handling |
|---|---|---|
| "4 villages", spatial join needed | **1 village (Sokhda)**; farms already carry `VILLAGE`/`ID_1=22` | Still perform and show the point-in-polygon join — the rubric awards it — but note it is confirmatory |
| `round1_crop_classification.csv` provided | **Not present in the data folder** | We supply our own R1-derived crop map (see §4) |
| Overview says 966 farms / 1 village; Data tab says 4 villages | Overview is correct | Follow the data |

### 3.4 The Round-1 asset — this is our unfair advantage

**Sokhda is village ID 22 in the Round-1 village shapefile** (verified: R1 `villages_clean.shp` record
22 = "Sokhda"). Round 1 ended with an exact, leaderboard-verified reconstruction of the crop area of every
village. For village 22:

| Crop | Area (ha) |
|---|--:|
| Rice | 73.33 |
| Cotton | **297.08** |
| Groundnut | **213.93** |
| Bajra | 65.12 |
| Maize | 41.42 |
| **Total cropped** | **690.90** |

Cotton + groundnut = **74%** of Sokhda's cropped area. This is a hard, quantitative, externally-validated
constraint on the crop map — and no other team has it.

Two things to be scrupulous about:
1. **Provenance honesty.** These totals came from Round-1 leaderboard calibration (exact-cell oracle reads),
   not from a free-running classifier. In the writeup they are described as *"our Round-1 calibrated
   village-level crop areas"*, with the method stated plainly. We do not present them as a model output.
   They are legitimately "the crop classification carried forward from Round 1" — that is exactly what the
   rules instruct us to do.
2. **The 447.9 vs 690.9 gap.** The 966 digitized farm polygons cover 447.9 ha; the village's true cropped
   area is 690.9 ha (village polygon = 1174.1 ha). The digitized plots are a **~65% subset** of cropland.
   So the R1 totals are applied as *proportions*, rescaled to the digitized area — not as absolute
   quantities. This must be stated, not buried.

### 3.5 Auxiliary data we can reuse (Capella stays primary — non-negotiable per the rules)

From the Round-1 project, already fetched and working: Sentinel-1 C-band VV/VH (dense, Jun–Nov),
Sentinel-2 optical + monthly NDVI (Jun/Sep/Oct usable, Jul–Aug 100% cloud), Dynamic World cropland,
GLCM texture machinery, and the GEE fetch scripts. Everything is on the same AOI. **Sokhda is inside the
R1 AOI**, so all of it applies directly.

Rule: aux data *refines or cross-checks*, never *replaces*. In particular Sentinel-2 NDVI is reserved
mainly for **independent validation** of the health index — using it as an input would weaken the
"SAR-primary" claim, while using it as a check strengthens the "Validity & Plausibility" score.

---

## 4. What we must produce

### 4.1 The CSV (this is the gate — get it exactly right)

```
village_id, farm_id, crop_type, health_index, yield_estimate_to_date
```
- One row per farm. **All 966 farms, no gaps, no NaN.**
- `village_id` — from the village shapefile (`22` / Sokhda).
- `farm_id` — the farm `FID`.
- `crop_type` — one of exactly `Rice, Cotton, Maize, Bajra, Groundnut`.
- `health_index` — our farm-level score. Define range and meaning explicitly.
- `yield_estimate_to_date` — potential **as of Oct 13**, explicitly *not* a final harvest forecast.

### 4.2 The notebook
Public, self-contained, runs top-to-bottom without errors on Kaggle. Must contain the full pipeline:
crop-classification application → health index → yield-to-date → village aggregation.

### 4.3 The writeup (≤4 pages, penalty over)
Must cover: how R1 classification was applied to the new farm boundaries; health-index methodology and
reasoning; yield-to-date approach; key findings (village summaries, notable patterns).

### 4.4 Media gallery
Cover image (required) + farm-level health map (colour-coded) + village summary chart/table + supporting
plots (temporal trends, texture visualisations).

---

## 5. The questions the method must answer

These are the questions a judge will implicitly ask. Every one needs an answer we can defend in one or two
sentences, backed by the evidence in `../RESEARCH_LOG.md`.

1. **What does "healthy" mean in an X-band HH backscatter signal?** (Not obvious — X-band saturates early
   with biomass. Our answer must be about canopy structure, roughness, dielectric/moisture and *uniformity*,
   not a naive "brighter = healthier".)
2. **Why is a single-date mean insufficient, and what does the temporal trajectory add?**
3. **How do we compare a rice plot to a cotton plot** when their phenology, structure and Oct-13 status are
   completely different? (Answer: the index must be crop-relative.)
4. **How is Oct 13 different per crop?** Cotton and groundnut are still standing; rice, maize and bajra are
   largely harvested. "Yield to date" therefore means different fractions of the season per crop.
5. **How do we know the answer is not noise?** (Independent cross-checks, spatial structure, ablations.)
6. **Why should a judge trust the crop map** when Round 1's own research showed HH-only X-band cannot
   cleanly separate five crops? (Answer: we do not free-run a 5-class classifier — we apply an
   area-constrained assignment anchored to R1's calibrated village totals.)
7. **What are the honest limitations?** Stating them well *gains* points under "Technical Soundness" and
   "Validity"; hiding them loses points when a judge spots them.

---

## 6. Hard constraints and gotchas

- **Capella must remain primary and central.** Aux refines, never replaces.
- **Notebook must run on Kaggle** (~16 GB RAM, ~12 h, limited disk). 2.1 GB of SLC cannot be fully
  processed there naively — the pipeline needs an AOI-cropped design and/or a precomputed-intermediates
  dataset, with the SLC preprocessing code present and runnable. R1's submission used exactly this pattern.
- **Public notebook / public writeup.** Private attached resources auto-publish after the deadline.
- **≤4 pages** on the writeup.
- Deadline: competition page read "12 days to go" at kickoff — confirm the exact UTC deadline early.
- Host contact for clarifications: `insights@galaxeye.space`.

---

## 7. Definition of done

- [ ] `submission.csv`: 966 rows, 5 columns, correct dtypes, zero NaN, crop names spelled exactly.
- [ ] Notebook executes end-to-end from a clean kernel, no errors, well-commented, *why* stated per step.
- [ ] Writeup ≤4 pages covering all four required topics.
- [ ] Media gallery: cover + health map + village summary + ≥2 supporting plots.
- [ ] Every parameter in the pipeline has a stated physical or statistical justification.
- [ ] Validation section: ≥3 independent plausibility checks, with results shown (including any that fail).
- [ ] Limitations section written honestly.
- [ ] Every intermediate versioned and logged (the Round-1 reproducibility lesson).
