# R2 RESEARCH LOG

Append-only. Every investigative move, what it returned, and what it changes in the plan.
Format: `[#] date — MOVE → FINDING → SO WHAT`.
Session 1 = 2026-07-31.

---

## Phase A — Grounding on the delivered data (local, no web)

### [A1] Enumerate the R2 data folder
**Move:** `find` + `du` over `data/`.
**Finding:** 4 Capella SLC folders (441–742 MB each, ~2.1 GB total), `Farm_boundaries_shp/Sokhda_Farms.*`,
`Village_Shp/Sokhda_Village.*`. **No `round1_crop_classification.csv`.** Each SLC folder has the SLC tif, a
geocoded preview tif, and `*.json` / `*_digest.json` / `*_extended.json`.
**So what:** (a) We must supply the crop map ourselves. (b) The dataset description's "4 villages" is wrong —
the files are a single village, Sokhda, matching the Overview's "966 farms across 1 village".

### [A2] Read the shapefiles
**Move:** pyshp read of both shapefiles; polygon areas computed in EPSG:32643.
**Finding:** 966 farm polygons, fields `FID, id, ID_1, VILLAGE`; every record `ID_1=22`, `VILLAGE='Sokhda'`.
Village shapefile: 1 polygon, `ID=22`, `VILLAGE='Sokhda'`.
Areas — farms total **447.9 ha**; median **0.276 ha**, mean 0.464, min ~0, max 3.49; **37% < 0.2 ha,
68% < 0.5 ha**. Village polygon **1174.1 ha**. CRS geographic WGS84 (`GCS_WGS_1984`).
**So what:** Smallholder fragmentation dominates. The required spatial join is confirmatory only (village
is already an attribute) but we still perform it — the rubric explicitly awards it. Also: a few polygons
have ~0 area → need a degenerate-geometry guard so no farm is dropped (coverage = 10 rubric points).

### [A3] Read Capella `*_extended.json` per scene
**Move:** parse `collect.image` / `collect.radar`.
**Finding:** all stripmap, HH, left-looking, ENL 1.0, azimuth/range looks 1.0.
Center incidence **35.244° / 28.768° / 28.692° / 31.528°** for Jun06 / Jun19 / Aug14 / Oct13.
Scale factors **0.00212186 / 0.00236205 / 0.00198903 / 0.00136443**. Ground range res 1.15–1.38 m,
ground azimuth res 1.23 m. Pixel spacing 0.735 m × 1.07–1.28 m.
**So what:** Three things.
1. **Incidence angle varies by 6.6° across dates.** Any multi-temporal comparison *must* be
   incidence-normalized or the "temporal trend" is partly a geometry artefact. Non-negotiable.
2. **Jun-19 and Aug-14 differ by only 0.076° in incidence** — near-identical geometry. That is the one pair
   where repeat-pass interferometric coherence is even worth attempting.
3. ~1.2 m resolution → a median 0.276 ha plot holds ~2000 resolution cells. Within-field statistics are
   well-sampled; this is the strongest technical card we hold.

### [A4] Check scene coverage of Sokhda
**Move:** read the geocoded preview tifs, transform bounds to EPSG:4326, compare to village bbox.
**Finding:** all four previews span ~73.021–73.216 E, 22.286–22.465 N. Village bbox
(73.133–73.180 E, 22.408–22.442 N) is **fully inside all four**.
**So what:** 100% coverage, all dates, all farms. R1's crippling coverage problem does not exist here.
Every one of the 966 farms gets a real 4-date measurement.

### [A5] Link Sokhda to the Round-1 village index
**Move:** read R1 `villages_clean.shp` records.
**Finding:** **record ID 22 = "Sokhda"** — the exact village of Round 2.
**So what:** ★ The single biggest strategic finding. R1's exact reconstruction gives Sokhda's true crop
areas: Rice 73.33, Cotton 297.08, Maize 41.42, Bajra 65.12, Groundnut 213.93 ha (total 690.90 ha).
Cotton + groundnut = 74% of cropped area. This becomes a hard area constraint on the crop assignment.
Caveat: digitized farms total 447.9 ha ≈ 65% of the 690.9 ha cropped area, so the constraint is applied as
*proportions*, rescaled — stated openly in the writeup.

---

## Phase B — Literature and technical research (web)

