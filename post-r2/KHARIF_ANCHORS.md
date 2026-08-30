# The yield anchors, rebuilt from kharif-only multi-year district statistics

`e10_kharif_anchors.py`. This closes item **A5**, the only finding in the whole post-R2 pass
that should move a shipped column.

## The defect, restated

Our anchors come from `data_aux/vadodara_apy.csv` - a single **annual** district figure for
2022-23. The deliverable observes 6 June to 13 October 2025, which is **kharif**. §10.2
argued from agronomy that an all-season mean answers a different question, because Gujarat
grows bajra twice and the summer crop is irrigated.

That was a mechanism argument. It is now a measurement.

## The new dataset

**data.gov.in resource `35be999b-0208-4354-b557-f6ca9a5355de`** - *"District-wise,
season-wise crop production statistics from 1997"*, 246,091 records, fields
`State_Name / District_Name / Crop_Year / Season / Crop / Area / Production`.

461 Vadodara records, 1997-2012, with **Kharif, Rabi, Summer and Whole Year as separate
rows**. The e9 census confirmed no competitor used it. It is the only source found that
splits kharif from the annual figure at district level, which is exactly the axis our defect
lies on.

*(Cached at `post-r2/results/e10_kharif_anchors/vadodara_season_crops.csv`. The API is
paged; a 1000-row request times out, 250 works.)*

## The mechanism, measured

| Vadodara bajra | t/ha, 16-year median | area |
|:--|--:|--:|
| **kharif** | **1.22** | 129,800 ha |
| **summer** | **1.96** | 81,900 ha |
| ratio | **1.60x** | summer is 39% of bajra area |

Summer bajra yields 1.6x kharif bajra and occupies nearly two-fifths of the area, so an
all-season mean is pulled materially above the kharif figure. Predicted in §10.2 from
agronomy; confirmed here on 16 years of district data.

**And the defect is narrower than expected.** The kharif-to-all-season ratio, per crop:

| crop | kharif / all-season | has a second season in Vadodara? |
|:--|--:|:--|
| Rice | **1.000** | no |
| Maize | **1.000** | negligible |
| **Bajra** | **0.818** | **yes - summer, 82k ha** |
| **Groundnut** | **0.795** | **yes - summer, 16 yr** |

Rice and maize have no material second season here, so their anchors were already
effectively kharif and need no correction. The seasonal defect touches **exactly bajra and
groundnut** - the same two crops with thin district bases (7,022 and 1,004 ha), and the same
two `data_aux/SOURCES.md` already carries a RETRACTED area claim about. Three independent
lines land on the same pair.

## Three estimators, so no single source is load-bearing

The dataset ends in 2012 and our anchor is 2022-23, so levels are not directly comparable.
Three independent estimates of the 2022-23 kharif anchor:

- **A** our own 2022-23 annual level x the measured seasonal ratio from this dataset
- **B** this dataset's own kharif series, linearly extrapolated to 2022 *(a decade past the
  data - deliberately the weakest, included because a third estimator that disagrees is more
  informative than two that agree)*
- **C** the median of three competitors' independently sourced kharif figures

| crop | A | B | C | median | spread (cv) | **ours** | error |
|:--|--:|--:|--:|--:|--:|--:|--:|
| Rice | 1.69 | 1.82 | 2.00 | 1.82 | 7% | 1.69 | -7% |
| Maize | 2.31 | 2.26 | 2.57 | 2.31 | 6% | 2.31 | **+0%** |
| **Bajra** | 2.22 | 1.91 | 1.79 | **1.91** | **10%** | **2.71** | **+42%** |
| Groundnut | 2.00 | 1.62 | 2.73 | 2.00 | **23%** | 2.51 | +26% |

Rice and maize: three estimators agree to within 7%, and our anchors sit inside that. **Our
anchor table is not wholesale wrong** - it is wrong for one crop, and possibly a second.

## Can a dataset that ends in 2012 say anything about kharif 2025?

