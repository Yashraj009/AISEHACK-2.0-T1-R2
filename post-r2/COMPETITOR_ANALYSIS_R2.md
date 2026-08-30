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

### 1.3b Why we got it wrong, and why that matters for how we answer

We did not invent the unsquared form. It comes from a real citation - ESA's EDAP
"Technical Note for Capella Data Assessment" (Issue 1.0), p7, which states verbatim:

> `RADAR backscatter: beta0 = sc * |pixel|^2, where sc is a Scale Factor`

Fetched and extracted from the source PDF while writing this document. The transcription in
our notes was accurate. **The error is one level down: identifying ESA's `sc` with the
product JSON's `collect.image.scale_factor`.** Those are not the same quantity.

Capella's own reference implementation settles what `sc` must be. `capella-reader`'s
`rtc_isce3.py` computes `beta0_complex = SF * DN`, so the *power* carries SF squared -
which means ESA's `sc` equals the JSON field **squared**. Both formulas are correct; only
the substitution was wrong.

This matters for Round 3 because it changes our answer from an admission into a precise
technical point. If a judge cites ESA at us, the response is not "we made an error" but:
the ESA formula is stated in terms of a scale factor that is not the annotated JSON field,
identifying the two produces backscatter above 0 dB for a distributed target, and Capella's
own reference implementation resolves the ambiguity in favour of the square.

One more consequence worth stating plainly: the same misidentification made us record
Round 1's correct ~-18/-19 dB cropland means as *implausibly low*, and "fix" a Round 1
implementation that had it right. The lesson is Megalodon's, exactly: **per-date
consistency cannot catch a common-mode error in your own chain.** All four of our dates
were wrong by the same mechanism, so every internal cross-check passed.

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
| ~~A3~~ | ~~Re-pose uniformity / reweight~~ | Orion, Megalodon | **dropped** | **Mis-scoped, and now closed.** Not an SNR proxy (§8.2); CoV-excess does not port, our grid is 4-5 looks (§10.3); plot-size de-biasing makes it worse (§11.1); and under spatial hold-out no weighting beats any other (§11.2). The index is insensitive to this choice. Report the decorrelator argument and move on |
| ~~A4~~ | ~~Measure rho(health, yield) within crop~~ | Orion | **done** | **Measured, and we pass** - see §3.2.6 |
| A5 | **Re-derive the yield anchors** with a declared minimum-area rule and state fallback | Megalodon | 3 hours | **The only change identified that should move a shipped column.** Bajra is +52% above three independent government statistics, off a 7,022 ha base, and contradicts our own retraction in SOURCES.md (§9.4b) |
| A6 | **Reduce yield's dependence on the crop label** (eta^2 0.82 -> nearer 0.5) | Coding Bits, Orion | half a day | Our yield inherits the crop map's disagreement wholesale (§9.4). Conditioned on agreeing labels we correlate +0.68 to +0.75 with the closest teams, so the model is sound and the label is the problem |

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

---

## 8. Experiments run against these findings

All three live in `post-r2/experiments/` and read the shipped Round 2 artefacts as
read-only inputs. The Round 2 submission is frozen; nothing below writes to `results/`,
`docs/`, `src/` or `notebooks/`.

### 8.1 e1 - the calibration correction, applied end to end

The correction is one multiply by SF per date, because the scale factor is a per-scene
constant. So the whole submission can be rebuilt without touching a raster: scale the
per-date linear power, re-derive the temporal block exactly as `farm_stats.py` does, and
re-run the **real** `d4_submission.main()` against the corrected frame with its output
paths redirected into `post-r2/`.

| quantity | shipped vs calibrated |
|:--|:--|
| `crop_type` | **958/966 unchanged (99.2%)** - 8 reassignments |
| `health_index` | Spearman **0.9908**; median delta 0.905 points; 7 farms move >100 ranks |
| `yield_estimate_to_date` | Spearman **0.9836**; median delta 0.008 t/ha; 9 farms move >100 ranks |
| village production | 594.9 t -> **597.8 t** (+0.5%) |

**This is the strongest possible outcome for us.** The bug is real, and the product is
almost completely insensitive to it - because every shipped quantity is a difference
between dates or a rank within a crop, never an absolute level. Our own stated discipline
is precisely what contained our own error. That is the sentence to put in the Round 3
report, and it is worth more than never having had the bug.

What still must change: the formula, the `prep_r2.py` comment calling the square an R1
bug, and REPORT §2.4's explanation.

### 8.2 e2 - the uniformity term, and what it revealed about our weighting

**T1. We do not have Megalodon's artefact.** Their retraction was caused by variance
rising as a farm approaches the noise floor, so dim farms read as non-uniform:
rho(CV, brightness) negative. Ours is **+0.173** - the opposite sign. Our term is not an
SNR proxy.

But rho(CV, pixel count) = **+0.229**, which is the *Coding Bits* artefact, not the
Megalodon one: larger plots read as more variable. That is a real confound and it is what
backlog item B3 (plot-size de-biasing) exists to remove.

