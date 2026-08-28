# Round 2 shortlist: what the other five teams did, and what we take from it

Written 2026-08-29, after the Round 2 writeups went public and six teams were shortlisted.
Sources are the five competitor writeups as published. Every number attributed to us in this
document was recomputed from the shipped artefacts at the time of writing, not quoted from
`docs/REPORT.md`, so the comparisons are measured rather than remembered.

The five other teams:

| # | Team | Writeup title | One-line identity |
|:--|:--|:--|:--|
| 1 | **Coding Bits** | Crop Health & Yield from Capella X-band SAR - Sokhda Village | The methodologist. Spatial hold-out for every fitted weight |
| 2 | **8bit** | SAR-Only ... Incidence-Angle-Corrected Capella | The purist. No optical input at all, incidence-matched pairs only |
| 3 | **Megalodon** | Worst band, best resolution | The instrument specialist. Retracted its own published finding |
| 4 | **Project Orion** | Per-Farm Crop Health and Yield-to-Date from Raw Capella X-Band SLC | Our methodological twin, and our sharpest critic |
| 5 | **oindrieelmondal** | X-Band SAR Crop Health & Yield-to-Date for Sokhda | The most candid about its own weaknesses |

---

## 1. The finding that matters most: our radiometric calibration is wrong

This is not an adoption suggestion. It is a defect in our pipeline, found by reading two
competitors and then measuring our own data.

### 1.1 What we ship

`src/prep_r2.py` forms brightness as

    beta0 = scale_factor * |z|^2

and carries a comment asserting that squaring the scale factor was a Round 1 bug.
`docs/REPORT.md` §2.4 then concedes that our gamma0 "reads about +17 dB above the physically
expected level" and attributes this to Capella's undeclared absolute accuracy.

### 1.2 What two other teams ship

Both use the *square*:

- **Coding Bits**: `sigma0 = (scale_factor * |A|)^2 * sin(theta)`. They state they tested our
  convention explicitly - "the scale factor applies to power rather than amplitude" - and rejected
  it because it places the scene maximum at **+46.9 dB**, not physically attainable for a
  distributed target. Theirs gives a scene max of **+20.2 dB** and a median field of **-20.2 dB**.
- **Project Orion**: `beta0 = |I+jQ|^2 * scale_factor^2`, citing Capella's own reference
  implementation (`capella-reader`, `rtc_isce3.py`: `beta0_complex = SF * DN`). A complex
  amplitude scaled by SF gives power scaled by SF squared. Their AOI median gamma0 is **-21.5 dB**.

### 1.3 The measurement that settles it

Our scale factors, read from the product metadata:

| date | scale_factor | 10log10(SF) |
|:--|--:|--:|
| 2025-06-06 | 2.121865e-03 | -26.73 dB |
| 2025-06-19 | 2.362054e-03 | -26.27 dB |
| 2025-08-14 | 1.989032e-03 | -27.01 dB |
| 2025-10-13 | 1.364434e-03 | -28.65 dB |

Spread across dates: **1.731x = 2.38 dB** - matching Megalodon's independently reported "1.73x".

Median gamma0 over our own cached AOI rasters, as shipped, versus the same rasters under the
squared convention:

| date | ours, as shipped | under SF^2 | scene max, as shipped |
|:--|--:|--:|--:|
| 2025-06-06 | **+7.44 dB** | -19.29 dB | +41.74 dB |
| 2025-06-19 | **+8.11 dB** | -18.15 dB | +49.45 dB |
| 2025-08-14 | **+7.22 dB** | -19.79 dB | +47.36 dB |
| 2025-10-13 | **+9.26 dB** | -19.39 dB | +47.04 dB |

Three independent lines of evidence converge:

1. **Physics.** A median field gamma0 of +7 to +9 dB means the field returns roughly five times
   more power than it receives. That is impossible for a distributed agricultural target. Under
   SF^2 we land at -18 to -20 dB, the textbook range for vegetated surfaces.
2. **Two competitors' measured values.** Coding Bits -20.2 dB, Orion -21.5 dB. We land at
   -18.2 to -19.8 dB under the squared convention. Agreement.
3. **Coding Bits' falsification test reproduces on our data exactly.** They report the rejected
   convention giving a **+46.9 dB** scene max. Ours, using precisely that convention, gives
   **+41.7 to +49.5 dB**. Their accepted convention gives **+20.2 dB**; ours under SF^2 would be
   about +20.8 dB. The 26.7 dB gap between the two conventions is exactly 10log10(SF).

Our own report already noticed the anomaly and explained it away as a vendor property. The cause
was our own formula.

### 1.4 What it actually costs us

Honest accounting, because the damage is smaller than the error sounds.

The scale factor is **per-scene, not per-pixel**, so the error is one constant dB shift applied
to all 966 farms on a given date. Consequences:

- **Anything z-scored or ranked across farms within a fixed date or date-pair is untouched.**
  The constant cancels. This covers `level`, `growth`, `uniform`, and the within-crop health
  scoring - i.e. most of the health index.
- **Cross-date differences carry a spurious constant offset**, again identical for every farm:

  | quantity | spurious offset |
  |:--|--:|
  | `growth` = 14 Aug - 19 Jun (health) | **+0.75 dB** |
  | `completion` = 13 Oct - 14 Aug (yield) | **+1.64 dB** |
  | June pair, 6 -> 19 Jun (rice evidence) | **-0.47 dB** |
  | season span, 19 Jun -> 13 Oct | **+2.38 dB** |

