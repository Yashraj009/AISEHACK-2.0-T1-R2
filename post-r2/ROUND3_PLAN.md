# Round 3 preparation - the deep pass

Written 2026-08-29, after eight post-R2 experiments closed out the competitor analysis.

## The question that prompted this

*"Should we analyse the writeups once more, or is it good now?"*

**The five writeups are mined out.** Sections 1-12 of `COMPETITOR_ANALYSIS_R2.md` extracted
every claim, tested the six that could touch our numbers, and graded all of them. A ninth
read would produce restatement, not information.

**But what came packaged with them has never been opened:**

| source | volume | why it matters |
|:--|--:|:--|
| Orion notebook | 221,508 chars | prose says *what*; code says *which constant, which threshold* |
| 8bit notebook | 144,642 chars | the only fully SAR-only pipeline - their incidence-matching in full |
| Coding Bits notebook | 135,090 chars | Quegan-Yu and the TPS geocode as actually implemented |
| Megalodon notebook | 11,155 chars | short, so probably an orchestrator - check what it imports |
| 3 methodology PDFs | 42,851 chars | the 4-page reports, which are NOT the Kaggle writeups |
| **total** | **555,246 chars** | never read |

A writeup is an argument. A notebook is the evidence. Everything we tested so far came from
arguments.

## Two of our own assets outrank anything a competitor has

Found while scoping this plan:

1. **We are one data-pull from real ground truth, and nobody else has any.**
   `data_aux/farm_to_survey_number.csv` maps **947 of 966 farms** to Gujarat land-record
   survey numbers (567 distinct). `ground_truth_TEMPLATE.csv` has 100 rows staged with a
   `vf12_crop` column that is **entirely empty**, and `ground_truth_vf12.csv` was never
   created. The join is built; the data was never fetched.

   Every validation in this competition - ours and all five competitors' - is a proxy
   agreeing with another proxy. Actual per-parcel crop for even 100 farms converts our
   crop column from *"kappa 0.103 against our own rebuild"* into a measured accuracy, and
   makes us the only team that can say what the number really is.

2. **`src/wcm.py` inverts the Water Cloud Model and is not wired into the submission.**
   It is imported by nothing on the delivery path. Our health index is a dimensionless
   z-score; the WCM produces canopy water content in kg/m^2. Megalodon reasoned about the
   WCM qualitatively and no team inverted it. We wrote the inversion and shipped the
   z-score.

## Constraints that hold throughout

- **Round 2 stays frozen.** `results/`, `docs/`, `src/`, `notebooks/` are what was judged.
  Everything here writes to `post-r2/` only. Verified each session by re-running the three
  gates and the submission md5 (`89b0e4e2aef63ace4989fc0a44590ee5`).
- **Test before adopting.** Standing instruction, and it has already paid twice: two of six
  borrowed ideas would have made the product worse. Every recommendation carries an
  evidence grade (OWN / MECH / THEIRS), and THEIRS is not actionable.
- **Personal data.** 7/12 records carry owner names. Extract the crop column only, report
  aggregate accuracy only, never publish an owner name or an individual-linked survey
  number. `ground_truth_vf12.csv` stays gitignored.
- **No commits until asked.**

---

# The plan

Six tracks. A and E start first because they have external latency; the rest are
compute-bound and can run whenever.

## Track A - What is Round 3? (gates prioritisation)

Everything downstream depends on an unknown: is R3 a **defence** of the R2 work, or a **new
technical round**? The two need almost opposite preparation.

| if R3 is | then priority is |
|:--|:--|
| presentation / viva of R2 | fix the defects, rehearse the adversarial answers, ship a figure pack |
| new village or more villages | pipeline generality, transfer, and speed |
| more scenes over Sokhda | phenology curve-fitting, which 4 dates cannot support |
| an open extension | the differentiator is ground truth (Track E) |

**A1** Competition page, rules, and any R3 announcement - Kaggle, the ANRF/GalaxEye channels,
the R2 result email.
**A2** Read the Round 2 rubric again against what the shortlist rewarded (all six shortlisted
writeups share five traits - already documented in §6.1 of the analysis).
**A3** Write the finding as a one-page brief that fixes the priority order for B-F.

## Track B - Mine the notebooks and PDFs (555k chars)

Not a read-through. Targeted extraction against questions the prose left open.

**B1 Extraction harness.** Convert all four notebooks and three PDFs to plain text in
`post-r2/results/e9_notebooks/`, indexed by team and cell, so it can be grepped rather than
re-parsed. Report code-vs-markdown split per team.

**B2 The constant hunt.** Every hard-coded number in a competitor pipeline, with the line
that sets it. Specifically: crop thresholds, health weights, completion/progress fractions,
yield anchors, speckle-filter windows, erosion buffers, incidence corrections. Cross-tabulate
against ours. Where five teams pick similar values for a thing we set differently, that is a
prior worth testing; where they all differ, the parameter does not matter.