**T2. The term is null against both independent witnesses.**

| witness | raw rho | brightness partialled out |
|:--|--:|--:|
| Sentinel-2 NDVI, 13 Oct | -0.030 | +0.084 |
| Sentinel-1 VH | -0.020 | +0.051 |

**T3.** Within crop and after partialling, four of five crops turn weakly positive
(groundnut +0.167, maize +0.153, cotton +0.092, bajra +0.020) and rice runs negative
(-0.065).

**The real finding is one level up.** Our weights are `w_k` proportional to
`1 / sum_j |rho(k,j)|` - each family rewarded for being *uncorrelated with the others*.
The rule is genuinely blind to every witness, which is why REPORT §4 defends it. But
independence is not information, and **a family carrying only noise correlates with
nothing**, so the rule hands it the largest weight. Measured:

| family | shipped weight | mean \|rho\| vs the two witnesses |
|:--|--:|--:|
| `growth` | 0.283 | **0.285** |
| `persist` | 0.228 | 0.221 |
| `level` | 0.189 | 0.214 |
| `uniform` | **0.301** | **0.025** |

Spearman(shipped weight, witness informativeness) = **-0.200**. The rule is mildly
*anti*-correlated with how informative a family actually is. The most informative family
draws a mid-range weight; the only uninformative one draws the largest.

**T4. And yet removing it makes the index worse.** Four weightings, all still blind - none
reads a witness to set a weight:

| scheme | rho vs NDVI | rho vs S1 VH |
|:--|--:|--:|
| **shipped** (blind, `1/sum` of `\|rho\|`) | **+0.127** | **+0.156** |
| equal | +0.122 | +0.151 |
| drop uniform, rest equal | +0.078 | +0.133 |
| drop uniform, rest as shipped | +0.086 | +0.136 |

The shipped weighting is the best of the four, on both witnesses, and dropping `uniform`
costs the most. The reading: `uniform` earns its place as a **decorrelator, not as a
measurement**. `level` and `persist` are both brightness-like and partly redundant;
re-weighting toward them adds correlation without adding information. The blind rule's
independence logic has real merit even though the mechanism that produces it can be
argued against.

*Caveat, stated so it is not overread:* the T4 composite approximates the shipped index
(robust-z within crop, weighted sum) but omits imputation and the bounded transform, so
treat the ordering as indicative rather than exact.

**This lands us where two other teams landed by different routes.** Coding Bits measured
their uniformity at -0.146 against October greenness and near-neutral on leave-one-out,
and **kept it at 0.20** on temporal-persistence grounds. Orion kept theirs at 0.20 using
CoV excess over the L=1 speckle prediction. Three teams independently retain a
near-neutral uniformity term. We are not the outlier - we simply weight ours highest and
had not measured why.

**Revised action for A3.** Not "drop or reweight". Instead: re-pose the term as Orion does
(CoV excess over the speckle prediction rather than raw CoV), de-bias for plot size per
B3, and *report the decorrelator argument explicitly* rather than letting the weight look
like a claim about uniformity being healthy. The honest framing is that the largest weight
in our index is carried by a term that stabilises the composite rather than one that
measures condition - and that we tested this rather than assumed it.

### 8.3 e3 - the consensus check, RUN

oindrieelmondal published their submission notebook, so their `submission_round2.csv` is
public. This is the first external check our crop column has ever had.

**The file is verifiably theirs.** Their labels crossed with *our* `area_ha` reproduce the
hectares published in their own writeup to 0.1 ha on all five crops (Bajra 36.8, Cotton
176.3, Groundnut 130.8, Maize 31.9, Rice 71.8), and the confusion-matrix column sums
reproduce their farm counts exactly (171 / 294 / 277 / 61 / 163). The join is sound.

**Per-farm agreement is below chance.**

| measure | value |
|:--|--:|
| raw agreement | **17.2%** |
| Cohen's kappa | **-0.111** |
| our own independent rebuild (REPORT 7.1) | +0.103 |
| label-shuffle null, 999 draws | mean +0.0007, 95% interval [-0.034, +0.032] |

Of the farms we call Rice, **0.0%** are theirs. Cotton 16.9%, Groundnut 30.8%, Bajra
10.1%, Maize 10.9%.

Three controls, because a result this extreme is usually a join bug - Megalodon lost a
finding to exactly that (a 1-based shapefile FID against a 0-based raster label):

1. **Join integrity** - passes, as above.
2. **Off-by-one sweep** - shifting their `farm_id` by -2, -1, +1, +2 gives kappa -0.025,
   -0.026, -0.017, -0.007. **No shift recovers agreement**, so the disagreement is real
   rather than a registration artefact.
3. **Chance null** - observed kappa falls *below* the shuffle interval.