- **The season integral does not cancel**, because it combines dates in linear power and each
  date is scaled differently. Measured: Spearman between the shipped integral and the corrected
  one is **0.9916** (n=913), Pearson 1.0000; median rank shift 19 places, **124 farms move more
  than 50 ranks and 11 move more than 100**. Real, but the ordering broadly survives.
- **Every absolute-level claim is void.** §2.4's "+17 dB above expected" is really about +27 dB,
  and its stated cause is wrong.

**Verdict:** our shipped rankings are largely robust, which is a defensible position, but the
*explanation* in the report is incorrect and a judge who knows Capella will see it. This must be
fixed before Round 3, and fixing it is cheap - one multiply per date.

**Actions:**
- Correct `src/prep_r2.py` to `beta0 = scale_factor**2 * |z|**2`, and delete the comment claiming
  the square was an R1 bug (it was correct).
- Rewrite `docs/REPORT.md` §2.4. The new version is stronger, not weaker: we can now claim an
  absolute level consistent with two independent teams, instead of conceding a 17 dB discrepancy.
- Re-run the pipeline and diff. Expect the health index to be nearly unchanged and the yield
  accumulation term to move for roughly 12% of farms.

---

## 2. Team profiles

### 2.1 Coding Bits - the methodologist

The strongest methodology in the field, and the one we have most to learn from.

| axis | what they did |
|:--|:--|
| Calibration | `sigma0 = (SF*|A|)^2 sin(theta)`, chosen by physical-plausibility falsification |
| Geocoding | **Thin-plate spline** over the 225 GCPs. Polynomial left ~8 m residual against a 24.7 m median plot dimension; the spline interpolates every GCP exactly. Verified at runtime by re-running under a forced polynomial and asserting the outputs differ |
| Speckle | **Quegan-Yu multitemporal filter** - exploits cross-date correlation instead of spatial averaging, so a 0.4 ha plot keeps its full pixel count. 2.4-2.8x effective looks, no spatial blurring |
| Crop type | Area constraint + **November** Sentinel-2 greenness. Explicitly *not* SAR. Dual-lever allocation: `score[i,c] = L[i,c] + price[c] + gamma[c]*z(log area_i)` - the price fixes area, the size preference fixes the plot-count distribution |
| Health | `CHI = 0.60 Vigour + 0.20 Uniformity + 0.10 Conformity + 0.10 Wetness`. Three weights are physical priors; **only one is fitted, and under spatial hold-out** (west half selects, east half reports) |
| Yield | Season-integrated backscatter in linear power. Weight on health chosen by the same hold-out; **zero weight on health selected**, monotonic across the range |
| Validation | vs Oct NDVI rho=+0.622 (n=879); >0.8 ha rho=+0.742; 5-fold out-of-sample R^2=0.621 |
| Village total | **1,268 t** across 447.5 ha |

**What is genuinely excellent:**

1. **Spatial hold-out for weight selection.** West half selects the weight, east half reports the
   result. They then report that the western optimum (w=0.45) improves the east by only 0.0006 -
   within noise - while the applied physical prior (w=0.10) improves *both* halves independently
   (+0.0143 west, +0.0101 east). That is how you distinguish a generalising term from an
   overfitted one, and they used it to *reject* their own data-driven optimum.
2. **The informative null.** For the radar-only crop map they do not compare against random
   assignment. They note the area constraint alone induces a crop/plot-size association that may
   correlate with greenness independently, build that constraint-only null (H=12), and show the
   radar map beats it (H=115). Most teams, us included, compare against a null that is too easy.
3. **The model-ceiling test, and refusing the ceiling.** A gradient-boosted regressor predicting
   NDVI scores 0.560 within crop against 0.462 for their unfitted index. They **do not adopt it**:
   an index optimised to predict NDVI is trainable only where optical data already exists, which
   forfeits the operational reason to use radar. That is a rubric-winning argument.
4. **Using the rain event rather than discarding it.** 12.5 mm fell in the six hours before the
   19 June pass. Rather than drop the scene, they reason that a closed canopy attenuates the soil
   contribution, so the *magnitude of the rain response is an inverse proxy for canopy cover* -
   the only June canopy information in the dataset. Water Cloud Model, applied backwards.
5. **Plot-size de-biasing.** Mean backscatter rises with plot area (r up to +0.27) purely because
   larger samples are better determined. They regress each feature on log(area) and remove the
   trend; residual area correlation falls below 0.001. **We do not do this.**
6. **Degenerate-output assertions.** Schema checks pass on a collapsed index or a single-crop map.
   They test for those explicitly.

**Where they are weaker than us:** their crop map is driven by Sentinel-2, not SAR, in a SAR
challenge - they flag this honestly but it is a real exposure. Their village total of 1,268 t is
2.1x ours, unreconciled.

### 2.2 Team 8bit - the purist

The shortest writeup, and the only one that is genuinely SAR-only.

- **The core idea, and it is a good one:** the four scenes span 28.69-35.24 deg incidence. Rather
  than correct for that, they **anchor every temporal metric on the 19 Jun / 14 Aug pair, which is
  0.08 deg apart**, making it radiometrically comparable with no empirical correction at all.
- Crop assignment: Round 1 acreage as an area constraint in a **transportation linear program**
  minimising phenological template mismatch. Explicitly "a constraint, not a join key".
- Health (X-CHI): October canopy level, Jun->Aug establishment, phenological conformity,
  speckle-corrected within-field evenness - each **ranked within crop class** before aggregation.