The obvious objection, and it deserves a tested answer rather than an assurance.

**What is actually taken from it.** Estimator A uses our own 2022-23 *level* and only the
*ratio* from this dataset. A ratio is far more time-stable than a level, because seeds,
inputs and irrigation lift kharif and summer yields together and largely cancel. That is the
argument. Below it is tested four ways.

### Test 1 - is the ratio stable inside the window?

| crop | ratio 97-04 | ratio 05-12 | slope/yr | p | verdict |
|:--|--:|--:|--:|--:|:--|
| **Bajra** | 0.827 | 0.813 | +0.0014 | 0.861 | **flat** |
| Groundnut | 0.694 | 0.854 | +0.0083 | 0.677 | halves differ by 0.16 - **noisy, not flat** |
| Rice | 1.000 | 1.000 | 0.0000 | 1.000 | constant |
| Maize | 1.000 | 1.000 | -0.0040 | 0.010 | see below |

**A correction to my own reading.** Maize's p = 0.010 initially read as "drifts - unsafe". It
is a false alarm: the series never leaves 0.90-1.00 and is 1.000 for twelve of fifteen years.
A significant slope on an essentially constant series is a significance test on numerical
noise, and the effect size is nil. Maize needs no correction; the flag was mine, not the
data's.

Groundnut's p = 0.677 does **not** mean stable - it means too noisy to detect drift, while
the two halves differ by 0.16. High p-values are not evidence of stability.

### Test 2 - is the second season growing? (which way any residual error points)

| crop | summer area share 97-04 | 05-12 | slope/yr | p |
|:--|--:|--:|--:|--:|
| Bajra | 0.278 | 0.369 | +0.0112 | 0.122 |
| Groundnut | 0.779 | **0.923** | +0.0196 | **0.023** |

Bajra's summer share is rising but not significantly. If it has kept rising to 2025, the
modern annual figure is *more* inflated than in 2012, so our ratio correction is
**conservative** - it under-corrects rather than over-corrects. That is the safe direction.

Groundnut's summer share is 78-92% and significantly growing: in Vadodara, groundnut is
mostly a *summer* crop. That is a substantive finding beyond the anchor, and it bears on
Orion's separate claim about groundnut in central Gujarat (`DELIVERABLE_MINING.md` §3).

### Test 3 - the decisive one: carry the ratio forward out of sample

Fit the ratio on **1997-2004 only**, then use it to predict 2005-2012 kharif yield from the
same years' all-season yield. That is exactly the operation we perform for 2022, run where
the answer is known.

| crop | ratio (97-04) | predicted error | naive error | better? |
|:--|--:|--:|--:|:--|
| **Bajra** | 0.827 | **7.9%** | 23.1% | **yes - 3x** |
| Groundnut | 0.694 | **34.3%** | 27.4% | **no - worse than doing nothing** |
| Rice | 1.000 | 0.0% | 0.0% | no-op |

*"Naive" is using the all-season figure directly - what we currently ship.*

This independently confirms the split decision reached below on other grounds. Bajra's ratio
survives being carried across an eight-year gap with a threefold accuracy gain. Groundnut's
**makes the estimate worse**, so the groundnut correction is not merely unsupported - it is
measurably harmful, and would have been adopted by anyone reasoning from the mechanism alone.

### Test 4 - do the two sources describe the same district?

Vadodara kharif area, this source versus our independent 2022-23 APY row:

| crop | 1997 | 2012 | slope/yr | p | extrapolated 2022 | **our 2022-23 APY** |
|:--|--:|--:|--:|--:|--:|--:|
| Bajra | 12,100 | 8,400 | -191 | 0.044 | ~6,490 | **7,022** |
| Rice | 53,500 | 44,600 | -95 | 0.776 | ~43,650 | **49,818** |
| Maize | 46,600 | 44,100 | -434 | 0.040 | ~39,760 | **40,794** |
| Groundnut | 2,700 | 200 | -63 | 0.081 | ~0 | 1,004 |