**Why below chance, and why that is not a bug.** Both pipelines impose an area constraint,
so each is allocating a fixed budget of hectares per crop. When two constrained
allocations disagree about *which* farms receive a label, the fixed marginals force
negative dependence. kappa < 0 is the expected signature of two disagreeing constrained
assignments, not evidence of an error.

**And yet the village mix agrees closely.**

| crop | ours % | theirs % | delta |
|:--|--:|--:|--:|
| Cotton | 43.22 | 39.39 | +3.83 |
| Groundnut | 30.76 | 29.24 | +1.53 |
| Rice | 10.60 | 16.03 | -5.43 |
| Bajra | 9.45 | 8.22 | +1.23 |
| Maize | 5.97 | 7.12 | -1.15 |
| | | **mean \|delta\|** | **2.63 pp** |

**This is the single most important result in this document.** Two independent teams,
the same 966 parcels, the same four scenes: they agree on the village crop mix to a mean
of 2.63 percentage points and disagree on individual farms at a rate worse than chance.

That is precisely the claim REPORT §7.2 already makes - *"the product should be read at
village and crop-group level... a single farm's label should not be acted on alone"* - and
it has just been confirmed against an external team rather than against ourselves. Our
kappa = +0.103 self-criticism was not pessimism. It was, if anything, generous.

Both caveats stated: oindrieelmondal report 50.8% of their own farms carrying crop-type
confidence below 0.40, so this is agreement between two acknowledged-uncertain labellings,
and neither is truth. And a single comparison is one draw - the other four teams' CSVs
would turn this into a consensus rather than a pairing.

**What to do with it:**
- Put the number in the Round 3 report. A measured external kappa is worth more than a
  self-assessed one, and reporting a *negative* external result is exactly the behaviour
  every shortlisted writeup shares.
- It converts backlog items B1/B2 (per-farm confidence, tiered labels) from
  presentation polish into a substantive necessity. Orion's two-tier scheme -
  "an allocation on a measured axis, not a classification" - is now the demonstrably
  correct description of what all of us are shipping.
- Ask the other four teams for their CSVs. Where four or more agree, that is the closest
  thing to ground truth Sokhda will ever have.

---

## 9. All six submissions, side by side

All five competitor deliverables are now in `post-r2/writeups_submissions/`. Every file has
the same schema and the same `farm_id` 1..966, so the six are directly comparable.
`e4_consensus_all.py` runs the whole comparison.

### 9.1 The structural result

| column | agreement across the six teams |
|:--|:--|
| **crop type** | mean pairwise Cohen's kappa **+0.060** - chance |
| **health index** | mean pairwise Spearman **+0.337** |
| **yield to date** | mean pairwise Spearman **+0.073** - chance |

**Six independent pipelines, the same 966 parcels, the same four scenes: they agree on
health and they do not agree on crop type or yield.** That is a statement about the
problem, not about any one team, and it is the single most useful thing this comparison
produced.

Only one pair agrees on crop type at all: Coding Bits x Megalodon at kappa +0.461 - and
both derive their map from optical phenology, so they are not independent evidence. Every
other pair sits between -0.111 and +0.200.

### 9.2 There is no usable consensus crop map

The hope in §6.3.1 was that majority voting across six teams would yield pseudo-ground-truth.
It does not.

| teams agreeing | farms | % |
|:--|--:|--:|
| 2 of 6 | 264 | 27.3% |
| 3 of 6 | 410 | 42.4% |
| 4 of 6 | 222 | 23.0% |
| 5 of 6 | 66 | 6.8% |
| **6 of 6** | **4** | **0.4%** |

Four farms out of 966 carry unanimous agreement. And the majority label is not better than
its members: scored by Kruskal-Wallis **effect size** (epsilon^2, which unlike raw H does
not grow with sample size) against the two withheld sensors -

| labelling | eps2 vs S2 NDVI | eps2 vs S1 VH |
|:--|--:|--:|
| 8bit | **0.2565** | 0.0797 |
| Coding Bits | 0.2340 | 0.0547 |
| DeepThinkers | 0.2236 | 0.0969 |
| Megalodon | 0.1809 | 0.0288 |
| **GDHTM** | 0.1699 | **0.0988** |
| Orion | 0.1560 | 0.0383 |
| *consensus* | *0.1657* | *0.0263* |

The consensus is beaten by four of six individual maps on NDVI and by every one of them on
Sentinel-1 VH. With pairwise kappa near 0.06, majority voting averages disagreement rather
than accumulating evidence, and destroys signal instead of building it.

**Report this as a negative result.** It is a clean, quantified answer to a question worth
asking, and "we tried to build a consensus reference and it does not exist" is a stronger
contribution than a hedge about label uncertainty.

**Where we sit:** 5th of 6 on NDVI separation, **1st of 6 on Sentinel-1 VH**. Our agreement
with the majority label is 51.6% overall, mid-pack (Megalodon 69.3%, Coding Bits 68.0%,
8bit 52.9%, DeepThinkers 38.9%, Orion 29.9%).

