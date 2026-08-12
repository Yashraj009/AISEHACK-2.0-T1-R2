# Kaggle Writeup — copy/paste guide

> **Title (80 char field, 77 used):**
> `Dasymetric Mapping of Village Crop Statistics to Parcel Level from X-band SAR`
>
> **Subtitle (140 char field, 138 used):**
> `Crop type, health index and yield-to-date for 966 farms from four Capella scenes, kharif 2025; Sentinel-1 and Sentinel-2 withheld to test.`
>
> **Card / thumbnail (560×280):** `media_gallery/thumbnail_560x280.png`
> **Cover image:** `media_gallery/cover.png`

### Which image goes where — nothing appears twice

**MEDIA GALLERY (7 items, in `upload/media_gallery/`)** — browsed *without* the text, so every
item stands alone: what we built, and evidence it is real.

| # | file | why it is in the gallery |
|:---:|:---|:---|
| 1 | `cover.png` | required cover — both deliverables at a glance |
| 2 | `gallery_00_method_overview.png` | the entire approach in one image, so the gallery alone explains the method |
| 3 | `gallery_01_health_index_map.png` | **required by the guidelines** |
| 4 | `gallery_02_yield_to_date_map.png` | **required by the guidelines** |
| 5 | `gallery_03_crop_classification_map.png` | supporting map the guidelines invite |
| 6 | `gallery_05_village_aggregate.png` | village-level summary table and the aggregation rule |
| 7 | `gallery_07_independent_validation.png` | the headline evidence: it validates on sensors it never saw |

**PROJECT DESCRIPTION (6 figures, in `upload/description_figures/`)** — these are *argument*. They
need the surrounding prose to mean anything, so they are inline, not in the gallery. Insert each
with the 🖼 toolbar button at the marked point below.

---

**Team GDHTM** — Yash Sorathiya · Jenish Sorathiya · Yajurshi Velani · Mahi Parmar · Aayush Pandya\
Sokhda village (`village_id` 1), Vadodara, Gujarat · 966 farms · kharif 2025

## The shape of the problem, and the one technique that answers it

Everything we know about this village's crops, we know only **in aggregate**: the crop-area shares
at village level, the yield anchor at district level. Nothing is known per farm — which is exactly
what the brief asks for.

So both deliverables are built the same way: **hold the aggregate, and let the SAR supply only the
variation inside it.** Distributing a known total across finer units using an ancillary variable
correlated with the true distribution is *dasymetric mapping*, and we apply it twice.

| known in aggregate | disaggregated to | ancillary variable from Capella |
|:---|:---|:---|
| Round 1 village crop-area shares (MSE 11.071) | 966 parcel labels | per-farm soft evidence, area-constrained |
| Vadodara district yield (APY) | 966 parcel t/ha | completion × accumulation |

Neither aggregate is error-free and we do not pretend otherwise — the Round 1 shares are our own
best estimate of the village mix, not ground truth. The case for holding them is comparative: the
aggregate is estimated from a whole village of evidence, a per-farm label from one parcel of it.

The health index has no aggregate to anchor to at all, so it is a **rank within crop**, never an
absolute level — the same discipline applied to a quantity with no total to honour.

## The one rule this project is built on

**Every value in `submission.csv` comes from the four provided Capella X-band HH scenes.**
Sentinel-1 and Sentinel-2 are used *only* to test the product after it is built. No optical or
C-band measurement enters any shipped number.

That constraint costs accuracy and we kept it anyway. It keeps the Capella imagery the primary
source as the guidelines require, and it makes the validation mean something — a witness that also
helped build the product cannot independently confirm it.

It is a claim about **arrows**, so the method diagram in the gallery *(item 2)* states it directly:
no arrow runs from a witness into a deliverable, while the two aggregates above are drawn in amber
and labelled as inputs.

## 1. Applying the Round 1 crop classification to the new boundaries

Round 1 ended at **MSE 11.071** across its 145 village × crop cells. The mechanism that carries
Sokhda's shares onto the new parcels is a **constrained assignment**:

1. **Per-farm soft evidence from X-band** — the 19 June double-bounce response of flooded paddy,
   August volume scattering for tall woody cotton, the August-minus-June difference. Deliberately weak.
2. **Bias to the Round 1 shares** — log-probabilities are shifted until the **area-weighted argmax
   shares match Round 1 exactly**. Area-weighted, because the Round 1 quantity is an area share.
3. **Argmax only at the very end**, once the constraint is satisfied.