- Yield (RYPI): multiplicative - accumulated canopy x conformity x evenness, scaled village-wide.
- Validation: Sentinel-2 13 Oct (0.2% cloud), held out entirely. NDVI rises 0.260 -> 0.415 across
  health deciles (**+59% spread**), decile-trend rank correlation **+0.988**, Kruskal-Wallis
  **H=243, p=2e-51**. Reproduces with an identical SHA-256.

**What to take:** the decile-trend presentation. "NDVI rises monotonically from 0.260 in the
lowest health decile to 0.415 in the highest, rank correlation +0.988" is far more legible to a
judge than a single scalar rho, and it is computed from data we already have.

**Their weakness:** almost no negative results, and the writeup is thin on mechanism. We beat them
comfortably on honesty and depth.

### 2.3 Megalodon - the instrument specialist

The best physics, and the single most impressive act of scientific honesty in the field.

| axis | what they did |
|:--|:--|
| Crop type | Re-ran frozen Round 1 rules on the new polygons. Cotton 452 / Groundnut 341 / Rice 133 / Bajra 40, **Maize 0** |
| Geocoding | RPC through Copernicus DEM to 1.5 m, co-registered to 14 Aug |
| Grid alignment | Slide the stack across the polygons, keep the shift maximising **farm-explained variance**. Shuffling farm labels collapses it to 0.0005 |
| Health | Water Cloud Model: `L` (peak-date level) + `V` (peak minus own June baseline), equal weight, within crop calendar |
| Yield | District APY x crop progress x health multiplier, area-normalised to mean 1 so health redistributes without inflating the anchor |
| Validation | **vs Sentinel-1 VH rho=0.746** (fully independent); vs S2 NDVI 0.616; best of nine alternatives 0.608/0.509; margin +0.135 [0.074, 0.201] |
| Village total | **578.34 t** to date, 905.50 t full season |

**The retraction.** They first published that more uniform fields score higher (rho=-0.53) -
exactly what the rubric expects. Then they found the texture had been computed on
noise-subtracted intensity, which adds variance in proportion to how near the noise floor a farm
sits; dim farms are near the floor *and* unhealthy, so the statistic was **a signal-to-noise proxy
wearing an agronomic label**. Corrected, it gives rho=+0.02, and all five structure metrics
reverse sign: the best fields are the *more* variable ones (rho=+0.43 once brightness is
partialled out). Their explanation is that the uniform-is-healthy expectation comes from optical
imagery; at 1.2 m X-band a healthy canopy is resolved, so rows and biomass gradients are real
structure. **"Uniform here means uniformly nothing."**

This should worry us. **Our `uniform` family carries the single largest weight in our health
index (0.301) and has the same sign as their retracted finding.** Our own §7.1 finding 3 already
reports that the uniformity-health relationship "holds on the date that feeds the index but fails
on an independent date". Megalodon supplies the mechanism for why. This is the highest-priority
item after the calibration fix.

**Other things they did that we did not:**

- **Measured the auxiliary-data ceiling *before* fetching anything.** A covariate constant within
  a cell can explain at most 0.226 of farm-to-farm health variance at 250 m, 0.049 at 1 km, and
  **0.000 at 50 km**. NASA POWER is a 50 km cell against a 3.4 km village - it cannot rank farms
  at all. We use NASA POWER for rainfall context; this is the argument for why that is the
  correct, and only, use of it.
- **The geoid bug.** 14.96 m out against the vendor preview because geoid undulation came from a
  metadata field not on the terrain surface. Fixing it (N=-60.00 m, matching EGM2008 for Gujarat)
  raised farm-explained variance from 0.39 to **0.51**. Their lesson: *per-date consistency cannot
  catch a common-mode error in your own chain* - which is exactly the class of error our
  calibration bug belongs to.
- **A 1-based/0-based FID join bug** that attached every farm's statistics to its neighbour. Two
  independently computed layers shifted identically, so they still agreed and the error read as
  physics. Caught only because the same quantity computed two ways gave two answers.
- **Pre-registration.** Decision reference, statistic, cohort, bootstrap and candidate list went
  into a protocol file *before* any candidate ran, because "selecting a pipeline by validation
  score is fitting one level up from the coefficients".
- **Confidence that predicts error.** Ranking farms by their index and again by Sentinel-1,
  disagreement falls monotonically across all five confidence quintiles (0.292 -> 0.149).
- **Rain physics at 9.65 GHz.** ITU-R P.838: a 25 mm/h cell costs ~8.6 dB two-way, larger than any
  between-date offset present. 19 June took 21.9 mm yet measured *brighter*, so wet-soil
  brightening dominates attenuation.

### 2.4 Project Orion - our methodological twin, and our critic

Structurally the closest to us: same dasymetric instinct, same insistence on reserved validation
scenes, same habit of reporting what failed. Also the team that argues directly against our
central design choice.

**The collision.** Orion reads Round 1's Sokhda output as *village-level hectares* and then
refuses to use it:

> "It is deliberately not used as a prior: Round 1 classified pixels, and its log records
> per-village shares as its least stable output - processing changes that barely moved the
> aggregate score shifted individual villages by over 6 percentage points, cotton being the crop
> mass repeatedly left."

Their final cotton share is **13.7%**, against the **43.0%** their own Round 1 pipeline produced.
They present that disagreement as a result.

**And here is the thing they did not know.** Their reported Round 1 read for Sokhda is
Rice 10.6 / Cotton 43.0 / Maize 6.0 / Bajra 9.4 / Groundnut 31.0%. Ours, recomputed from the
shipped submission, is:

