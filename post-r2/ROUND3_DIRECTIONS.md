# Where to go next, and how each direction can be killed

Written 2026-08-29, after e14. Everything here is ranked against a single measured fact rather
than against how interesting it sounds.

## The one number that ranks everything

Three independent measurements say the same thing, and they were not designed to agree:

| measurement | result | source |
|:--|--:|:--|
| sampling noise as a share of between-farm signal | **15.9%** | e11 |
| share of yield variance explained by the crop label alone | **eta^2 = 0.820** | e4 |
| agreement of six independent pipelines' crop labels | **kappa = 0.060** | e4 |

**The crop label is the bottleneck, and it is an information limit rather than a processing
one.** So a direction earns priority by adding *label information*, not by refining what we
already compute. That single test disposes of most of the obvious backlog.

---

## What e14 established today

`e14_embeddings.py` tested Google's Satellite Embedding v1 (AlphaEarth) - 64 continuous bands
at 10 m for 2025, encoding a full year of Sentinel-1, Sentinel-2, Landsat, DEM and climate.
It was chosen specifically because e13 had just rejected a *categorical* 10 m product: a mode
over 18 pixels is ill-posed at 0.18 ha, a mean of a continuous vector is not.

961/966 farms returned a complete vector. Five-fold **spatially blocked** CV (KMeans on
centroids, so no farm is predicted by its own neighbours):

| classifier | kappa | accuracy | majority baseline |
|:--|--:|--:|--:|
| 64-band embedding | **+0.155** | 48.5% | 47.0% |
| `area_ha` alone (size floor) | +0.017 | 38.2% | 47.0% |
| our own Capella features (self-check) | +0.753 | 83.2% | 47.0% |

Controls, both of which killed earlier candidates:

- **Permutation:** 5 shuffles give -0.001, +0.008, +0.007, -0.009, -0.045. Observed +0.155 is
  **8.3 permutation SDs** above the null. No CV leakage.
- **Farm size** (the control that killed Dynamic World): `rho(area, correct) = +0.016,
  p = 0.63`. Decile kappas range -0.006 to +0.323 with no sign flip. Not a size artefact.

**This is the first independent cross-sensor evidence that our Capella labels carry real crop
information** - kappa +0.155 against a six-team consensus of +0.060, from a sensor stack that
has never seen Capella. That matters on its own, because until today nothing outside our own
pipeline corroborated our labels.

### But the pooled kappa hides where it lives, and this is the actual finding

| our crop | n | embedding reproduces it |
|:--|--:|--:|
| **Cotton** | 449 | **84.9%** |
| Groundnut | 220 | 28.6% |
| Bajra | 147 | 10.9% |
| Rice | 86 | **4.7%** |
| Maize | 54 | **0.0%** |

**Essentially all of the agreement is cotton.** This matches the published prediction for
Sentinel-1 monsoon phenology in central India - cotton has the most distinctive signature,
while the cereal/legume group overlaps heavily - which was written down before the test ran.

So the honest reading is two-sided, and both sides are useful:

1. Our cotton labels (47% of farms) have independent support. Our rice, maize and bajra labels
   have **none**, from a year of two other sensors.
2. That is not proof they are wrong. An *annual* embedding compresses the year, and our rice
   channel is a two-date event - the 6 -> 19 June brightening driven by a rain event verified
   at the overpass hour (e12). A days-scale flooding signature is exactly what an annual
   average destroys.

**Verdict: the embedding is NOT adoptable as a label source** (0.0% recall on maize forbids
it). It **is** adoptable as a per-farm second opinion and as a prioritiser for where scarce
human effort should go. That distinction is what directions 2 and 3 below are built on.

---

# Tier 1 - directions that add label information

## D-1. Dense Sentinel-1. **CLOSED 2026-08-29 -- REJECTED, and both premises were wrong.**