### 9.3 Our crop mix is the modal position

| crop | **GDHTM** | CodingBits | 8bit | Megalodon | Orion | DeepThinkers | spread |
|:--|--:|--:|--:|--:|--:|--:|--:|
| Cotton | **43.22** | 44.60 | 43.06 | 48.47 | 13.69 | 39.39 | 34.8 pp |
| Groundnut | **30.76** | 32.19 | 28.06 | 38.78 | 25.88 | 29.24 | 12.9 pp |
| Rice | **10.60** | 10.91 | 13.49 | 8.85 | 18.39 | 16.03 | 9.5 pp |
| Bajra | **9.45** | 9.84 | 7.73 | 3.91 | 12.90 | 9.0 pp | |
| Maize | **5.97** | 2.46 | 7.66 | 0.00 | 29.14 | 7.12 | 29.1 pp |

On cotton, groundnut and rice we sit within 1.5 pp of Coding Bits and close to 8bit and
DeepThinkers. Orion is the outlier on cotton (13.7 against a 39-48 cluster) and on maize
(29.1 against 0-7.7), which is the position §2.4 already argued against. Megalodon ships
zero maize deliberately.

### 9.4 Yield: what the anti-correlation actually is

**This subsection corrects an earlier reading in this document.** The first pass concluded
that our yield column was an outlier because our per-crop *ordering* is inverted. That was
wrong, and `e5_anchors.py` disproved it.

**The observation.** Pairwise Spearman on yield puts us negatively correlated with three of
five teams (Coding Bits -0.266, 8bit -0.315, Orion -0.313), null with Megalodon (0.000)
and DeepThinkers (-0.069). We are the only team in that position.

**The wrong explanation, tested and rejected.** Our bajra anchor is 40-100% above every
other team's, so it looked like the ordering inversion was the cause. Correcting bajra to
the external median changes the cross-team correlations by a mean of **-0.001**. It is not
the cause.

**The right explanation.** Our yield is 82% explained by the crop label (eta^2 = 0.820), and
the crop maps agree at chance. So the yield columns inherit the crop disagreement. Holding
the label fixed - restricting to farms where we and they assign the *same* crop - separates
the two:

| vs team | all farms | crop labels agree | n | change |
|:--|--:|--:|--:|--:|
| Megalodon | +0.000 | **+0.678** | 321 | +0.678 |
| DeepThinkers | -0.069 | **+0.751** | 166 | +0.821 |
| Coding Bits | -0.266 | +0.019 | 351 | +0.284 |
| Orion | -0.313 | -0.173 | 180 | +0.140 |
| 8bit | -0.315 | -0.262 | 292 | +0.054 |
| | | | **mean** | **+0.395** |

**Conditioned on agreeing about the crop, our yield agrees strongly with the two teams whose
method most resembles ours** - Megalodon +0.678 and DeepThinkers +0.751, both of which
anchor on district statistics discounted by crop progress, exactly as we do. The remaining
negatives sit with 8bit (whose shipped column has a unit problem, §9.5) and Orion (whose
crop map is the field outlier, §9.3).

So the honest statement for Round 3 is not "our yield is an outlier". It is: **our yield
column is a good measurement carried on a bad label**, and its cross-team disagreement is
the crop map's disagreement, not the yield model's. That is the same conclusion §7.2 of the
report already reaches about the crop column, now shown to propagate into yield.

It also raises the priority of decoupling yield from the label. Orion faced the mirror-image
problem - their health and yield were the same number - and fixed it by adding a term no
health component contained. Ours is the other failure mode: too much of the column is the
label. Reducing eta^2 from 0.82 by letting the SAR carry more of the variance is the
structural fix, and Coding Bits (0.474) and Orion (0.499) show it is achievable.

### 9.4b The bajra anchor is still wrong, for its own reasons

Independent of the above, the anchor does not survive comparison. Full-season t/ha, cotton
omitted because teams quote lint and kapas interchangeably:

| crop | **ours** | district base | Orion | DeepThinkers | Megalodon | ext. median | ours vs |
|:--|--:|--:|--:|--:|--:|--:|--:|
| **Bajra** | **2.71** | 7,022 ha | 1.79 | 1.36 | 1.89 | 1.79 | **+52%** |
| Groundnut | 2.51 | 1,004 ha | 3.03 | 2.73 | 1.94 | 2.73 | -8% |
| Maize | 2.31 | 40,794 ha | 3.11 | 2.03 | - | 2.57 | -10% |
| Rice | 1.69 | 49,818 ha | 2.54 | 1.74 | 2.00 | 2.00 | -15% |

Bajra is the sole outlier, and its district base is 7,022 ha - 2.5% of the five-crop area.
Applying Megalodon's rule (a district mean is usable only where the district sows enough of
the crop) with a declared 20,000 ha threshold flags exactly two crops: **bajra and
groundnut**.