| crop | Orion's R1 read | **our shipped share** | delta |
|:--|--:|--:|--:|
| Cotton | 43.0% | **43.22%** | +0.22 |
| Groundnut | 31.0% | **30.76%** | -0.24 |
| Rice | 10.6% | **10.60%** | 0.00 |
| Bajra | 9.4% | **9.45%** | +0.05 |
| Maize | 6.0% | **5.97%** | -0.03 |

**Two independent Round 1 pipelines agree on the Sokhda crop mix to within a quarter of a
percentage point.** Orion calls this constraint unstable and abandons it; we hold it; and their
own number is ours. (Caveat: I cannot rule out that both teams recovered a common published
source rather than converging independently. Worth establishing before leaning on it in public -
but if it holds, it is the strongest single defence of our approach we have.)

**Where the four teams actually land on cotton:**

| team | cotton share of 447.5 ha |
|:--|--:|
| Megalodon | 48.5% |
| **GDHTM (ours)** | **43.2%** |
| oindrieelmondal | 39.4% |
| Project Orion | 13.7% |

Three teams cluster at 39-49% by three different methods. Orion is the lone outlier, and the
outlier is the team that discarded the constraint.

**The maize cross-check kills it.** Orion assigns maize **130.4 ha** in Sokhda alone. Megalodon
cites official Vadodara Kharif-2025 statistics putting maize **under 50 ha district-wide**. Orion's
single village exceeds its entire district by 2.6x. Ours is 26.7 ha. Megalodon's is 0.

**What Orion does better than us, and we should take:**

1. **Two-tier crop labels with explicit confidence.** Rice and cotton get Tier 1 from measured
   physical thresholds and are 100% stable across clustering hyperparameters; maize/bajra/groundnut
   are Tier 2, "an allocation on a measured axis, not a classification", ranked on October gamma0
   with district-proportional cut points. Every row carries `crop_confidence`. This is strictly
   more honest than our single flat label with a global kappa=0.103 caveat.
2. **The circularity test.** They rank Tier 2 on gamma0_T4, then note NDVI correlates +0.533 with
   that same axis, so any NDVI test of Tier 2 tests the rule that produced it. Their non-circular
   question: regress NDVI on gamma0_T4, then ANOVA on the *residual*. Tier 2 explains 19% of raw
   NDVI variance and **0.2% of the residual** (eta^2 0.193 -> 0.0018, p=0.52) - the labels carry
   nothing beyond the ranking axis. The Tier 1 control moves the opposite way (eta^2 0.0003 raw ->
   0.060 residual, p=3.7e-4). **We have no equivalent test and our crop labels need one.**
3. **Audit scene vs reserved scene.** The 13 Oct scene set a design decision (the biomass sign),
   so they retire it from validation and report the headline against **18 Oct**, read by nothing
   upstream. Audit reads +0.411, reserved reads +0.356, and they state that the 0.055 gap *is the
   size of the selection effect* and quoting the higher number would overstate the result. We use
   13 Oct Sentinel-2 as a witness *and* it is the date our completion sign correction was made
   against - we have the same contamination and do not account for it.
4. **Pre-registered expected signs.** `EXPECTED_SIGN` is a module constant declared above the code
   that opens the optical file. Three features violate their declaration and they report all
   three, including that their conformity component carries 0.30 of the index and is **null on
   standing crops** (+0.036 against a declared +1). They did not reweight, because "fitting one is
   exactly what would stop the reserved scene being a test".
5. **A negative control declared to be null.** June soil wetting is carried as an explicit control
   expected ~0; it scores -0.053 against the index's +0.377. That is how you demonstrate the index
   tracks canopy and not soil moisture.
6. **The Moran's I ceiling argument.** Their index gives I=+0.256; the reserved NDVI over the same
   farms gives +0.203. Rather than celebrate, they observe that **the optical reference is the
   ceiling for structure that is genuinely field condition**, so carrying 126% of it means the
   excess is structure from something else (June soil wetting, at +0.407, is the candidate).
   Reported as an open question. Our Moran's I is 0.105 against a permutation null only - we never
   asked what the ceiling should be.
7. **Sub-village spatial reporting.** A single-village study makes the required village table one
   row carrying no spatial information, so they also report the same arithmetic on a fixed
   **500 m grid**: 46 zones, >=5 farms each, covering 946/966 farms, each with area-weighted
   health, yield, production, dominant crop and measured-vs-imputed share. Health spreads 30.8 to
   62.8 across zones - **32 points of within-village variation** hidden behind one number. Cheap,
   and we should ship it.
8. **Forcing health and yield apart.** They measured within-crop rho(health, yield) = **exactly
   1.000** - the two submitted columns carried one measurement between them, while the rubric
   scores them separately. They added an accumulation term that no health component contains,
   dropping rho to 0.928, after which yield ranks fields *better* than health on every crop.
   **We should measure our own rho immediately** - our yield is
   `anchor x completion x accumulation` and our health shares the season-integral family, so we
   are exposed to the same collapse.

### 2.5 oindrieelmondal - the most candid

Weakest methodology of the five, strongest instinct for reporting its own limits. Two-stage
phenology matching (Stage A rice vs non-rice on the flood signature; Stage B the rest by
reference-shape matching constrained to the Round 1 quota).

**What is genuinely useful to us:**

- **They ran the calibration cross-check we should have run.** Their sigma0 against Capella's own
  preview product, per date: +1.81, +0.94, +1.57, **-2.00** dB. Three dates cluster near +1-2 dB,
  "weakly consistent with a possible double sin(theta) correction", but the fourth reverses sign
  and they refuse to call it resolved. Note that their chain reads
  "DN -> power -> scale_factor -> beta0", which is *our* convention - and they are the only other
  team reporting an unexplained absolute offset. That is corroboration of §1 from a second
  direction.