> **Verdict (`e17_dense_s1.py`, written up in `LABEL_CORROBORATION.md`):**
> (a) "No dense series in the pipeline" was FALSE -- `witness_season.py` already holds ten
> S1 scenes, 12 Jun-10 Oct, orbit 34. Nothing needed fetching.
> (b) The cost was understated: `docs/REPORT.md:16` says Capella primacy is required BY THE
> GUIDELINES, so training the label on C-band is potentially disqualifying, not just awkward.
>
> Tested as a witness, at zero cost: dense S1 gives **kappa +0.135, BELOW the annual
> embedding's +0.155**. Rice 3.5%, bajra 1.4%, maize 7.4%. The stated kill criterion fired.
> Timing IS worth +0.089 kappa (mechanism was right), but it is not enough.
>
> **The finding that replaces it:** 42.5% of farms are corroborated by NEITHER independent
> sensor -- 91.9% of rice, 92.6% of maize, 87.8% of bajra, against 5.8% of cotton. As far as
> any independent sensor can tell, our map is cotton plus noise.

### Original rationale, kept for the record

**The gap.** We compute every feature from **four Capella dates**. There is no dense temporal
series anywhere in the pipeline. Published kharif crop classification in India using
Sentinel-1 time series reaches 83% overall accuracy single-sensor and 80-96% fused with
Sentinel-2. Sentinel-1 gives roughly 6-12 day revisit, so **20-30 dates over Jun-Oct 2025**,
VV and VH, at 10 m - free, and through the GEE project we already have working.

**Why it is not speculative.** e14 just showed that a *compressed annual summary* of these
same sensors recovers cotton at 84.9% over these exact 966 parcels. The sensors demonstrably
see this village. What the annual embedding destroys is phenological timing - which is
precisely what a dense series keeps, and precisely what separates the four crops the embedding
failed on.

**The real cost, stated plainly.** `s1_vh_db` is one of our two held-out witnesses. Training on
Sentinel-1 spends it. Nothing is fetched until a replacement witness is reserved and frozen -
candidates are a Sentinel-2 date outside the S1 training window, or a fully withheld Capella
date. **Reserve the witness first; this is not negotiable, because an unwitnessed pipeline is
how five of six teams shipped an undetected bug.**

**Kill criterion.** Blocked-CV kappa on the four non-cotton crops no better than e14's. If a
dense series cannot beat an annual average on rice and maize, the timing hypothesis is wrong
and this closes.

## D-2. Label as a distribution. **CLOSED 2026-08-29 -- propagation REJECTED as ill-defined.**

> **Verdict (`e18_label_distribution.py`, written up in `LABEL_DISTRIBUTION.md`):** the
> posterior already exists (`p_Rice..p_Groundnut` in d4_debug.csv) and is openly unsure --
> median max 0.409, 69.4% of farms below 0.5. But it is **not calibrated in level** (Q1
> under-confident by +28.7pp, curve non-monotonic) and **barely ranks within crop** (only
> cotton clears p<0.05, at rho +0.095; rice is negative).
>
> **The blocker is e15.** Cotton's label SD is **2.25x its own yield**, because cotton is lint
> and the other four are grain. An expectation over the crop posterior therefore ADDS
> NUMBERS IN DIFFERENT UNITS, moving the village total **+12.8%**. D-2 is not unhelpful, it
> is ill-defined until e15's unit question is settled. That dependency was invisible until
> both experiments existed.
>
> **Also retired:** e11's inference that the crop label is the dominant error. Label entropy
> does NOT predict witness disagreement (rho -0.021 within crop, +0.033 global) any more than
> sampling SE did (+0.052). Neither measure predicts it.
>
> **Adopted:** ship the posterior as transparency, not as arithmetic.

### Original rationale, kept for the record

**The gap.** We ship one hard label per farm and a yield that is 82% determined by it. A wrong
label is a silently wrong yield with no trace in any output.

**What changed.** Until e14 there was no second opinion to build a distribution from. Now there
is a per-farm cross-sensor posterior, plus our own Capella posterior, plus a calibrated
sampling SE (e11, split-half ratio 0.966).

**What to build.** Per farm: agreement flag, label posterior, and yield propagated through the
label distribution rather than through the argmax. Village total becomes an interval.

**Test.** (a) Does the yield interval widen exactly on the farms where the two sensors
disagree, and not elsewhere? (b) Does the village aggregate stay inside the band implied by
Round 1's official MSE of 11.071? A method that moves the aggregate materially is changing the
answer, not quantifying it.

