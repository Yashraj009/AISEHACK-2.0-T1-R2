# Goa sprint brief — 2–3 September

Everything from the post-R2 pass, in the form it is needed on-site. Ten documents and eighteen
experiments compress to this. If you read one file before the sprint, read this one.

---

## 1. State of play in sixty seconds

- **R2 submission is frozen and untouched.** md5 `89b0e4e2aef63ace4989fc0a44590ee5`,
  `d11_ship.py` READY. Nothing since R2 has changed a shipped number.
- **18 experiments run since R2.** Ten borrowed or self-proposed ideas tested; **seven
  rejected**, including three of my own four Round-3 directions.
- **One real defect found in our own work** (calibration, e1) and one in our data source
  (cotton units, e15). Both measured, neither applied — see §4.
- **Ground truth is dead for now.** Krishi-DSS API unavailable, AnyROR needs a person. No team
  in this competition has ground truth either.
- **Regression suite: `py -3.12 post-r2/tests_regression.py`, 5 checks, passing.** Run it after
  any change on-site.

**The headline finding, if you say one thing:** we are the only team that has measured *where
its own crop map is unsupported*. Two independent sensor stacks back our cotton on **78.8%** of
farms; **42.5% of the village is backed by neither**, and that 42.5% is almost entirely rice,
maize and bajra.

---

## 2. Adversarial Q&A — the questions a judge can actually land

**"Your calibration is wrong. Two teams use scale_factor², you use scale_factor."**
Correct, and we found it ourselves before reading their code. Verified against the vendor's own
declared noise floor (`nesz_peak`): under our convention the darkest 0.1% of pixels sit **+26 to
+28 dB above** the declared floor, which is physically impossible. Under SF² they land within
**0.35 dB mean absolute error across all four scenes**. Effect on the product, measured in e1:
**958/966 crop labels unchanged**, health ρ = 0.9908, production +0.5%. It is a defect in the
level, not in the ranking, and the ranking is what the deliverable is.

**"Groundnut at 30.8%? Orion says 16%."**
Round 1's official truth file gives Sokhda **31.0%**. Our figure was right to the decimal. We
had earlier let the *district* APY table overrule a village measurement, wrote that down as a
mistake, and retracted it in `data_aux/SOURCES.md`.

**"Cotton at 0.34 t/ha is impossibly low."**
It is **lint**, not seed cotton. Every official source reports cotton this way — APY, USDA FAS,
CEIC; Gujarat's own figure is 647 kg/ha. Multiply by **2.94** for kapas. We tested converting
(e15) and **rejected** it: the host-dummy range test failed its own control (it condemns maize
and rice too, which are not in dispute), the shortlisted field splits 4:1 toward lint, and the
cross-crop ordering test mildly opposes conversion. Restating would move the village total
**+25%** on evidence that does not decide.

**"Six teams produce six different crop maps. Why is yours right?"**
We do not claim it is, and we are the only team that measured the question. Six-team Cohen's
κ = **0.060** — chance. Only 4 of 966 farms are unanimous. We then tested our labels against two
sensors that never saw Capella: cotton is corroborated on **78.8%**, but **not one rice, maize
or bajra farm** is backed by both. We can tell you exactly which 42.5% of our map rests on
nothing. Nobody else can.

**"Why no optical? NDVI would settle this."**
Sokhda had **zero** Sentinel-2 scenes under 20% cloud in June, July, August *or* September. The
best July scene is 92.6% cloud. Optical does not exist for the accumulation period. That is why
the season witness had to be built from Sentinel-1.

**"Your health index weighting looks arbitrary."**
It is insensitive, and we proved it against ourselves. A spatial hold-out (e7) put three
weighting schemes within **0.007** of each other while the spread between spatial halves was
0.007–0.068. We had previously claimed the shipped weighting was "best of four"; that claim was
**overturned by our own test** and withdrawn.

**"Isn't the rice signal just rain?"**
It is a rain-*driven mechanism*, and we verified the rain independently rather than taking it
from a competitor. Open-Meteo hourly at the actual overpass hours: **0.0 mm** in the six hours
before 6 June, **17.3 mm** before 19 June. Two other teams independently report the same event.
Sentinel-1 straddles it (12 and 24 June, never sampling the 19th) and *still* shows rice
brightening most, +2.18 dB against +1.88 for the rest.

**"You have no ground truth."**
Correct — and neither does any team here. What we did instead: built the sampling design and
**tested it** (e16). Stratified 20-per-crop is unbiased at every error structure; the
uncertainty-first scheme we were about to adopt would have biased the accuracy estimate by
**−12.4 to −23.6pp**. We also found and removed a parcel of 4.8×10⁻⁹ ha that had been staged for
a human to go and physically identify.