Why constrain rather than classify freely? Because we measured what happens otherwise: in Round 1,
free per-pixel assignment scored **5× worse than assigning nothing at all**. The resulting map, with
its area table, is gallery item 5.

The physics underneath is visible in the season each crop draws:

![gallery_06_temporal_trajectory.png](figures/gallery_06_temporal_trajectory.png)

*Left: rice peaks on 19 June — double bounce off stems in standing water, HH-favoured, persisting up to ~46 days after transplanting. Right: the two inter-date differences that separate the classes.*  *(Kaggle: insert `gallery_06_temporal_trajectory.png` here)*

**One Round 1 signature was re-imported, after four tests.** Checking every Round 1 feature sign
against the Round 1 reconstruction, 13 of 15 agree — but Groundnut × NDVI-entropy *significantly
contradicts* it (ρ −0.531, p = 0.003), evidence that the tail of that ladder partly fitted
leaderboard noise. Only the rice August-minus-June signature passed all four transfer tests. Adding
it moved rice from **not corroborated (p = 0.38) to p = 2.65×10⁻¹³**. The equivalent maize signature
was tried and **rejected** — it degraded both witnesses.

## 2. Health index methodology

| family | measurement | why it belongs |
|:---|:---|:---|
| `level` | August γ⁰ | peak canopy volume |
| `growth` | 14 Aug − 19 Jun | the **only geometry-matched** date pair (0.076° apart) |
| `uniform` | −(within-farm CV) | patchiness means gaps, waterlogging or pest damage |
| `persist` | season integral | canopy held all season, not on one lucky date |

**The weights are derived, not hand-chosen.** Each is inversely proportional to that family's total
absolute correlation with the others — $w_k \propto 1 \big/ \sum_j |\rho(k,j)|$ — giving `growth` 0.283, `uniform` 0.301,
`persist` 0.228, `level` 0.189. The rule reads only the feature matrix and is **blind to every
witness by construction**; weights chosen by watching NDVI would turn a held-out check into a
fitting target. It also beat every hand-tuned variant we tried.

**Scored within crop.** Cotton and groundnut differ by ~4 dB for reasons unrelated to health, so a
pooled index would largely re-measure crop type. 50 means *typical for that crop* — on the map
*(gallery item 3)*, 40 reads as "below par for this crop", not "failing".

Which component actually carries the ranking, and does any single weight hold it up?

![gallery_09_robustness.png](figures/gallery_09_robustness.png)