Bajra and maize land within 8% and 3% of a source that shares no lineage with this one, over
a decade of extrapolation. The two datasets are measuring the same district on the same
scale, which is the consistency check that licenses the ratio to travel.

Groundnut again fails: its area collapses to near zero here while our APY row reports
1,004 ha. A ~1,000 ha base is why every groundnut estimate in this document is noisy, and why
its cross-validation could not work.

### Answer

The dataset's **levels** are unusable for 2025 and are not used. Its **ratios** are usable for
bajra - flat inside the window, validated out of sample at 3x the accuracy of doing nothing,
and drawn from a district that two independent sources agree on. They are **not** usable for
groundnut, which the same tests reject. Rice and maize need nothing.

One dataset, four tests, three different answers per crop. That is the level of scrutiny any
external source should get before it touches a shipped number.

## What to adopt, and what not to

Testing the correction rather than assuming it - the same discipline applied to a competitor
idea now applied to our own proposed fix:

| option | village t | vs Megalodon | bajra median | groundnut median |
|:--|--:|--:|--:|--:|
| shipped | 594.9 | +3% | 2.57 | 1.86 |
| **bajra only** | **561.4** | **-3%** | **1.81** | 1.86 |
| bajra + groundnut | 507.0 | -12% | 1.81 | **1.48** |
| all four | 512.9 | -11% | 1.81 | 1.48 |

Peer per-crop medians: bajra **1.79 / 1.88 / 1.30**, groundnut **1.84 / 2.72 / 2.43**.

- **Adopt the bajra correction.** 2.714 -> 1.91 t/ha. Three estimators agree to 10%, our
  error is +42%, and the corrected median of 1.81 t/ha lands inside the peer range. The
  village total moves 594.9 -> 561.4 t, from +3% to -3% against the team we already agree
  with most closely.
- **Do not adopt the groundnut correction.** Three independent reasons, and the last is
  decisive: the estimators disagree at 23% cv; applying it puts our groundnut median at
  1.48 t/ha, **below all three peers**; and the temporal cross-validation shows the ratio
  makes the estimate **worse than doing nothing** (34.3% vs 27.4%). The seasonal mechanism is
  real for groundnut - it is 78-92% a summer crop here - but a mechanism being real does not
  make a correction derived from it accurate. Report the ratio, flag the exposure, leave the
  number.
- **Leave rice and maize alone.** Measured error 0% and -7%, inside estimator spread.

**Rank safety.** An anchor is a per-crop multiplicative constant, so a positive scalar cannot
reorder farms within a crop. Spearman between the shipped and corrected yield columns is
0.9613, and every within-crop ordering - and the entire health index - is untouched. This
corrects a level, which is the only thing an anchor sets.

**What it does not fix.** REPORT §7.2's finding that bajra's season-integral term contradicts
the witness (rho -0.219) is about the ordering *inside* the crop and is unaffected by any
anchor change. Two separate bajra defects; this addresses one, and the other remains open and
reported.

## Status

Measured, not applied. Round 2 stays frozen. This is the change to make first if Round 3
permits a resubmission, and the finding to present if it does not.


---

# Cotton, added 2026-08-29 (`e15_cotton_anchor.py`)

Cotton was absent from this document while being **455 of 966 farms and 43.2% of village
area** -- the largest unexamined assumption in the yield column. Tested now. **The anchor is
NOT changed.** What follows is why, because the reasoning is the deliverable here.

## What is proven: `vadodara_apy.csv` mixes two unit systems in one column

production / area against the stated yield column, per crop:

| crop | area ha | production | yield kg/ha | implied | ratio |
|:--|--:|--:|--:|--:|--:|
| Rice | 49,818 | 91,300 | 1,690 | 1,833 | 1.08 |
| Maize | 40,794 | 91,000 | 2,312 | 2,231 | 0.96 |
| Bajra | 7,022 | 17,400 | 2,714 | 2,478 | 0.91 |
| Groundnut | 1,004 | 2,500 | 2,514 | 2,490 | 0.99 |
| **Cotton** | 185,479 | 829,400 | 776 | 4,472 | **5.76** |