**B3 The undocumented-move hunt.** Things present in code and absent from the writeup:
dropped experiments, commented-out branches, tuning loops, "v2" functions. Failed approaches
are as informative as shipped ones and nobody writes them up.

**B4 The library census.** Every import across four notebooks. Any package doing real work
that we do not use is a capability gap - and a name to search in Track C.

**B5 Two specific implementations, read closely.** Coding Bits' Quegan-Yu filter and TPS
geocode - the two Tier-C items still unbuilt on our side. Reading their code is much cheaper
than deriving from the papers, and e8 already showed the TPS is worth ~1.8 m to us.

**B6 The three PDFs.** These are the 4-page methodology reports, a different document from
the Kaggle writeup. Diff them against the writeups; where a team says something in one and
not the other, that is usually where the doubt lives.

## Track C - Literature, aimed at our specific open questions

Deep research, not background reading. Each item exists to settle a question our own data
raised.

**C1 What crop separability is actually achievable with 4-date single-pol X-band HH?**
Our kappa vs an independent rebuild is 0.103, and six teams agree at chance (kappa 0.060).
Either everyone is doing it badly, or the information is not in the data. The literature
bounds this, and the answer determines whether crop type is worth more effort at all -
or whether the honest deliverable is a *distribution* over crops per farm.

**C2 Rice at X-band without the transplanting window.**
Collision 1 measured the classic dark-flood rule failing here (-0.71 dB, wrong sign) while
our 6->19 June wetting response separates rice by 3.23 dB. Both Coding Bits and Megalodon
confirm 19 June was a rain day. Is "wetting response as a proxy for exposed soil / standing
water" an established mechanism, and what does the literature say its limits are?

**C3 Multitemporal speckle filtering with only 4 acquisitions.**
Quegan-Yu claims 2.4-2.8x effective looks for Coding Bits. The filter's variance reduction
depends on the number of dates; 4 is few. What does the original paper predict for N=4, and
what does it assume about temporal stationarity that a growing season violates?

**C4 Validate our own WCM parameters.**
`wcm.py` cites El Hajj et al. RSE 176 (2016) Table 5, fitted at X-band HH on TerraSAR-X /
COSMO-SkyMed. Before wiring it into anything: are those coefficients appropriate for these
crops at this incidence range, and what is the reported inversion error?

**C5 SAR yield estimation - what accuracy is real?**
Our yield is 82% crop label (eta^2 0.820). The literature's achievable per-field yield error
tells us whether the remaining 18% is a floor or a failure.

**C6 Uncertainty quantification without labels.**
The universal gap - see Track D1. What is the standard approach for calibrated per-unit
uncertainty when no ground truth exists?

**C7 Gujarat kharif agronomy.** Sowing and harvest windows per crop for Vadodara,
kharif 2025 specifically, to replace `COMPLETION` constants that are currently reasoned
rather than sourced. This also settles A5's kharif-vs-annual anchor question at source.

## Track D - Approaches all six teams missed

Candidates generated from the gap between what the six pipelines do and what the problem
admits. Each is a hypothesis to test, not a plan to adopt.

**D1 Per-farm uncertainty, calibrated.** *(the biggest gap, and it is universal)*
All six teams ship point estimates. Four ship a confidence number; none demonstrates it is
*calibrated* - that a farm marked 0.8 is right 80% of the time. Megalodon comes closest
(disagreement falls monotonically across confidence quintiles) and even that is a monotonic
check, not a calibration curve.

We can go further because we hold something they do not: two independent witnesses and,
potentially, real ground truth. A credible interval per farm on health and yield, plus a
proper probability per crop label instead of a hard label, is defensible, novel in this
field of six, and directly addresses the "no ground truth" problem rather than working
around it.

**D2 Ship the WCM.** Health in kg/m^2 of canopy water alongside the ranked index. Turns
"brighter than its neighbours" into a physical quantity. Code exists; needs C4 first.

**D3 The crop label as a distribution.** If C1 says per-farm crop is information-limited,
then a hard label is the wrong deliverable and a per-farm probability vector is the honest
one. It also fixes A6 structurally: yield conditioned on a *distribution* over crops stops
inheriting a wrong hard label wholesale (eta^2 0.820 is the symptom).

**D4 Semi-supervised self-training.** Orion's tier-1 rice/cotton labels are 100% stable
across clustering hyperparameters. High-confidence labels can seed a classifier for the
uncertain 70%. Risk: confirmation bias. Must be tested against a witness, not against itself.

**D5 Spatial modelling of the residual.** Moran's I = 0.105 says neighbouring farms share
condition. We report the statistic and never use the structure. Kriging or a spatial random
effect could sharpen per-farm estimates - and Orion's ceiling argument (§2.4.6) says how to
tell real field structure from an artefact.