## D-3. Ground-truth selection. **DONE 2026-08-29 -- MY OWN PROPOSAL WAS REJECTED.**

> **Verdict (`e16_gt_selection.py`, written up in `GROUND_TRUTH_SELECTION.md`):** the active-
> learning citation below is about selecting TRAINING labels; our sample MEASURES a frozen
> map. Uncertainty-first selection is biased **-12.4pp** at moderate dependence and -23.6pp at
> strong, and inverse-probability weighting does not rescue it. **Stratified 20-per-crop is
> kept.** Active learning does win the competing objective (47.3 errors found per 100 vs 35.1)
> -- the two goals are formally in conflict. The hybrid (70 stratified + 30 targeted) is
> unbiased and becomes correct once D-2 gives discovered errors somewhere to go.
>
> **Real defect fixed:** seven degenerate parcels were in the eligible pool and one was staged
> for a human to identify (farm 19, 4.8e-09 ha). Guard added to `src/make_gt_sample.py`, sheet
> regenerated, two assertions added.

### Original rationale, kept for the record

**The gap.** Track E is blocked on a person doing per-record AnyROR VF-12 lookups. 100 rows are
staged in `ground_truth_TEMPLATE.csv`. **How those 100 were chosen has never been optimised.**

**What the literature says.** Spatially explicit active learning reached 80% overall accuracy
at **97 samples**, against 169 samples for conventional selection - same accuracy, 43% fewer
lookups. The selection rule is worth more than the sample size.

**The rule to use here, which e14 supplies for free.** Prioritise farms by (i) Capella-vs-
embedding disagreement, (ii) predicted sampling SE, (iii) crop stratification weighted toward
**rice, maize and bajra**, where e14 found *zero* independent corroboration and where our
30.8% groundnut share collides with Orion's 16%.

**Test before asking anyone to type anything.** Simulate on our own labels: how many lookups
does an active-learning order need before the estimated accuracy stabilises, against a random
order? If the two curves coincide, keep the simple random sample and say so.

**Cost: zero.** It re-sorts a file that already exists.

---

# Tier 2 - directions that attack yield

Yield is a scored output and only 18% of it is anything but the label, so these are second -
but two of them are cheap and one is a unit-error risk on 47% of the village.

## D-4. Cotton anchor. **DONE 2026-08-29 -- anchor kept, defect documented and guarded.**

> **Verdict (`e15_cotton_anchor.py`, written up in `KHARIF_ANCHORS.md`):** the APY table does
> mix units -- cotton is bales-of-lint at ratio 5.76 while the other four crops sit at
> 0.91-1.08 -- but the anchor is **kept**. Every official source (APY, USDA FAS, CEIC,
> Gujarat state) reports cotton as lint; the host-dummy test was **discarded for failing its
> own control** (it condemns maize and rice too); the field is split 4:1 toward lint; and the
> ordering test mildly opposes conversion. Restating would move the village total **+25.0%**
> on evidence that does not decide. Two things adopted: a unit statement in the deliverable,
> and a regression assertion in `post-r2/tests_regression.py`.

### Original rationale, kept for the record

`KHARIF_ANCHORS.md` validated bajra (adopted, 2.714 -> 1.91 t/ha) and groundnut (rejected on
out-of-sample evidence). **Cotton does not appear in it at all**, and cotton is 449 of 961
farms.

The specific risk is a unit trap, not a modelling one: Indian cotton yield is customarily
reported as **lint** in kg/ha or in **bales/ha (1 bale = 170 kg lint)**, while everything else
in our table is seed or grain. A lint/seed-cotton mix-up is roughly a 3x error on half the
village total, and `d4_submission.py`'s only guard is `assert mx < 25.0`, which a 3x cotton
error passes without complaint.

**Test.** Pull the district cotton series by season and unit from the same data.gov.in resource
used in e10, run the same four validations (ratio stability, share trend, temporal CV,
cross-source area agreement), and check the shipped 0.35 t/ha figure against both unit
conventions.

## D-5. Wire the water-cloud model. (C4 / D2, coded but unused.)