Those are the same two crops `data_aux/SOURCES.md` already carries a **RETRACTED** section
about, conceding the table is *"a bad prior for this village"*. We applied that retraction to
the AREA prior and left the YIELD anchor drawn from the same rows of the same table. That
inconsistency is ours, found without any competitor's help, and it is the cleanest argument
for the fix.

Effect of correcting bajra alone: village production 594.9 t -> **556.4 t (-6.5%)**, moving
us from 3% above Megalodon's 578.3 t to 4% below it. Small at aggregate level, for the same
reason the calibration error was small: this product is built from ranks and shares.

**Two separate bajra defects, and only one is fixed by the anchor.** Rescaling a crop by a
positive scalar cannot change that crop's *within-crop* rank, so REPORT §7.2's finding that
bajra's season-integral term contradicts the witness is untouched: rho stays -0.265. The
anchor sets the level; the witness disagreement is about the ordering inside the crop. Both
are real; A5 addresses one.

### 9.5 One observation about another team's file

8bit's shipped `yield_estimate_to_date` sums to **21,566 t** over 447.5 ha, roughly 48 t/ha,
against 578-1,268 t for the other five. Their per-crop medians run 31-71 t/ha. Their writeup
describes the index as "scaled village-wide", so this looks like an unscaled or
wrong-unit column in the delivered CSV rather than a method difference. Noted because it
distorts any cross-team yield statistic that includes them, not as a criticism of their
method - excluding them, the five-team production spread is 578 to 1,268 t, and we sit
second-lowest at 594.9 t, within 3% of Megalodon.

---

## 10. Testing the claims instead of deferring to them

Everything above began with something another team asserted. A shortlisted writeup is a
hypothesis, not a result, and two of these claims would change numbers we ship. Both were
re-tested against evidence that owes nothing to any competitor (`e6_verify_claims.py`).

### 10.1 Calibration, adjudicated by the vendor's own noise floor

The three arguments for the squared convention were all somebody's reading: Coding Bits
argued from physical plausibility, Orion cited `capella-reader`, and the ESA note states a
formula whose `sc` is ambiguous. None is independent of a human interpretation.

The product metadata carries `collect.image.nesz_peak`, an **absolute** dB level Capella
declares per scene. A real scene contains smooth dark surfaces whose return approaches the
system noise floor, so the darkest percentiles must sit near it - never tens of dB above,
which would mean the sensor never reaches its own noise anywhere in the scene.

| date | declared NESZ | darkest 0.1%, as shipped | vs NESZ | under SF^2 | vs NESZ |
|:--|--:|--:|--:|--:|--:|
| 2025-06-06 | -26.13 | 0.0 | **+26.1** | -26.7 | **-0.6** |
| 2025-06-19 | -27.76 | -1.5 | **+26.3** | -27.7 | **+0.0** |
| 2025-08-14 | -27.97 | -1.4 | **+26.6** | -28.4 | **-0.4** |
| 2025-10-13 | -27.35 | 0.9 | **+28.2** | -27.8 | **-0.4** |

Under SF^2 the measured noise floor lands on the declared one with a mean absolute error of
**0.35 dB, across four scenes with four different NESZ values and four different scale
factors**. As shipped it sits 27 dB above, which is physically impossible.

**The calibration finding no longer rests on any competitor claim.** It is confirmed on
vendor metadata alone, and that is how it should be written in Round 3.

*Also settled:* the GEO preview cannot adjudicate this - it is `uint8`, 0-255, a stretched
quicklook with no radiometric meaning. That is why DeepThinkers' preview comparison gave an
offset that reversed sign on one of four dates. Their open question has an answer, and the
answer is that the instrument they used cannot measure the thing.

### 10.2 The bajra anchor: the field is right, for a reason none of them gave

Three teams quoting 1.36-1.89 t/ha against our 2.71 is a majority, not evidence. Two
independent checks:

**Our own table is not internally consistent.** Yield should equal production over area:

| crop | implied kg/ha | stated kg/ha | gap |
|:--|--:|--:|--:|
| **Bajra** | 2,478 | **2,714** | **+9.5%** |
| Rice | 1,833 | 1,690 | -7.8% |
| Maize | 2,231 | 2,312 | +3.6% |
| Groundnut | 2,490 | 2,514 | +1.0% |

(Cotton's apparent -83% is the bales-to-tonnes conversion: 829,400 bales x 170 kg = 141 kt
over 185,479 ha = 760 kg/ha lint, consistent with the stated 776.)

The yield column is not derivable from the columns beside it, and bajra carries the largest
gap of the four, in the direction that inflates our anchor. The table's own production over
area gives **2.478 t/ha, not 2.714** - a 9% cut before any competitor number is consulted.

**And the remaining gap has a mechanism.** Gujarat grows bajra in two seasons that are not
comparable:

| | grain yield |
|:--|:--|
| summer, irrigated | **4,000-5,000 kg/ha** (ICRISAT pearl millet manual) |
| rainfed kharif | **1,200-1,800 kg/ha** |
| irrigated, general | 2,500-3,500 kg/ha |

