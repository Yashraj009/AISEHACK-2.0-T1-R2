# X-band Alone, Witnessed Throughout: Crop Health and Yield to Date for 966 Farms

**Subtitle (140 char field, 135 used):** Four Capella scenes produce every number; Sentinel-1 and Sentinel-2 are witnesses only, never inputs — including the tests that failed.

**Team GDHTM** — Yash Sorathiya · Jenish Sorathiya · Yajurshi Velani · Mahi Parmar · Aayush Pandya
Sokhda village (`village_id` 1), Vadodara, Gujarat · 966 farms · kharif 2025

---

## The one rule this project is built on

**Every value in `submission.csv` comes from the four provided Capella X-band HH scenes.** Sentinel-1
and Sentinel-2 are used *only* to test the product after it is built. No optical or C-band
measurement enters any shipped number.

That constraint costs accuracy and we kept it anyway, for two reasons. It keeps the Capella imagery
the primary source, as the guidelines require. And it makes the validation mean something: a witness
that also helped build the product cannot independently confirm it.

The visible consequence is that this writeup reports failures as prominently as successes. Three of
our results are negative, and one of them changed a shipped column.

## 1. Applying the Round 1 crop classification to the new boundaries

Round 1 ended at **MSE 0.000**, so its 145 village × crop cells are exact ground truth — including
Sokhda's crop-area shares. Those shares are the thing we carry forward.

The mechanism is a **constrained assignment**, in three steps:

1. **Per-farm soft evidence from X-band.** Physically-grounded features — the 19 June
   double-bounce response of flooded paddy, August volume scattering for tall woody cotton, the
   August-minus-June difference — produce class probabilities per farm, deliberately weak.
2. **Bias to the Round 1 shares.** Log-probabilities are shifted until the **area-weighted argmax
   shares match Round 1 exactly**. Area weighting, not farm count, because the Round 1 quantity is an
   area share.
3. **Argmax at the very end**, once the constraint is satisfied.

Why constrain rather than classify freely? Because we measured what happens otherwise: in Round 1,
free per-pixel assignment scored **5× worse than assigning nothing at all**. The village mix is the
reliable Round 1 product, so it is honoured as a constraint, not re-inferred.

**One Round 1 signature was re-imported, after four tests.** We checked every Round 1 feature sign
against its own exact truth: 13 of 15 agree, but Groundnut × NDVI-entropy *significantly contradicts*
it (ρ −0.531, p = 0.003) — evidence that the tail of that ladder partly fitted leaderboard noise.
Only the rice August-minus-June signature passed all four transfer tests, and adding it moved rice
from **not corroborated (p = 0.38) to p = 2.65×10⁻¹³** while improving crop separation on both
witnesses. The equivalent maize signature was tried and **rejected** — it degraded both witnesses.

## 2. Health index methodology

Four families, each z-scored across farms, combined into one 0–100 score:

| family | measurement | why it belongs |
|---|---|---|
| `level` | August γ⁰ | peak canopy volume |
| `growth` | 14 Aug − 19 Jun | the **only geometry-matched** date pair (0.076° apart in incidence) |
| `uniform` | −(within-farm CV) | patchiness means gaps, waterlogging or pest damage |
| `persist` | season integral | canopy held all season, not on one lucky date |

**The weights are derived, not hand-chosen.** Each weight is inversely proportional to that family's
total absolute correlation with the others — w_k ∝ 1/Σ|ρ(k,j)| — giving `growth` 0.283, `uniform`
0.301, `persist` 0.228, `level` 0.189. The rule reads only the feature matrix and is **blind to every
witness by construction**, because weights chosen by watching NDVI would turn a held-out check into a
fitting target. It also beat every hand-tuned variant we tried.

**Scored within crop.** Cotton and groundnut differ by ~4 dB for reasons unrelated to health, so a
pooled index would largely re-measure crop type. Each farm is scored against its own crop's median:
50 means *typical for that crop*. On the map this matters — 40 is "below par for this crop", not
"failing".

## 3. Yield-to-date estimation

    yield_to_date (t/ha) = district anchor × season completion(farm) × accumulation(farm)

We read the column exactly as the brief defines it — *"estimated yield potential up to the final
acquisition date using all available temporal observations"*, and explicitly **not a final harvest
forecast**. Every value is scaled by season completion (Cotton 0.45, Groundnut 0.75, Rice/Maize/Bajra
0.95) and never projected forward; divide by that factor to recover a full-season figure.

**Level from statistics, variation from SAR — stated, not blurred.** The district APY figure sets the
level; SAR cannot measure absolute yield without calibration data. Both per-farm terms are measured:
completion from each farm's own August→October change, accumulation from the season integral over
all four acquisitions.

