# Gap Analysis → Best-Available Fixes

For each defect found in the implementation review, the strongest alternative I could find, with the
evidence that justifies it and a concrete implementation. Ordered by rubric impact per hour of work.

Research trail for this document = `RESEARCH_LOG_T_U.md` Phase T (technical) and Phase U (validation).
Written 2026-08-06.

---

## Summary table

| # | Gap | Best fix | Effort | Rubric |
|---|---|---|---|---|
| G | Growth term crosses a 6.55° geometry change | **Use the geometry-matched pair with village-median centering** | 30 min | Soundness |
| A | Rice "specular in August" contradicts own data | **Early-season stem–water double bounce** (published, matches data) | 1 h | Soundness |
| D | Yield ≡ health (Spearman 1.000) | **Per-farm measured season completion + season integral** | 2 h | Creativity, Validity |
| E | Health is a percentile → uniform by construction | **Bounded z-transform (Φ(z)) instead of rank** | 1 h | Aggregation, Validity |
| H | Texture inert; CV carries speckle + area bias | **ENL-corrected coefficient of variation** | 1 h | Soundness |
| B | "6.8× rice enrichment" is circular | **Leave-channel-out re-run** | 30 min | Validity |
| C | Writeup ≠ code on imputation | **Implement spatial kNN, or fix sentence** | 45 min | Docs |
| F | Offset quoted as +28 dB, actually ~+17 dB | Correct the number, anchor to S1 | 10 min | Soundness |

---

## G. The growth term — the single most valuable fix

**The problem.** `d_aug_jun06` spans 35.24° → 28.69°, the widest geometry gap in the dataset. The
geometry-matched pair (Jun19×Aug14, 0.076° apart, `[G4]`'s "cleanest temporal measurement") was rejected
because Jun 19 sits ~7.9 dB above Jun 06 on wet, monsoon-onset soil `[J5]`.

**The insight that dissolves it.** *The rejection reason applies to the absolute level, not to the
between-farm ranking.* Every use the pipeline makes of the growth term is a **between-farm contrast**
(`z()` across farms, then ranked within crop). A village-wide wet-soil brightening on Jun 19 is a
**common-mode offset** — it shifts all 966 farms together and **cancels identically in the z-score**.

So the correct move is not to abandon the geometry-matched pair. It is:

```python
# growth on the geometry-matched pair (Δθ = 0.076°), village-median centred
raw = f["g0_db_20250814"] - f["g0_db_20250619"]
growth = raw - np.nanmedian(raw)      # removes the common-mode wet-soil offset [J5]
```

This is the same operation `z()` already performs implicitly, made explicit and justified — and it buys a
**6.47° reduction in uncalibrated angular dependence** on the index's most influential family (ρ +0.557
with health, higher than any other).

**The one caveat, stated.** Rice's Jun-19 double-bounce peak (§A) *is* a genuine between-farm signal on
that date, so it would partly leak into "growth". Two mitigations, both cheap: growth is already ranked
**within crop** downstream, which absorbs a crop-constant offset; and the flood channel can be regressed
out of growth explicitly if you want it clean.

**Also fix the claim.** The writeup says γ⁰ *"normalise[s] the 28.7°–35.2° incidence spread"*. γ⁰ reduces
angular dependence; it does not remove it, and no residual normalisation was applied (the cosine-N fit was
rejected at N = 6.81). Change to: *"γ⁰ reduces but does not eliminate the angular dependence; we therefore
build the growth term on the one date pair matched to 0.076°."* That sentence is both more honest **and**
more impressive.

---

## A. The rice mechanism — the literature backs the code, not the writeup

**Evidence found (T1).** For paddy rice at co-pol X-band:

> Co-polarised backscatter at the **beginning of the growing season is dominated by double-bounce
> scattering from the stem–water interaction at X-band**. The first backscatter increase relates to
> increasing double bounce from the surface–stem interaction, **occurring up to 46 days after
> transplanting**. Short wavelengths (K, X) show **high dynamic range early in the season with an early
> peak**, then decline as volume scattering and canopy attenuation take over. For inundated vegetation,
> **HH is preferred over VV** and gives more accurate results.

**Why this settles it.** Gujarat kharif paddy is transplanted from about mid-to-late June. **19 June falls
squarely inside the ≤46-day double-bounce window.** So:

| date | mechanism | prediction | measured |
|---|---|---|--:|
| 19 Jun | stem–water double bounce in bunded, puddled paddy, HH-favoured | rice **brightest** | **10.64 dB** vs ~8 for all others ✓ |
| 14 Aug | canopy closed; volume scattering + two-way attenuation kill the double-bounce path | rice **declines**, mid-pack | 6.92 dB, 3rd of 5 ✓ |
| 13 Oct | harvested/drained | recovers to bare-soil level | ✓ |

