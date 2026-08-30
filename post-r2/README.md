# post-r2/

Everything in this folder was produced **after** the Round 2 submission closed and the
writeups went public. None of it changes the Round 2 deliverable.

## The rule

The Round 2 submission is **frozen**. `results/submission.csv`, `docs/`, `src/` and
`notebooks/` are what was submitted and judged, and they stay exactly as they were shipped.
Nothing in this folder writes to any of them.

Experiments read the shipped artefacts and write only to `post-r2/results/`. Where an
experiment needs to run a shipped pipeline stage, it redirects that stage's output paths
rather than editing the stage.

## Contents

| path | what it is |
|:--|:--|
| `COMPETITOR_ANALYSIS_R2.md` | Full teardown of the five other shortlisted writeups, with a ranked adoption backlog |
| `sokhda_six.html` | The same analysis as a standalone page for the team |
| `experiments/` | Scripts that test the findings against our own data |
| `results/` | Their output. Regenerable; nothing here is a deliverable |
| `writeups_submissions/` | The five competitors' published Round 2 deliverables, as downloaded. Read-only inputs |

## Experiments

| # | question | verdict |
|:--|:--|:--|
| `e1_calibration` | Two teams form β₀ with the scale factor **squared**. Does correcting ours change the submission? | **Barely.** 99.2% of crop labels unchanged, health ρ=0.9908, village production +0.5%. The bug is real; the product is insensitive to it, because nothing shipped is an absolute level |
| `e2_uniformity` | Our largest health weight has the sign Megalodon publicly retracted. Is ours also a signal-to-noise proxy? | **No** - ρ(CV, brightness) is +0.173, the opposite sign. But the term is null on both witnesses (0.025), yet removing it makes the index *worse*. It earns its place as a decorrelator |
| `e4_consensus_all` | All six submissions side by side. Is there a consensus crop map? | **No.** 4 farms of 966 unanimous; the majority label separates the withheld sensors worse than 4 of 6 individual maps. Teams agree on health (rho +0.337) but not crop (kappa +0.060) or yield (rho +0.073). Our bajra anchor is the field outlier |
| `e3_consensus` | One competitor published their submission. How far do we agree on crop type? | **Village mix agrees to 2.63 pp; per-farm agreement is BELOW chance** (17.2% raw, kappa -0.111). Three controls rule out a join bug. Confirms REPORT 7.2 against an external team |

| `e5_anchors` | Our bajra anchor is 40-100% above every other team's. Is it wrong, and is it why our yield anti-correlates? | **Wrong yes, cause no.** +52% above the external median off a 7,022 ha base, and inconsistent with our own SOURCES.md retraction. But correcting it changes cross-team correlation by -0.001 - the anti-correlation is the CROP MAP: holding the label fixed lifts agreement by +0.395 on average, to +0.68/+0.75 with the two closest teams |

| `e6_verify_claims` | The competitors are not authorities. Do their two shipped-number claims survive independent testing? | **Calibration: CONFIRMED on vendor NESZ alone** (4 scenes, 0.35 dB mean error) - no competitor claim load-bearing. **Bajra: confirmed via mechanism** - our anchor is an ANNUAL figure on a KHARIF deliverable, and Gujarat summer bajra yields 2-3x kharif. **And one of their ideas fails here**: Orion's CoV-excess assumes L=1; our grid is 4-5 looks |

| `e7_test_theirs` | The three ideas still graded THEIRS. Do they work on our features? | **Plot-size de-biasing REJECTED** (-0.012 NDVI, -0.009 S1 - real artefact, correction makes it worse). **Spatial hold-out ADOPTED as method**, and it overturned e2's T4: the shipped weighting is NOT best, the index is simply insensitive to weighting. **Geocoding residual still unmeasured** on our chain |