Our anchor is an **annual** district figure, every season summed, and it lands at 2.5-2.7
t/ha - exactly where a blend of high-yield summer bajra and lower rainfed kharif bajra
should land. Every competitor figure is explicitly a **kharif** estimate, and all three sit
inside the rainfed kharif band.

Round 2 observes 6 June to 13 October 2025. That is kharif. **The anchor must be a kharif
anchor, and ours is not.** This is a season-matching error in our own sourcing, statable
without citing anybody.

**Which other anchors carry the same exposure:**

| crop | second season in Gujarat | exposure |
|:--|:--|:--|
| **Bajra** | summer, irrigated, 2-3x yield | **HIGH - annual mean is inflated** |
| Maize | rabi maize, higher yield | MODERATE - same mechanism, smaller |
| Rice | summer rice is minor | low |
| Groundnut | ~90% kharif in Gujarat | low |
| Cotton | kharif only | none |

So **A5 is not "copy their bajra number"**. It is: source a kharif anchor for every crop,
and check each crop for a second cropping season before using an annual district mean. That
rule catches bajra, flags maize, and is derived from agronomy rather than from a
competitor's table.

### 10.3 One competitor idea that would have broken our pipeline

Orion re-poses uniformity as **CoV excess over the L=1 speckle prediction**: at one look,
fully developed speckle gives CoV = 1.0 exactly, so any excess is real heterogeneity. It is
better posed than raw CoV and I had it in the backlog as item A3.

It does not port to us. `prep_r2.py` resamples by **average** onto a 5 m base grid, which
multilooks. Measured on our own farm statistics:

| date | median farm CoV | implied looks |
|:--|--:|--:|
| 2025-06-06 | 0.431 | 5.4 |
| 2025-06-19 | 0.476 | 4.4 |
| 2025-08-14 | 0.488 | 4.2 |
| 2025-10-13 | 0.469 | 4.5 |

Our data is 4-5 looks, not 1. Subtracting a 1.0 baseline would make every farm's "excess"
large and negative, and the ordering would be dominated by the looks estimate rather than by
heterogeneity - **precisely the failure Megalodon documented and retracted**: *"a per-pixel
estimate against a farm-level statistic drove most farms negative."*

Adopting Orion's formulation verbatim would have introduced the exact bug another team had
already published a retraction about. If we adopt it, the baseline must be our own estimated
looks per date, not 1.0.

### 10.4 Evidence grade for every recommendation in this document

| grade | meaning |
|:--|:--|
| **OWN** | measured on our data or our metadata; no competitor claim load-bearing |
| **MECH** | their claim, but we found and verified the mechanism independently |
| **THEIRS** | rests on their assertion. Not established for us. Test before adopting |

| item | grade | note |
|:--|:--|:--|
| A1 calibration = SF^2 | **OWN** | vendor NESZ, four scenes, 0.35 dB mean error (§10.1) |
| A1 impact is small | **OWN** | full rebuild: 99.2% of labels unchanged, health rho 0.9908 |
| A5 bajra anchor is wrong | **MECH** | our table's own internal gap + the kharif/annual season mechanism (§10.2) |
| A6 yield over-depends on label | **OWN** | eta^2 0.820; +0.395 mean lift when the label is held fixed |
| Uniformity is not an SNR proxy | **OWN** | rho(CV, brightness) = +0.173, opposite sign to Megalodon's |
| Uniformity is null but load-bearing | **OWN** | 0.025 vs witnesses, yet dropping it costs 0.127 -> 0.078 |
| Blind weights anti-correlate with information | **OWN** | Spearman(weight, informativeness) = -0.200 |
| No usable consensus crop map | **OWN** | 4/966 unanimous; consensus loses to 4 of 6 individual maps |
| Our crop mix is the modal position | **OWN** | within 1.5 pp of Coding Bits on three crops |
| A3 CoV excess over L=1 | **THEIRS - and it fails** | our grid is 4-5 looks (§10.3). Do not adopt as written |
| Quegan-Yu speckle filter | **THEIRS** | 2.4-2.8x looks claimed on their data. Never run on ours |
| Thin-plate spline geocoding | **THEIRS** | ~8 m polynomial residual is their measurement. Ours is unmeasured |
| Spatial hold-out for weights | **THEIRS** | sound in principle; never run on our features |
| Plot-size de-biasing | **PARTLY OWN** | we measured rho(CV, npix) = +0.229, so the artefact is real here. The correction itself is untested |
| 500 m grid sub-village table | **THEIRS** | presentation only, no correctness risk; the 32-point spread is their number, not ours |

Nothing in the THEIRS rows should enter a Round 3 report as established. The two that would
have changed shipped numbers are now OWN and MECH respectively, and one THEIRS row turned
out to be actively wrong for us.

---

## 11. The remaining borrowed ideas, run on our own features