- **They state the number that hurts.** 50.8% of farms (491/966) carry crop-type confidence below
  0.40, and they recommend those for manual or optical review before `crop_type` is treated as
  final. Compare our single global kappa=0.103.
- **The crop-label load-bearing check.** Randomly reassigning the crop label of the 491
  low-confidence farms moves `health_index` by only ~2.86 points on 0-100. They report this as a
  *limitation*, not a robustness win: it means crop-conditioned normalisation differentiates crops
  less strongly in practice than the design rationale implies. **This is a test we should run, and
  our within-crop scoring makes the same promise theirs does.**
- **Testing an external hypothesis and reporting it unsupported.** Literature says erectophile
  cereals decrease in backscatter during peak growth. Maize: -0.05 dB raw, **+0.08 dB after
  outlier cleaning - sign reverses**. Bajra: -0.34 dB, an order of magnitude below the claimed
  -2.5 to -4.0. They report the hypothesis as largely unsupported and note the reversal is itself
  evidence that outlier handling matters.
- **Reporting the promotion criterion honestly.** Their production weighting cleared one threshold
  (25.0-point low-confidence cut against a 10.0 minimum) but missed the other (+0.028 mean
  confidence against +0.03). They promoted it and said so, "rather than only the more flattering
  one".

**Their weaknesses:** health components correlate 0.75-0.88 pairwise, which they disclose,
undermining their own weight-sensitivity result; `f_stage` constants are admitted to be the
weakest-justified numbers in the pipeline; and their village crop mix diverges from district norms
without resolution.

---

## 3. Where we stand

### 3.1 Head-to-head

| axis | GDHTM | Coding Bits | 8bit | Megalodon | Orion | oindrieel |
|:--|:--|:--|:--|:--|:--|:--|
| Calibration convention | **SF (wrong)** | SF^2 | n/s | per-scene | SF^2 | SF-like, offset unresolved |
| Geocoding | 225 GCPs, average-resample | **TPS spline** | n/s | RPC + DEM, geoid-fixed | RPC, height fitted per scene | STAC corners |
| Speckle handling | erosion + averaging | **Quegan-Yu multitemporal** | speckle-corrected evenness | ENL-matched texture | CoV vs L=1 prediction | 4x4 multilook |
| Crop type driver | R1 shares + SAR evidence | area constraint + **S2 Nov** | R1 + transportation LP | frozen R1 rules | clustering, **2 tiers** | 2-stage, R1 quota |
| Per-farm crop confidence | **no** | yes (margin, quartile-validated) | no | yes (quintile-validated) | **yes, tiered** | yes |
| Health weights | blind, from feature correlations | 3 priors + **1 spatial hold-out** | rank-then-combine | equal, WCM-derived | fixed, exposed | fixed, sensitivity-tested |
| Yield structure | anchor x completion x accumulation | integrated backscatter | multiplicative | APY x progress x health | **Y_ref x f x a x g** | BASE x 5 factors |
| Independent witness | S2 + S1, 10-scene integral | S2 Oct, 5-fold OOS | S2 Oct | **S1 VH rho=0.746** | **reserved 18 Oct scene** | none of note |
| Negative results reported | **3** | several | ~0 | **retraction** | **3+ incl. null component** | **several** |
| Reproducibility | notebook asserts equality | offline identical | SHA-256 | byte-identical, audit script | logged, cross-platform | notebook public |
| Village production | 595 t | 1,268 t | n/s | 578 t | 1,002 t | n/s |

### 3.2 Where we are genuinely ahead

1. **The dasymetric framing.** No other team names the technique or applies it consistently to two
   different quantities. It gives our report a spine theirs lack, and it is the correct description
   of what several of them are doing without saying so.
2. **Witness discipline.** We are the only team with a **season-integrated** witness of the right
   shape. Others validate a season-long accumulation term against a single-instant NDVI. We built a
   10-scene Sentinel-1 integral (12 Jun - 10 Oct, one relative orbit) because Sokhda had **zero**
   Sentinel-2 scenes under 20% cloud across June-September. That is a real methodological win.
3. **We report a witness that contradicts us and keep the number.** Bajra's season-integral term
   runs against the witness at -0.219, and we ship the value flagged rather than tuning it. Only
   Megalodon and Orion match that standard.
4. **The sign error we caught and corrected** (§7.1 finding 3) is the same class of error as
   Megalodon's retraction, and we caught ours before shipping.
5. **Gate discipline.** A 19-check ship gate plus a gate asserting the prose matches the artefacts
   is stronger than anything except Megalodon's `audit_claims.py`.
6. **Our two scored columns are genuinely independent measurements - measured, and we beat Orion.**
   Orion found within-crop rho(health, yield) = **exactly 1.000** on their first attempt and had to
   add an accumulation term to break it, reaching 0.928. Ours, measured:

   | crop | n | rho |
   |:--|--:|--:|
   | Bajra | 149 | +0.133 |
   | Groundnut | 221 | +0.160 |
   | Rice | 86 | +0.338 |
   | Cotton | 455 | +0.541 |
   | Maize | 55 | +0.595 |
   | **pooled** | **966** | **+0.170** |

   Our *worst* crop (+0.595) is well below Orion's *post-fix* figure (0.928), and pooled we sit at
   +0.170. The rubric scores health and yield separately; ours carry separate information. This is
   a direct pass on a test that forced another shortlisted team to restructure a deliverable.

### 3.3 Where we are behind

Ordered by how much it would cost us in front of a judge.

