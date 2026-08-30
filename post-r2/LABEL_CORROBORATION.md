# What two independent sensors say about our crop map

`e17_dense_s1.py`. This closes **D-1**, and the answer is not the one D-1 predicted.

## D-1 was wrong on both of its premises

**Premise 1: "there is no dense temporal series anywhere in the pipeline." False.**
`src/witness_season.py` already fetched **ten Sentinel-1 RTC scenes, 12 Jun to 10 Oct 2025**,
every one on relative orbit 34 descending, per farm, sitting in
`results/tables/witness_season.csv`. Capella gives four dates; this gives ten over the same
season. Nothing needed fetching, and the "largest available gain" was already on disk.

**Premise 2: the cost is "a spent witness." Understated.** `docs/REPORT.md:16` states that
Capella primacy is required *by the guidelines*, not merely preferred by us. Training the crop
label on C-band would make C-band the primary source of the headline output — potentially
disqualifying, not merely awkward. D-1 as written proposed spending something we may not own.

So the question was re-posed to cost nothing: using the witness **as a witness**, does the
dense series corroborate the labels the annual embedding could not?

## T1 — it does not. D-1's kill criterion fires.

Same 956 farms, same spatially blocked 5-fold CV, same protocol as e14.

| crop | n | dense S1 | e14 annual embedding | change |
|:--|--:|--:|--:|--:|
| Cotton | 449 | **88.2%** | 84.9% | +3.3pp |
| Groundnut | 220 | 29.1% | 28.6% | +0.5pp |
| Maize | 54 | 7.4% | 0.0% | +7.4pp |
| Rice | 86 | **3.5%** | 4.7% | −1.2pp |
| Bajra | 147 | **1.4%** | 10.9% | **−9.5pp** |

Pooled **kappa +0.135 — lower than the annual embedding's +0.155.** Ten dates of dedicated
C-band, spanning exactly our season, are *worse overall* than one annual multi-sensor average.

D-1's stated kill criterion was "blocked-CV kappa on the four non-cotton crops no better than
e14's." **It is not better. D-1 closes.**

Controls all pass, so this is a real measurement and not a broken test: 10.5 permutation SDs
above null, area-only floor kappa +0.017, and `rho(area, correct) = +0.064, p = 0.048` — weak
and marginal, nothing like the confound that killed Dynamic World in e13.

## T2 — the mechanism D-1 named was right; it just isn't enough

| feature set | kappa |
|:--|--:|
| 10 dates + 9 deltas (full phenology) | **+0.135** |
| 10 dates, no deltas | +0.142 |
| last 3 dates only (Sep–Oct) | +0.134 |
| season mean + integral only (**timing removed**) | **+0.046** |
| first 3 dates only (Jun–Jul) | +0.024 |

**Timing is worth +0.089 kappa** — flattening the series to a mean and an integral destroys
two-thirds of what it knows. So D-1's *reasoning* was sound: annual averaging really does
throw away most of the crop signal.

But it is not sufficient. Even with the full season shape preserved, rice sits at 3.5%, bajra
at 1.4% and maize at 7.4%. **The information about those three crops is not in C-band VH at
this revisit, in any arrangement.** A correct mechanism does not rescue a false conclusion.

Note also that almost everything lives in the **late** dates (Sep–Oct alone: +0.134; Jun–Jul
alone: +0.024). Discrimination here is a harvest-timing signal, not an emergence signal.

## T5 — but "C-band is blind to rice" is *not* established

Our rice channel is the Capella 6 → 19 June brightening (+3.23 dB for rice against +0.07 to
+1.12 for every other crop), driven by 17.3 mm of rain in the six hours before the 19 June
overpass (e12, verified from Open-Meteo). **Sentinel-1 flew 12 June and 24 June — it straddles
that event without ever sampling it.**

On the closest available pair, 12 → 24 June:

| crop | n | Δ dB |
|:--|--:|--:|
| **Rice** | 86 | **+2.184** |
| Groundnut | 220 | +2.059 |
| Bajra | 147 | +1.940 |
| Cotton | 449 | +1.788 |
| Maize | 54 | +1.787 |

Rice brightens **most**, the same direction as our Capella channel — but by +0.30 dB against
our +3.23 dB, at p = 0.070. Suggestive, not significant.

**So the honest statement is narrow:** a 12-day C-band VH series does not separate rice here,
which is exactly what you would expect of a days-scale flooding event falling between two
acquisitions. That is a point *in favour* of our X-band channel, not against it — and it is
the kind of claim that would have been overstated in either direction without the test.

## T4 — the finding that actually matters

Cross-tabulating our labels against **both** independent sensors:

| | farms | % of village |
|:--|--:|--:|
| both sensors agree with us | 383 | 40.1% |
| dense S1 only | 86 | 9.0% |
| embedding only | 81 | 8.5% |
| **neither agrees with us** | **406** | **42.5%** |

Both-agree is 40.1% against 23.8% expected if the sensors were independent — they are
correlated in what they can see, and what they can see is cotton.

Per crop:

| crop | both agree | **neither** |
|:--|--:|--:|
| Cotton | 78.8% | **5.8%** |
| Groundnut | 13.2% | 55.5% |
| Bajra | 0.0% | **87.8%** |
| Rice | 0.0% | **91.9%** |
| Maize | 0.0% | **92.6%** |

**Not one rice, maize or bajra farm — 287 farms, 30% of the village — is corroborated by both
independent sensors. Cotton is corroborated on 78.8%.**

Stated plainly: *as far as any independent sensor can tell, our crop map is cotton plus
noise.* That is consistent with everything measured since Round 2 ended — six-team kappa
0.060, e14's per-crop split, and yield's eta² of 0.820 on the label — and it is the strongest
form of the bottleneck finding yet, because it now has two independent sensors behind it
rather than a competitor consensus that e4 showed was worthless.

## Consequences

1. **D-1 is closed.** No Sentinel-1 fetch, no witness spent, no primacy risk. The dense series
   we already own answers the question and the answer is no.
2. **Track E is now unambiguously the top priority**, and T4 tells it exactly where to look:
   the 406 uncorroborated farms, concentrated in rice, maize and bajra.
3. **e16's split design becomes the right one**, and now has a concrete targeting variable.
   The stratified 70 still produce the unbiased headline; a separate discovery set drawn from
   the "neither" group is where new information is. e16 proved these must not be pooled —
   selecting on suspected-wrongness biases the accuracy estimate by up to −23.6pp.
4. **The writeup gains a genuinely strong claim** it could not make before: our cotton labels
   are backed by two independent sensor stacks at 78.8%, and we can say precisely which 42.5%
   of the village is not backed by anything. No other team has quantified where its own map is
   unsupported.

## Standing constraint

Nothing in this document becomes a model feature. The season witness stays a witness — Capella
primacy is a guideline requirement, and `i5_validation`'s independence rests on this series
never having been read by the model. Both would be forfeited at once.