**"Why not classify from Sentinel-1? It's free and dense."**
Two reasons, and the second is measured. (a) The guidelines require Capella primacy, so C-band
cannot be the source of the headline output. (b) We tested it anyway as a witness: ten S1 dates
across our season give **κ +0.135 — below** the annual embedding's +0.155, with rice at 3.5% and
bajra at 1.4%. It does not help.

**"What is your single biggest weakness?"**
Rice, maize and bajra: **287 farms, 30% of the village, corroborated by no independent sensor**.
Say it before they find it.

---

## 3. Do not re-propose these on-site

Each was tested and priced. Re-opening one costs sprint hours and the answer will not change.

| idea | why it is closed |
|:--|:--|
| Dense Sentinel-1 for classification | κ +0.135, **below** the annual embedding; series already in repo (e17) |
| Dynamic World non-crop filter | half a farm-size detector; effect flips sign across area deciles (e13) |
| WorldCereal crop type | 2021 product, **κ = −0.010**; v2 not due until 2026 (e13) |
| Quegan-Yu speckle filter | buys 5.6–6.4% of between-farm signal (e11) |
| Any covariate coarser than ~1 km | ceiling 0.041 at 1 km, **0.000** past 11 km (e12) |
| ERA5 / NASA POWER / OpenWeatherMap | one value for all 966 farms (e12) |
| USDA ERS | US farm *finances*, 16 US states (e12) |
| AlphaEarth embeddings as a label source | 0.0% recall on maize, 4.7% on rice (e14) |
| Propagating the label posterior into yield | ill-defined: cotton is lint, the rest grain (e18) |
| Restating cotton as seed cotton | evidence does not decide; +25% on the village total (e15) |
| Forcing GDAL polynomial order 2 | 0.07 m; recommendation withdrawn (e8) |

---

## 4. Known defects we ship, and the reason

Be first to name these. Each is documented and each has a reason.

1. **Calibration uses SF, not SF².** Level is wrong by a constant; ranking is not. Correcting it
   changes 8 of 966 labels. Not applied because the R2 submission is frozen.
2. **The yield column mixes units.** Cotton is lint, the other four grain or pod. Defensible
   (every official source does this) but it must be *stated*, because 0.34 next to bajra's 2.57
   reads as an error otherwise. Guarded by an assertion.
3. **Nine degenerate parcels** carry submission rows while enclosing ~0 ha. They are excluded
   from anything spatial. Orion independently documented ten.
4. **The label posterior is not calibrated in level** — under-confident by +28.7pp in its lowest
   quintile, and it barely ranks within crop.

---

## 5. If R3 is… (the four scenarios, and what to reach for)

The format is still unknown. This is what to open in each case.

| if it is | reach for | ready? |
|:--|:--|:--|
| **presentation / viva of R2** | §2 above, plus `sokhda_six.html` and the figure pack | **yes** |
| **new village / more villages** | portability facts in §6 | partly — see §6 |
| **more scenes over Sokhda** | phenology; four dates cannot support a curve fit, more can | this is the best case for us |
| **open extension** | ground truth was the differentiator and it is blocked | no |

**The most likely productive case is more scenes.** Everything measured since R2 says our limit
is information, not processing — and more acquisition dates is the one input that adds
information we cannot otherwise get. e17 quantified the mechanism: preserving season *timing* is
worth **+0.089 κ** over a flattened series. Four Capella dates is the binding constraint.

---

## 6. Portability, measured

If a new AOI appears, this is what you face — measured, not guessed.

- **12 of 33 files in `src/` hardcode `Sokhda` or `Vadodara`.**
- **20 of 33 hardcode the 2025 acquisition dates.**

One change has been made to reduce the sharpest edge: `src/common.py` now takes the village and
data paths from the environment, defaulting to Sokhda so nothing changes when unset.

```bash
AISE_VILLAGE=Newname AISE_DATA=/path/to/data py -3.12 src/prep_r2.py
```

Verified: with nothing set, `submission.csv` md5 is unchanged and all 5 regression checks pass.

**Still hardcoded and NOT fixed:** `DATES` and `INCIDENCE_DEG` in `common.py`, the Vadodara APY
yield anchor, and `sokhda_r1_truth.csv` as the crop-mix prior. A new village needs all four
replaced. That is a deliberate call — a refactor four days before a sprint is how frozen
pipelines break — but it is a known 1–2 hour job, not a surprise.

---

## 7. Two things still outstanding

1. **Rotate three credentials.** The data.gov.in key, the USDA ERS key and the GEE client secret
   were all pasted into a chat transcript. They live outside the repo in `~/.config/aisehack/`;
   the repo tree was checked and contains nothing credential-shaped. **This is the only item
   with a real deadline.**
2. **Nothing is committed.** 19 pending changes, four days of work, no history. Awaiting the go.

---

## 8. The one-line version

*We took every idea the five other shortlisted teams published, tested ten of them, threw seven
away including three of our own — and the thing we can say that nobody else can is exactly which
42.5% of our crop map no independent sensor will corroborate.*