1. **The calibration bug** (§1). Fixable in one line.
2. **No per-farm crop confidence.** Four of five competitors ship one. We ship a flat label with a
   global kappa=0.103 caveat, which is honest but strictly less useful than Orion's tiers or
   oindrieel's 50.8% disclosure.
3. **The uniformity term.** Largest weight in our health index (0.301), same sign as the finding
   Megalodon publicly retracted, and our own §7.1 already says it fails on an independent date.
4. **No spatial or temporal hold-out for anything.** Coding Bits selects weights on the west half
   and reports on the east; Orion reserves an entire scene. Our weights are blind-derived, which
   is a good defence, but "blind" is not "held out".
5. **No plot-size de-biasing.** Coding Bits measured r up to +0.27 between backscatter and plot
   area and removed it. Our median plot is 0.27 ha with a wide spread; we have almost certainly
   got the same artefact and have never looked.
7. **Circular validation on 13 October.** Our completion-term sign correction was made against
   13 Oct Sentinel-2, and 13 Oct Sentinel-2 is also a headline witness. Orion retires such a scene
   and reports against a reserved one.
8. **No sub-village spatial product.** Our village table is one row.
9. **Weak null.** Our Moran's I of 0.105 is tested against a permutation null. Orion asks what the
   *ceiling* should be; Coding Bits builds a constraint-only null. Both are harder tests.

---

## 4. Claim collisions - where the writeups contradict each other

These are the most valuable content in the set, because the teams are describing the *same
966 farms*. Two I have already resolved on our own data.

### Collision 1: does the rice flood signature work? **RESOLVED - both sides are right**

- **Orion**: the classic dark-flood rule fails. Farm-level `min(T1,T2) -> T3` rise is **-0.36 dB**
  median, "the wrong direction entirely against the +6 dB it needs".
- **Coding Bits**: no acquisition falls in the flooded transplanting window; rice does not separate
  on Aug->Oct retention (delta=-0.033 dB, p=0.36).
- **Us, Megalodon, oindrieel**: all three use a June flood/transplant signature and report it works.

Measured on our data:

| test | our result |
|:--|:--|
| Orion's rule: `min(6Jun,19Jun) -> 14Aug` rise, all farms | **-0.17 dB** (Orion: -0.36 dB) |
| same, rice-labelled farms only | **-0.71 dB** |
| **our** signature: `6 Jun -> 19 Jun` change, rice | **+3.23 dB** |
| same, next-highest crop (maize) | +1.12 dB |
| same, remaining crops | +0.07 to +0.83 dB |

**Orion is right about the rule they tested, and it is not the rule we use.** Our rice evidence is
the 6->19 June brightening, where rice separates from every other crop by 2.1-3.2 dB. The classic
rule Orion falsified - dark flooded field brightening into canopy by August - genuinely fails on
our data too (-0.71 dB for rice, wrong sign). Two different features, one works, one does not.

Caveat to state honestly: our rice labels were partly assigned using this feature, so the
separation is not fully independent. The magnitude of the gap is nonetheless large, and both
Coding Bits and Megalodon independently confirm 19 June was a rain day (12.5 mm and 21.9 mm
respectively), which supplies the mechanism - a flooded or bare transplanted paddy responds to
surface wetting far more strongly than a field already carrying canopy. That is also precisely
Coding Bits' "Wetness" logic, applied to a different target.

**Action:** state this explicitly in the Round 3 report. It converts a possible criticism into a
demonstration that we tested the standard rule, found it fails, and use a different one.

### Collision 2: calibration convention. **RESOLVED - we are wrong** (§1)

### Collision 3: is a uniform field a healthy field? **UNRESOLVED, and it is our exposure**

- **Us**: `uniform = -(within-farm CV)`, weight **0.301**, the largest in our index.
- **Megalodon**: published rho=-0.53 supporting this, then **retracted it** - the statistic was a
  signal-to-noise proxy. Corrected: rho=+0.02, and structure metrics reverse to +0.43 once
  brightness is partialled out.
- **Coding Bits**: Uniformity correlates **-0.146** with October greenness, opposite in sign to
  their other three components. Leave-one-out changes agreement by 0.017, within noise. They keep
  it at weight 0.20 on temporal-persistence grounds and report the contribution as near-neutral.
- **Orion**: uses CoV *excess over the L=1 speckle prediction*, weight 0.20 - a different and
  better-posed quantity, since at one look fully developed speckle gives CoV=1.0 exactly, so any
  excess is real heterogeneity.
- **oindrieel**: inverse within-farm std, weight 0.25.

Three of five teams report this term as neutral, negative, or retracted. **We give it the largest
weight in our index.** Our own §7.1 finding 3 already reports it failing on an independent date.

**Action, highest priority after calibration:** (a) recompute uniformity as CoV *excess over the
L=1 prediction*, per Orion, rather than raw CoV; (b) partial out brightness before correlating, per
Megalodon, to check whether ours is also an SNR proxy - we have 20%+ of pixels near the noise floor
by our own reckoning, the exact condition that creates the artefact; (c) if it survives neither,
reweight and report the change as a finding.

### Collision 4: should the Round 1 shares be used at all? **We are on the strong side**

Covered in §2.4. Three of four teams reporting a cotton share land at 39-49%; Orion alone at 13.7%
after discarding the constraint, and its maize allocation exceeds its own district total by 2.6x.
Orion's own Round 1 read matches ours to 0.25 pp.

### Collision 5: village production. **UNRESOLVED, and someone is badly wrong**

| team | total production, to date |
|:--|--:|
| Megalodon | 578 t |
| **GDHTM** | **595 t** |
| Project Orion | 1,002 t |
| Coding Bits | 1,268 t |