**D6 Sub-look coherence.** Megalodon split the Doppler spectrum to form coherence within a
single image, using it to detect hard targets (metal, vehicles) inside field polygons. We
have `src/sublook.py`. Bright scatterers displace a field mean by up to 19 dB - a masking
win independent of the health method.

**D7 Growth-curve fitting.** Four dates, three parameters - underdetermined per farm, but a
crop-level curve with per-farm scaling may be identifiable. Tests whether "conformity to
expected trajectory" can be a fit rather than a distance.

**D8 Absolute calibration against stable targets.** Our calibration is now correct, but
absolute registration and level against the vendor's geocoded product remains unmeasured
(e8's stated caveat, and the class of error both our bug and Megalodon's geoid bug belonged
to).

## Track E - Real ground truth (the differentiator)

The one thing that would put us in a different category from all five competitors.

**E1 Re-establish the access path.** `src/kdss_client.py`, `src/ingest_ground_truth.py` and
`src/fetch_dcs_parcels.py` exist; the token is expired and PMFBY CCE yield needs an officer
login. Establish what is still reachable without privileged access.
**E2 Pull the crop column for the staged 100-farm sample**, respecting the data rules: crop
column only, no owner names, no individual-linked survey numbers published.
**E3 Measure real accuracy** - overall and per crop, with confidence intervals, on the
sample. This is the number no other team can produce.
**E4 If it works, extend** toward the 567 distinct survey numbers.
**E5 If it is blocked, document the blocker precisely** and fall back to the strongest
available proxy. A documented, precisely-characterised blocker is itself a reportable
finding, and it is what §7.2 of the report already gestures at.

## Track F - Things not asked for, added deliberately

These were not in the request. Each is included because leaving it out would cost us.

**F1 The R3 format question (Track A) is the highest-leverage unknown**, and it was not in
the brief. If R3 is a live defence, half of D is wasted effort and rehearsal is everything.

**F2 Ground truth (Track E) was not mentioned** and is the single biggest differentiator
available. It was staged before Round 2 and never completed.

**F3 A failure-mode regression suite.** Between them the five teams document a geoid bug, a
1-based/0-based FID join error, a calibration double-correction, an SNR-proxy artefact, and
a speckle-filter-induced correlation. **Every one survived internal consistency checks in a
competent pipeline.** Our own calibration error is a sixth of exactly that class. Each
becomes a cheap assertion; together they are a test suite no other team has, and a genuinely
novel contribution to write up.

**F4 Judge-facing deliverables.** Our figures are built for a written report. A defence needs
a different pack: one slide per finding, the negative results foregrounded, and the
adversarial Q&A from §6.2 rehearsed with numbers to hand.

**F5 An honest self-audit, published.** We found three defects in our own pipeline this week
(calibration, bajra anchor, yield/label coupling) and corrected three of my own analytical
errors. Every shortlisted team reports failures; **none reports a post-hoc audit of its own
submission.** Doing that openly is differentiating precisely because it is uncomfortable.

**F6 Compute and reproducibility budget.** Kaggle runtime is a hard constraint and D2, D5
and D7 all add cost. Measure before adopting.

**F7 Team logistics.** Who presents, what is rehearsed, and what the one-sentence summary of
this work is. Out of scope for me, but it should not be discovered late.

---

# Execution order

| # | task | track | blocks | cost |
|:--|:--|:--|:--|:--|
| 1 | Find out what R3 actually is | A1-A3 | everything | small |
| 2 | Re-establish the ground-truth path | E1 | E2-E5 | small, external latency |
| 3 | Notebook extraction harness + constant/library census | B1-B4 | D | medium |
| 4 | Literature on C1, C2, C6 (the three that change what we build) | C | D1, D3 | medium |
| 5 | Failure-mode regression suite | F3 | - | small, high value |
| 6 | Per-farm calibrated uncertainty | D1 | - | large, highest payoff |
| 7 | Crop label as a distribution | D3 | needs C1 | medium |
| 8 | Read Quegan-Yu + TPS implementations | B5 | Tier-C decisions | medium |
| 9 | WCM validation, then wire it | C4, D2 | - | medium |
| 10 | Remaining D items, by what 1-9 reveals | D | - | tbd |

Nothing here is adopted on anyone's authority, including mine. Every item that could change
a number gets tested on our own data first, and reported with its evidence grade whether it
worked or not.

---

# Progress log

Updated 2026-08-29. Phase 3 confirmed: **2-3 September, in-person, Goa** - a working sprint
alongside GalaxEye and IIT Madras researchers, not a defence. Four days out at time of writing.