Read cotton's production as **bales of 170 kg** rather than tonnes and it reconciles:
829,400 x 170 / 185,479 = **760 kg/ha against a stated 776, ratio 0.98**.

**Established: the cotton row is bales-of-lint; the other four are tonnes of grain or pod.**
Seed cotton (kapas) equivalent at a 34% ginning outturn is **2,282 kg/ha = 2.28 t/ha**, i.e.
2.9x what we ship. `SOURCES.md` already flagged cotton as lint in prose; nothing in code acted
on it, and `d4_submission.py:431` applies `district_yield[c]` uniformly across all five crops.

## What was tested and what each test decided

**T2 -- cotton's low ratio is not the bug.** Our yield reproduces the anchor at 0.95 (bajra),
0.94 (maize), 0.97 (rice) but **0.44** for cotton. That is the *completion* term and it is
correct: cotton is long-duration and still standing on 13 October, so a "to date" figure
should sit well under the full-season anchor. The unit question is only about the 776 itself.

**T3 -- the host dummy, DISCARDED by its own control.** Our cotton (max 0.605) does not
overlap the host's cotton range (min 1.51), which looks damning. But **maize and rice do not
overlap either** -- and they are anchored to the real district figure and are not in dispute.
A test that condemns two crops known to be fine is not an oracle. The host's
`Sokhda_Dummy_Submission.xlsx` is generated data, not calibrated to Vadodara for any crop.

*Recorded deliberately:* stopping at T3 would have "confirmed" the hypothesis with a test that
fails its own control. This is the same failure mode as e13's Dynamic World screen.

**T4 -- the field is split, so there is nothing to borrow.**

| team | cotton median t/ha | convention |
|:--|--:|:--|
| coding_bits | 2.430 | seed cotton (kapas) |
| project_orion | 1.124 | lint |
| megalodon | 0.660 | lint |
| deep_thinkers | 0.470 | lint |
| **ours** | **0.344** | **lint** |
| 8_bits | 48.350 | a different unit entirely, not t/ha |

Four of five t/ha teams are on the lint scale. Competitor agreement is not available as
evidence -- the same conclusion e4 reached on crop labels.

**T5 -- cross-crop ordering, and it points the other way.** Spearman of the host's per-crop
ordering against the APY table is **-0.300 as lint and -0.500 as kapas** (p = 0.62, 0.39).
Neither is significant on five points, but the conversion makes the fit *worse*, not better.

**External statistics all use lint.** Gujarat cotton yield is published at 647 kg/ha
(2022/23) and 574 kg/ha (2023/24), India 475 kg/ha -- USDA FAS, CEIC and the APY series alike.
Our 776 for a good district is in exactly that family. A published source states the figure as
"776 kg lint/ha" verbatim.

**T6 -- the size of the decision.** Village production as shipped is **594.9 t**, of which
cotton is 76.6 t (12.9%). Restating cotton as seed cotton gives **743.6 t, +25.0%** on the
headline number.

## Verdict

**Keep the lint anchor. Do not restate cotton.** Every official statistical source uses lint,
the only test that favoured kapas failed its own control, the ordering test mildly opposes it,
and a +25% move on the village headline needs evidence that decides. It does not exist.

**But ship the unit statement.** The deliverable must say, in the yield section, that cotton
is **lint** while the other four crops are grain or pod, and give the x2.94 kapas conversion.
A single column carrying two unit systems is a defect even when the number is defensible, and
a judge who does not know this will read 0.34 against bajra's 2.57 as an error.

**And guard it.** `post-r2/tests_regression.py::test_apy_units_are_homogeneous` now asserts
the inhomogeneity is still present and still explained by the bales reading. If the source is
ever corrected upstream, that assertion fires and e15 gets re-run rather than silently
inheriting a 2.9x shift.