The prediction matches on **every date**. The current writeup's "specular reflection scatters away from the
sensor, so rice is darkest on 14 Aug" is wrong twice over: rice is **not** darkest on 14 Aug (Bajra 6.37 and
Groundnut 6.58 are both lower), and specular loss belongs to *open water before transplanting*, not to a
closed canopy in mid-August.

**The code was right all along.** `d4_submission.py:107` already says *"double-bounce off water and bunds"*
and weights `flood = Jun19 − Jun06` at 2.2. Only the prose and the figure annotation are wrong.

**Fix:** rewrite the rice paragraph around early-season double bounce with the ≤46-day window as the
physical time constant; move the `gallery_1` annotation from the 14 Aug point to the **19 Jun spike**; cite
the TerraSAR-X rice literature. This upgrades the rice channel from a heuristic that happens to work into a
mechanism with a published time constant that predicts the observed shape on all four dates.

---

## D. Yield — give it a genuinely independent axis

**The problem.** Within every crop, Spearman(health, yield) = **1.000**. Both crop terms are constants, so
the yield column is health re-scaled. Two deliverables, one number.

**Evidence found (T3).** The established SAR-yield approaches are: fit a curve to the time series and use
its **parameters** as growth descriptors; **accumulate the growth curve over the season** and combine
accumulated with current values; compare **nearby fields of the same crop** to remove soil and
agro-climatic bias.

**Fix — make both remaining terms measured, not constant:**

```
yield_to_date[farm] = anchor[crop]                      # district APY, unchanged (sets the level)
                    × completion[farm]                  # ← now PER-FARM and MEASURED
                    × accumulation[farm]                # ← season integral, not the health composite
```

1. **`completion[farm]` from measured senescence.** The question is literally *"how far through its cycle
   is this field on 13 Oct?"* — and `d_oct_aug` measures exactly that: a farm that has senesced or been
   harvested by October has brightened toward bare soil (the village median is **+2.38 dB**), while one
   still carrying canopy has not. Map `d_oct_aug` within crop onto a band centred on the crop's nominal
   completion (Cotton 0.45, Groundnut 0.75, others 0.95), e.g. ±0.15. Now a late-sown cotton plot still in
   full canopy correctly reads *less* complete than its harvested neighbour.
2. **`accumulation[farm]` from the season integral** rather than the health composite — this is the
   published "accumulate the growth curve" method, and `season_integral` is already computed.

**Result:** yield stops being a monotone image of health (they will correlate, as they should, but not at
1.000), the "to date" framing becomes a *measurement* rather than a per-crop constant, and it directly
implements a citable method. This is the highest creativity-per-hour item on the list.

**Minimum viable version if time is short:** one disclosure sentence — *"within a crop, yield is a
monotone transform of health; the crop-level terms carry all independent information."* Stating it costs
nothing; being caught not stating it costs credibility.

---

## E. Health index — keep the ranking, recover the magnitude

**The problem.** `rank(pct=True)` forces every crop to mean 50, min ~0, max 100. Consequences: no absolute
health information exists; the village aggregate is 50.267 **by construction**, which makes the rubric's
village-level summary vacuous; and the diverging red↔green cover map renders half the village red, which
reads as a failure claim the data does not support.

**Fix — replace the rank with a bounded transform of the same z-score:**

```python
from scipy.stats import norm
S_c = (S[m] - np.nanmedian(S[m])) / (1.4826*np.nanmedian(np.abs(S[m]-np.nanmedian(S[m]))))
out[m] = 100.0 * norm.cdf(S_c)          # monotone in S, but NOT forced uniform
```