`e7_test_theirs.py`. Three items were still graded THEIRS after §10. Two could change the
health index, so both were tested rather than adopted.

### 11.1 Plot-size de-biasing - does not transfer

Coding Bits regress every feature on log(area) and remove the trend, reporting residual
area correlation below 0.001. The artefact is genuinely present in our data too:

| family | rho vs log(area) | after de-biasing |
|:--|--:|--:|
| `level` | +0.129 | +0.067 |
| `growth` | -0.175 | -0.171 |
| `uniform` | -0.234 | -0.168 |
| `persist` | +0.247 | **+0.376** |

But removing it does not help, and `persist` gets *worse* - its area dependence is not
linear in log(area), so a linear detrend amplifies it. Against the two withheld witnesses:

| index | rho vs NDVI | rho vs S1 VH |
|:--|--:|--:|
| shipped | **+0.127** | **+0.156** |
| plot-size de-biased | +0.115 | +0.147 |

**VERDICT: rejected for us** (-0.012 NDVI, -0.009 S1). The artefact is real; the correction
as specified makes the index slightly worse on both witnesses. If it is revisited, the
detrend has to be non-linear for `persist`, and that is a different method than the one
being borrowed.

### 11.2 Spatial hold-out - the method is good, and it corrects one of our own findings

Coding Bits derive weights on the western half and report on the eastern. Applied to our
four families, both directions:

| weights derived on | resulting `uniform` weight | scored on | rho NDVI | vs shipped |
|:--|--:|:--|--:|--:|
| west half | 0.418 | east | **+0.203** | +0.185 |
| east half | 0.441 | west | **+0.135** | +0.160 |

Two things fall out.

**Our blind rule consistently over-weights `uniform`.** On the full sample it assigns 0.301;
on either half alone it assigns 0.418-0.441. `uniform` is the family with no witness signal
(§8.2), so the rule's bias toward it strengthens as the sample shrinks - exactly what a rule
that rewards being uncorrelated should do when noise gets noisier.

**And this corrects §8.2's T4.** There I reported the shipped weighting as "best of four" on
the full sample. It does not survive the hold-out. Mean across both directions:

| weighting | mean held-out rho NDVI | mean rho S1 VH | spread between halves |
|:--|--:|--:|--:|
| derived on the other half | 0.169 | 0.183 | 0.068 |
| shipped, full-sample blind | 0.172 | 0.181 | 0.025 |
| equal | 0.166 | 0.174 | 0.004 |

The three schemes sit within **0.007** of each other, while the spread *between the two
halves* is 0.007-0.068 - an order of magnitude larger. The ranking flips by direction:
west-derived weights beat shipped on the east, east-derived weights lose to shipped on the
west.

**The honest statement is that our health index is insensitive to the weighting choice.**
That is a robustness result, not a vindication of the blind rule, and it is a better claim
than the one §8.2 originally made. It also means A3 was mis-scoped: there is no weighting
fix worth chasing, because no weighting is measurably better than any other.

*(Held-out rho values are not directly comparable to §8.2's full-sample figures: the
within-crop z-scoring is recomputed inside each half, so the scales differ. The comparison
that matters is between schemes within a single row.)*

### 11.3 Geocoding residual - still untested, and now flagged as such

Coding Bits report a polynomial GCP fit leaving ~8 m residual against a 24.7 m median plot,
which is why they moved to a thin-plate spline. Our median plot is 0.274 ha - a **52.4 m
square** - so the geometry is comparable but not identical.

Our chain resamples by average onto a 5 m base grid, so a residual of their size would be
1.6 base pixels and would mix neighbouring fields at boundaries. We erode before sampling,
which is the mitigation, but **the residual itself has never been measured on our fit**.

**STATUS: THEIRS.** Measuring it requires the GCP fit residuals out of `prep_r2.py`'s
geocoding step - a code change rather than an analysis. This is the one borrowed claim whose
*premise* remains untested for our pipeline, and it should be written that way rather than
cited as a reason to adopt splines.

### 11.4 Where the borrowed ideas ended up

Of the six ideas taken from other teams that could have touched our numbers:

| idea | outcome |
|:--|:--|
| Calibration = SF^2 | **Adopted.** Confirmed on vendor NESZ alone (§10.1) |
| Kharif-matched yield anchors | **Adopted.** Mechanism verified independently (§10.2) |
| CoV excess over L=1 | **Rejected.** Our grid is 4-5 looks; would reproduce Megalodon's retracted bug (§10.3) |
| Plot-size de-biasing | **Rejected.** Real artefact, but the correction makes the index worse (§11.1) |
| Spatial hold-out | **Adopted as a method**, and it overturned one of our own conclusions (§11.2) |
| Thin-plate spline geocoding | **Undecided.** Premise unmeasured on our chain (§11.3) |

Two adopted, two rejected, one adopted as method, one still open. A shortlisted writeup is a
hypothesis; four of these six needed testing before they could be believed, and two of them
would have made the product worse.