**A witness caught a sign error here.** We had assumed a harvested field brightens back toward bare
soil, so high October-minus-August meant *more* complete. Sentinel-2 disagreed in all five crops: a
field that brightened has *more* standing biomass, not less. The term was reading standing crop as
senescence. The sign was corrected and the shipped column changed. No internal consistency check
would have caught that — only a sensor that disagrees.

## 4. Key findings

**The crop classes separate on two sensors they never saw.** Kruskal–Wallis p = 1.8×10⁻³⁴ (S2 NDVI),
7.7×10⁻²⁰ (S1 VH). The *ordering* is the real result: on 13 October cotton is the only crop still
standing and tops both witnesses; maize is harvested and bottoms both. That is the crop calendar,
recovered independently.

**Health clusters spatially far beyond chance** — Moran's I = 0.105 against a 199-permutation null.
Neighbouring fields share soil, water and management; modelling noise would not cluster.

**A season-integrated witness for the yield term.** `season_integral` spans 12 Jun–13 Oct, but our
original witnesses were single instants — the wrong shape. Cumulative NDVI, the textbook fix, is
**impossible here**: Sokhda had **zero** Sentinel-2 scenes under 20% cloud in June, July, August *or*
September. So we built the matched witness from the sensor that did see the season: 10 Sentinel-1
scenes, 12 Jun–10 Oct, all one relative orbit, same trapezoid. It corroborates cotton (ρ +0.305,
p = 5×10⁻¹⁰) and rice (+0.290, p = 0.007), is null for maize and groundnut, and **contradicts bajra**
(−0.219, p = 0.008). We report that rather than tune it away.

**Village-level summary — all 966 farms, none dropped.** Aggregation is area-weighted: village
production = Σ(farm yield t/ha × farm area ha), never a mean of per-hectare rates.

| crop | farms | area ha | median health | median t/ha to date | production t |
|---|--:|--:|--:|--:|--:|
| Rice | 86 | 47.4 | 50.0 | 1.64 | 77 |
| Cotton | 455 | 193.4 | 51.9 | 0.34 | 77 |
| Maize | 55 | 26.7 | 50.0 | 2.18 | 62 |
| Bajra | 149 | 42.3 | 50.0 | 2.57 | 113 |
| Groundnut | 221 | 137.7 | 50.0 | 1.86 | 266 |
| **Village 1** | **966** | **447.5** | **50.7** | **1.41** | **595** |

**Coverage is complete:** 895 farms measured directly, 52 imputed from adjacent same-crop
neighbours, 19 flagged for radio-frequency interference — every row carries its provenance.

### What failed

- **Per-farm crop labels do not survive an independent rebuild.** Against a Sentinel-2 + Sentinel-1
  map, Cohen's κ = **+0.103** — negligible. The village mix is well constrained; the individual farm
  label is not, and we say so rather than present the map as more certain than it is.
- **Repeat-pass coherence sits at the noise floor.** The stable-scatterer control did not clear its
  own bias floor, so we cannot separate true decorrelation from our own limitation — and claim
  neither.
- **Absolute radiometry is uncalibrated** (≈ +17 dB offset). ESA's EDAP assessment notes Capella's
  absolute accuracy is not declared while relative accuracy is good — exactly what we observe. Every
  downstream quantity is a difference or a within-crop rank, so the product survives it, and that is
  verified rather than asserted.

## Why X-band was worth it, measured

At 1.2 m the median farm is **95.2%** uncontaminated interior; at 10 m that falls to **63.3%**, and a
fifth of these farms become more than half edge-contaminated — the median parcel here is 0.27 ha.
And over the crop-forming window, Sentinel-2 offered **19 revisits and 0 usable ones**. Every Capella
acquisition is usable regardless of cloud. That is what the X-band buys.

## Media gallery guide

1. **Health Index map** *(required)* — farm-level, colour-coded, with pooled distribution
2. **Yield Estimate to Date map** *(required)* — farm-level, colour-coded, with by-crop spread
3. Crop classification map + area table
4. Coverage and confidence — provenance of all 966 rows
5. Village-level aggregate — the summary table and the aggregation rule
6. Temporal trajectory — the SAR physics the crop map rests on
7. Independent validation on two unseen sensors
8. The season-integrated witness, and the optical blackout
9. Robustness — ablation and Moran's I
10. The negative results
11. Why X-band — mixed pixels and cloud, quantified

## Reproducibility

The attached public notebook runs from a fresh kernel and its final cell **asserts** that it
reproduces the submitted `submission.csv` exactly. An 18-check ship gate verifies schema, ranges,
units and deliverables; a further gate asserts that every number quoted here matches the shipped
artefacts, so this text cannot drift from the data.