*Component importance by ablation: drop each family and re-rank. `uniform` matters most (ρ 0.686), no single weight is load-bearing, and randomising all weights ±50% still leaves ρ ≥ 0.943. Right: health clusters spatially far beyond a 199-permutation null (Moran's I = 0.105) — neighbouring fields share soil and management, and modelling noise would not cluster.*  *(Kaggle: insert `gallery_09_robustness.png` here)*

## 3. Yield-to-date estimation

$$\text{yield\_to\_date}\;[\mathrm{t/ha}] \;=\; \underbrace{\text{anchor}_{\text{district}}}_{\text{level, from statistics}} \;\times\; \underbrace{\text{completion}_{\text{farm}} \;\times\; \text{accumulation}_{\text{farm}}}_{\text{variation, measured from SAR}}$$

We read the column exactly as the brief defines it — *"estimated yield potential up to the final
acquisition date using all available temporal observations"*, and explicitly **not a final harvest
forecast**. Values are scaled by season completion (Cotton 0.45, Groundnut 0.75, Rice/Maize/Bajra
0.95) and never projected forward; divide by that factor to recover a full-season figure.

This is the second dasymetric step, and both per-farm terms are measured rather than assumed:
completion from each farm's own August→October change, accumulation from the season integral over
all four acquisitions. The map is gallery item 4; cotton reads pale there because on 13 October it
is only ~45% through picking, so the level is set by crop and the SAR contributes the spread.

**A witness caught a sign error here.** We assumed a harvested field brightens back toward bare soil,
so high October-minus-August meant *more* complete. Sentinel-2 disagreed in all five crops: a field
that brightened has *more* standing biomass. The term was reading standing crop as senescence. The
sign was corrected and the shipped column changed — no internal consistency check would have caught
that, only a sensor that disagrees.

The accumulation term was then tested with a witness of the **right shape**:

![gallery_08_season_witness.png](figures/gallery_08_season_witness.png)

*`season_integral` spans 12 Jun–13 Oct, but our original witnesses were single instants. Cumulative NDVI is impossible here — Sokhda had **zero** Sentinel-2 scenes under 20% cloud in June, July, August or September. So the matched witness is 10 Sentinel-1 scenes on one orbit, same trapezoid. It corroborates cotton (ρ +0.305) and rice (+0.290), is null for maize and groundnut, and **contradicts bajra** (−0.219, p = 0.008). We report that rather than tune it away.*  *(Kaggle: insert `gallery_08_season_witness.png` here)*

## 4. Key findings

**The crop classes separate on two sensors they never saw.** Kruskal–Wallis p = 1.8×10⁻³⁴ on
Sentinel-2 NDVI and 7.7×10⁻²⁰ on Sentinel-1 VH *(gallery item 7)*. The **ordering** is the real
result: cotton is the only crop still standing on 13 October and tops both witnesses; maize is
harvested and bottoms both. That is the crop calendar, recovered independently.

**Village-level aggregation — all 966 farms, none dropped** *(gallery item 6)*. The rule is
area-weighted,

$$\text{village production}\;[\mathrm{t}] \;=\; \sum_{\text{farms}} \Big( \text{yield}_{\text{farm}}\;[\mathrm{t/ha}] \times \text{area}_{\text{farm}}\;[\mathrm{ha}] \Big)$$

never a mean of per-hectare rates, which would let a 0.05 ha plot count as much as a 5 ha one.

| crop | farms | area ha | median health | median t/ha to date | production t |
|:---|:---:|:---:|:---:|:---:|:---:|
| Rice | 86 | 47.4 | 50.0 | 1.64 | 77 |
| Cotton | 455 | 193.4 | 51.9 | 0.34 | 77 |
| Maize | 55 | 26.7 | 50.0 | 2.18 | 62 |
| Bajra | 149 | 42.3 | 50.0 | 2.57 | 113 |
| Groundnut | 221 | 137.7 | 50.0 | 1.86 | 266 |
| **Village 1** | **966** | **447.5** | **50.7** | **1.41** | **595** |

**Coverage is complete, and every row declares its provenance.**

![gallery_04_coverage_and_confidence.png](figures/gallery_04_coverage_and_confidence.png)

*895 measured, 52 imputed, 19 RFI-flagged — 966 total. Missing coverage is spatially clustered in the north-west rather than random, which is why imputation borrows from adjacent farms of the same crop instead of a village mean. Per-farm crop confidence is low **by design**.*  *(Kaggle: insert `gallery_04_coverage_and_confidence.png` here)*

### What failed

![gallery_10_negatives.png](figures/gallery_10_negatives.png)

*Left: repeat-pass coherence sits at the noise floor and the stable-scatterer control does not clear its own bias floor — so we cannot separate true decorrelation from our own limitation, and claim neither. Right: "a uniform canopy should score higher" holds on the date that feeds the index (ρ −0.631) and **fails** on an independent date (−0.168). We report the failure rather than quote the circular version.*  *(Kaggle: insert `gallery_10_negatives.png` here)*

- **Per-farm crop labels do not survive an independent rebuild.** Against a Sentinel-2 + Sentinel-1
  map, Cohen's κ = **+0.103** — negligible. The village mix is well constrained; the individual farm
  label is not, and we say so rather than present the map as more certain than it is.
- **Absolute radiometry is uncalibrated** (≈ +17 dB offset). ESA's EDAP assessment notes Capella's
  absolute accuracy is not declared while relative accuracy is good — exactly what we observe. Every
  downstream quantity is a difference or a within-crop rank, so the product survives it, and that is
  verified rather than asserted.

## 5. Why X-band was worth it, measured

![gallery_11_why_xband.png](figures/gallery_11_why_xband.png)

*At 1.2 m the median farm is **95.2%** uncontaminated interior; at 10 m that falls to **63.3%** and a fifth of these farms become more than half edge-contaminated — the median parcel here is 0.27 ha. Over the crop-forming window Sentinel-2 offered **19 revisits and 0 usable ones**. Every Capella acquisition is usable regardless of cloud.*  *(Kaggle: insert `gallery_11_why_xband.png` here)*

**Reproducibility.** The public notebook runs from a fresh kernel and its final cell **asserts** that
it reproduces the submitted `submission.csv` exactly. A 19-check ship gate verifies schema, ranges,
units and deliverables; a separate gate asserts that every number quoted here matches the shipped
artefacts, so this text cannot drift from the data.