Identical ordering (so every ablation, Moran's I and witness correlation is unchanged), but the
**distribution can now move**: a uniformly poor crop lands low instead of being stretched to fill 0–100.
Keep the percentile as a debug column.

To make it genuinely absolute, centre `S_c` on the crop's **expected** trajectory rather than the observed
village median — then "50" means "as expected for this crop", not "median of this village".

**Also:** recolour the health map on a sequential ramp (or caption the diverging one explicitly as a
within-crop rank), and re-do the village-level table so it carries information.

---

## H. Uniformity and texture — fix the speckle, and two problems disappear

**The problem.** Texture contributes nothing (ρ(health, `glcm_resid`) = **−0.024** at 0.10 weight, sign
inverted from intent); `level` and `persist` correlate at **0.742**, so 0.45 of the weight sits on one
axis; and health carries an area bias (ρ 0.086) that the writeup attributes to "more pixels, less speckle".

**That attribution is the clue, and it is fixable.** Observed CV over a finite sample of speckled SAR
contains a pure speckle term set by the equivalent number of looks:

```
CV²_observed ≈ CV²_true + 1/ENL
⇒  CV_true = sqrt(max(CV²_obs − 1/ENL, 0))
```

They **measured** ENL ≈ 2.1 (fine) / 3.5 (base) `[G6]`. At ENL 3.5 the speckle floor is CV ≈ 0.53 — against
a median observed `cv_20250814` of **0.488**, i.e. *the observed within-field CV is at or below the pure
speckle floor.* The uniformity family is currently measuring speckle, not canopy. And because effective
looks scale with plot pixel count, the speckle term is **larger for small plots** — which is precisely the
area bias, arriving through the front door.

**Fix:** compute ENL-corrected CV per farm using the per-farm pixel count, and use that as the uniformity
feature. Expected outcomes, all good: uniformity becomes a real canopy measure; the area bias shrinks
toward zero; and the rubric's own "uniform canopy scores higher" test (§7 of the writeup, currently a
documented failure at ρ −0.049 on the independent October date) gets a fair second chance.

This is the most likely single change to convert a documented failure into a documented pass.

For texture: either drop it and redistribute the 0.10, or keep it and state plainly that it contributes
nothing measurable. Add one line noting the level/persist collinearity when reporting the ablation — the
"worst family drop ρ ≥ 0.879" result is partly measuring redundancy rather than robustness.

---

## B. Replace the circular check with a real one

**The problem.** `flood_hit` carries weight 2.2 in `e["Rice"]` — the largest weight in the evidence
function — so "64% of flood-detected farms are labelled Rice" is a tautology.

**Fix — leave-channel-out.** Re-run `assign_crop` with the flood terms zeroed, then ask whether the
flood-detected farms *still* come back Rice on the strength of the remaining evidence alone. If they do,
that is genuine corroboration and a much stronger claim than the current one. If they don't, you have
learned that rice rests entirely on one channel — also worth knowing, and honest to report.

**Second, independent test:** rice fields are hydrologically distinctive. Test the rice labels against a
wetness proxy that never enters the model — Sentinel-1 C-band VV in July, or S2 NDWI in August. Different
sensor, different physics, zero circularity.

---

## C. Imputation — implement the better method

The writeup promises spatial imputation from *"adjacent covered farms"*; the code does a village-wide
crop median. Since missingness is spatially clustered along the NW swath edge, the promised method is
genuinely the right one:

```python
# same crop, nearest k covered neighbours by centroid distance
from scipy.spatial import cKDTree
tree = cKDTree(cent[~bad & (crop == c)])
_, idx = tree.query(cent[bad & (crop == c)], k=min(5, n_ok))
hi[bad & (crop == c)] = np.nanmedian(hi_ok[idx], axis=1)
```

Add a sensitivity line: how do the village aggregates change if the 52 imputed farms are dropped entirely?
If the answer is "barely", say so — it retires the concern permanently.

---

## F. The offset number

Change **+28 dB → ~+17 dB**, and anchor it to the measurement rather than a textbook range:

> Our X-HH γ⁰ over the farms reads **+9.6 dB** on 13 Oct; Sentinel-1 RTC C-VH over the same farms three
> days earlier reads **−14.7 dB**. Co-polarised backscatter typically sits 5–8 dB above cross-polarised,
> so the expected X-HH value is ≈ −8 dB and the offset is ≈ **+17 dB**.

The +28 dB figure came from `[J5]`, which measured **Round 1's** offsets — and Round 1 carried the `scale²`
bug, worth −28.6 dB on the October scene. It does not describe this pipeline.

**Free positive result to add alongside it:** between-farm dB spread on 13 Oct is **1.48 dB (ours) vs
1.82 dB (S1 RTC)** on the same farms. Comparable spread is direct evidence that the contrasts survive the
offset — turning "we assume a constant offset cancels" into "we measured that it does".

---

## Suggested order of work

Half a day gets the first six:

1. **G** growth pair (30 min) — biggest soundness gain, smallest diff
2. **F** offset number + spread evidence (10 min)
3. **A** rice mechanism, prose + figure (1 h)
4. **B** leave-channel-out (30 min)
5. **C** spatial imputation (45 min)
6. **E** bounded z-transform + recolour (1 h)
7. **H** ENL-corrected CV (1 h) — may convert a failure into a pass
8. **D** yield independence (2 h) — highest creativity gain

Every one of these is additive to the existing structure. None requires reprocessing the SLCs.