A 2.1x spread on the same 447.5 ha. We and Megalodon agree within 3%, and both anchor on district
APY discounted by crop progress. Orion anchors on Gujarat First Advance Estimates with per-crop
completion `g`; Coding Bits anchors on the midpoint of the published per-crop range in the brief.
Much of the spread is the crop mix, not the yield model - Orion assigns 130 ha to maize where we
assign 27.

**Action:** reconcile explicitly. Being one of the two teams in the low cluster, with an
independent team at +3%, is a defensible position and worth stating in Round 3.

### Collision 6: does more rain mean brighter or darker at X-band?

- **Megalodon**: ITU-R P.838 gives ~8.6 dB two-way loss for a 25 mm/h cell, larger than any
  between-date offset here; 19 June took 21.9 mm yet measured **brighter**, so wet-soil brightening
  dominates attenuation.
- **Coding Bits**: 12.5 mm in the preceding six hours; scene reads +1.34 dB brighter with 2.6x the
  inter-field spread.
- **oindrieel**: all five crops show a synchronised rise on 19 June, "a shared monsoon-onset
  moisture event rather than five independent crop-specific signals".

Consistent across three teams: **wet-soil brightening dominates**. Our 6->19 June rice signature
sits directly in this regime, which is the mechanism that makes it work (§Collision 1) but also
means it is a soil-and-flood signal, not a canopy signal. We should say so.

---

## 5. Adoption backlog

Ranked by rubric impact divided by effort. "Cost" is my estimate of implementation time.

### Tier A - do before anything else

| # | Item | Source | Cost | Why |
|:--|:--|:--|:--|:--|
| A1 | **Fix `beta0 = SF^2 * |z|^2`**, rerun, diff | Coding Bits, Orion | 1 line + rerun | Correctness. Removes a 27 dB error and a wrong explanation from the report |
| A2 | **Rewrite REPORT §2.4** | - | 30 min | Turns a conceded 17 dB anomaly into an absolute level corroborated by two teams |
| A3 | **Re-pose uniformity as CoV excess over L=1**, and partial out brightness | Orion, Megalodon | half a day | Our largest health weight may be an SNR proxy; Megalodon retracted exactly this |
| ~~A4~~ | ~~Measure rho(health, yield) within crop~~ | Orion | **done** | **Measured, and we pass** - see §3.2.6 |

### Tier B - high value, clearly bounded

| # | Item | Source | Cost | Why |
|:--|:--|:--|:--|:--|
| B1 | **Per-farm crop confidence**, from the assignment margin, validated by quartile | Orion, Coding Bits, Megalodon | half a day | Four of five ship one; we ship a flat label. Coding Bits' quartile agreement (30.6 -> 61.2%) is the template |
| B2 | **Two-tier crop labels** - rice/cotton measured, the rest allocated and flagged | Orion | half a day | Strictly more honest than one label plus a global kappa, and matches what our kappa=0.103 already admits |
| B3 | **Plot-size de-biasing**: regress every feature on log(area), remove the trend | Coding Bits | 2 hours | They measured r up to +0.27. We have never checked, and our plots span 0.05-3.5 ha |
| B4 | **500 m grid sub-village table** | Orion | 2 hours | Our village table is one row. Orion found 32 points of health spread hidden behind theirs |
| B5 | **Non-circular label test**: regress witness on the ranking axis, ANOVA the residual | Orion | 3 hours | Our crop labels have no test that is not partly circular |
| B6 | **Decile-trend presentation** of health vs NDVI | 8bit | 1 hour | "+0.988 rank correlation across deciles, NDVI 0.260 -> 0.415" reads far better than a scalar rho |
| B7 | **Reserved-scene validation** - retire 13 Oct S2, report against a later date | Orion | 3 hours | 13 Oct set our completion sign *and* is a headline witness. Same contamination Orion accounts for |

### Tier C - worth doing if Round 3 allows

| # | Item | Source | Cost | Why |
|:--|:--|:--|:--|:--|
| C1 | **Quegan-Yu multitemporal speckle filter** | Coding Bits | 1-2 days | 2.4-2.8x effective looks with zero spatial blurring; ideal at 0.27 ha |
| C2 | **Thin-plate spline geocoding** over the 225 GCPs | Coding Bits | 1 day | ~8 m polynomial residual against a 24.7 m plot. Our resampling is average over a GCP fit |
| C3 | **Spatial hold-out protocol** for any fitted constant | Coding Bits | 1 day | Our weights are blind, which is good; held-out would be better |
| C4 | **Pre-registered expected signs** as a module constant | Orion, Megalodon | 3 hours | Cheap, and it converts every sign check into a real test |
| C5 | **Auxiliary-data ceiling calculation** before fetching | Megalodon | 3 hours | Justifies our NASA POWER usage rigorously (0.000 explanatory power at 50 km) |
| C6 | **Moran's I ceiling argument** - compare against the witness's own I | Orion | 1 hour | Turns a bare number into an interpretable one |
| C7 | **Degenerate-output assertions** in the ship gate | Coding Bits | 1 hour | Our 19 checks are schema/range; a collapsed index would pass them all |
| C8 | **`audit_claims.py`** - re-derive every quoted figure from source, exit non-zero on mismatch | Megalodon | 1 day | We have a prose-vs-artefact gate; theirs goes back to the rasters |

### Explicitly rejected

- **Coding Bits' S2-driven crop map.** Better separation, but it makes the crop column optical in a
  SAR challenge. Our SAR-primary constraint is worth more than the accuracy.