---

## 12. The geocoding residual, finally measured

§11.3 left this as the one borrowed claim whose premise was untested for us. It is now
measured (`e8_geocoding.py`), without touching the frozen pipeline.

`prep_r2.geocode()` calls `rasterio.warp.reproject(gcps=...)`, and GDAL given 225 GCPs and
no explicit order fits an **order-3 polynomial** - the same class Coding Bits measured at
~8 m and replaced with a thin-plate spline.

**Method note.** Scoring a spline by its residual *at* the control points would be rigged:
a TPS interpolates every control point exactly, so its error there is zero by construction
and says nothing about accuracy anywhere else. Both are scored by **leave-one-out** - fit on
224, predict the held-out one - which is what matters for a farm boundary sitting between
control points.

*A first run of this reported a 140 km residual for order 3. That was `lstsq` failing on a
cubic design matrix built from raw row/col values in the tens of thousands, not a real
result. Coordinates are centred and scaled before fitting, as GDAL does internally.*

| date | poly1 | poly2 | poly3 | TPS | (median LOO error, m) |
|:--|--:|--:|--:|--:|:--|
| 2025-06-06 | 5.62 | **2.93** | 3.00 | **1.41** | |
| 2025-06-19 | 7.08 | **3.39** | 3.85 | **1.99** | |
| 2025-08-14 | 7.25 | **3.51** | 3.88 | **1.77** | |
| 2025-10-13 | 6.60 | **2.83** | 3.38 | **1.80** | |

| date | poly1 | poly2 | poly3 | TPS | (95th percentile, m) |
|:--|--:|--:|--:|--:|:--|
| 2025-06-06 | 16.18 | 17.69 | 15.75 | 12.10 | |
| 2025-06-19 | 20.84 | 20.75 | 18.80 | 15.39 | |
| 2025-08-14 | 21.55 | 22.75 | 20.15 | 15.22 | |
| 2025-10-13 | 18.97 | 20.61 | 18.20 | 15.13 | |

**Verdict, in three parts, none of which is the one their writeup implies:**

1. **The premise does not transfer as stated.** Their polynomial residual was ~8 m; ours is
   **3.6 m median** - inside one 5 m base cell, and 7% of our 52 m plot side. Our fit is
   about twice as good as the one they rejected, so their number is not our number, and
   "polynomial geocoding is a defect" is not a claim we can inherit.
2. **But the spline still halves it**, 3.62 -> 1.78 m median and 18.5 -> 15.2 m at the 95th
   percentile. The tail is where this bites: a 19 m error is **35% of a plot side**, which
   is real boundary mixing on the worst-placed farms. Erosion before sampling is currently
   our only guard against it.
3. ~~**The cheapest win is not the spline at all.** Forcing **order 2** recovers 0.46 m...~~
   **WITHDRAWN.** Mining Coding Bits' notebook turned up the comment *"gcps= alone fits a
   2nd-order polynomial"* - so there is no order-3 default to force away from. We could not
   verify that directly (`osgeo` is not installed; an attempted marker-warp test produced an
   empty raster and its apparent 564 m offset was the corner of an all-zeros array, not a
   measurement), but the question is moot: order 2 and order 3 differ by **0.07 m** on
   held-out points and 0.35 m in-sample. No recommendation either way. See
   `DELIVERABLE_MINING.md` §2, which also records the trap that
   **`METHOD='GCP_TPS'` is silently ignored by GDAL - the working key is `SRC_METHOD`.**

So: **adopt, but neither for their reason nor necessarily by their method.** Order 2 first
because it is nearly free; the spline afterwards if the tail matters.

**Caveat, stated.** This measures the GCP fit only. It cannot see a common-mode error that
shifts every GCP equally - the class Megalodon's geoid bug belonged to, and precisely the
class our own calibration error belonged to. Our absolute registration against the vendor's
geocoded product remains a separate and still-unmeasured question.

### 12.1 Final scorecard on the borrowed ideas

| idea | outcome | why |
|:--|:--|:--|
| Calibration = SF^2 | **Adopted** | confirmed on vendor NESZ alone, 0.35 dB mean error (§10.1) |
| Kharif-matched anchors | **Adopted** | mechanism verified independently: annual vs kharif bajra (§10.2) |
| Spatial hold-out | **Adopted as method** | and it overturned one of our own conclusions (§11.2) |
| Polynomial -> order 2 / spline | **Adopted, reframed** | their 8 m premise is false for us; ours is 3.6 m, but order 2 and then TPS still improve it (§12) |
| CoV excess over L=1 | **Rejected** | our grid is 4-5 looks, not 1 (§10.3) |
| Plot-size de-biasing | **Rejected** | artefact is real, correction makes the index worse (§11.1) |

Six borrowed ideas. **Two adopted as given, two adopted only after reframing, two rejected.**
Not one of them was safe to take on the strength of a shortlisted writeup alone.