`src/wcm.py` exists and `wcm_k_db` plus `vwc_*` columns are already computed per farm per
date - and nothing consumes them. WCM is the physical route to a *within-crop* yield
modulation, which is exactly the 18% the label does not explain.

**Test.** Does adding WCM change the within-crop yield ranking against a reserved witness, at
all? If it moves nothing, drop the columns rather than shipping a model that does not act.

---

# Tier 3 - defensive, and worth real marks in a rubric-judged round

## D-6. Failure-mode regression suite. **STARTED** -- `post-r2/tests_regression.py`, 3 checks passing.

Between them the five other teams document a geoid bug, a 1-based/0-based FID join error, a
calibration double-correction, an SNR-proxy artefact and a speckle-filter-induced correlation.
**Every one of them survived internal consistency checks in a competent pipeline.** Our own
scale-factor error is a sixth of exactly that class, and e12's "village extent 139 x 1110 km"
was a seventh caught only because the number was absurd on its face.

Each becomes one cheap assertion. Together they are a test suite no other team has, and the
suite is itself a novel contribution to write up.

## D-7. Ship the two things already validated and still unshipped.

- **Calibrated per-farm uncertainty** (e11: split-half ratio 0.966, rho +0.9663), presented
  honestly as *sampling* uncertainty, which is not our dominant error term.
- **The ten-farm non-crop flag** (e13): flagged by our own SAR rule *and* Dynamic World,
  median health 1.1 against a village median of 50.7. A flag, never a filter.

---

# Priced out - do not spend Round 3 on these

| candidate | why not | evidence |
|:--|:--|:--|
| Any covariate coarser than ~1 km | ceiling 0.041 at 1 km, **0.000** past 11 km | e12 |
| ERA5 / NASA POWER / OpenWeatherMap history | one value for all 966 farms | e12 |
| WorldCereal crop type | 2021 product, **kappa = -0.010**; v2 not due until 2026 | e13 |
| Dynamic World as a filter | half a farm-size detector, sign flips across deciles | e13 |
| Quegan-Yu speckle filter | buys 5.6-6.4% of between-farm signal | e11 |
| USDA ERS | US farm *finances*, 16 US states | e12 |
| **Satellite Embedding as a label source** | **0.0% recall on maize, 4.7% on rice** | **e14** |
| Forcing polynomial order 2 in geocoding | 0.07 m, immaterial; recommendation withdrawn | e8 |

Coarse data keeps exactly two legitimate uses, both about level or timing rather than ranking:
**temporal context** (the 19 June rain event, verified at the overpass hour) and **aggregate
anchors** (district yield, which is never asked to rank).

---

# Cheap ideas not yet tested, listed so they are not lost

- **Sentinel-2 harmonic / gap-filled NDVI.** Monsoon cloud is the obvious objection, so the
  first test is a cloud-free scene count over Jun-Oct 2025, before any fitting.
- **Neighbour label smoothing.** Farmers plant in blocks; `src/pb_mrf.py` already exists. Test
  Moran's I on the label field first - if labels are not spatially autocorrelated beyond
  chance, there is nothing to smooth.
- **Full-resolution SLC texture** rather than texture on the detected product. We already have
  `subcoh_*` from sublooks; GLCM currently runs post-detection.
- **The e13 irrigation lead.** `rho = -0.167` against withheld NDVI, wrong-signed but
  significant, and coherent with the kharif/summer occupancy story in `KHARIF_ANCHORS.md`.
  Open lead, not a result.

---

# Suggested order

1. ~~**D-4 cotton anchor check**~~ - **done**, anchor kept, defect guarded.
2. ~~**D-3 active-learning reselection**~~ - **done**, proposal rejected on test; sheet defect fixed.
3. ~~**D-1 dense Sentinel-1**~~ - **closed**, rejected on test; the series was already in the repo.
4. ~~**D-2 label as a distribution**~~ - **closed**, propagation ill-defined until e15 is settled.
5. **D-6 / D-7** - defensive and presentational, and both are already mostly done.

Nothing above is adopted. Each entry names the test that decides it and the result that would
kill it, which is the same standard that has already rejected six of the ten ideas examined
since Round 2 ended.
