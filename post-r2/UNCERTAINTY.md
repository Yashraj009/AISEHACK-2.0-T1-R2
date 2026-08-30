# Per-farm uncertainty: calibrated, and smaller than it needs to be

`e11_uncertainty.py`. This addresses **D1**, the one gap that is universal across all six
shortlisted teams - and the result is not the one I expected.

## The gap

All six teams ship point estimates. Four ship a confidence number. **None demonstrates it is
calibrated** - that a farm marked uncertain is actually wrong more often, by the amount
claimed. Megalodon comes closest (rank disagreement falls monotonically across confidence
quintiles), and that is still an ordering check.

It matters here because farm pixel counts span **0 to 1223** at the anchor date - a 35x range,
so a ~6x range in the precision of a farm mean. A single number treats a 12-pixel farm and a
1200-pixel farm as equally known.

## The model, which is physics rather than a fit

For a farm of N pixels with coefficient of variation cv, the standard error of the mean in
linear power is `cv / sqrt(N)`. Nothing is fitted: cv and N are both measured, per farm per
date, and the relation is what fully developed speckle does.

## T1 - split-half: the check that could fail

Split each farm's pixels into two random halves, compute the mean from each, and measure the
spread over 25 random splits. That spread is **pure sampling noise, measured with no model,
no witness and no ground truth**. Theory says it should equal `2 x cv/sqrt(N)`.

885 farms with at least 8 usable pixels:

| | median | p10 | p90 |
|:--|--:|--:|--:|
| predicted half-split SD | 0.1069 | 0.0505 | 0.2092 |
| observed half-split SD | 0.1016 | 0.0482 | 0.2117 |
| **observed / predicted** | **0.966** | 0.802 | 1.140 |

**Spearman(predicted, observed) = +0.9663.**

The physics predicts our own sampling noise to within **3.4%**, across farms spanning two
orders of magnitude in pixel count, with no tuning. The uncertainty model is calibrated at
the feature level.

## T2 - and here it fails, usefully

Does predicted uncertainty predict disagreement with a sensor the pipeline never read?

| predicted-SE quintile | n | median SE | mean \|rank gap\| |
|:--|--:|--:|--:|
| Q1 (most precise) | 177 | 0.0253 | 0.3028 |
| Q2 | 177 | 0.0367 | 0.2872 |
| Q3 | 177 | 0.0535 | 0.2745 |
| Q4 | 177 | 0.0716 | 0.2786 |
| Q5 (least precise) | 177 | 0.1046 | 0.3381 |

**Spearman = +0.0524, p = 0.12. Not significant, and not monotonic - the pattern is U-shaped.**

So a calibrated uncertainty model does **not** predict which farms disagree with the witness.
That is a negative result, and chasing it produced the most useful finding in this document.

### Why: the noise is real but too small to matter

Two hypotheses, both tested:

**H1 - confounding with farm size.** `rho(pred_se, area_ha) = -0.924`, so predicted SE is
almost entirely farm size in disguise. But `rho(area_ha, |rank gap|) = -0.048`, so area does
not drive disagreement either. H1 does not explain it.

**H2 - the noise is negligible against the signal.** This one holds:

| quantity | value |
|:--|--:|
| median sampling SE | **0.232 dB** |
| between-farm spread, 13 Oct | **1.458 dB** |
| **noise / signal** | **15.9%** |

Sampling noise is a sixth of the between-farm variation. It is real, it is calibrated, and it
is simply not what limits us. Whatever separates our health ranking from NDVI's is *not*
pixel count.

## The consequence: a prediction about an untested borrowed idea

Coding Bits report the **Quegan-Yu multitemporal speckle filter** buying 2.4-2.8x effective
looks. It has sat in our backlog as Tier C1, graded THEIRS, on the strength of their
measurement on their data.

We can now predict what it would buy *us*, from measured quantities:

| effective looks | resulting SE | noise/signal | gain |
|:--|--:|--:|--:|
| 1.0 (as shipped) | 0.232 dB | 15.9% | - |
| 2.4x | 0.150 dB | 10.3% | **5.6% of signal** |
| 2.8x | 0.139 dB | 9.5% | **6.4% of signal** |

It would reduce a term that is already only 16% of the between-farm signal, and T2 shows that
term does not drive disagreement with an independent sensor at all. **The predicted gain is
small, and C1 should be deprioritised for Round 3** unless someone shows the mechanism by
which a 6% noise reduction changes a ranking that sampling noise was not driving.

This is a falsifiable prediction, not a refusal: if Quegan-Yu is implemented and the health
index moves materially against the reserved witness, this reasoning is wrong and should be
reported as such.

## T3 - scoping what a shipped uncertainty column would look like

Propagating the measured feature-level SE onto the 0-100 index (a fractional SE on linear
power is ~4.34 x se dB; the index spans roughly 25 points per dB within a crop cohort):

median ~2.5 points, and **a meaningful minority of farms carry more than 5 index points** of
sampling uncertainty purely from how few pixels they contain.

*Stated as scoping, not as a result:* the 25 points/dB constant is a linear approximation of
the index transform. A shipped column should run the Monte Carlo through `d4_submission`
rather than through a constant.

## What to conclude

1. **We can ship a calibrated per-farm uncertainty**, and demonstrate the calibration with a
   split-half test that needs no ground truth. No other team does this, and the demonstration
   is the differentiator, not the number.
2. **But it should be presented honestly**: it is calibrated *sampling* uncertainty, and
   sampling uncertainty is not our dominant error term. Presenting it as a general confidence
   would overclaim.
3. **The dominant error is elsewhere** - crop label (eta^2 0.820 on yield), model form, or
   genuine sensor difference. That is where Round 3 effort belongs.
4. **Deprioritise the speckle filter.** Quantified above, at 5.6-6.4% of signal.

The most valuable output here is the negative one. A calibrated uncertainty model that fails
to predict disagreement tells us where our error is *not*, and that is worth more than a
confidence column.