| `e8_geocoding` | Coding Bits replaced a polynomial GCP fit (~8 m residual) with a spline. Does that premise hold for us? | **No, and yes.** Ours is 3.6 m median, not 8 - their claim does not transfer. But the spline still halves it, and the cheapest win is neither: GDAL auto-picks order 3, which OVERFITS our lattice, and order 2 is better by 0.46 m for a one-argument change |
| `e14_embeddings` | Google Satellite Embedding v1 (AlphaEarth): 64 continuous bands at 10 m for 2025. Does an independent sensor stack corroborate our Capella crop labels? | **Partly, and the split is the finding.** Blocked-CV kappa **+0.155** (8.3 permutation SDs above null; not a size artefact, unlike e13) - but recall is **84.9% cotton, 28.6% groundnut, 10.9% bajra, 4.7% rice, 0.0% maize.** First cross-sensor support our labels have ever had, and it covers only cotton. **Not adoptable as a label source**; adoptable as a per-farm second opinion |
| `e15_cotton_anchor` | Cotton is 455/966 farms and was never anchor-checked. Is the 776 kg/ha district figure a unit trap? | **Real defect, anchor KEPT.** The APY table mixes units - cotton is bales-of-lint at ratio 5.76 vs 0.91-1.08 for the other four - but every official source (APY, USDA FAS, CEIC) reports cotton as lint, the host-dummy test was **discarded for failing its own control**, and the field is split 4:1 toward lint. Restating would move the village total **+25.0%** on evidence that does not decide. Adopted: a unit statement, and a regression assertion |
| `e16_gt_selection` | D-3 proposed re-sorting the 100 manual ground-truth lookups by active learning. Is that right? | **No -- my own proposal, rejected by its own test.** The AL literature selects TRAINING labels; our sample MEASURES a frozen map. Uncertainty-first is biased **-12.4pp** (-23.6pp at strong dependence) and IPW does not rescue it. Stratified kept. AL does win error-discovery (47.3 vs 35.1 per 100) -- the goals conflict. **Real fix:** 7 degenerate parcels were in the pool, 1 was staged for a human to go find |
| `e17_dense_s1` | D-1 said fetch a dense Sentinel-1 series to recover the crops the annual embedding lost. Right? | **No, and the series was already in the repo** (`witness_season.csv`, 10 scenes). Dense S1 gives **kappa +0.135, below** e14's +0.155; rice 3.5%, bajra 1.4%. Timing is worth +0.089 (mechanism right, conclusion wrong). **Headline: 42.5% of farms are corroborated by NEITHER independent sensor** - 92% of rice/maize/bajra vs 5.8% of cotton |
| `e18_label_distribution` | D-2 said ship the label as a distribution and propagate it into yield. Sound? | **No -- ill-defined, and e15 is why.** The posterior already exists and is openly unsure (median max 0.409), but is uncalibrated in level (+28.7pp at Q1) and barely ranks within crop. Cotton's label SD is **2.25x its own yield** because cotton is lint and the rest are grain, so the expectation adds different units and moves the village total **+12.8%**. Also **retires e11's claim** that the label is the dominant error: entropy predicts witness disagreement no better than sampling noise did |

Run any of them with `py -3.12 post-r2/experiments/<name>.py` from the repo root.

## Evidence grades

Recommendations carry a grade, because a shortlisted writeup is a hypothesis, not a result:

- **OWN** - measured on our data or our metadata; no competitor claim load-bearing
- **MECH** - their claim, but the mechanism was found and verified independently
- **THEIRS** - rests on their assertion. Not established for us. Test before adopting

The two claims that would change shipped numbers are now OWN and MECH. One THEIRS item
(Orion's L=1 CoV baseline) was tested and **fails on our grid** - adopting it verbatim would
have reproduced the exact bug Megalodon publicly retracted. See section 10 of the analysis.

## Status

| | |
|:--|:--|
| Round 2 submission | **frozen and untouched** - every gate still passes |
| e1, e2 | run; results in `results/` |
| e3 | run |
| Next directions | **`ROUND3_DIRECTIONS.md`** - ranked, each with the test that kills it |
| **Sprint brief** | **`SPRINT_BRIEF.md`** (+ `sprint_brief.html`, unpublished) - read this one first |
| Regression suite | `post-r2/tests_regression.py` - 5 checks, all passing |
| Nothing here is committed | pending review |
| Kaggle credential | stored at `~/.kaggle/kaggle.json`, **outside the repo**. Rotate it - it was pasted in chat |