| task | track | status |
|:--|:--|:--|
| Find out what R3 is | A | **done** - working sprint, Goa, 2-3 Sep, confirmed by the team |
| Mine notebooks + PDFs (555k chars) | B1-B6 | **done** - `DELIVERABLE_MINING.md` |
| Kharif-season anchors, new dataset | C7 / A5 | **done** - `KHARIF_ANCHORS.md`, adopt bajra only |
| Per-farm calibrated uncertainty | D1 | **done** - `UNCERTAINTY.md`, calibrated but not limiting |
| Real ground truth | E | **BLOCKED ON A PERSON** - see below |
| Screen new data sources (ceiling test) | new | **done** - `DATA_SOURCES.md` |
| Failure-mode regression suite | F3 | not started |
| WCM validation and wiring | C4 / D2 | not started |
| Crop label as a distribution | D3 | not started, needs C1 |

## Track E is blocked, and precisely why

`vf12_crop` is filled from **AnyROR VF-12**, a per-record government portal lookup, and the
Krishi-DSS route in `src/kdss_client.py` needs a session token copied out of a browser after
an interactive login. `data_aux/.kdss_token` does not exist.

Interactive account login and CAPTCHA-solving are both outside what I will do, so this needs
a person. `internal/research/GROUND_TRUTH_HOWTO.md` has the procedure and
`data_aux/ground_truth_TEMPLATE.csv` has 100 rows staged and waiting.

It remains the single highest-value item available: no team in this competition has ground
truth, it is the only way to settle our 30.8% groundnut share against Orion's 16%, and
`src/ingest_ground_truth.py` already handles the stratified re-weighting and chance baseline.
**Partial collection is useful** - the ingest script skips blank rows, so even 20-30 filled
rows produce a measured accuracy.

## What changed in the recommendations

- **A5 kharif anchors: adopt bajra only** (2.714 -> 1.91 t/ha). Groundnut rejected on
  out-of-sample evidence - its ratio makes the estimate *worse* than doing nothing.
- **C1 Quegan-Yu speckle filter: deprioritised.** Quantified at 5.6-6.4% of between-farm
  signal, on a noise term shown not to drive witness disagreement.
- **e8 part 3 (force polynomial order 2): withdrawn**, immaterial at 0.07 m.
- **A3 uniformity reweighting: closed**, the index is insensitive to the weighting choice.

## Where the error actually is

Three separate measurements now agree that our limiting error is **not** measurement noise:

- sampling noise is 15.9% of between-farm signal and does not predict witness disagreement
- yield is 82% explained by the crop label (`eta^2 = 0.820`)
- crop labels agree at chance across six independent pipelines (`kappa = 0.060`)

**The crop label is the bottleneck, and it is an information limit rather than a processing
one.** That points Round 3 at D3 (label as a distribution) and Track E (real labels), not at
better filtering.

## A reusable screening rule, added 2026-08-29

`e12_data_ceiling.py` measures, on our own farms, the most any covariate constant within a
cell of side L could explain of within-crop health variation:

| 100 m | 250 m | 500 m | 1 km | 5 km | 11 km+ |
|--:|--:|--:|--:|--:|--:|
| 0.685 | 0.226 | 0.125 | 0.041 | 0.015 | **0.000** |

Our 250 m figure (0.226) reproduces Megalodon's (0.226) exactly, and both give 0.000 at
50 km - independent corroboration from two different pipelines.

**Any future data proposal gets priced against this table before it is fetched.** Anything on
a cell larger than the village cannot rank farms inside it, which disposes of every weather
API, reanalysis product and country-level statistic for the ranking job in one line. Coarse
data keeps two legitimate uses - temporal context and aggregate anchors - and both are about
level or timing rather than ranking.


## Superseded by `ROUND3_DIRECTIONS.md`, 2026-08-29

`e14_embeddings.py` added the first independent cross-sensor evidence on our crop labels (kappa +0.155, but 84.9% of it is cotton and 0.0% is maize). That reorders the backlog, and the new order - with the test that kills each item - is in **`ROUND3_DIRECTIONS.md`**.

Headline changes: cotton has never been anchor-checked despite being 47% of farms and carrying a lint/seed unit trap (**new top item**); the staged ground-truth sample should be re-sorted by active learning before anyone types into it (zero cost); and dense Sentinel-1 is the largest available gain but spends the `s1_vh_db` witness, so a replacement witness must be frozen first.

## A3 closed, 2026-08-29

"Write the finding as a one-page brief that fixes the priority order" is done: **`SPRINT_BRIEF.md`**. It carries the adversarial Q&A, the eleven closed ideas, the four shipped defects, the four R3 scenarios, and the measured portability debt (12/33 files hardcode the village, 20/33 hardcode the dates).

Track E is **dead for R3** - the Krishi-DSS API is unavailable and AnyROR needs a person. Planning no longer assumes ground truth arrives.