- **A fitted model for the health index.** Coding Bits' own argument against adopting their 0.560
  GBM applies to us verbatim, and we should borrow the argument rather than the model.
- **Orion's decision to drop the Round 1 shares.** §2.4 and Collision 4 - the evidence runs against
  them.

---

## 6. Round 3 preparation

### 6.1 What the shortlist tells us the judges rewarded

Every one of the six shortlisted writeups has all of these. That is not a coincidence, it is the
scoring function:

1. **Reported negative results.** Every shortlisted team ships failures. Megalodon retracted a
   published finding; Orion reports a component of its own index as null; oindrieel reports an
   external hypothesis unsupported; we report three failures including one that changed a shipped
   column.
2. **Validation against something the pipeline never read.** Universal.
3. **Explicit reproducibility with a hash or an assertion.** Universal.
4. **A stated scope limit on X-band.** Every team says some version of "relative within crop, not
   absolute biophysical retrieval".
5. **Physical justification for constants**, not fitted ones.

We are strong on 1-3 and 5, and should sharpen 4.

### 6.2 Adversarial Q&A - questions we should have answers ready for

| likely question | our answer |
|:--|:--|
| "Another team says the Round 1 shares are the least stable output and refused to use them." | Their own Round 1 read for Sokhda matches ours to 0.25 pp. Three of four teams land at 39-49% cotton; the team that dropped the constraint is the outlier at 13.7%, and its maize allocation exceeds the entire district total by 2.6x. |
| "Your uniformity term has the sign another team retracted." | Recomputed as CoV excess over the L=1 speckle prediction, with brightness partialled out - here is what survived. *(Requires A3 first.)* |
| "Your absolute calibration is off." | Fixed; our level now agrees with two independent teams at -18 to -20 dB. *(Requires A1.)* |
| "The rice flood signature is known to fail here." | It does - we measured the standard rule at -0.71 dB for rice, wrong sign, matching Orion. Our feature is a different one, the 6->19 June wetting response, where rice separates by 2.1-3.2 dB. |
| "Your crop labels only reach kappa=0.103." | Correct and we report it prominently. The product is designed to be read at village and crop-group level, which is the level Round 1 was scored at. Tiered confidence now marks which labels are measured and which are allocated. *(Requires B1/B2.)* |
| "Health and yield may be the same number twice." | Measured. Within-crop rho spans +0.133 (bajra) to +0.595 (maize), pooled +0.170. Another shortlisted team measured exactly 1.000 on theirs and reached 0.928 after restructuring - our worst crop is below their best. |
| "Village production estimates span 2.1x across teams." | We and Megalodon agree within 3% on independent pipelines; both anchor on district statistics discounted by crop progress. The spread is driven by crop mix, not the yield model. |

### 6.3 Use-cases beyond what was asked

1. **Consensus pseudo-ground-truth.** Six teams labelled the *same* 966 farms. Where four or more
   agree, that is the closest thing to labels that will ever exist for Sokhda, and it would let us
   measure our crop column against something external for the first time. **This is partially
   executable today**: oindrieelmondal published their submission notebook and datasets publicly
   (`kaggle.com/code/oindrieelmondal/final-submission-for-anrf-aisehack-2-0-round-2`,
   plus `datasets/oindrieelmondal/auxiliary-dataset` and `datasets/oindrieelmondal/anrf-2-phase1`).
   One competitor CSV in hand converts our kappa=0.103 self-criticism into a two-way agreement
   measurement. Ask the other four; several may share.
2. **Convergent validity as evidence.** Where independent teams derive the same constant, it is
   corroborated; where we are the lone dissenter, it is a defect. §1 is the first instance and it
   went against us. The Sokhda crop mix (§2.4) is the second and it went for us. Both belong in
   the Round 3 report.
3. **Cross-team physics register.** Collisions 1, 3 and 6 are cheap experiments on data we already
   hold, and each converts a possible criticism into a demonstrated test.
4. **Anchor reconciliation.** Four teams, four different yield anchors (APY, First Advance
   Estimates, Third Advance Estimates, the brief's published range) and a 2.1x production spread.
   Documenting which anchor we use, in which units, and why, is a differentiator - Orion's note
   that "Indian statistics quote the same crop three ways" and their cotton lint->kapas conversion
   at 34% ginning outturn is the standard to match.
5. **Failure-mode library.** Between them the five teams document a geoid bug, an FID off-by-one, a
   calibration double-correction, an SNR-proxy artefact and a speckle-filter-induced correlation.
   Every one is a check we can add cheaply, and every one is a class of error that survived
   internal consistency checks in a competent pipeline.
6. **Presentation calibration.** The two most persuasive devices in the set are 8bit's decile trend
   and Coding Bits' single validation table where each row states what it *establishes*, not what
   it measures. Both are formatting changes to numbers we already have.

---

## 7. Recommended order of work

1. **A1 + A2** - calibration fix and report correction. Everything else sits downstream of a
   correct radiometry.
2. **A3** - the uniformity term. Largest weight, weakest evidence, one public retraction against it.
3. **B1 + B2** - crop confidence and tiering. Biggest presentation gain per hour.
4. **B3, B4, B6** - plot-size de-biasing, the 500 m grid, the decile plot. All cheap.
5. **B5, B7** - the non-circular label test and the reserved scene. These need care.
6. **Tier C** as Round 3 scope allows.

The single highest-value action outside the code is obtaining one or more competitor submission
CSVs (§6.3.1). It is the only route to an external check on the crop column, which is the
weakest part of our submission and the one we are most honest about.