### [B1] X-band SAR for crop biomass / temporal monitoring
**Move:** search — TerraSAR-X HH backscatter crop biomass temporal signature.
**Finding:** Short wavelengths (X, Ku, Ka) are **poorly correlated with LAI and total biomass**; the X-band
signal **saturates early** with crop parameters — X-band "is not the optimal frequency to monitor crop
growth on crops with significant biomass" (Bouman and successors). HH/HV backscatter shows strong soil
moisture sensitivity (~12.6–13.4 dB per cm³/cm³ at HH for biomass < 1 kg/m²). Multitemporal TerraSAR-X does
successfully track sugarcane and grassland development.
**So what:** ⚠ This kills the naive index. **"Brighter = healthier" is physically wrong at X-band.** We must
build the index on what X-band *is* good at: canopy **structure** and roughness, **dielectric/moisture**
state, **temporal change**, and — with 1.2 m pixels — **spatial uniformity and texture**. And we should say
this explicitly in the writeup: knowing why the obvious index is wrong is exactly the "Technical Soundness"
signal a judge is looking for.
Sources: [Bouman/X-band saturation + grassland](https://mdpi.com/2072-4292/6/10/10002/htm) ·
[Sugarcane TerraSAR-X](https://pmc.ncbi.nlm.nih.gov/articles/PMC3230945/) ·
[Dual-pol TerraSAR-X biomass](https://link.springer.com/article/10.1007/s41064-019-00076-x)

### [B2] X-band → rice yield specifically
**Move:** search — X-band high-res SAR growth and yield in paddy rice. (Direct fetch 403'd; used abstract.)
**Finding:** **Panicle biomass is best correlated with X-band σ⁰.** X-band is described as promising for
*direct assessment of rice grain yield*, while having limited capability for whole-canopy variables except
in very early growth stages.
**So what:** ★ A gift for the yield component. X-band's weakness for total biomass is paired with a
strength for the *grain-bearing* structure — which is precisely what a yield estimate wants. This gives a
citable physical justification for an X-band-based yield proxy rather than an arbitrary one.
Source: [Potential of X-Band for growth and yield in paddy rice](https://www.mdpi.com/2072-4292/6/7/5995)

### [B3] Single-polarization (HH-only) vegetation indices
**Move:** search — single-pol SAR vegetation index, HH only.
**Finding:** The classical RVI needs HH+VV+HV; DpRVI needs a dual-pol covariance matrix. Dual-pol is
"significantly more effective"; **single-pol has no established radar vegetation index**.
**So what:** Confirms there is no off-the-shelf formula to copy — which is precisely why the competition
says "no prescribed formula". Our index must be *constructed*, and the fact that no standard exists is a
point in favour of the "Methodological Creativity" score. Our substitute axes for the missing polarimetric
information: **temporal** (4 dates), **spatial/textural** (1.2 m), and **interferometric** (SLC phase).
Sources: [DpRVI Sentinel-1](https://www.sciencedirect.com/science/article/abs/pii/S0034425720303242) ·
[Enhanced PRVI](https://www.mdpi.com/2072-4292/16/23/4476)

### [B4] Interferometric coherence for agriculture
**Move:** search + fetch — repeat-pass coherence as a vegetation/crop index.
**Finding:** Coherence and NDVI move **inversely**, approximately **linearly, R² ≈ 0.62** over farmland;
coherence works as a **proxy to fill NDVI gaps** under cloud. Relationship depends on crop type, phenology
and irrigation. X-band temporal decorrelation has been characterised at 4/7/11/15-day baselines, with
class- and growth-condition-dependent behaviour. C- and X-band repeat-pass coherence is established for
crop-type mapping.
**So what:** Coherence is a legitimate, literature-backed "health/vegetation" axis and the rubric names
"temporal coherence" explicitly. **But our shortest baseline is 56 days (Jun19→Aug14) at X-band**, far
beyond the 4–15 day baselines the literature uses. Expect near-total decorrelation over growing crops.
That is still informative — *low coherence = actively growing vegetation, high coherence = bare / fallow /
harvested / built* — which is a real signal. Plan: attempt it on the one geometrically-matched pair, and
report the result honestly whichever way it lands. A well-documented negative result scores better than a
silent omission.
Sources: [Coherence↔NDVI linear relationship, R²≈0.62](https://pmc.ncbi.nlm.nih.gov/articles/PMC7174376/) ·
[S1 coherence as vegetation index](https://www.sciencedirect.com/science/article/pii/S0034425722003169) ·
[C- and X-band repeat-pass coherence for crop mapping](https://ieeexplore.ieee.org/document/10281890/)

### [B5] GLCM texture on SAR for field heterogeneity
**Move:** search — GLCM texture SAR crop heterogeneity/health.
**Finding:** GLCM second-order texture on SAR is well-established and materially improves crop
classification; texture matters most where fields are **small and fragmented** and coarse imagery cannot
resolve them. Window size and metric choice drive performance.
**So what:** Directly applicable — Sokhda is exactly the "small, fragmented fields" case, and we have 1.2 m
data instead of the 10–20 m the literature struggles with. Round 1 independently found **entropy** to be the
best-performing texture metric (groundnut radar-entropy alone was worth 4.39 MSE points), so we start from
entropy rather than re-deriving it. Texture must be computed on **unfiltered** imagery — speckle filtering
destroys the very second-order statistics being measured.
Sources: [GLCM crop classification](https://peerj.com/articles/cs-536/) ·
[S1 GLCM object-level](https://www.mdpi.com/2073-4395/10/6/845) ·
[SAR+optical texture fusion](https://pmc.ncbi.nlm.nih.gov/articles/PMC7648193/)

### [B6] Coefficient of variation as a crop indicator
**Move:** search — CV of SAR backscatter, field uniformity, precision agriculture.
**Finding:** CV is an established unitless SAR crop metric — high CV = strong backscatter variation
(planting/growth/harvest cycles), low CV = static. Used in NISAR's cropland-extent algorithm for crop/
non-crop classification. Within-field variability is examined by comparing backscatter against crop
parameters at multiple points; heterogeneity knowledge is "essential for effective field management".
**So what:** Gives us a citable basis for **two distinct** CV features, which must not be confused:
- **Spatial CV** *within* a farm on one date → canopy uniformity. Low spatial CV = uniform canopy.
  This maps word-for-word onto the rubric's "fields with visibly stronger/**more uniform** canopy structure
  score higher".
- **Temporal CV** across the 4 dates per farm → cropping dynamism; near-zero temporal CV means nothing
  ever grew there (fallow/abandoned), which is a red flag, not a healthy field.
Sources: [CV for crop area classification](https://www.sciencedirect.com/science/article/abs/pii/S0303243417303318) ·
[CV approach, smallholder Kenya](https://www.mdpi.com/2073-445X/15/3/371) ·
[NISAR cropland algorithm](https://doi.org/10.3390/rs17061094) ·
[Within-field variability, S1](https://www.mdpi.com/2072-4292/11/13/1569)

### [B7] Rice phenology backscatter signature
**Move:** search — rice/cotton multitemporal SAR phenology, X-band HH.
**Finding:** Concrete numbers. HH is preferred for rice because it responds to the plant's **vertical
structure**. Backscatter is at **minimum during transplanting/flooding** (specular reflection off standing
water) — this minimum marks Start of Season. Reported range: **−22.0 to −17.7 dB at start of season**,
rising to a **−16.1 to −14.2 dB maximum at peak/heading**. Phenology stages (transplanting → vegetative →
reproductive → maturity) are separable from backscatter.
**So what:** Gives us a *quantitative expected trajectory* for rice, against which each farm's measured
4-date curve can be scored — rather than an arbitrary index. It also independently corroborates Round 1's
strongest empirical finding: the "rice flood dip" (VH_Aug − VH_Jun) was R1's single largest scalar gain
(193 → 164). Same physics, now with published dB values to cite. The R1 model's other locked signatures
(cotton still standing in October, groundnut on drier/lighter soils) carry over as priors too.
Sources: [X-band SAR ↔ rice LAI by phenological phase](https://doi.org/10.3390/rs11121462) ·
[SCATSAT-1 rice phenology dB values](http://meddiscoveries.org/articles/1034.html) ·
[RADARSAT-2 rice phenology](https://www.mdpi.com/2072-4292/10/2/340)

### [B8] Incidence-angle normalization
**Move:** search — incidence angle normalization, cosine method, gamma0.
**Finding:** σ⁰ follows a cosine law with exponent N describing the strength of the angular dependence;
normalization is to a reference angle, typically swath centre. Over Sentinel-1's 25–45° range, identical
targets differ by **several dB** purely from angle. Fixed-N normalization is standard but flawed: the
angular dependence **changes with crop growth stage**, so "dynamic N" methods keyed on NDVI or a
polarization ratio outperform fixed N.
**So what:** With a 28.7°–35.2° spread across our four dates, uncorrected angular effects are the same
order of magnitude as the crop signal we are trying to measure. Plan: normalize to a reference angle
(31.5°, the October scene — our anchor date) using a cosine-N law; use γ⁰ (which absorbs part of the
angular dependence by construction) as the working quantity; and **empirically fit N from the data itself**
over stable targets, rather than assuming a textbook value. Report the fitted N and the before/after effect
— that is a strong, checkable "Technical Soundness" exhibit.
Sources: [Dynamic cosine method, C-band agriculture](https://doi.org/10.3390/rs16203838) ·
[Dynamic cosine for maize, NDVI-based](https://www.mdpi.com/2072-4292/13/15/2856) ·
[Normalizing local incidence angle, S1](https://pdfs.semanticscholar.org/5097/a317754b74b1b92345e58855262b94dda754.pdf)

### [B9] ★★ Capella radiometric calibration — the authoritative formula
**Move:** Vendor docs were vague ("a constant scaling factor... to sigma nought"). ESRI's page and the
SNAP forum thread had no formula. Fetched the **ESA EDAP "Technical Note for Capella Data Assessment"
(Issue 1.0)** PDF and text-extracted it locally with pypdf.
**Finding — verbatim from the ESA technical note, SLC product table:**

> *"Complex numbers: RADAR backscatter: **β₀ = sc · |pixel|²**, where sc is a Scale Factor annotated in the
> products. Measured Quantity Units m²/m² (power)."*

Also from the same document: absolute **radiometric accuracy is not declared** in the product; the measured
NESZ is *lower* than the annotated values, "suggesting a possible residual error in the absolute
radiometric calibration"; **relative** radiometric calibration accuracy is assessed as good; geolocation
accuracy ≈ 1.3–1.7 m std (stripmap); slant-range res 0.5–0.75 m, azimuth 1.0–1.2 m.

**So what:** Two consequences, one of them a correction to our own code.
1. ⚠ **Round 1's `prep_stack.py` line 48 computes `beta0 = |z|² · scale²`, squaring the scale factor.** The
   correct form is `β₀ = scale · |z|²`. Because the scale factor differs per scene, the error is not a
   harmless global constant: it imposes a **per-date offset of 10·log₁₀(scale)** — −26.73, −26.27, −27.01,
   −28.65 dB for Jun06/Jun19/Aug14/Oct13. The *relative* date-to-date distortion is up to **2.4 dB**, which
   is the same magnitude as the crop-growth signal itself. It also explains R1's implausibly low ~−18/−19 dB
   cropland means. **This must be fixed for R2, where the temporal trajectory is the whole deliverable.**
   Then σ⁰ = β₀·sin θ and γ⁰ = β₀·sin θ / cos θ = σ⁰ / cos θ.
2. **"Absolute accuracy not declared, relative accuracy good"** is a *citable justification* for building a
   **relative** health index and a **relative** yield estimate — which is exactly what the competition asks
   for. This turns a data limitation into a defended design decision.
Sources: [ESA EDAP Technical Note for Capella Data Assessment](https://earth.esa.int/eogateway/documents/20142/37627/Technical%20Note%20for%20Capella%20Data%20Assessment.pdf) ·
[Capella scaling GEO images (dB = 10log10(DN/SC) for GEO)](https://support.capellaspace.com/scaling-geo-images-in-qgis) ·
[ESRI Capella GEO workflow](https://doc.esri.com/en/arcgis-pro/latest/help/analysis/image-analyst/capella-geo-workflow.html)

### [B10] SAR-based yield estimation frameworks
**Move:** search — SAR backscatter yield estimation, growth-curve integration, seasonal accumulation.
**Finding:** Established approaches: (a) fit a **logistic curve** to the SAR time series and use its
parameters as growth descriptors; (b) **accumulate the growth curve over the season** and regress
accumulated + current values against yield, comparing nearby fields to remove agro-climatic and soil bias;
(c) assimilate SAR into a process crop model (e.g. ORYZA2000). District-level yield simulation accuracy of
86–91%, block-level 82–97%, is reported.
**So what:** Two directly transferable ideas. **(1) Season-integrated backscatter, not a single date** — the
accumulated growth curve is the yield-relevant quantity, and with 4 dates we can form a trapezoidal
time-integral. **(2) Neighbour-relative comparison** — comparing each farm against nearby farms of the same
crop removes soil and agro-climatic bias. That is the correct way to build a *relative* yield index without
ground truth, and it is a published technique rather than an invention of ours.
Sources: [ORYZA + time-series SAR for yield](https://www.researchgate.net/publication/334741937_INTEGRATING_TIME-SERIES_SAR_DATA_AND_ORYZA_CROP_GROWTH_MODEL_IN_RICE_AREA_MAPPING_AND_YIELD_ESTIMATION_FOR_CROP_INSURANCES) ·
[Wheat productivity indicators from S1 time series](https://doi.org/10.3390/rs12152385) ·
[Patch-based DL/ML yield from SAR](https://www.sciencedirect.com/science/article/abs/pii/S0168169924007312)

### [B11] Yield/health estimation without ground truth
**Move:** search — relative yield potential, unsupervised, no ground truth, plausibility validation.
**Finding:** Established that unsupervised/relative approaches are legitimate: clustering works on
*relative* membership and needs no absolute indicators; scale-transfer methods (e.g. QDANN) map subfield
yield with no subfield labels; potential yield is commonly anchored to **previous-season official yield
statistics** rather than field measurements.
**So what:** Validates the intended design — a *relative* index anchored to public district yield
statistics — as accepted practice, not a workaround. Anchoring to Vadodara district APY yields also gives
the "Validity & Plausibility" section a concrete external check: our village-aggregate production must land
in the right ballpark against published district figures.
Sources: [Subfield yield mapping without ground truth](https://www.sciencedirect.com/science/article/abs/pii/S003442572400453X) ·
[Unsupervised satellite features for maize yield](https://www.mdpi.com/2072-4292/17/21/3641)

### [B12] 2025 Kharif season context, Gujarat
**Move:** search — Gujarat/Vadodara 2025 monsoon rainfall; Gujarat kharif crop calendar.
**Finding:** Kharif sowing follows monsoon onset, roughly July–August, harvest September–October; in
Gujarat cotton and groundnut sowing concentrates in the **first two weeks of July**, and cotton + groundnut
dominate state kharif acreage. For 2025: IMD's seasonal forecast was 88% of LTA (deficit); the **Gujarat
region deficiency reached 39% by 31 July** (Saurashtra/Kutch 49%), but heavy July rain cleared the
accumulated deficit and August/September came in **above** normal (108% and 115% of LPA).
**So what:** ★ This is the interpretive backbone for the whole season narrative, and it aligns with our
acquisition dates almost perfectly:
- **Jun 06 and Jun 19 are pre-monsoon / pre-sowing.** They are *not* crop observations — they are a
  **bare-soil reference**: per-farm soil roughness and baseline dielectric state, free of vegetation. That
  is enormously useful, because subtracting a per-farm bare-soil baseline removes the static soil/roughness
  component from the later dates. This reframing turns two "wasted" early dates into the calibration
  reference for the other two.
- **Aug 14 is peak vegetative**, following the dry-then-wet July — a genuine crop-condition observation.
- **Oct 13 is post-monsoon**: rice/maize/bajra harvested or senescing; cotton and groundnut still standing.
- The dry-July / wet-August-September pattern is a real, citable driver of within-village variation
  (late sowing, waterlogging in low-lying plots) — which is where the DEM comes in.
Sources: [IMD Monsoon 2025 salient features](https://internal.imd.gov.in/section/nhac/dynamic/spldaily.pdf) ·
[IMD monsoon information](https://mausam.imd.gov.in/responsive/monsooninformation.php) ·
[Gujarat kharif sowing — cotton & groundnut dominate](https://www.prokerala.com/news/articles/a1794041.html)

---

## Phase C — Researcher lineage review (ORCID, session 2 = 2026-08-01)

User supplied two ORCIDs as "actively working in this kind of problem". Both resolved via the ORCID public
API (`pub.orcid.org/v3.0/{id}/record`) — the HTML pages are JS-rendered and return nothing to a fetcher.

### [C1] ORCID 0009-0003-2879-0550 → **Haixia Bi**
**Move:** ORCID public API record dump.
**Finding:** Xi'an Jiaotong University (current); previously University of Bristol, University of Derby.
PhD Xi'an Jiaotong; earlier Ocean University of China. **27 indexed works, 2016–2026.** Corpus is
overwhelmingly **PolSAR image classification under label scarcity**, plus remote-sensing detection/fusion:

| Year | Work | Venue | DOI |
|---|---|---|---|
| 2017 | Unsupervised PolSAR Image Classification Using Discriminative Clustering | TGRS | 10.1109/tgrs.2017.2675906 |
| 2019 | A Graph-Based Semisupervised Deep Learning Model for PolSAR Image Classification | TGRS | 10.1109/tgrs.2018.2871504 |
| 2019 | An Active Deep Learning Approach for Minimally Supervised PolSAR Image Classification | TGRS | 10.1109/tgrs.2019.2926434 |
| 2020 | PolSAR Image Semantic Segmentation With 3D DWT and Markov Random Field | IEEE TIP | 10.1109/tip.2020.2992177 |
| 2022 | PolSAR Classification Based on Robust Low-Rank Feature Extraction and MRF | GRSL | 10.1109/lgrs.2020.3034700 |
| 2023 | Self-Distillation-Based Polarimetric Classification with Noisy and Sparse Labels | Remote Sensing | 10.3390/rs15245751 |
| 2024 | Polarimetry-Inspired Contrastive Learning for Class-Imbalanced PolSAR Classification | TGRS | 10.1109/TGRS.2024.3403100 |
| 2025 | Learning with noisy labels via Mamba and entropy KNN framework | Applied Soft Computing | 10.1016/j.asoc.2024.112596 |
| 2025 | ECP-Mamba: Efficient Multiscale Self-Supervised Contrastive Learning with SSM for PolSAR | TGRS | 10.1109/TGRS.2025.3601583 |
| 2025 | PolSAR Classification With Complex-Valued Diffusion Model as Representation Learners | TAES | 10.1109/TAES.2025.3572877 |
| 2026 | CV-CPKAN: Complex-Valued Convolutional Kolmogorov–Arnold Framework for PolSAR | Remote Sensing | 10.3390/rs18020330 |
| 2026 | GHSS-Net: Graph-Enhanced Hybrid Self-Supervised Framework for PolSAR | TAES | 10.1109/TAES.2025.3644845 |
| 2026 | Complex-Valued Source-Free Domain Adaptation for PolSAR Classification | TGRS | 10.1109/TGRS.2026.3663159 |
| 2026 | RectMamba: SSM with entropy-divergence framework for noisy label rectification | Neurocomputing | 10.1016/j.neucom.2025.131998 |

(Remainder: hyperspectral DWT, rotated object detection, pansharpening QA, salient object detection,
multimodal land-cover fusion, phase unwrapping, human activity recognition — peripheral to us.)

### [C2] ORCID 0009-0004-6547-508X → **Zuzheng Kuang**
**Move:** same.
**Finding:** PhD student, Xi'an Jiaotong University. 8 works, 2023–2026, **all co-authored inside Bi's
group** — the complex-valued / self-supervised PolSAR sub-line: CV-CPKAN, CV diffusion representation
learners, ECP-Mamba, GHSS-Net, polarimetry-inspired contrastive learning, CV self-supervised with attention
(IGARSS 2023), diffusion-based generative few-shot PolSAR (IGARSS 2024).
**So what:** Kuang is Bi's student, not an independent line. Treat as **one lab, one research programme**.

### [C3] ★ Transfer assessment — what this lineage actually gives us
**Move:** map their programme onto our problem statement, honestly, including what does *not* transfer.

**The mismatch, stated up front:** their entire corpus operates on **PolSAR** — full/dual-polarimetric
covariance or coherency matrices (T3/C3), Cloude–Pottier decomposition, complex-valued *polarimetric*
channels. **We have single-pol HH.** There is no covariance matrix, no scattering decomposition, no
polarimetric feature vector. None of their *architectures* can be lifted as-is. Also: none of their work is
agricultural — no crop, yield or phenology paper in either record.

**The match, which is the real point:** their programme is not fundamentally "about polarimetry", it is
about **classifying SAR data when labels are scarce, noisy, or absent** — which is *exactly* our situation
(966 farms, zero labels of any kind, no ground truth). Five concrete, citable transfers:

| # | Their contribution | Our transfer | Confidence |
|---|---|---|---|
| **T1** | **Unsupervised discriminative clustering** [TGRS 2017]: physics-based label *initialisation* (Cloude–Pottier + K-Wishart) → discriminative softmax-regression classifier → MRF smoothness → alternate-minimise an energy function → converged labels *are* the classification | Identical three-part skeleton with the physics swapped: initialise crop labels from the **phenological trajectory prior** (B7) instead of Cloude–Pottier, refine with a discriminative classifier, regularise with MRF over the **farm adjacency graph**, iterate. Gives our crop step a **published unsupervised framework** instead of an ad-hoc heuristic | **High — strongest single transfer** |
| **T2** | **MRF spatial regularisation** [TIP 2020, GRSL 2022, TGRS 2017] | Neighbouring plots in an Indian village are highly correlated in crop choice (shared irrigation, block sowing). MRF / graph smoothing over farm adjacency is directly justified, cheap (`scipy.sparse`), and improves both crop map and health map. Also pairs with the Moran's I validation already planned | **High** |
| **T3** | **Graph-based semi-supervised learning** [TGRS 2019] | We can generate a *small set of high-confidence pseudo-labels* (e.g. unmistakable rice flood-dip plots) and **propagate** them over a farm graph built from feature similarity + spatial adjacency. ~30 lines of scipy; turns "no labels" into "very few labels" | **Medium-high** |
| **T4** | **Noisy-label rectification** [Neurocomputing 2026 RectMamba; ASC 2025 entropy-KNN; Remote Sensing 2023 self-distillation with noisy/sparse labels] | Our area-constrained crop assignment produces **inherently noisy pseudo-labels**. Their entropy/KNN-consistency rectification is a small post-step: flag farms whose features disagree with their assigned class's neighbourhood, re-assign, re-check. Directly on-point and easy to defend | **Medium-high** |
| **T5** | **Complex-valued representation learning** [CV-CPKAN 2026, CV diffusion 2025, CV-SSL IGARSS 2023] | We hold **SLC complex** data; most teams will take `\|z\|` and discard phase on line one. Their programme is the citable argument that **phase carries exploitable structure**. We cannot use their CV networks (no polarimetric channels) but we take the *principle* → interferometric/sub-aperture coherence and complex-domain statistics (see [D1]) | **Medium — principle, not architecture** |

**So what:** this lineage does not hand us a crop model. It hands us the **methodological spine for
label-free classification**, which is the hardest unsolved part of R2. Framing for the writeup:
*"we transfer the label-scarce SAR classification methodology developed for PolSAR (Bi et al., TGRS
2017/2019, TIP 2020) to single-polarisation X-band agricultural time series, substituting phenological
physics for polarimetric physics at the initialisation step."* That is a defensible research lineage rather
than a bag of heuristics — and it is honest about the single-pol limitation instead of hiding it.
Sources: [Unsupervised PolSAR discriminative clustering](https://ieeexplore.ieee.org/document/7880590/) ·
[Robust low-rank + MRF (preprint)](https://ar5iv.labs.arxiv.org/html/2009.05942) ·
[Self-distillation, noisy/sparse labels](https://www.mdpi.com/2072-4292/15/24/5751)

---

## Phase D — New method leads (gaps in PLAN.md, verified this session)

### [D1] ★ Zero-/short-baseline and sub-aperture coherence — a way to keep the coherence axis alive
**Move:** search — sub-aperture / split-spectrum / zero-baseline coherence, single image.
**Finding:** Largest observed InSAR coherence occurs for **same-day pairs**; vegetation decorrelates
progressively with temporal baseline, and higher frequencies (X-band) lose coherence fastest over dense
vegetation. Separately, a 2026 arXiv line ("Beyond Backscatter: InSAR coherence from detected SAR images")
works on recovering coherence-like information without a conventional interferometric pair.
**So what:** Our repeat-pass pair is 56 days at X-band — [B4] already predicts near-total decorrelation, and
this confirms it. **But the SLC is complex, so we can split one acquisition into azimuth sub-apertures (or
range sub-bands) and form a coherence with a *zero* temporal baseline.** That measures *spatial/structural*
decorrelation only — volume scattering from a canopy decorrelates between sub-looks, a bare or harvested
field does not. This gives us a coherence-family feature **on every one of the four dates**, immune to the
56-day problem, and it directly exploits the phase everyone else discards [T5]. Cost: moderate (FFT split +
complex cross-correlation). Report the repeat-pass attempt *and* this as the fallback that works.

### [D2] ★★ Water Cloud Model — the missing physical backbone for the yield step
**Move:** search — WCM inversion, S1, vegetation water content, bare-soil reference.
**Finding:** WCM (semi-empirical, canonical) splits total backscatter into a vegetation-cloud term plus a
**two-way-attenuated soil term**: `σ⁰_total = σ⁰_veg(V1,V2,θ) + τ²(V2,θ)·σ⁰_soil`. Widely inverted on
Sentinel-1 for LAI, vegetation water content (VWC), and soil moisture; modified variants add soil–vegetation
interaction and first-order scattering terms. VOD retrievals build on it with pixel-based soil parameters.
**So what:** PLAN.md's health index is a *statistical composite* with no physical model behind it — that is
its weakest point for a "Technical Soundness" rubric. WCM fixes this, and **our data is unusually well
suited to inverting it**: the standard blocker is that the soil term is unknown, and **Jun 06 + Jun 19 are
pre-monsoon, pre-sowing bare soil [B12]** — i.e. a *direct per-farm measurement of σ⁰_soil*. That converts
an under-determined inversion into a constrained one. Output is a per-farm **vegetation water content /
optical-depth proxy**, which is a physically meaningful biomass quantity to drive yield — far stronger than
"z-scored backscatter". Caveats to state: single-pol and only 2 in-season dates ⇒ fit V1,V2 with fixed
literature coefficients per crop, treat output as *relative* VWC, and keep the June soil term as a prior not
a constant (soil moisture changes between June and August).
Sources: [Crop water content, S1+S2 WCM](https://pmc.ncbi.nlm.nih.gov/articles/PMC6767680/) ·
[Modified WCM soil moisture over partial vegetation](https://www.sciencedirect.com/science/article/abs/pii/S0303243418303015) ·
[First-order backscatter in WCM for LAI/SM, dual-pol S1](https://www.sciencedirect.com/science/article/abs/pii/S0034425723003073) ·
[S1 vegetation optical depth over ISMN](https://www.tandfonline.com/doi/full/10.1080/17538947.2025.2555412)

### [D3] K-distribution shape parameter — a principled replacement for raw spatial CV
**Move:** search — K-distribution order/shape parameter as SAR texture measure.
**Finding:** Under the multiplicative model, the K-distribution efficiently characterises SAR signal
statistics; its **shape/order parameter α** is an established heterogeneity measure. Low α ⇒ very
heterogeneous (urban); high α ⇒ homogeneous (pasture, certain crops). Used to stratify scattering classes
into heterogeneity sub-categories.
**So what:** PLAN.md's "uniformity" component is spatial CV, which conflates **speckle** with **real scene
texture** — a serious flaw, because with ENL 1.0 single-look data speckle *dominates* CV. The
K-distribution α **separates the two by construction** (speckle is the Gamma part, scene texture is the
Gamma-modulating part). With ~2000 looks per median plot [A3] we have ample samples to fit α per farm per
date by method-of-moments. This is a strictly better, more citable "canopy uniformity" feature than CV, and
costs ~15 lines. Keep CV as the interpretable companion, report both.
Sources: [Heterogeneous SAR texture via MRF / K-distribution](https://ieeexplore.ieee.org/document/861636/) ·
[Texture feature selection for crop discrimination, SAR](https://www.sciencedirect.com/science/article/abs/pii/S0034425796001563)

### [D4] Self-supervised / representation learning on the farm time series — feasibility triage
**Move:** search — self-supervised contrastive learning for SAR/SITS crop classification without labels.
**Finding:** Established and active: contrastive pre-training for satellite image time series (MoCo-style),
TS2Vec-style contextual-consistency encoders, time-series-specific augmentations (bidirectional flipping,
channel permutation, crop-and-resize, random smoothing), optical↔SAR cross-modal contrastive bridging, and
geospatial foundation models for label-limited crop mapping.
**So what:** Legitimate as a *method family* and it rhymes with the Bi lineage [ECP-Mamba, GHSS-Net], **but
our n is 966 farms × 4 dates**. That is far too small to train a contrastive encoder that beats a
well-designed physical feature set, and a deep model here would be exactly the over-engineering that costs
us documentation time. **Verdict: not the primary method.** Carry it as a *comparison arm* — embed farm
patch stacks with a small unsupervised encoder, cluster, and report agreement/disagreement against the
physical model. A documented "we tried it, here is why the physical model wins on 966 samples" is worth
rubric points; a half-trained network is not.
Sources: [SSL pre-training for large-scale crop mapping, S2 SITS](https://www.sciencedirect.com/science/article/abs/pii/S0924271623003386) ·
[Optical↔SAR contrastive feature extraction for crop classification](https://www.sciencedirect.com/science/article/pii/S0924271622003136) ·
[SSL + geospatial foundation models for crop biophysical parameters](https://www.sciencedirect.com/science/article/abs/pii/S0034425725002299)

### [D5] Competition page and rubric — BLOCKED
**Move:** WebFetch of the Kaggle overview URL.
**Finding:** Kaggle competition pages are JS-rendered; the fetcher returns only the page `<title>`.
No rubric, no deadline, no submission schema recovered. PLAN.md cites a `00_BRIEF.md` that **is not present
in this working directory**.
**So what:** ⚠ Open blocker [O8]. All rubric-weighted decisions (how much effort to spend on writeup vs
modelling, exact submission columns, deadline) are currently running on PLAN.md's second-hand summary.
Need the user to paste the overview/rules/evaluation text or supply `00_BRIEF.md`.

---

## Phase E — Scope resolved + full-text extraction (session 3 = 2026-08-01)

### [E1] ★★ Competition scope, rubric and deadline — [D5]/[O8] CLOSED
**Move:** user pasted the full Overview / Description / Submission / Evaluation text.
**Finding — the parts that change our plan:**
- **Deadline: Aug 13 2026, 00:00 GMT+5:30** ⇒ effective working window is **Aug 1–12, ~11 days**.
- Judged **by a human panel against the published rubric — no leaderboard, no metric.**
- **Rubric (100):** Technical Soundness **25** · Methodological Creativity **20** · Validity &
  Plausibility **20** · Village-Level Aggregation & Coverage **10** · Documentation & Reproducibility
  **15** · Presentation Quality **10** · Required Elements (pass/fail gate).
- CSV columns confirmed exactly: `village_id, farm_id, crop_type, health_index, yield_estimate_to_date`;
  crop_type ∈ {Rice, Cotton, Maize, Bajra, Groundnut}.
- Deliverable is a **Kaggle Writeup ≤4 pages** + **media gallery with a required cover image** + **public
  notebook** + project link. Private attached resources auto-publish after the deadline.
- **Aux data explicitly permitted and explicitly rewarded** under Creativity — "weather, optical (S2,
  Landsat), DEM, soil, public agricultural statistics" — provided Capella "remains the primary and central
  dataset… auxiliary data should refine or complement it, not replace it."
- R1 crop map: "carry forward"; but **"If you did not participate in Round 1, or your Round 1 crop map
  needs refinement, you're free to (re)build a crop classification step"** — and it is explicitly "a means
  to an end for this round, not the primary deliverable."
- Confirms 966 farms, **1 village**, 5 crops, HH pol, the 4 dates — [A1]'s "4 villages" discrepancy is
  settled in our favour, no host email needed [O4 closed].
- Judges: GalaxEye (host), Deb Jyoti Pal, Rahulsundar. Top teams advance to the Goa finale, Sep 2–3.

**So what:** four decisions change.
1. **55 of 100 points are execution, not modelling** (Validity 20 + Docs 15 + Presentation 10 + Aggregation
   10). `PLAN.md` already said this; the rubric now proves it. The last three days are writing, not
   modelling, and that is not a concession — it is where the points are.
2. **Aggregation (10 pts) is nearly free**: one village, full coverage on all four dates [A4]. All 966 farms
   processed + one clearly-stated aggregation rule = 10 points. **Do not lose a single farm** — the
   degenerate-polygon guard [A2] is now worth real points.
3. ⚠ Technical Soundness names "**polarimetric structure**" as a scorable physics axis — **impossible at
   single-pol HH**. Do not fake it. State the limitation explicitly and show the three substitute axes we
   *do* exploit: temporal trajectory, spatial/textural, interferometric/complex [B3]. A judge who reads
   "we cannot do polarimetry, here is what we did instead and why" scores that as soundness, not weakness.
4. **`PLAN.md`'s "hold Sentinel-2 NDVI back as validation-only" is now a partial mistake.** Aux integration
   is worth Creativity points *by name*. Resolution: use **DEM/TWI + IMD weather as refinement inputs**
   (uncontroversial, clearly "complementing" SAR), and keep **S2 NDVI as an independent witness only** —
   then say *why* in the writeup. That earns Creativity for the aux integration and Validity for the
   untainted cross-check, instead of trading one for the other.

### [E2] ★★ Bi et al. TGRS 2017 — full formulation extracted (P-B is now buildable)
**Move:** PDF supplied by user; text-extracted with pypdf.
**Finding — the complete model.** Loss over labels `Y` and classifiers `W`, both optimised:

```
E(Y,W|X) = Ec(Y,W|X) + Es(Y,W|X)                                        (1)

Ec = −Σ_i Σ_j (1/N_j)·1{y_i=j}·log[ e^{W_j^T x_i} / Σ_l e^{W_l^T x_i} ]  (4)   softmax/cross-entropy
     + α_c Σ_i Σ_j W_ij²                                                 (5)   L2 regulariser
Es = α_s Σ_i Σ_{j∈N(i)} S_ij                                             (6)   label smoothness
S_ij = |y_i − y_j| · exp( −‖v_i − v_j‖²₂ / 2σ )                          (7)
```

- `1/N_j` (count of pixels currently in class *j*) is a **class-imbalance correction** — deliberate, and
  important for us: Cotton is 43% of area and Maize 6% [A5].
- `v_i` = a feature that **changes sharply across edges** (they use Pauli components); `σ` = mean squared
  distance between adjacent features. Effect: smoothing is strong inside homogeneous regions and *released*
  across strong edges.
- **Optimisation = alternating minimisation.** Subproblem 1: fix `Y`, solve `W` by L-BFGS on the gradient
  `∇_{W_j}E = −Σ_i[ x_i( (1/N_j)1{y_i=j} − P(y_i=j|x_i;W) ) ] + 2α_c W_j` (10). Subproblem 2: fix `W`,
  solve `Y` — an MRF labelling problem, solved by **belief propagation** (graph cut also valid). Then
  **update `N_j`** and iterate.
- **Published hyperparameters:** `α_c = 5×10⁻⁵`; `α_s` best in **1–2**; **iteration number 2–3** (paper uses
  α_s=1, 3 iterations). Explicitly warns: α_s too large + too many iterations **erodes small/thin classes**
  (road CA fell 39.76% by iteration 5).
- Reported gain over the initialisation: +2.91% (SR alone) / **+6.45%** (SR+MRF) on Flevoland, +14.16% /
  **+24.32%** on Oberpfaffenhofen.

**So what:** P-B is fully specified and needs no deep learning. Our adaptation, stated precisely:
| Their term | Our substitution |
|---|---|
| pixel `i` | **farm polygon** `i` (N = 966, not millions — trivially fast) |
| 58-D feature from coherency matrix `T` | our farm feature vector: level, temporal Δ, season integral, spatial CV, K-dist α, GLCM entropy, sub-aperture coherence, DEM/TWI |
| Cloude–Pottier + K-Wishart initialisation | **phenological trajectory-agreement initialisation** [B7] + R1 area proportions [A5] |
| `N(i)` = 4/8-pixel neighbourhood | **farm adjacency graph** (shared boundary / centroid k-NN) |
| `v_i` = Pauli components | γ₀ trajectory vector — releases smoothing across genuine crop boundaries |
| belief propagation over an image lattice | BP or ICM over a 966-node graph — small enough that even exhaustive ICM converges instantly |
The class-imbalance term `1/N_j` and the area constraint [A5] are complementary, not redundant: one
balances the *loss*, the other constrains the *solution*. **⚠ Heed their warning** — cap α_s at ~1 and
iterations at 3, or Maize and Bajra (6% and 9% of area) will be smoothed out of existence.

### [E3] ★★ Water Cloud Model — X-band HH coefficients found (P-D is now buildable)
**Move:** El Hajj, Baghdadi, Zribi et al., *Soil moisture retrieval over irrigated grassland using X-band
SAR data*, Remote Sensing of Environment 176 (2016) 202–218. PDF supplied; extracted.
**Finding — the model and its fitted X-band parameters, verbatim:**

```
σ⁰_tot = σ⁰_veg + T²·σ⁰_sol                     (4)
σ⁰_veg = A·V1·cosθ·(1 − T²)                     (5)
T²     = exp(−2·B·V2·secθ)                      (6)
σ⁰_sol = C(θ)·exp(D·Mv)                         (7)
```
`V1,V2` vegetation descriptors; `θ` incidence; `Mv` volumetric soil moisture (Vol.%).

Fitted at **X-band, HH** (TerraSAR-X + COSMO-SkyMed, irrigated grassland), Table 5:

| V1=V2 | A_HH | B_HH | C_HH | D_HH | RMSE_HH |
|---|---|---|---|---|---|
| Biomass (kg/m²) | 0.0345 | 0.0995 | 0.0334 | 0.03971 | 0.85 dB |
| **VWC (kg/m²)** | **0.0438** | **0.1047** | **0.0324** | **0.03971** | 0.86 dB |
| Veg. height (m) | 0.1045 | 0.4314 | 0.0357 | 0.03971 | 0.79 dB |
| LAI (m²/m²) | 0.0205 | 0.0613 | 0.0338 | 0.03971 | 0.86 dB |
| FCOVER | 0.1021 | 0.3696 | 0.0355 | 0.03971 | 0.82 dB |
| NDVI | 0.0767 | 0.7944 | 0.0644 | 0.03971 | 0.76 dB |

Also: bare-soil sensitivity **D_HH = 0.172 dB per Vol.% (= 0.03971 linear), R² = 0.87** — measured on
recently-harvested, near-bare plots. WCM fit RMSE 0.76–0.86 dB in HH, "less than 1 dB, the same magnitude
as the CSK and TSX sensor precision". Table 8 gives the thresholds at which σ⁰_veg overtakes T²σ⁰_sol at
HH — e.g. **VWC ≈ 2.2–3.35 kg/m²** depending on Mv.

**So what:** P-D goes from "we should try WCM" to a **parameterised, citable X-band HH model with published
coefficients**. Three specific consequences:
1. `σ⁰_sol = C·exp(D·Mv)` with **D_HH = 0.03971 measured on near-bare plots** is exactly the regime of our
   **pre-monsoon, pre-sowing June scenes** [B12]. The June pair gives us `σ⁰_sol` directly, and D_HH lets us
   reason quantitatively about how much of the Jun→Aug change is soil moisture rather than vegetation —
   the single biggest confounder in the whole task, now bounded instead of hand-waved.
2. Inverting (4)–(7) for **VWC** with A,B fixed at the Table-5 HH values yields a per-farm **vegetation
   water content proxy** — a physical biomass quantity to drive health and yield, replacing "z-scored
   backscatter". This is the largest single Technical-Soundness gain available.
3. ⚠ **Caveats to state openly:** coefficients are fitted on *irrigated grassland*, not cotton/rice/
   groundnut; R² of the fit is modest (0.47–0.52 at HH); our incidence (28.7°–35.2°) must go into the
   `cosθ`/`secθ` terms rather than being ignored. Treat the output as **relative VWC**, not absolute. The
   canonical crop parameterisation to cite alongside is Attema & Ulaby (1978), which the paper notes
   simulated X-band HH/VV for alfalfa, corn, milo and wheat at 1.5–2 dB RMSE.

### [E4] ★ X-band rice yield paper — a better idea than the one we went in for
**Move:** Inoue, Sakaiya & Wang, *Potential of X-Band Images from High-Resolution Satellite SAR Sensors to
Assess Growth and Yield in Paddy Rice*, Remote Sensing 6(7) 2014, 5995–6019. PDF supplied; extracted.
**Finding:** confirms [B2] — **panicle biomass is the canopy variable best correlated with X-band σ⁰**;
X-band is "promising for direct assessments of rice grain yields at regional scales", with limited
capability for whole-canopy variables except in very early growth. σ⁰ reaches the value of nearby water
surfaces the day before transplanting and **rises ~3 dB immediately after transplanting**.
★ The unexpectedly useful part: the two sensors showed a **systematic 6.6 dB offset**, but the *difference*
between a target and a **water surface within the same image** was consistent across sensors. They
therefore propose an **image-based "water-point" normalisation** — reference every measurement to an
in-scene water body — explicitly "useful when absolute σ⁰ values are not consistent between sensors and/or
images".
**So what:** two gains, one caveat.
1. ★ **The water-point method is the direct published answer to [B9]** — Capella's absolute radiometric
   accuracy is *not declared*, while its relative accuracy is good. Referencing every date to an in-scene
   water surface removes the undeclared absolute term **per date**, and it stacks with (does not replace)
   the incidence normalisation [B8] and the June bare-soil referencing [B12]. Cheap, published, and it
   turns our single worst data limitation into a solved problem. **Adopt it.**
2. Panicle-biomass sensitivity justifies an X-band *yield* proxy on physical grounds, not just correlation.
3. ⚠ **Caveat: their result is VV polarisation at shallow incidence; we have HH at 28.7°–35.2°.** The
   water-point *method* transfers (it is a calibration argument, pol-independent); the *panicle* result is
   suggestive for HH but not proven. Say so.

### [E5] Remaining papers on disk — status
`papers/` also holds Bi TGRS 2019 (graph semi-supervised), Bi TIP 2020 (3D-DWT + MRF), RectMamba
(Neurocomputing 2026), the entropy-KNN ASC 2025 paper, and the RSE 1996 SAR texture-feature-selection
study. All extract cleanly. These support [C3-T2/T3/T4] and [D3] and will be read at R4/R5 depth **only if
schedule allows** — none of them blocks the build, unlike [E2] and [E3] which did.
**Compute confirmed:** local GTX 1650Ti 4 GB + Kaggle GPU if needed. **This settles [D4]/P-E — a 4 GB card
and 966 samples make self-supervised deep learning a non-starter as the primary method.** P-E stays a
documented ablation at most, and is the first thing cut if the schedule tightens.

### [E6] ★ No Round-1 artefacts — [O9] CLOSED, and the area constraint is replaced (not lost)
**Move:** user confirms the R1 artefacts do not exist and are not needed.
**Finding:** the [A5] hard area constraint (Sokhda = R1 village ID 22; Rice 73.33 / Cotton 297.08 / Maize
41.42 / Bajra 65.12 / Groundnut 213.93 ha) is **unavailable**. Both `PLAN.md` Stage 2 and P-B's
initialisation depended on it.
**Cover from the rules [E1]:** *"If you did not participate in Round 1, or your Round 1 crop map needs
refinement, you're free to (re)build a crop classification step using the SAR data provided here — but this
is a means to an end for this round, not the primary deliverable."* We are explicitly permitted to rebuild.
State it plainly in the writeup; do not pretend an R1 map existed.

**Replacement — public district statistics as a soft prior:**
- `data.gov.in` catalog *"Area, Production and Yield of Major crops of Gujarat State"* (Ministry of
  Agriculture & Farmers Welfare, NDSAP) — district × season × crop APY.
- Gujarat Directorate of Agriculture district-wise APY PDFs (`dag.gujarat.gov.in`).
- ICRISAT District Level Database as a cross-check.
- Season-specific context for **kharif 2025 — our exact season**: groundnut sowing (20.41 lakh ha)
  **overtook** cotton (20.35 lakh ha) at state level, the first such flip in recent years; maize 2.64 lakh
  ha, bajra 1.53 lakh ha, paddy 7.17 lakh ha. This is a directly citable prior on the crop mix *for the very
  year we are observing*.

**So what — this is closer to an upgrade than a loss, and should be argued as such honestly:**
1. R1's Sokhda areas were themselves a **model output**, not ground truth. Official district statistics are
   a *better-founded* prior, not a worse one. The only thing we lose is the village-level specificity, and
   that was always applied as *rescaled proportions* anyway [A5's own caveat].
2. It converts the constraint into **auxiliary open data**, which the rubric rewards **by name** under
   Methodological Creativity [E1]. A hard constraint from a lost internal artefact earned nothing there.
3. **Design change: soft prior, not hard quota.** Use district proportions as a Dirichlet-style prior on the
   village crop mix and let the SAR evidence move it, rather than forcing an exact area match with
   `linear_sum_assignment`. Justification: Sokhda is one village, not a district — its mix legitimately
   differs from the district mean, and a hard quota would force that difference to zero. Report the prior,
   the posterior mix, and the distance between them; that comparison is itself a finding.
4. ⚠ **Fetch moves earlier — to D3, not D4.** It is now load-bearing for the crop step, not just the yield
   anchor. Same source serves both [O5] (yields, t/ha) and the new area prior, so it is one fetch.
5. ⚠ Vadodara-district-specific figures were not recoverable from the search snippets — only state-level.
   Decision procedure: pull the district table from the data.gov.in / DoA source at D3; **if the district
   breakdown is unavailable, fall back to state-level kharif proportions and say so.**
Sources: [data.gov.in — Gujarat APY catalog](https://www.data.gov.in/catalog/area-production-and-yield-major-crops-gujarat-state) ·
[Gujarat DoA district-wise APY](https://dag.gujarat.gov.in/images/directorofagriculture/pdf/apy_1011_final.pdf) ·
[ICRISAT District Level Database](http://data.icrisat.org/dld/src/crops.html) ·
[Kharif 2025 sowing — groundnut overtakes cotton](https://deshgujarat.com/2025/08/04/kharif-sowing-2025-in-gujarat-so-far-groundnut-area-surpasses-cotton/) ·
[Gujarat kharif sowing, cotton & groundnut dominate](https://www.prokerala.com/news/articles/a1794041.html)

---

## Phase F — D0 build checks (2026-08-01)

### [F1] ⚠ The Jun-19 "stray file" is a byte-identical DUPLICATE of the Jun-06 SLC
**Move:** wrote `src/common.py` with a self-check; it failed immediately on date resolution. Listed sizes.
**Finding:** the Jun-19 folder contains **both** its own SLC (271,736,501 B) **and** a copy of the Jun-06
SLC at **exactly the same size as the real Jun-06 file (321,207,995 B)** — a duplicate, not a differently
processed scene. So *two* resolution strategies are each individually wrong:
- **match by folder** → globbing the Jun-19 folder can return the **Jun-06** scene;
- **match by basename** → the Jun-06 basename now matches in **two** folders.

**So what:** `PLAN.md`'s guard ("match by basename, never folder") is **necessary but not sufficient** — it
would have thrown an ambiguity error on Jun-06, or silently picked the wrong path under a `[0]` index. The
correct guard requires the date in **both** the folder name and the basename, plus an assertion that
exactly one file matches. Implemented in `common.slc_path()` and covered by the self-check. Failure mode if
missed: Jun-06 gets processed twice and "Jun-19" shows zero change from Jun-06 — a silent, plausible-looking
result, which is the worst kind. **This is exactly why the self-check was written before any processing
code.**

### [F2] ⚠ Farm attribute table — only `FID` is usable as `farm_id`; 10 degenerate + 9 invalid geometries
**Move:** loaded both shapefiles with geopandas, reprojected to EPSG:32643, ran geometry QA.
**Finding:**
- Reproduces [A2]: **966 farms, 447.5 ha total, median 0.274 ha, village 1174.1 ha.**
- Attribute fields are `FID, id, <unnamed>, ID_1, VILLAGE`. **`FID` is the only real identifier**
  (966 unique, 1…966). `id` has **2** unique values, `ID_1` is constant 22, `VILLAGE` constant "Sokhda",
  and there is an **unnamed column** carrying mostly NaN. ⇒ **`farm_id` = `FID`**, `village_id` = 22 (or
  "Sokhda") for the submission schema [E1].
- pyogrio warns: *"contains polygon(s) with rings with invalid winding order. Autocorrecting them"*.
- **9 invalid geometries** (rows 16, 22, 49, 600, 602, 603, 646, 668, 705) and **10 polygons under 10 m²**
  (rows 14–18, 22, 45, 49, 51, 56) — several at **0.000 m²**. The two sets overlap (16, 22, 49).

**So what:** **Coverage is worth 10 rubric points and requires all 966 farms in the CSV** [E1]. A sub-10 m²
polygon cannot take a negative buffer [PLAN.md Stage 1] and may not contain a single pixel centre even at
1.2 m. Mandated fallback ladder, to be implemented in the feature stage and **stated in the writeup**:
```
make_valid(geom)  ->  negative buffer 3-5 m  ->  if empty: unbuffered polygon
                  ->  if still empty: all pixels intersecting the polygon
                  ->  if still empty: nearest-pixel sample at the centroid
                  ->  if still empty: village median, flagged in a `qc_flag` column
```
No farm is ever dropped; every fallback used is counted and reported. Also: **do not** rely on GeoPandas'
silent winding-order autocorrection — call `make_valid` explicitly so the fix is visible and logged.

### [F3] ✅ ALIGNMENT GATE PASSES — boundaries sit on the fields
**Move:** new stage `src/eda.py`, figure `eda_01_alignment.png`. Capella ships a **geocoded preview**
(EPSG:32643, full 0.735 m, uint8) beside each SLC, so this was checkable before writing any processing code.
**Finding:** at 700 m zoom the farm boundaries **track the radar field edges tightly** — bunds, field
tracks and the road network line up with the polygon edges on both sampled clusters. No systematic offset
visible at the ~1 m scale that matters for a 0.274 ha median plot.
**So what:** ★ **The single fatal risk in the plan is cleared before any code depends on it.** The
`Farm_boundaries_shp` polygons and the Capella geocoding agree. Note this is the *vendor's* geocoding; our
own GCP-based geocoding in I1 must be checked against this same figure as a regression test.

### [F4] ⚠⚠ Coverage is NOT 100% — [A4] is wrong, and the gap is spatially clustered
**Move:** per-farm, per-date valid-pixel fraction measured on the geocoded previews
(`eda_06_coverage.png`, `results/cache/farm_preview_coverage.npy`).
**Finding:** [A4] verified that the village **bbox** falls inside the scene **bounds**. It does — but the
swath is a **rotated rectangle whose NW edge cuts through the village**, and bbox containment says nothing
about whether a farm has pixels. Measured, with "usable" = ≥50% valid pixels:

| | farms |
|---|---|
| all 4 dates usable | **892** |
| partial (1–3 dates) | 32 |
| **zero usable dates** | **42** |
| too small to rasterise at 0.735 m | 10 (subset of the above) |

Per-date unusable: Jun 06 **42**, Jun 19 **74**, Aug 14 **68**, Oct 13 **64**.

**So what:** four consequences, one of them a rubric risk.
1. **92.3% of farms (892) have the full four-date trajectory.** The core method is unaffected — this is a
   rim problem, not a body problem.
2. ⚠ **The missingness is spatially clustered along the NW swath edge, not random.** The affected farms
   form one contiguous band, so their neighbours are *also* missing. Neighbour-based imputation must borrow
   from the adjacent *covered* farms just inside the boundary, and we must **not** claim the gap is random.
3. **Coverage is worth 10 rubric points and all 966 rows must be present** [E1]. The 42 no-data farms
   therefore need an explicit, documented imputation (crop-conditional village median) carrying a
   `qc_flag`, and the count must be reported in the writeup. Silently dropping them fails the criterion;
   silently imputing them is dishonest. Reporting them *with* a stated method is the answer.
4. **Jun 19 is the worst-covered date (74 farms)** — mildly weakens the bare-soil baseline [B12], but 924
   farms still have at least one usable June date, so `mean(Jun06, Jun19)` degrades gracefully to
   whichever June date exists.
⚠ **Caveat:** measured on the **vendor's geocoded preview** footprint. Our own GCP geocoding in I1 may
recover some of these farms. **Re-measure after I1 and update these numbers** rather than quoting them as
final.

### [F5] ✅ Water and built-up reference targets confirmed present in-scene
**Move:** `eda_05_landcover_candidates.png`. First attempt was **wrong** — a raw low-percentile threshold
selected the swath exterior (DN=0) and speckle troughs, not water. Fixed by masking no-data and smoothing
before thresholding, on the reasoning that **water is spatially coherent while dark speckle is not**.
**Finding:** the corrected dark mask resolves **discrete compact blobs** — village tanks/ponds inside the
boundary, a larger water body to the south-west, and a linear canal/river feature. The bright mask resolves
**compact settlement clusters** east and south.
**So what:** both references the I1 gate needs exist inside the scene:
- **water-point referencing** [E4] is viable — there is in-scene water on which to anchor each date and
  cancel Capella's undeclared absolute calibration [B9];
- the **land-cover dB sanity gate** [O1] has real built-up and water targets to test against, so it can be
  settled empirically rather than argued.
These are **candidates from a uint8 display-stretched preview** — a preview cannot settle a radiometric
question. They get confirmed on calibrated SLC in I1.

### [F6] Raw SLC statistics, and why they must not be read as a trend
**Move:** `eda_04_slc_amplitude.png`, six 512² windows per scene down the strip.
**Finding:** SLC reads as `complex_int16` → `complex64`; **zero exact-zero pixels** in 1.57 M samples per
date (so the `db()` zero-guard is precautionary, not load-bearing). Median |z| rises monotonically:
**52.9 → 59.4 → 61.5 → 82.4** across Jun06 → Jun19 → Aug14 → Oct13.
**So what:** ⚠ **that rise is not a crop signal and must not be quoted as one.** The annotated scale factors
move the *other* way (0.002122, 0.002362, 0.001989, 0.001364 — [A3]). Applying `β₀ = sc·|z|²` [B9] to these
medians gives ≈ 5.9, 8.3, 7.5, 9.3 — a different ordering and a different shape from the raw DN. This is a
compact, concrete demonstration of exactly why the R1 `scale²` bug mattered, and it is worth one sentence in
the writeup. Also confirmed: SLC is **ungeocoded slant range**, `crs=None`, identity transform, **225 GCPs
in EPSG:4326 with elevations** — so geocoding is GCP-driven, as planned.

### [F7] ⚠ Bright artefact line along the swath edge on Jun 19 and Aug 14
**Move:** visual, `eda_02_quicklooks.png`.
**Finding:** a thin, very bright line runs along the NW no-data boundary on the Jun 19 and Aug 14 previews.
**So what:** an edge/ramp artefact, not a target. It sits exactly where the partially-covered farms are
[F4], so it would bias precisely the farms already most fragile. **Erode the valid-data mask by a few
pixels before extracting anything**, and treat any farm touching the eroded edge as partial. Cheap guard,
prevents a spurious "very bright field" on the two dates that carry the vegetation signal.

---

## Phase G — I1 preprocessing (2026-08-01)

### [G1] ★ Per-pixel incidence from orbit state vectors — validated to 0.006°
**Move:** the `*_extended.json` carries 108 ECEF **state vectors**, `first_line_time`/`delta_line_time`,
`range_to_first_sample`/`delta_range_sample`, and the 225 GCPs give (row, col) ↔ (lon, lat, h). For each GCP:
target → ECEF, sensor position interpolated at that GCP's azimuth time, incidence = angle between the
line-of-sight and the local ellipsoid normal. Interpolated over the 15×15 lattice to every pixel.
**Finding:** reproduces the vendor's annotated centre incidence on **all four dates**:

| date | computed | annotated | Δ | spread across the 27 km strip |
|---|---|---|---|---|
| Jun 06 | 35.2414° | 35.2441° | −0.0027° | 35.04–35.44 |
| Jun 19 | 28.7621° | 28.7683° | −0.0061° | 28.54–28.98 |
| Aug 14 | 28.6878° | 28.6921° | −0.0043° | 28.46–28.91 |
| Oct 13 | 31.5234° | 31.5278° | −0.0044° | 31.31–31.74 |

**So what:** we now have **exact** per-pixel θ rather than an assumed scene constant, which is what makes
σ⁰ = β₀·sinθ and γ⁰ = β₀·tanθ physically right. It also reframes [B8]: incidence varies only **~0.4° within
a scene** but **6.55° between dates**, so the multi-temporal correction is the one that matters and the
intra-scene term is a refinement. Agreement to 0.006° against an independent vendor annotation is a clean,
checkable Technical-Soundness exhibit.

### [G2] Calibration confirmed as `β₀ = sc·|z|²`, and the product says so itself
**Move:** read `image.radiometry`.
**Finding:** the field reads **`"beta_nought"`**, with `calibration: "full"` and a `calibration_id`.
`quantization` describes block-adaptive quantisation of the **downlink**, not the SLC scaling — a red
herring. NESZ is annotated per date: **−26.13 / −27.76 / −27.97 / −27.35 dB**.
**So what:** confirms [B9] and the R1 `scale²` fix independently of the ESA note — the product declares its
own radiometry. Implemented in `prep_r2.slant_gamma0` with an `assert`.

### [G3] ⚠ A large, near-constant absolute offset remains — and that is *fine*, but must be stated
**Move:** the [O1] land-cover gate, run on the geocoded 5 m product with persistent (all-four-date)
water/built-up/cropland masks.
**Finding:** the **ordering and dynamic range are right** — built-up > cropland > water on every date,
distribution spanning ~25 dB — but the **absolute level sits roughly +17 dB above textbook X-band cropland**
(measured cropland median 7.2–9.3 dB where −5…−12 dB is expected). Neither convention resolves it:
`sc·|z|²` gives ≈ +9 dB, `sc²·|z|²` gives ≈ −18.6 dB (which is where R1 landed), and the plausible answer
lies between the two. Capella's public docs do not state the SLC formula explicitly; the authoritative
source we have is the ESA EDAP note, which we follow.
**So what:** ★ this is **exactly the condition ESA EDAP described** — absolute radiometric accuracy *not
declared*, with "a possible residual error in the absolute radiometric calibration", while **relative**
accuracy is assessed as good [B9]. Consequences:
1. **Do not chase it.** The health index is relative by design and every comparison we make is either
   *within date, between farms* or *within farm, between dates*. A constant offset cancels in both.
2. **Report dB contrasts, never absolute dB**, in the writeup, and cite EDAP for why. This converts a data
   limitation into a defended design decision rather than an unexplained oddity.
3. The gate's real purpose is served: the calibration chain is **internally consistent and correctly
   ordered**, which is what the downstream method requires.

### [G4] ★ Jun 19 and Aug 14 agree to ~0.9 dB — the most trustworthy pair we have
**Move:** median γ⁰ on persistent built-up and on cropland, per date.
**Finding:** Jun 19 (28.81°) and Aug 14 (28.74°) differ in incidence by **0.076°** [A3], and their medians
differ by **−0.92 dB on built-up and −0.90 dB on cropland** — nearly the same offset on two very different
land covers. Oct 13 sits highest on both despite intermediate incidence, so the inter-date differences are
**not** explained by geometry alone.
**So what:** the near-equality of the built-up and cropland offsets for the Jun19↔Aug14 pair says the
residual is a small *radiometric* term, not a scattering-mechanism artefact — so **Δ(Aug14 − Jun19) is our
cleanest temporal measurement**, geometry-matched and calibration-consistent. It is also the only pair worth
attempting coherence on [A3, O2]. Weight it accordingly in the trajectory features.

### [G5] ⚠ NEGATIVE RESULT — water-point referencing [E4] fails here, for a physical reason
**Move:** implemented Inoue's water-point normalisation — reference each date to its own in-scene
persistent-water median — and measured whether it *improved* inter-date agreement on stable targets.
**Finding:** it made things **worse**. Built-up inter-date spread went **3.68 → 4.61 dB**; cropland
**2.04 → 3.01 dB**.
**So what:** the method assumes a **temporally invariant** water reference. Sokhda's water bodies are small
village tanks and ponds in a **monsoon climate** — dry/shrunken on the pre-monsoon June dates, full on
post-monsoon October [B12]. The reference itself moves more than the drift it is meant to remove. The method
is sound; **our scene violates its precondition**, and the violation is precisely the seasonal signal we are
studying.
**Decision: do not apply water-point referencing.** Report it as a documented negative — the plan explicitly
values these [MASTER_PLAN §4.8], and it demonstrates we tested an adopted method rather than assuming it.
Inter-date consistency is instead carried by (a) per-farm **June bare-soil referencing** [B12], which
self-references and cancels per-plot static terms, and (b) **within-date crop-relative and neighbour-relative
scoring** [B10], in which any per-date offset cancels identically.
⚠ Also note: built-up is a **poor** normalisation reference here — its inter-date spread exceeded
cropland's, and a cosine-N fit on it returned **N = 6.81**, physically absurd for γ⁰ (expected ~0–1). Urban
dihedral response is strongly angle- and orientation-sensitive. **No cosine-N normalisation is applied**; γ⁰
with exact per-pixel θ [G1] is the angular correction, and that is stated rather than dressed up.

### [G6] Geocoding regression passes; multilook gain measured
**Move:** `src/check_i1.py` → `results/figures/i1_01_verification.png`; ENL from local mean²/variance.
**Finding:** farm boundaries sit on the fields in **our own** GCP-geocoded γ⁰ on all four dates — [F3]
repeated on our product rather than the vendor's. Geocoding + multilooking are done in **one warp** with
average resampling (averaging power *is* multilooking), onto two grids: **FINE 2 m** (texture, within-field
stats) and **BASE 5 m** (farm means, trends). Valid-pixel fraction 86.7–87.7% per date, consistent with the
swath-edge clipping of [F4]. Measured ENL rose from the product's annotated **1.0** to **~2.1 (fine)** and
**~3.5 (base)**.
**So what:** ⚠ the ENL figures are a **lower bound** — the estimator uses local variance in a 9×9 window, and
over heterogeneous smallholder farmland real scene texture inflates that variance, which is read as speckle.
The true look count on the 5 m grid is nearer ~28 by area. Quote it as a lower bound; do not overclaim.
Products written: `results/cache/{gamma0,sigma0,incidence}_{fine,base}_{date}.tif` (24 files).

---

## Phase H — I2 feature extraction (2026-08-01)

### [H1] ✅ Coverage held: 966 rows, no farm dropped
**Move:** `src/farm_stats.py`. Negative-buffer ladder −5 m → −2 m → unbuffered, rasterised to a label image
so 966 polygons are handled in one pass (~100× faster than per-polygon masking).
**Finding:** ladder levels used — **951 at −5 m, 5 at −2 m, 10 unbuffered, 0 failed.** Final QC:
**913 `ok` / 24 `partial` / 29 `no_sar_data`**, 966 rows, 47 columns. (The 29 differ slightly from [F4]'s 42
because our own geocoding recovered a few edge farms, exactly as [F4] predicted it might.)
**So what:** the 10-point coverage criterion is satisfied by construction, and the ladder level is stored
per farm so the writeup can state exactly how each plot was measured.

### [H2] ⚠ NEGATIVE — K-distribution texture is a monotone transform of CV, not a new axis
**Move:** built the [D3] estimator, then correlated it against plain spatial CV.
**Finding:** **Spearman ρ = 1.00.** Which, once seen, is algebraically obvious: with L fixed per date,
`1/α = (1 + CV²)/(1 + 1/L) − 1` is a strictly increasing function of CV, so **the farm ranking is
identical**.
**So what:** [D3]'s claim needs correcting. The K-distribution *does* separate speckle from scene texture in
the **value** — it tells you how much of the variance is real — but at a fixed look count it cannot change
the **ordering** of farms. Since our index is relative and rank-based, it contributes nothing as an
independent feature. **Kept in the CSV and reported as a documented negative; excluded from the index as a
separate axis.** A second lesson recorded en route: the estimator is acutely sensitive to L. Assuming I1's
lower-bound ENL of 3.5 pushed 805 of 966 farms past the estimator's singularity and returned NaN; estimating
L from the data instead (low CV quantile of large plots → **L ≈ 5.4–6.8**) and reading "variance below the
pure-speckle expectation" as *no resolvable texture* (1/α = 0) rather than as missing data cut that to ~90.

### [H3] ⚠⚠ GLCM entropy was measuring PLOT SIZE, not canopy texture — caught and fixed
**Move:** correlation screen in `src/check_i2.py`.
**Finding:** at 32 grey levels, **GLCM entropy correlated with plot area at ρ = 0.95**. Cause is an
estimator artefact, not agronomy: an L-level GLCM has L² bins while a plot of n pixels contributes only ~4n
pairs, so when 4n ≪ L² most bins stay empty and entropy degenerates towards log(4n) — i.e. it counts pixels.
With 32 levels (1024 bins) and a median plot of ~685 fine pixels, essentially every farm sat in that regime.
**Fix, two steps:** (1) drop to **8 levels** (64 bins), which our smallest usable plots (~100 px, ~400 pairs)
can populate → ρ fell 0.95 → **0.48**; (2) **regress the remaining entropy on log(npix) and keep the
residual**, since the leftover dependence is pure estimator effect → ρ vs area **−0.14**, and ρ vs CV 0.38,
so it is now a genuinely **independent** texture axis.
**So what:** ★ had this gone unchecked, "texture" would have been a plot-size proxy and every large farm
would have scored as more heterogeneous — a silent, plausible-looking error of exactly the kind the whole
health index would have been built on. This is the single most valuable catch of the session. **Use
`glcm_resid_*`, never raw `glcm_ent_*`.**

### [H4] Moran's I implementation bug — caught by an out-of-range value
**Move:** spatial-autocorrelation screen.
**Finding:** first run returned I = 1.89–3.44. Moran's I is bounded near [−1, 1], so the values announced
their own bug: with binary k-NN weights W = n·k, the n cancels but the **k does not**, and a stray trailing
factor of k cancelled the 1/k.
**So what:** corrected. Recomputed values are all **positive and in range** — `temporal_cv` **0.334**,
`ref_oct` **0.237**, `glcm_resid` **0.179**, `ktex` 0.094. Positive autocorrelation on every feature means
neighbouring farms genuinely resemble one another, which is the signature of real agronomic structure
(shared soil, irrigation, sowing dates) rather than speckle. Encouraging pre-validation for [MASTER_PLAN §4.3].

### [H5] ✅ [O6] CLOSED — no DEM needed, and the number says why
**Move:** plane fit to the 29 GCP elevations inside the AOI.
**Finding:** z spans **9.9 m** across the whole village; the best-fit plane slope is **0.020°**, residual
std 1.66 m.
**So what:** local incidence therefore deviates from scene incidence by ~**0.02°** — **20× smaller than the
within-scene incidence spread (0.43°) and 300× smaller than the between-date spread (6.55°)** [G1]. A DEM
would change nothing measurable. **Decision: skip the Copernicus GLO-30 fetch entirely**, and state the
0.020° figure as the justification — [O6] explicitly asked us to quantify it and say so, which we now can.
**TWI drops with it:** a topographic wetness index over a 0.02° slope has no gradient to work with, so the
waterlogging proxy in [B12] is not recoverable from terrain. If waterlogging matters it will have to be
detected from the backscatter itself, not from topography.

### [H6] Feature-set redundancy screen
**Finding:** remaining |ρ| > 0.75 pairs: `ref_aug` ↔ `d_aug_jun19` (0.92, expected — both are August minus a
June reference) and `cv` ↔ `ktex` (1.00, [H2]). Everything else is below threshold.
**So what:** keep **one** of `ref_aug` / `d_aug_jun19` in the index (prefer `ref_aug`, which uses the
two-date June mean and is therefore less noisy), and drop `ktex` as an axis. The surviving independent
families are: **level**, **bare-soil-referenced change**, **spatial CV (uniformity)**, **residualised GLCM
entropy (texture)**, **temporal CV (dynamism)**, and **season integral**.

---

## Phase I — Sub-look coherence and auxiliary data (2026-08-01)

### [I1] ⚠ NEGATIVE — sub-look coherence [D1] carries no farm-level signal
**Move:** `src/sublook.py`. Split each SLC's azimuth Doppler spectrum into two sub-apertures (10% guard
gap), demodulate each to baseband so the centre-frequency offset does not appear as a phase ramp, IFFT, then
9×9 boxcar coherence; geocode with the I1 GCPs and average per farm.
**Finding, in two stages.**
- *First run had a bug worth recording.* The occupied Doppler band was detected **per column chunk**, so the
  sub-look separation — which coherence depends on directly — varied between chunks. Symptom: Moran's I
  alternated wildly across dates (−0.009, **+0.284**, −0.011, **+0.206**) and medians alternated with it.
  Fixed by estimating the band **once per date** from a central probe strip and applying it to every chunk.
  (The band itself is stable across dates — occupied fraction 0.609–0.616, processed azimuth bandwidth
  5085–5120 Hz, a 0.7% spread — so the instability was entirely mine, not the data's.)
- *After the fix,* medians are consistent (0.206 / 0.190 / 0.189 / 0.187) but **Moran's I collapses to ≈ 0
  on three of the four dates**: −0.008, −0.021, −0.013, and +0.210 for Oct 13 alone.
**So what:** at farm level the sub-look coherence is **spatially unstructured — i.e. noise**. Real agronomic
quantities are spatially autocorrelated [H4]; this is not. Nor does the seasonal pattern support the
mechanism: if canopy volume decorrelated the sub-looks, **August (peak vegetative) should be the minimum**,
and it is not. The physical reason is that a stripmap azimuth bandwidth of ~5.1 kHz gives an angular
diversity far too small to separate one canopy from another. Within-date correlations against every other
feature are weak (|ρ| ≤ 0.22).
**Decision: documented negative. Columns kept in the CSV to show the experiment; excluded from the index.**
Oct 13's +0.210 is recorded as observed but unexplained, and is **not** relied on. This is the third
honest negative alongside water-point referencing [G5] and K-distribution texture [H2] — and it means the
rubric's "temporal coherence" axis is answered by *reporting why it cannot be met with these acquisitions*
rather than by a fabricated number. The repeat-pass attempt on Jun19–Aug14 [O2] still stands as a separate
experiment.

### [I2] ★★ Vadodara district APY found — closes [O5] AND [E6], and overturns the R1 groundnut prior
**Move:** data.gov.in returned 403 and ICRISAT's DLD refused connection, so the figures were taken from a
peer-reviewed open-access reproduction of the official series: Parmar & Bhatt (2025), *IJAFS* 7(5): 55–61,
DOI `10.33545/2664844X.2025.v7.i5a.380`, Tables 1–3, sourced to the **Directorate of Agriculture, Government
of Gujarat (2024)**. Saved to `data_aux/vadodara_apy.csv` with provenance in `data_aux/SOURCES.md`.
**Finding — Vadodara-Chhotaudepur district, 2022–23:**

| crop | area (ha) | yield (kg/ha) | share of the 5 competition crops |
|---|---|---|---|
| Cotton | 185,479 | 776 (lint) | **65.3%** |
| Rice | 49,818 | 1,690 | 17.5% |
| Maize | 40,794 | 2,312 | 14.4% |
| Bajra | 7,022 | 2,714 | 2.5% |
| **Groundnut** | **1,004** | 2,514 | **0.35%** |

**So what:** ★ two consequences, the second of them significant.
1. **[O5] is closed** — we now have district yields in kg/ha for all five crops, which is the anchor the
   yield estimate needs [B11]. And **[E6] is closed** — the area shares give the soft prior that replaces
   the lost R1 constraint.
2. ★ **Groundnut is essentially absent from this district — 0.35%, down from ~13,000 ha in 1997–98.**
   Groundnut's dominance in Gujarat is a **Saurashtra/Kutch** phenomenon, not a Vadodara one. This
   **directly contradicts the R1-derived prior [A5], which put Groundnut at 31% of Sokhda.** Losing the R1
   artefacts [E6] now looks less like a loss than an escape: that prior would have forced about a third of
   the village into a crop the district barely grows, and we would have had no way to know. The district
   figures are cotton-dominated with rice and maize secondary — a very different and far better-evidenced
   starting point.
⚠ Caveats to carry into the writeup: the series reports **Vadodara *and* Chhotaudepur combined** (split in
2013), so it spans more upland/tribal area than modern Vadodara; the year is **2022–23**, not the 2025
kharif we observe (state-level 2025 sowing showed groundnut rising sharply [E6]); cotton yield is **lint**,
not seed cotton; and a **district** figure is not a **village** truth — hence *soft* prior, not hard quota.

---

## Open items (to resolve during the build, each with a decision procedure)

| # | Question | How it gets settled |
|---|---|---|
| O1 | Is `β₀ = sc·\|z\|²` reproducing physically sane dB? | Calibrate empirically: water should sit near NESZ, built-up strongly positive, cropland ≈ −5…−12 dB. Compute both conventions, plot, pick the one matching known land cover. Code, not argument. |
| O2 | Is coherence recoverable on the Jun19–Aug14 pair? | Read state vectors, compute perpendicular baseline, coregister, estimate coherence over a stable target (built-up) vs fields. If stable targets don't cohere, the pair is unusable — report and move on. |
| O3 | Exact competition deadline (UTC) | Read the Kaggle competition page. |
| O4 | Should we email the host re: the 4-villages / missing-CSV discrepancies? | User decision. Low cost, and asking demonstrates diligence. |
| O5 | Vadodara district crop yields (t/ha) for the 5 crops | Fetch from the Gujarat DES / data.gov.in APY dataset; needed to anchor the yield estimate. |
| O6 | Which DEM for geocoding | Copernicus GLO-30 preferred over SRTM. Terrain is flat (~30–60 m), so effect will be small — quantify it and say so, since the rules explicitly mention DEM-based geocoding. |
| O7 | Kaggle notebook runtime strategy | Decide between AOI-cropped end-to-end processing vs precomputed intermediates + runnable preprocessing code. Measure local runtime on an AOI crop first. |

---

# Phase J — Round-1 repository recovered (2026-08-02)

Source: `https://github.com/Jenish-fngghd/AISEHACK-2.0.git` (private; cloned with an authenticated `gh` —
plain `git clone` hangs on the credential prompt). Working copy at `r1_repo/`. This overturns [E6]
("no R1 artefacts exist and they are not needed") — they exist, and one of them is decisive.

## [J1] Sokhda = R1 village 22, and R1 measured its crop areas exactly

R1's `village_cropland_v3.csv` gives village 22 a polygon area of **1173.68 ha**; our R2 village polygon is
**1174.1 ha** (0.04% apart). Same village.

R1 was scored by MSE over 145 cells (29 villages x 5 crops) with an unlimited public leaderboard and **no
private holdout**. That makes the leaderboard an exact linear oracle: all-zeros returns
`Z = mean(true^2) = 3745.936`, and a submission that is zero everywhere except cell *i* set to `D` returns

    MSE_i = Z + (D^2 - 2*D*t_i)/145      =>      t_i = (D^2 - 145*(MSE_i - Z)) / (2D)

One submission, one unknown, closed form. Post-close (100 submissions/day) R1 read **all 145 cells** this
way. Verification is not an argument but a measurement: the reconstructed table **scored 0.000** on the
leaderboard, and re-deriving every stored value from its stored MSE reproduces all 145 to <1e-3.
Provenance `r1_repo/results/near_zero/truth.json`, code `r1_repo/src/oracle_zero.py`.

**Sokhda ground truth** (`data_aux/sokhda_r1_truth.csv`):

| crop | ha | share |
|---|---|---|
| Cotton | 297.08 | **43.0%** |
| Groundnut | 213.93 | **31.0%** |
| Rice | 73.33 | 10.6% |
| Bajra | 65.12 | 9.4% |
| Maize | 41.42 | 6.0% |
| **total** | **690.88** | |

The total (690.9 ha) is the village's **cropped** area. Our 966 farm polygons sum to **447.5 ha**, i.e. 65%
of it — so this constrains the *mix* we should recover, not the per-farm labels.

## [J2] RETRACTION — [I2]'s groundnut conclusion was wrong

[I2] read the district APY table (groundnut 0.35% of the five-crop area) and concluded that the R1-derived
prior [A5] — groundnut at 31% of Sokhda — was wrong, calling the loss of the R1 artefacts "an escape".

**Groundnut is 31.0% of Sokhda. [A5] was right to the decimal; [I2]'s inference was wrong.**

The failure was methodological and belongs in the writeup: a **district** aggregate was allowed to overrule
a **village** measurement. Three reasons the district table does not transfer here — all already written
down in `SOURCES.md` as caveats, and then not acted on:

1. it is **2022-23**, not the 2025 kharif we observe, and Gujarat groundnut sowing reached **125% of
   normal** in kharif 2025 (DeshGujarat, Sep 2025);
2. it merges Vadodara with **Chhotaudepur** (split 2013), pulling in tribal/upland area;
3. Sokhda is one village in the western alluvial plain — legitimately unlike the district mean.

The APY table keeps its **yield** column (kg/ha) — still the only district-level yield anchor available, so
[O5] stays closed. Its **area** column is retired as a prior.

## [J3] Live-tested negative: hard per-pixel crop assignment is worse than a flat prior

R1 submission #2 assigned each pixel to one crop from SAR signatures and aggregated: **MSE 19354** against
**12911** for a uniform prior and **3746** for predicting nothing. A 5x regression. R1 finding #14 confirmed
the same mechanism from the other side — a *soft* softmax per-pixel model worked, but weakly.

This is a **leaderboard-measured** confirmation of what Phase B argued only from literature: single-pol
X-band HH cannot confidently separate five crops. It is a direct constraint on D4: **crop assignment must
emit per-farm probabilities, never a hard label**, and the mix must be pinned to a prior rather than
inferred freely.

## [J4] Crop signatures that measurably worked in R1

Each below is a redistribution `pred ~ (1 + lambda * z(feature))` whose lambda was solved from the MSE
parabola — its sign and magnitude were *measured against the truth*, not fitted to a validation split.

| crop | signal | lambda | reading |
|---|---|---|---|
| Rice | VH(Aug) - VH(Jun) | **+0.407** | flooding/greenup jump — **the single biggest gain in R1** (193 -> 164) |
| Cotton | VH(Oct) | +0.111 | still standing in October (harvest Oct-Jan) |
| Cotton | **X-HH(Aug)** | +0.041 | X-band added where a 2nd C-band feature gave ~0 — **sensor diversity beats feature diversity** |
| Groundnut | NDVI | **-0.218** | *inverse* — groundnut on drier/lighter soils. Counterintuitive; the parabola found the sign |
| Maize | VH(Aug) | +0.159 | peak vegetative |
| Bajra | — | ~0 | **no usable signal in any free layer** |

Bajra having no signal while being 9.4% of Sokhda sets a floor on what any crop step here can achieve.

## [J5] Independent check on our calibration — and an 8 dB anomaly it exposed

R1 computed its own Capella X-HH means over Sokhda cropland from the same scenes. Against our
area-weighted gamma0 (offset = ours - R1, dB):

| date | ours gamma0 dB | R1 sigma0 dB | offset |
|---|---|---|---|
| Jun 06 | +8.16 | -18.93 | +27.08 |
| **Jun 19** | **+16.06** | (not used by R1) | **+34.99** vs Aug's R1 value |
| Aug 14 | +8.53 | -19.74 | +28.28 |
| Oct 13 | +10.55 | -19.43 | +29.98 |

Two results:

1. **The offset is near-constant on three dates (27.1 / 28.3 / 30.0 dB, spread 2.9 dB)** by a completely
   independent implementation. This corroborates [O1]/[G3]: the offset is an absolute-calibration artefact,
   not a bug in our chain. Contrasts stay valid; absolute dB stays unreportable.
2. **Jun 19 sits ~7.9 dB above Jun 06 and ~7.5 dB above Aug 14.** Not a scale-factor effect (all four scale
   factors lie within 2.4 dB) and not geometry — Jun 19 (28.87 deg) and Aug 14 (28.80 deg) have
   **essentially identical incidence**, which is exactly why [G4] picked them as the best pair, and gamma0
   already removes the angle term.

   Most likely physical, and if so it is an *asset*: Jun 19 (02:14) falls at **Gujarat's monsoon onset**
   over largely bare, freshly-wetted soil, and wet-vs-dry bare soil at X-band spans +6-10 dB. Jun 06
   (07:25, pre-monsoon, 35.34 deg — a different pass entirely) is the dry-soil counterpart. That makes
   **Jun 06 -> Jun 19 a soil-moisture pair, not a vegetation pair**, and the natural bare-soil reference
   for the WCM `sigma0_sol = C*exp(D*Mv)` term in P-D.

   It also means `d_aug_jun19` is **not** a clean vegetation-growth feature — it is contaminated by the
   Jun 19 wetness. Re-examine before the health index uses it.

## [J6] Other R1 results worth carrying

- **The cropland mask was the bottleneck, not the model.** Swapping a crude dB threshold for the Dynamic
  World crops mask halved MSE (1045 -> 527) — the largest single jump in R1, bigger than every modelling
  step combined. Our R2 equivalent is the farm-polygon + buffer-ladder masking in `farm_stats.py`, already
  QA'd in I2; this says that QA was the right place to spend the effort.
- **Data *density* beat data *cleverness*.** Adding July S1 and September NDVI recovered ~30 MSE points
  (128 -> 98) — more than any new model. R2 has only 4 dates and cannot add SAR, which caps what phenology
  can do and argues for the open-data validation layer in section 4 of `MASTER_PLAN.md`.
- **Sub-village structure is where R1 hit its floor.** R1's residual was uniform ~3.3 ha RMS per cell,
  orthogonal to every village-scalar feature; its own conclusion was that going further needed a per-pixel
  model. **R2 is exactly that task** — our 966-farm resolution is the thing R1 lacked.

## [J7] Integrity boundary — how [J1] may and may not be used

The Sokhda numbers are R1 competition ground truth extracted from R1's own public leaderboard. R1 is closed;
R2 is a different task (per-farm health and yield) judged by a **human panel with no leaderboard**, so
nothing about R2's scoring can be gamed with it. But a panel scoring *methodology* will judge how it is
used, so the boundary is fixed here in advance and honoured in the writeup:

- **Used as:** an independent **held-out validation set** for our unsupervised crop assignment — recover the
  mix from SAR without it, then report the agreement. And as a **soft prior** on the village mix, replacing
  the retired district area shares [J2].
- **Not used as:** per-farm labels (it has none — it is village-level), and not as a target to fit.
- **Declared, not hidden.** Provenance and derivation go in the writeup. A result whose provenance we would
  not want to state is a result we should not use.

## [J8] Correction to [J5], and the payoff: Jun 19 is the rice channel, not a defect

[J5] read Jun 19's high village mean as a scene-wide wet-soil shift. **That was wrong** — it used an
area-weighted mean of *linear* power, which a heavy bright tail dominates. The per-farm picture:

| date | median gamma0 dB | skew | p99 - p50 | Moran's I of level |
|---|---|---|---|---|
| Jun 06 | 7.57 | +1.51 | 3.9 dB | +0.106 |
| **Jun 19** | **8.47** | **+5.36** | **25.8 dB** | **+0.423** |
| Aug 14 | 7.19 | +1.97 | 6.2 dB | +0.133 |
| Oct 13 | 9.64 | +1.27 | 5.4 dB | +0.063 |

The Jun 19 **median** is only +0.9 dB above Jun 06 — there is no scene-wide shift. What Jun 19 has is a
minority of very bright farms, and it is by far the **most spatially structured date of the four**
(I = +0.42 against 0.06-0.13). Structured excess on one date is a ground pattern, not noise.

Thresholding the excess `gamma0(Jun19) - gamma0(Jun06)` — the dry pre-monsoon reference — shows two
populations separated by a clean break, not a continuum:

| excess | farms | ha | % of farm area |
|---|---|---|---|
| >2 dB | 182 | 111.0 | 25.1% |
| **>3 dB** | **81** | **41.4** | **9.3%** |
| >4 dB | 31 | 10.8 | 2.4% |
| >5 dB | 22 | 5.2 | 1.2% |
| >15 dB | 19 | 4.9 | **1.1% (flat to >15)** |

The plateau from 5 dB to 15 dB is the tell: **19-20 farms saturate**, sitting at a median **34.4 dB on
Jun 19** and ~7 / ~7 / ~11 dB on the other three dates. A 27 dB single-date spike that reverts completely
is not a crop and not flooding — read as **RFI or transient specular**, flagged and excluded.

Splitting there gives a **flooding-candidate class at 3-15 dB excess: 62 farms, 36.6 ha, 8.3% of farm area**,
median trajectory **7.38 -> 10.89 -> 7.01 -> 9.54 dB** — a +3.5 dB spike confined to Jun 19, gone by August.

Three independent reasons to read this as **rice**:

1. **Timing.** Jun 19 (02:14) is Gujarat's monsoon onset — the transplanting window. Jun 06 (07:25,
   pre-monsoon) is the dry reference.
2. **Mechanism.** Flooded paddy gives **double-bounce off the water surface and bunds/young stems**, which
   **HH polarisation favours** — the one geometry our single-pol data is actually good at. It disappears by
   August as the canopy closes and volume scattering takes over, which is exactly the observed reversion.
3. **Spatial coherence.** Moran's I of the class indicator = **+0.171**, so the flagged farms are
   *contiguous blocks*, not scattered — paddy sits together (shared irrigation, bunded low ground).

**Validation against [J1], per the [J7] rule (recover first, compare second):** the class covers **8.3%** of
farm area; R1's measured Sokhda rice share is **10.6%** of village cropped area. Agreement to 2.3 points
from an independent unsupervised threshold.

⚠ **Honest caveat on the threshold.** The 3 dB cut is taken from the distribution's own break (the 3->4 dB
cliff and the 5-15 dB plateau are structural, visible without any reference to [J1]), but the *choice to cut
there rather than at 2 dB* was made while the 10.6% figure was on screen. State this in the writeup and
report the 2 dB alternative (25.1%) alongside, rather than presenting 8.3% as untouched.

**Consequences for the build:**

- **`d_aug_jun19` is retired as a growth feature.** Its correlation with the Jun 19 *level* is **-0.899** —
  it is almost entirely a Jun 19 artefact, not an August signal — and its spread (sd 3.73 dB) is ~3x
  `d_aug_jun06`'s (1.32 dB). Use **`d_aug_jun06`** for vegetation growth. Jun 06 also inter-correlates
  properly with Aug (r = +0.63) and Oct (+0.42), while Jun 19 correlates with nothing (+0.13 / +0.27 /
  +0.31) — it is the odd date out for *level*, precisely because it is carrying a different physical signal.
- **`flood_excess = gamma0(Jun19) - gamma0(Jun06)` is added as the rice channel**, and it is the
  X-band HH analogue of R1's single biggest gain ([J4], rice VH(Aug)-VH(Jun), lambda +0.407) — at 1 m
  instead of 10 m, and on the transplanting date itself rather than inferred from a monthly composite.
- **`rfi_flag`** for the 19 saturating farms; excluded from the health index, imputed like `no_sar_data`.

---

# Phase K — P-D (Water Cloud Model) swap, D5-D6 (2026-08-02)

Code `src/wcm.py`, self-checked. **Outcome: REJECTED as a health-index component, with the cause
quantified.** The plan's D5-D6 exit criterion was "measurable improvement or documented rejection" — this
is the second, and it is the more useful of the two for the writeup.

## [K1] The inversion is sound, and it found a real property of the model first

Implemented El Hajj et al. RSE 176 (2016) eqs. (4)-(7) at the X-band HH VWC parameterisation
(A=0.0438, B=0.1047, C=0.0324, D=0.03971) [E3], inverted with `brentq`.

The calibration offset [J5]/[O1] is handled without ever using an absolute dB: eq. (7) supplies
`sigma0_sol` from theory, [J8] establishes **Jun 06 as a dry pre-monsoon near-bare scene**, so a per-farm

    k_farm = observed(Jun 06) / (C * exp(D * Mv_dry))

absorbs the offset *and* that farm's soil roughness together. Median k = **19.51 dB**, IQR **1.06 dB** —
the spread is the between-farm roughness term, and the fact that it is only 1 dB wide says the village's
soils are uniform.

⚠ **The self-check caught an error in my own reasoning before any result was produced.** I had written that
the WCM is monotonic in V. It is not. Expanding for small V:

    sigma0(V) ~ sigma0_sol + 2AB*V^2 - 2B*sec(theta)*sigma0_sol*V

the derivative at V=0 is **negative** — a thin canopy attenuates the soil return faster than it contributes
volume scattering, so backscatter **dips before it climbs**. The turning point is

    V* = sec(theta) * sigma0_sol / (2A)   = 0.68 kg/m^2 at Mv=12%, 1.39 kg/m^2 at Mv=30%

**Consequence worth reporting in its own right: below V* the inversion is two-to-one — X-band HH cannot
distinguish a sparse canopy from a denser one.** Early-season and sparse fields sit inside that band. The
code takes the upper (dense-canopy) root and flags the case rather than silently picking one.

## [K2] ★ Why P-D fails here: our inter-date radiometry cannot support an absolute model

The data fixes one number that no modelling choice can move:

    median sigma0(Aug 14) / sigma0(Jun 06) = 0.916      (August is 0.4 dB DARKER than dry June)

The WCM, at any monsoon-plausible August soil moisture, cannot reach that:

| assumed Aug Mv | bare soil alone, x dry June | **even the dip floor** |
|---|---|---|
| 20 Vol.% | 1.37x | 1.24x |
| 30 Vol.% | 2.04x | 1.76x |

The floor is the *darkest the model can be at that Mv for any canopy load whatsoever*. Observed 0.92x is
below it by a factor of ~1.9. Sweeping the assumption confirms it: August only becomes invertible for
**Mv <= ~10 Vol.%**, which is not a mid-monsoon soil moisture.

Two candidate causes, and the evidence favours the second:

1. **August 14 fell in a monsoon break.** Possible, but it would need the topsoil back to pre-monsoon dryness.
2. **Residual per-date calibration error of a few dB.** [J5] measured our per-date offsets against Round 1's
   independent implementation as **27.1 / 28.3 / 30.0 dB — a 2.9 dB spread**. The WCM needs the *inter-date*
   soil contrast (~2x, i.e. 3 dB) to separate soil moisture from canopy. **The discrepancy and the known
   calibration uncertainty are the same size.** The model is being asked to resolve a signal smaller than
   our radiometric error bar.

This is the honest verdict: **P-D is defeated by absolute inter-date radiometry, not by the physics and not
by the implementation.** It is exactly the failure mode a product with "absolute radiometric accuracy not
declared" (ESA EDAP) should produce, and it retroactively justifies the [O1] decision to report only
contrasts.

## [K3] What survives, and what is NOT swapped

- **The health index is unchanged.** WCM VWC is *not* substituted for the vigour component. On Aug 14 the
  inversion pins **96% of farms at the dip floor** at Mv=30 — a degenerate output whose Spearman correlation
  with the raw dB level is **-0.12**, i.e. it has stopped carrying the observation at all. Substituting it
  would have replaced a working feature with an artefact.
- **Oct 13 does invert cleanly** (median 2.60 kg/m^2, IQR 1.79-3.26) because October is drier and brighter,
  putting farms on the rising branch. Its ranking correlates **+0.70** with raw October dB — related but not
  redundant, since the per-farm k and per-pixel incidence enter it.
- **The ranking is robust even though the level is not.** Perturbing every Mv by +/-8 Vol.% moves the median
  VWC by 0.4-0.9 kg/m^2 but leaves the farm ordering at **Spearman 0.966-0.998**. So the inversion is
  usable as an *ordering* and unusable as a *measurement* — stated that way, not blurred.
- `vwc_*` and `vwcflag_*` columns stay in `farm_features.csv` as evidence for the writeup. `vwc_20250606` is
  **degenerate by construction** (it is the calibration date — every farm inverts to V* by definition) and
  must never be used as a feature.

**Rubric value.** A working WCM implementation, a published-coefficient inversion, a self-check that caught
a genuine non-monotonicity, and a quantified account of why the model cannot close on this sensor is worth
more on Technical Soundness than a fitted number would have been. This is the fourth documented negative,
after [G5], [H2] and [I1].

---

# Phase L — P-B (discriminative clustering + MRF) swap, D7 (2026-08-02)

Code `src/pb_mrf.py`, self-checked. **Outcome: ACCEPTED as a spatial regulariser and a
coherence check, REJECTED as an independent recovery of the crop map.** The distinction is
the whole result and it was only visible because of the cold-start ablation.

## [L1] Implementation

Bi et al. TGRS 2017 [E2] discriminative-clustering energy `E(Y,W|X) = Ec + Es`:

- `Ec` — softmax regression on 14 standardised features, L2 (C=1), **`class_weight="balanced"`,
  which is exactly the paper's 1/N_j correction**. It matters here: Cotton is 43% of area and
  Maize 6% [J1], so an unweighted fit learns "predict Cotton" and stops.
- `Es` — MRF smoothness on an 8-NN centroid graph (the same graph as the Moran's I in [J8], so
  the two numbers are comparable), edge weight `exp(-||v_i - v_j||^2 / 2 sigma)` per the paper.
  Adjacency alone does not force agreement — two touching fields that look different are only
  weakly coupled. BETA = 0.6.
- Alternating minimisation: L-BFGS for W, **ICM** (not belief propagation) for Y.

Features are deliberately **raw and standardised, not the D4 `crop_evidence` combinations** —
feeding my own hand-weights back in would make any agreement number circular. Exclusions carry
their own findings: `ktex` [H2], `subcoh` [I1], `vwc_20250606` [K3] (degenerate by construction).

The area constraint [J1]/[J3] is applied to the **unary before the MRF**, so smoothing can never
be blamed for breaking it. It holds: P-B shares land at Rice 0.108 / Cotton 0.422 / Maize 0.059 /
Bajra 0.085 / Groundnut 0.327 against the constraint 0.106 / 0.430 / 0.060 / 0.094 / 0.310 —
worst deviation 0.9 points.

Self-check asserts the two properties without which nothing below means anything: **ICM never
increases the energy** (1169.1 -> 280.7 on a synthetic graph) and **the pairwise term actually
smooths** (neighbour agreement 0.34 -> 1.00 at strong coupling on pure-noise unaries).

## [L2] Result: 89% agreement with the D4 map — and why that number is NOT independent

Warm-started from the D4 posterior, the energy falls monotonically over 8 iterations
(1154.9 -> 1108.1, `Ec` 158.4 -> 131.2) and settles at

    agreement with D4:  89.3% by farm, 89.2% by area

Read naively that is strong mutual confirmation of the crop map. **It is not, and the ablation
proves it.** Re-running from three random Dirichlet initialisations instead of the D4 posterior:

| seed | agree by farm | agree by area | iterations to converge |
|---|---|---|---|
| 1 | 0.090 | 0.100 | 1 |
| 2 | 0.090 | 0.100 | 1 |
| 3 | 0.090 | 0.100 | 1 |

**0.09 is chance.** From a random start the W-step learns nothing from the features, the
area-constrained unary is near-flat, ICM moves fewer than 0.5% of labels, and the whole thing
converges in a single iteration to a degenerate local minimum. Identical across seeds because
it is not finding structure — it is failing to.

**Conclusion, stated plainly: the 14 SAR features do not contain enough class structure to
recover the crop map on their own.** The 89% is the warm start surviving; P-B is doing spatial
regularisation of the D4 map, not independent discovery. Reporting the 89% without the
cold-start row would have been the single most misleading number in this project.

## [L3] What P-B is therefore used for

- **NOT** as a replacement crop map. `pb_crop` does not enter `submission.csv`.
- **As a spatial-coherence measurement.** The 10.7% of farms the MRF moves are, by construction,
  farms whose D4 label disagreed with both their neighbours and the learned discriminant — a
  ranked list of where the hand-weighted evidence is weakest. That is a usable uncertainty
  product and it is honest about being one.
- **As a stress test that D4 passed.** Perturbing the map through an independent optimiser with
  a different objective changes 1 farm in 9 and leaves every area share inside 1 point. The
  confusion table shows the movement is between the ADJACENT classes the physics says are hard
  (Groundnut<->Bajra 27 farms, Groundnut<->Cotton 35) and essentially never between the classes
  with real separation (Rice<->Bajra: 1 farm).
- Written to `results/pb_crop.csv` with full posteriors, per [J3] — probabilistic, never hard
  confident labels.

**Rubric value.** Same shape as [K2]: the implementation is faithful, the negative is quantified,
and the ablation that produced it is the kind of check a panel looks for. Fifth documented
negative after [G5], [H2], [I1], [K2] — though this one is a *partial* negative, since the
regularisation output survives.

---

# Phase M — I5 validation battery, D8 (2026-08-02)

Code `src/witness.py` (fetch) + `src/i5_validation.py` (all eight checks of MASTER_PLAN §4).
**Outcome: the CROP MAP validates strongly on independent sensors; the HEALTH INDEX validates
only weakly, and one uniformity test fails outright.** Both are reported. This is where the 20
"Validity & Plausibility" points live, and they are earned by checks that could have failed —
two of them did.

## [M1] The witnesses, and why they are legitimate

Microsoft Planetary Computer STAC: Sentinel-2 L2A and Sentinel-1 RTC as public COGs, anonymous
SAS token, Copernicus open licence. No account, free to anyone — satisfies the open-data rule.

**Sentinel-2 flew Sokhda on 2025-10-13 — the SAME DAY as our Capella October acquisition — at
0.003% cloud** (`S2B_MSIL2A_20251013T053659_R005_T43QCE`). A same-day optical witness is the
strongest independent check available for a health product. Sentinel-1 RTC C-band VH is
2025-10-10, three days off (`S1A_IW_GRDH_1SDV_20251010T010231_..._rtc`) — different band,
different polarisation, different geometry.

956 of 966 farms recovered on both. **Neither layer is an input.** Nothing in `submission.csv`
has ever seen them; that is what keeps the correlation meaningful and preserves SAR primacy.

Incidental sanity check: S1 VH median is **-14.7 dB**, textbook for vegetated fields. Our own
X-band medians sit near +7 to +10 dB, which is the [J5]/[O1] ~+28 dB offset showing up again from
a completely independent direction.

## [M2] ★ The crop map validates strongly — on sensors it never saw

| crop | median S2 NDVI (13 Oct) | median S1 VH dB | n |
|---|---|---|---|
| Cotton | **0.374** | -14.17 | 449 |
| Groundnut | 0.293 | -14.98 | 229 |
| Bajra | 0.255 | -14.84 | 138 |
| Rice | 0.234 | -15.49 | 86 |
| Maize | **0.199** | **-15.77** | 54 |

Kruskal-Wallis: **NDVI H=164.3, p=1.8e-34; VH H=95.8, p=7.7e-20.** The five classes — assigned
from X-band HH alone — have genuinely different October signatures on two unrelated sensors.

**And the ORDERING is the agronomically correct one, which no significance test could have
manufactured.** On 13 October, Cotton is the only crop still fully standing (picking runs
Oct–Jan, `COMPLETION` 0.45) and it has the highest NDVI *and* the highest VH. Maize is harvested
and bare (`COMPLETION` 0.95) and sits lowest on *both*. Rice, also harvested, sits second-lowest.
The classes rank in exactly the order the crop calendar predicts. This is the single strongest
result in the project.

**Tension with [L2], stated rather than hidden.** P-B cold-started at chance, which said the
features do not carry enough per-farm class structure to recover the map unaided. Here the same
classes separate at p=1e-34. Both are true and they are not contradictory: a signal too weak to
label an individual farm can still be overwhelming as a difference of group medians at n=966.
The correct reading is **the crop map is right about the village's composition and only
moderately reliable about any single farm** — which is precisely how it is presented, with
per-farm posteriors [J3] rather than confident labels.

## [M3] The health index validates only WEAKLY — reported as such

| witness | target | rho | p | n |
|---|---|---|---|---|
| S2 NDVI same-day | health_index, all farms | **0.071** | 2.8e-02 | 956 |
| S2 NDVI same-day | **health_raw_z (pre-ranking)** | **0.229** | 3.2e-12 | 904 |
| S1 VH | health_index, all farms | 0.130 | 5.3e-05 | 956 |
| S1 VH | within Cotton | **0.305** | 4.2e-11 | 449 |
| S2 NDVI | within Cotton | 0.168 | 3.5e-04 | 449 |
| S2 NDVI | within Maize | **-0.173** | 0.21 | 54 |
| S1 VH | within Maize | **-0.235** | 0.087 | 54 |
| S2 NDVI | within Bajra | -0.004 | 0.97 | 138 |
| S2 NDVI | within Groundnut | 0.016 | 0.81 | 229 |

Honest reading:

- **Positive and significant, but small.** rho 0.07–0.13 pooled is a real but weak agreement.
- **The pre-ranking score does better than the shipped one** (0.229 vs 0.071). Ranking
  *within crop* is deliberate — cotton and groundnut differ ~4 dB for reasons unrelated to
  health — but it demonstrably discards agreement with the witness. The trade is defensible and
  it is a trade, not a free lunch.
- **It works where there is canopy left to see.** Cotton (still standing on 13 Oct) is the one
  class with solid agreement on both witnesses. Bajra and Groundnut are ~0; Maize is
  *negative* on both. That is coherent rather than random: for a harvested crop the October
  observation is measuring bare soil and residue, so neither our index nor NDVI is measuring
  plant health there — they are measuring different things about dirt.
- **Consequence for the writeup:** the health index should be presented as **best supported for
  standing crops and weakly supported for harvested ones**, not as uniformly validated. The
  Maize negative is stated, not dropped.

## [M4] Spatial structure — passes against a permutation null

199 permutations, 8-NN graph:

| layer | Moran's I | null mean | null p95 | significant |
|---|---|---|---|---|
| health_raw_z | **0.1293** | -0.0008 | 0.0232 | yes |
| health_index | 0.0717 | -0.0006 | 0.0244 | yes |
| yield_estimate_to_date | 0.0668 | -0.0002 | 0.0219 | yes |

All three clear the 95th percentile of the null comfortably. Real agronomic variation clusters
(shared soil, irrigation, management); pure modelling noise would not. Note again that the raw
score is more structured than the ranked one — same cost of within-crop ranking as [M3].

## [M5] Ablation and weight perturbation — passes clearly

Spearman of each variant's ranking against the shipped ranking:

| variant | rho |
|---|---|
| drop `uniform` | 0.879 |
| drop `growth` | 0.904 |
| drop `level` | 0.948 |
| drop `persist` | 0.970 |
| drop `texture` | 0.983 |
| all five weights jittered x0.5–1.5, 20 trials | **min 0.966, median 0.985** |

No single family is carrying the result — the largest single-drop effect leaves rho 0.88 — and
the hand-chosen weights are not load-bearing: randomising every weight by ±50% moves the ranking
by at most 0.034 in Spearman. **The health weights are therefore not a tuned fit; the ranking is
determined by the features, not by my choice of coefficients.** `texture` and `persist` contribute
least and could be dropped with almost no effect, which is worth saying plainly.

## [M6] ⚠ The rubric's own sentence — one pass, one FAIL

The brief says a visibly more uniform canopy should score higher. Tested directly:

| measure | rho vs health_index | p | n |
|---|---|---|---|
| `cv_20250814` | **-0.343** | 1.6e-26 | 912 |
| `cv_20251013` | **-0.049** | 0.14 | 916 |
| `area_ha` (should be ~0) | 0.086 | 7.2e-03 | 966 |

**The first row is circular and must not be claimed as validation.** `cv_20250814` IS the
`uniform` family, weight 0.20 — of course it correlates. The only non-circular version of the
test is `cv_20251013`, which never enters the index, and **it comes back at -0.049, i.e. nothing.**

So: the index satisfies the rubric's uniformity sentence *by construction on the August date* and
**fails to generalise that property to the October date**. Two candidate explanations, both
reportable: October within-farm CV on a partly-harvested field is measuring stubble patchiness
rather than canopy patchiness, or the August uniformity signal simply does not persist. Either
way the correct statement is "uniform in August scores higher, by design; we could not confirm
this independently in October."

`area_ha` at rho 0.086 is small but non-zero — a slight tendency for larger farms to score
higher, most likely because more pixels means less speckle noise means less extreme statistics.
Worth flagging as a known residual bias rather than pretending it is zero.

## [M7] Cross-proposal agreement

- **P-A vs P-B crop map: 0.893 by farm, 0.892 by area** — carrying the [L2] caveat that this is
  a warm-started number and not an independent recovery.
- **P-A health vs P-D October VWC ranking: rho 0.169** (n=918). Weak. Consistent with [K3]:
  the WCM ordering is real but it is dominated by the per-farm `k` calibration and incidence,
  not by canopy, so it is not a strong second opinion on health.

## [M8] Agronomic plausibility of the village aggregate

| crop | farms | ha | median kg/ha to date | production t | completion |
|---|---|---|---|---|---|
| Bajra | 140 | 41.5 | 2589 | 106.4 | 0.95 |
| Cotton | 455 | 192.8 | 350 | 72.9 | 0.45 |
| Groundnut | 230 | 141.9 | 1890 | 267.8 | 0.75 |
| Maize | 54 | 26.7 | 2222 | 60.9 | 0.95 |
| Rice | 87 | 44.7 | 1617 | 71.1 | 0.95 |

Every per-hectare figure sits inside the plausible Gujarat kharif range for its crop, and each is
the district APY yield [SOURCES.md — the one column NOT retracted in J2] scaled by season
completion and the health modifier, so this is a consistency check rather than an independent
one. Cotton's 350 kg/ha reads low against a full-season figure and should: on 13 October cotton
is 45% through picking, and the number is explicitly yield **to date**.

## [M9] Scoreboard

| check | verdict |
|---|---|
| 1. S2 same-day NDVI vs health | weak pass (rho 0.07 ranked / 0.23 raw) |
| 1b. crop classes separate on witnesses | **strong pass** (p=1e-34, correct ordering) |
| 2. S1 C-band VH vs health | weak pass (0.13; 0.31 within Cotton) |
| 3. Moran's I vs permutation null | pass, all three layers |
| 4. ablation + weight perturbation | **strong pass** (jitter rho >= 0.966) |
| 5. agronomic plausibility | pass (consistency, not independence) |
| 6. cross-proposal agreement | qualified — see [L2] |
| 7. uniform canopy scores higher | **circular on Aug; FAILS independently on Oct** |
| 8. report everything that fails | [M3] Maize negative, [M6] Oct CV null, [M7] weak P-D |

---

# Phase N — I8 repeat-pass coherence, D8 second half (2026-08-02)

Code `src/i8_repeat.py`, self-checked. **Outcome: NEGATIVE, and — importantly — a negative that
is honest about being UNINFORMATIVE rather than dressing itself up as a physical finding.**
Answers open question [O2]. Seventh documented negative.

## [N1] Why it was attempted, and why the failure was predicted in writing first

Repeat-pass coherence is the one product that uses SLC phase ACROSS acquisitions rather than
within one ([I1]/sublook did the latter). The rubric names temporal coherence as a scorable SAR
physics axis. If it worked it would be the strongest crop-dynamics layer available from this data.

The pair is forced: **Jun19 x Aug14**. Incidence 28.768 vs 28.692 deg — 0.076 deg apart, by far
the closest of the six possible pairs (the others differ by 2.8–6.6 deg, hopeless). 56-day
baseline. All four scenes are left-looking, same beam.

Three reasons to expect failure, **written into the module docstring before the run** so the
result could not be retrofitted:
1. 56 days at X-band (3.1 cm) over a growing canopy. Vegetation decorrelates in days [B4].
2. **No orbit state vectors ship with these products**, so the perpendicular baseline is unknown
   and the flat-earth/topographic fringe cannot be removed analytically. We remove the dominant
   fringe empirically (2D spectral peak of the interferogram), which is strictly weaker.
3. Range pixel spacing differs between the two scenes, 1.2825 vs 1.2855 m — 0.23%, several
   pixels of drift across a 3900-column AOI. Handled by estimating the offset per 512x512 block
   rather than globally.

## [N2] Method, and the part that actually matters — the controls

Per 512x512 block: amplitude FFT cross-correlation for the offset (amplitude, not complex —
the phase is unrelated by assumption, but relative brightness survives, which is *why*
coregistering a fully-decorrelated pair is still possible); sub-pixel refinement by 3-point
parabola on the correlation peak; sub-pixel shift applied as a Fourier phase ramp on the complex
data (an interpolation kernel would smooth the speckle of one image only, which looks identical
to decorrelation); empirical deramp; 9x9 boxcar coherence, same window as [I1].

**A bare "coherence was low" claim is worth nothing, because a coregistration bug produces the
identical number to real decorrelation.** So three controls run every time:

| control | what it proves | value |
|---|---|---|
| **SELF** — Jun19 vs itself, same code path | estimator is not broken | **1.0000** (asserted > 0.9) |
| **NULL** — Jun19 vs Aug14 mis-registered 200 px | empirical bias floor of a finite boxcar | **0.1161** |
| **STABLE** — brightest 1% of pixels, real pair | separates the two failure modes | **0.1596** |

Synthetic self-check (`--selfcheck`, no I/O): coh(z,z) > 0.99; unrelated complex Gaussians give
floor 0.094; a known (+3.0, -5.0) sub-pixel shift recovered to 0.01 px.

**The refinement that changed the verdict.** The first run compared STABLE (0.1596) against the
all-pixel NULL (0.1161), giving +0.044 — which looked like a pass. That comparison is wrong: a
neighbourhood dominated by one strong scatterer has FEWER effective looks than a speckle-only
one, so its coherence bias is *higher*. Scoring bright pixels against an all-pixel floor
manufactures an excess out of nothing but statistics. Recomputing the floor on the **same
brightest-1% pixels in the null run** gives 0.1217, and the like-for-like stable excess drops to
**+0.0379** — below the 0.05 threshold fixed in advance.

## [N3] Result

    SELF        1.0000     estimator sound
    NULL        0.1161     bias floor, all pixels
    REAL        0.1254     coregistered, all pixels
    STABLE      0.1596     brightest 1%
    STABLE-NULL 0.1217     same pixels, mis-registered   <- the fair floor
    FARMS       0.1286     per-farm mean, median over 966 farms

    excess over floor  +0.0093
    stable excess      +0.0379   (like for like)

Median estimated block offset: -1.0 row, **-21.4 col** — a coherent, physically plausible
registration shift, not noise. But block peak-to-sidelobe is 13.9 against 59.2 for the self
pair, i.e. the correlation surface is far flatter on the real pair than it should be.

**Verdict as coded: "STABLE TARGETS ALSO AT THE FLOOR — coregistration not demonstrated, result
UNINFORMATIVE, do not claim a finding."**

## [N4] The honest reading, which is the point of this entry

Farm coherence 0.1286 against a floor of 0.1161 is **zero coherence**. That is entirely
consistent with the literature — 56 days at X-band over kharif crops should decorrelate totally.

**But we cannot claim it as a measurement of crop decorrelation**, because the stable-scatterer
control did not clear its own floor by the margin fixed in advance. The +0.038 on bright targets
is a weak hint that coregistration partly worked (as is the consistent -21.4 px offset), not
proof that it did. Two possibilities remain live and we cannot separate them:

- the pair really is totally decorrelated, **and** our coregistration is good enough to have
  shown coherence had there been any; or
- the residual fringe we could not remove without orbit state vectors is itself suppressing
  coherence, in which case the number measures our own limitation.

**Correct statement for the writeup: "repeat-pass coherence was implemented with sub-pixel
coregistration and three controls; farm coherence sits at the boxcar bias floor, but because the
stable-scatterer control did not clear its own floor we report this as uninformative rather than
as evidence of crop decorrelation."** Claiming the physical finding would be over-reading a
control we failed.

## [N5] Consequence for the deliverable

- `repeat_coh_jun19_aug14` written to `results/i8_repeat_coh.csv` and the geocoded tif is kept
  for the writeup figure, but **it does not enter `submission.csv`**. Nothing at the noise floor
  should influence a per-farm number.
- The temporal-coherence rubric axis is therefore served by **[I1] sub-look coherence** (zero
  temporal baseline, cannot decorrelate through time), which was built precisely because this
  outcome was anticipated. That design choice is now vindicated by measurement rather than by
  assertion, which is a better story than if I8 had quietly been skipped.
- Slip order note: I8 was first on the cut list. It cost under an hour and produced a documented
  negative plus a vindication of [I1], so it earned its place. **D9 notebook is next and nothing
  further should be spent here.**

---

# Phase P — I9 notebook, D9 (2026-08-02)

*(Letter O skipped: `O1`/`O2` are already open-question IDs in MASTER_PLAN and reusing
them as log tags would be ambiguous.)*

`notebooks/I9_pipeline.ipynb`, built by `notebooks/build_notebook.py`.
**Executed top-to-bottom from a fresh kernel via nbclient: 20 code cells, 0 errors,
2 figures, reproduction assert passed exactly.** Documentation & Reproducibility is 15
rubric points and the wording is "judge can follow *why* each step was taken, not just
what ran" — so the notebook is written as an argument, not a script dump.

## [P1] Structure and the choice behind it

Ten sections: data + the duplicate-SLC trap; geometry/radiometry + the calibration
finding; per-farm features; crop type + the [J7] provenance declaration; health index +
the WCM failure; both coherence experiments; the validation battery; the P-B
cross-check + its cold-start ablation; **every negative in one table**; deliverable +
reproducibility proof.

**Code cells call the existing `src/` functions rather than restating the logic.** Two
reasons: the notebook then cannot drift from the shipped pipeline, and any judge
checking `src/` finds the same code. Nothing is reimplemented for display.

`FAST = True` reuses `results/cache/*.tif`; `FAST = False` rebuilds every raster from
the SLCs through `prep_r2.main()` / `farm_stats.main()` / `sublook.main()` — the same
code path, ~25 min. Default is FAST so the notebook runs in about a minute for a judge.

**Generated, not hand-written.** `build_notebook.py` holds the cells as a flat list, so
the notebook can be rebuilt reproducibly and its JSON never has to be merged by hand.
Kept in-repo because D10 will want edits.

## [P2] The reproducibility proof

Not "it ran". The final cell rebuilds `submission.csv` from the notebook's own
in-memory `crop` / `hi` / `yld` arrays and asserts it matches the shipped file:

    crop_type match vs shipped submission.csv: 1.0000
    health_index max abs diff: 0.0
    REPRODUCED. Notebook ran top to bottom from a fresh kernel.

`D4.validate(sub)` is also called inside the notebook, so the schema gate is visible to
the judge rather than buried in a script. Provenance printed: **895 measured, 52
imputed_village_median, 19 rfi_flagged** — no farm dropped.

## [P3] What the notebook is careful NOT to claim

A closing section splits the claims explicitly. Claimed with evidence: village crop
composition validated on two unseen sensors in crop-calendar order; health ranking
robust to its own hyperparameters; spatial structure beyond a permutation null; schema
and agronomic plausibility. **Not claimed:** per-farm label reliability ([L2]), health
validity for harvested crops ([M3] maize negative), uniformity generalising past August
([M6]), absolute radiometric calibration ([J5]), any physical reading of repeat-pass
coherence ([N4]).

Every negative appears in a single table in §9, with the note that two of the seven
([K2] WCM, [N1] repeat-pass) were **predicted to fail in writing before being run** —
which is what makes those failures informative rather than embarrassing.

## [P4] Judgement calls worth recording

- The §7e circularity is stated *in the notebook itself*, not just the log. A judge
  reading only the notebook must not be able to mistake `cv_20250814` (rho -0.343) for
  independent validation of the rubric's uniformity sentence.
- The [J2] retraction is included as a short subsection under crop typing. A methodology
  that never shows a retraction is either lucky or not looking.
- The [M2]/[L2] tension (classes separate at p=1e-34, yet cold-start recovery is chance)
  is given its own paragraph rather than left for a judge to notice as a contradiction.
- The +28 dB offset is surfaced early (§2) with the reason the deliverable survives it —
  everything downstream is differences and within-crop ranks, never absolute dB.

D9 complete. **Next: D10 writeup (<=4 pages) + media gallery + cover image.**

---

# Phase Q — I10 writeup + media gallery, D10 (2026-08-02)

`docs/WRITEUP.md` (1754 words, ~2.7 pages — comfortable headroom under the 4-page cap)
and `src/i10_media.py` producing `results/figures/cover.png` + six `gallery_*.png`.
Presentation Quality is 10 points and the wording is **"legible at a glance"**, so every
figure was rendered, *opened and inspected*, and re-cut until it read in two seconds.
Four rounds of that found three real defects and one substantive error.

## [Q1] The gallery

| file | the one point it makes |
|---|---|
| `cover.png` | crop type + health, side by side — the whole brief in one image |
| `gallery_1_trajectory` | each crop draws a different season; the rice August trough |
| `gallery_2_confidence` | per-farm confidence is low by design; provenance of all 966 rows |
| `gallery_3_witness` | crop classes separate on two sensors they never saw, in calendar order |
| `gallery_4_robustness` | ablation + Moran's I against a permutation null |
| `gallery_5_negatives` | the coherence controls and the uniformity failure |
| `gallery_6_yield` | the deliverable and the village aggregate |

Fixed crop colour identity across every figure so the reader learns it once. **The
gallery includes the failures on purpose** — a gallery of only good news reads as
marketing, and the panel is scoring honesty under Validity.

## [Q2] ★ A substantive error the figure caught that the prose had wrong

Plotting the seasonal trajectory showed **rice is the BRIGHTEST class on 19 June and
the DARKEST on 14 August.** The notebook prose (and my mental model) said "rice floods —
a strong specular drop **in June**". That is wrong. Kharif paddy in Gujarat is
transplanted into standing water from **late June**, so the specular flooded-field
signature lands on **14 August**, recovering by October once the canopy closes and the
field drains.

The classifier was never wrong — it uses `d_aug_jun19`, which is strongly negative for
rice and is exactly this trough. Only the *explanation* was wrong, in the notebook and
in my head. Corrected in `build_notebook.py`, re-executed, and annotated directly on
the figure.

**Lesson worth keeping: the figure was the check on the prose.** Nothing else in the
pipeline would have caught a wrong physical story attached to a correct feature —
every validation number would have passed identically.

## [Q3] ★ A reported-number inconsistency, found and closed

`RESEARCH_LOG`/`PROGRESS` claimed weight-jitter **rho min 0.978, median 0.991**. The
notebook and the new gallery both computed **0.966 / 0.985** from the identical
procedure.

Cause: `i5_validation.check_ablation` drew its jitter from the module-level `RNG`,
which by that point had already been consumed by **199 Moran permutations**. The
notebook and `i10_media` call the same loop standalone with a fresh generator, so they
sit at a different point in the stream. Both draws are legitimate; **shipping two
different numbers for one claim is not.**

Fix: a dedicated `jrng = np.random.default_rng(7)` inside `check_ablation`, so the
number no longer depends on which checks ran before it. Canonical value is now
**min 0.966, median 0.985** in all four places (validator, log, progress, notebook,
gallery), and the derived prose "moves the ranking by at most 0.022" became 0.034.

This is exactly the class of error a human panel would catch by reading two documents
side by side, and it existed only because the RNG was shared.

## [Q4] Figure defects fixed after inspection

- **Cover and two other two-panel maps:** geopandas' `legend=True` steals height from
  its own axes for the colourbar, dropping that panel's title below its neighbour's and
  reading as a mistake. Colourbars moved to dedicated `make_axes_locatable` axes so both
  map panels keep an identical box and one title baseline.
- **`gallery_5` right panel:** was a 966-point scatter blob in which rho −0.343 and
  −0.049 looked identical — destroying the entire point of the panel. Replaced with
  **decile-binned medians**, where the circular curve falls steeply and the independent
  one is visibly flat.
- **`gallery_5` left panel:** two-line sub-labels drawn in data coordinates landed on
  top of the tick labels. Folded into three-line tick labels.
- **`gallery_1` right panel:** a handful of extreme farms compressed the population into
  a corner; clipped to the 1–99 percentile.
- Legends moved out from on top of the polygons they describe.

## [Q5] Writeup structure

Five sections: **Approach** (including the explicit "we cannot do polarimetry at
single-pol HH — here are the three axes we exploit instead" table, which converts the
one unavoidable weakness into a soundness argument); **Auxiliary data** carrying the
[J7] provenance declaration and the [J2] retraction; **Methodological detail**
(sub-look coherence, the second crop map with its cold-start caveat attached in the
same paragraph as the 89 %); **Validation** with the two failures kept in; and
**Limitations** with all seven negatives tabulated plus the +28 dB offset and *why the
deliverable survives it*.

Every caveat the plan required is present: [J7] provenance, [J2] retraction, [L2]
cold-start, [M3] maize negative, [M6] circular-vs-independent uniformity, [N4]
uninformative coherence, [J5] calibration, the area-bias residual, and the coverage
counts.

## [Q6] One open item for the user

MASTER_PLAN's D10 row says "all four **required writeup topics** covered", but the four
are not recorded anywhere in the evidence trail — only the ≤4-page cap, the gallery and
the cover image are. The writeup covers the conventional set (approach, data/aux use,
validation, limitations). **Worth confirming against the Kaggle Submission tab before
final upload** in case the host names four specific headings.

D10 complete. **Next: D11 — buffer, final schema check, submit.**

---

# Phase R — host dummy submission decoded, D10 correction (2026-08-02)

User supplied the host's sample writeup and `Sokhda_Dummy_Submission.xlsx`. Reading the
actual file settled three schema questions and **caught a 1000x unit error that would
have shipped.**

## [R1] ★ The yield column is TONNES/ha, not kg/ha

Host dummy `yield_estimate_to_date`: **1.24 – 9.00**, and their sample writeup says
"estimated yield (tonnes/hectare)". Ours was **kg/ha** (bajra 2589, cotton 350) —
**wrong by a factor of 1000.**

Every internal check passed with the wrong unit, because nothing in the pipeline knew
what unit the column was supposed to be in. The schema gate checked `>= 0`; the
agronomic plausibility check compared against the same APY source that produced the
error; the ranking, the Moran's I and the ablation are all scale-invariant. **No
amount of internal validation can catch a unit convention that only exists in the
host's file.** That is a real methodological lesson, not just a bug.

Fix: single conversion point in `d4_submission.yield_to_date` (`YIELD_T_PER_KG`), plus
a **unit guard in `validate()`**:

    assert mx < 25.0, f"max yield {mx} t/ha -- looks like kg/ha, unit error"

No kharif crop yields 25 t/ha, so anything above that is a unit error rather than a
modelling one. Shipped values: Bajra 2.589, Maize 2.222, Groundnut 1.890, Rice 1.617,
Cotton 0.350 t/ha. Production tonnages are unchanged (t/ha x ha = t, previously
kg/ha x ha / 1000 = t), so the village aggregate stayed self-consistent through the
change — a useful confirmation the conversion landed in exactly one place.

Downstream propagation: `i5_validation.check_agronomy`, `i10_media.fig_yield`, the
notebook aggregate cell (all had a now-double-counted `/1000`), the colourbar label,
and the prose in both the notebook and the writeup.

## [R2] 966 is right, the host's "967" is not

Their sample writeup says "967 individually digitized plots". **Their own dummy
submission has 966 rows, farm_id 1–966**, and the shipped shapefile has 966 features
with FID 1–966, no empty or invalid geometry. We ship 966 and say so in the writeup.
No action beyond the note — the count was never wrong.

## [R3] village_id = 1, not the shapefile's 22

Farm shapefile carries `ID_1 = 22` for Sokhda; the host dummy uses `village_id = 1`.
With a single village the field carries no information either way, so we follow the
host's schema reference and keep the shapefile value in `d4_debug.csv` under
`shapefile_village_id` for traceability. Added an assert so it cannot drift.

## [R4] Other things the dummy settled

- `health_index` is an **integer** 0–100 in the dummy; ours is float to 2 dp. The
  schema names the column, not the dtype, and a float carries finer ranking
  information, so we keep the float. Noted rather than changed.
- The dummy's per-crop yield bands (Maize 4–9, Rice 3.5–7) are **synthetic random
  values**, explicitly "not the expected or correct answer" — so they are NOT a
  calibration target. Our cotton 0.35 t/ha sits below their dummy minimum and is
  correct: lint yield, 45% through picking, reported to date.
- **[Q6] closed.** The sample writeup names no "four required topics" — the D10 row's
  phrasing was mine, not the host's. Required elements are the <=4-page cap, the media
  gallery, the cover image, the public notebook and the 5-column CSV. All present.

## [R5] Verification against the host file

    columns identical to host : True
    rows / ids identical      : True
    village_id identical      : True
    crop vocabulary ok        : True
    nulls                     : 0
    d4.schema PASS rows=966 max_yield_t_ha=4.125

Notebook rebuilt and re-executed clean (0 errors, reproduction assert still exact),
gallery regenerated, writeup updated with the unit statement and both schema notes.

---

## Phase S — D11, the final gate (2026-08-02)

### [S1] One script that can say NO

`src/d11_ship.py`. Eighteen checks, run last, exit code 1 on any failure. The
point is not that it passes — it is that up to now nothing in the repo could
answer "is the *upload* complete", only "is the *model* right". Those are
different failures and the second one has been checked to death.

Three of the eighteen exist only because of Phase R, i.e. they exist because the
host's file told us something our own reasoning did not:

    yield is t/ha not kg/ha   max 4.125 t/ha (host dummy max 9.00)
    village_id identical      village_id=[1]
    row count identical       966 rows

All three are checked **against `Sokhda_Dummy_Submission.xlsx` directly**, not
against a constant we copied out of it. A hardcoded `assert n == 966` would
still pass if the host reissued the file with a different plot count; reading
their file each run means the gate tracks the authority instead of a snapshot
of it. Cheap, and it is exactly the class of error that got past us once.

### [S2] Result

    18/18 passed
    d11.done checks=18 failed=0 status=READY

Schema identical to host on columns, order, row count, farm_id set, village_id;
crop vocabulary a subset of ours; zero nulls. health_index 0.25–100.00, yield
0.141–4.125 t/ha. Writeup 1872 words ≈ 2.9 pages against a 4-page cap. Notebook
carries no stored error outputs. Cover image, six gallery figures, submission
CSV all present.

### [S3] What the writeup-length check is actually for

`words < 2600` at ~650 words/page. A soft heuristic, and deliberately soft: the
cap is on the *rendered* PDF, which we do not control from Markdown. It is a
tripwire against the failure mode where a late edit adds two sections and
nobody re-counts — not a claim that the PDF is 2.9 pages. Stated here so the
number is not read as more than it is.

### [S4] Closing position

Seven documented negatives, one retraction, one physics error in prose caught by
plotting, one 1000× unit error caught only by the host's own file. Every one of
those is in the writeup. The product is a crop map that validates on two sensors
it never saw, a health index reported as weak where it is weak, and a
yield-to-date that is explicitly to-date.

Nothing further is scheduled. The remaining work is upload, which is manual.
