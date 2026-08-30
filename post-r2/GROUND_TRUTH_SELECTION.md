# How to spend 100 manual lookups — and why my own proposal was wrong

`e16_gt_selection.py`. This tests **D-3 as I wrote it in `ROUND3_DIRECTIONS.md`**, and the
result is that the proposal was mis-specified. Recording it because the reasoning generalises.

## The proposal, and the error in it

D-3 said: re-sort the staged ground-truth sample by active learning — pick the farms where
Capella and the e14 embedding disagree, where predicted SE is highest, and where e14 found no
corroboration. The evidence cited was that spatially explicit active learning reaches 80%
accuracy at **97 samples** against 169 for conventional selection.

**That citation is about a different job.** Active learning selects *training* labels to
improve a classifier. Our sample does not train anything — `src/ingest_ground_truth.py` uses
it to **measure** the accuracy of a map that is already frozen. The two goals want opposite
samples:

- measuring accuracy wants a sample whose selection is **independent of correctness**
- improving a map wants exactly the farms **most likely to be wrong**

Selecting the hardest farms and averaging correctness over them estimates the accuracy of the
hard farms, not of the village. I imported a result from the literature without checking that
its objective was ours — the same failure the "test before adopting" rule exists to catch, and
this time the idea being adopted was my own.

## The test

956 farms (degenerate geometry dropped), 100-lookup budget, 400 synthetic replicates. Truth is
generated so our label is wrong more often where our confidence is low; the strength of that
dependence is swept, because that dependence is the whole question. **At strength 0 every
scheme must come out unbiased — that is the control that says the test is not rigged.**

| dependence | scheme | mean est | bias | RMSE |
|--:|:--|--:|--:|--:|
| **0.0** | random | 65.4% | +0.3pp | 4.7pp |
| | stratified | 65.2% | +0.2pp | 5.9pp |
| | uncertainty-first | 64.9% | −0.2pp | 4.7pp |
| | hybrid | 65.3% | +0.2pp | 6.9pp |
| **0.5** | random | 64.8% | −0.2pp | 4.5pp |
| | stratified | 65.2% | +0.2pp | 5.7pp |
| | **uncertainty-first** | 61.3% | **−3.7pp** | 6.1pp |
| **1.0** | random | 64.9% | −0.2pp | 4.1pp |
| | stratified | 64.8% | −0.2pp | 5.6pp |
| | **uncertainty-first** | 52.7% | **−12.4pp** | 13.4pp |
| | uncertainty + IPW | 53.5% | −11.6pp | 15.4pp |
| | hybrid (headline from 70) | 65.2% | +0.1pp | 6.7pp |
| **1.5** | random | 63.3% | −0.3pp | 4.5pp |
| | **uncertainty-first** | 40.0% | **−23.6pp** | 24.0pp |

The control passes: at strength 0 every scheme is within 0.7pp. Then:

- **Uncertainty-first is catastrophically biased** — −12.4pp at moderate dependence, −23.6pp
  at strong. It would have reported a 65% map as 40-53% accurate.
- **Inverse-probability weighting does not rescue it** (−11.6pp), and it *adds* variance even
  at strength 0 where there is nothing to correct (RMSE 4.7 → 9.3pp).
- **Random and stratified are unbiased at every strength.**

## The competing objective, which is where active learning does win

Errors discovered per 100 lookups, at dependence strength 1.0:

| scheme | errors found |
|:--|--:|
| **uncertainty-first** | **47.3** |
| hybrid | 36.6 |
| stratified | 36.2 |
| random | 35.1 |

Uncertainty-first finds **35% more errors** — and is the worst possible way to measure
accuracy. **The two goals are formally in conflict**, and one sample of 100 cannot serve both
without being split.

## Verdicts

**Rejected: uncertainty-first reselection.** My own D-3 proposal, killed by its own test.

**Kept: stratified 20-per-crop.** Unbiased at every dependence strength, and the stratification
buys per-class recall that a random sample of 100 cannot give — 6 maize rows cannot measure
maize accuracy. It costs about **1.3pp of headline RMSE** against simple random (5.6 vs 4.1),
which is the honest price of being able to say anything per crop, and it is worth paying.

**Available but not adopted: the hybrid** — 70 stratified for the headline, 30 targeted at
rice/maize/bajra where e14 found zero independent corroboration. Unbiased (+0.1pp) at a cost
of 1.1pp RMSE. It is **not** worth it while the map is frozen and error discovery cannot feed
back into anything. **It becomes the right design the moment D-2 makes the label a
distribution**, because then discovered errors have somewhere to go.

**Fixed: a real defect in the staged sheet.** `make_gt_sample.py` filtered on registry-match
quality but never on geometry, so **seven degenerate parcels were in the eligible pool and one
(farm 19, 4.8e-09 ha, centroid 835 km out) was staged for a human to go and identify.** Manual
lookups are the scarcest resource in this project — Track E is blocked on them — so that was
1% of the entire budget spent on a parcel nobody can stand on. One guard added at the pool,
sheet regenerated (0 rows were filled, so nothing was discarded and no result was peeked at).

Two assertions added to `post-r2/tests_regression.py`: the sheet must be findable on the
ground, and it must stay stratified — because the estimator in `ingest_ground_truth.py` is
only the one e16 validated while the sheet is balanced.

## What this changes for whoever does the lookups

Nothing about the procedure. The sheet is still 100 rows, 20 per predicted crop, in
`data_aux/ground_truth_TEMPLATE.csv`, and partial collection still works — `ingest` skips
blanks. What changed is that all 100 rows now point at parcels that exist, and the design
behind them has been tested rather than assumed.
