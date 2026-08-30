# The crop label as a distribution — and why it must not be propagated into yield

`e18_label_distribution.py`. This closes **D-2**, the last of my four Tier-1/2 directions.
Like the other three, it does not survive its own test — but this one fails for a reason that
is genuinely useful, and it retires a claim that has been load-bearing since e11.

## The premise needed correcting first

D-2 said "we ship one hard label per farm" and proposed building a distribution.
**The distribution already exists.** `results/d4_debug.csv` carries a full five-class posterior
(`p_Rice … p_Groundnut`) for all 966 farms. The deliverable ships its argmax and discards the
rest.

And that posterior is not confidently wrong — it is openly unsure:

- median maximum probability **0.409**
- **69.4% of farms have no class above 0.5**
- median normalised entropy 0.867 (1.0 = uniform)

Which already agrees with e17's finding that 42.5% of farms are corroborated by neither
independent sensor. The pipeline has been honest about this all along; nothing downstream
listens.

So D-2 is really one question: **is this posterior good enough to propagate?**

## T1 — it ranks, weakly, and its levels are badly wrong

Proxy for "our label is right": backed by at least one independent sensor (e14 embedding or
e17 dense S1). 956 farms, 57.5% backed.

| p_assigned quintile | n | mean p | % backed | gap |
|:--|--:|--:|--:|--:|
| Q1 | 192 | 0.280 | 56.8% | **+28.7pp** |
| Q2 | 192 | 0.345 | 41.7% | +7.2pp |
| Q3 | 190 | 0.409 | 45.8% | +4.9pp |
| Q4 | 191 | 0.513 | 62.3% | +11.0pp |
| Q5 | 191 | 0.799 | 81.2% | +1.3pp |

Pooled `rho = +0.206, p = 1.3e-10` — but the curve is **not monotonic** (Q1 sits above Q2 and
Q3), and Q1 is under-confident by nearly 29 points. **The levels are not calibrated.**

Within crop, which is the honest cut — the pooled number is confounded because cotton is both
the crop we are most confident about and the only crop the sensors can see:

| crop | n | rho | p | % backed |
|:--|--:|--:|--:|--:|
| Cotton | 449 | +0.095 | 0.044 | 94.2% |
| Maize | 54 | +0.168 | 0.23 | 7.4% |
| Bajra | 147 | +0.154 | 0.063 | 12.2% |
| Groundnut | 220 | +0.049 | 0.47 | 44.5% |
| **Rice** | 86 | **−0.143** | 0.19 | 8.1% |

Only cotton clears p < 0.05, at rho = +0.095, and rice runs the wrong way. **Within a crop,
the posterior barely ranks its own correctness.** Almost all of the pooled +0.206 is the
cotton effect.

*Control (T5):* re-running T1 on temperature-sharpened and flattened posteriors gives +0.217 /
+0.206 / +0.193, with the T = 1 row reproducing T1 exactly. An earlier version of this script
failed that check — positional indexing into a merge that had dropped 10 farms made the
control read −0.005. The control existed to catch exactly that, and did.

## T2 — the negative result that retires an e11 claim

`UNCERTAINTY.md` (e11) showed that calibrated sampling-noise SE does **not** predict
disagreement with the withheld Sentinel-2 witness (rho +0.052, p = 0.12), and concluded:
*"The dominant error is elsewhere — crop label, model form, or genuine sensor difference."*

That conclusion makes a falsifiable prediction: **label uncertainty must predict what sampling
noise could not.** Testing it:

| measure | rho vs \|rank gap\| | p |
|:--|--:|--:|
| label entropy, within-crop ranks | −0.021 | 0.52 |
| label entropy, **global ranks** | +0.033 | 0.31 |
| e11's sampling SE (same target) | +0.052 | 0.12 |

**Null both ways.** The global-rank variant was added because the within-crop version is
under-powered by construction — ranking health and NDVI inside the *same* cohort means a
mislabelled farm is misranked on both sides and the error largely cancels. Fixing that changed
nothing.

**Neither of our two uncertainty measures predicts disagreement with the unread sensor.**
e11's inference is not confirmed. The remaining candidate on its own list is the one it named
last: *genuine sensor difference* — X-band structural backscatter and optical greenness
measuring different things about a field. That would be a defence of our index rather than a
defect in it, but it is now the hypothesis standing by elimination, not by evidence, and it
should be stated that way.

## T3 and T4 — the blocker, and it comes from e15

Expectation over the posterior against the shipped argmax:

| | median t/ha | village total |
|:--|--:|--:|
| as shipped (argmax) | 1.414 | **594.9 t** |
| expectation over posterior | 1.582 | **670.9 t** |

**+12.8% on the village headline.** A step that claims to *quantify* uncertainty must not move
the answer by that much; this is changing the estimate, not describing it.

And T4 shows why, in one number:

| crop | median yield | median SD | **SD / yield** |
|:--|--:|--:|--:|
| **Cotton** | 0.344 | 0.775 | **2.25** |
| Groundnut | 1.863 | 0.713 | 0.38 |
| Maize | 2.181 | 0.752 | 0.34 |
| Rice | 1.635 | 0.543 | 0.33 |
| Bajra | 2.572 | 0.633 | 0.25 |

Cotton's label uncertainty is **2.25 times its own yield**. That is not a measurement of
anything real — it is e15 resurfacing. **Cotton's yield is in lint; every other crop is in
grain or pod.** Taking an expectation across the five classes therefore *adds numbers in
different units*, and because cotton is 47% of farms and sits 5.8× below the others, the
expectation drags the whole village upward. The +12.8% is a unit error wearing the costume of
an uncertainty estimate.

**This makes D-2 not merely unhelpful but ill-defined.** An expectation over a crop posterior
requires all five yields to be commensurable, and e15 established that ours are not.

## Verdict

**Rejected: propagating the posterior into yield.** It is ill-defined while cotton is lint
(e15), it moves the village total by +12.8%, and the posterior it would propagate is not
calibrated in level and barely ranks within crop.

**Adopted: ship the posterior as transparency, not as arithmetic.** Two columns —
`crop_confidence` (already computed) and the five class probabilities — reported alongside the
label, with the honest statement that they rank weakly within crop and are under-confident at
the low end. No other team ships a per-farm label distribution at all, and publishing one with
its measured limitations is worth more than publishing a yield interval built on a unit error.

**Retired: the claim that the crop label is the dominant error term.** It was inferred in e11
by elimination and has been repeated since. e18 tested it directly and it did not hold on that
target. What survives is narrower and still well-supported by e17: our labels for rice, maize
and bajra are *uncorroborated* by any independent sensor. Uncorroborated is not the same as
"the dominant source of witness disagreement", and the two should stop being used
interchangeably.

**Order of operations, if anyone returns to this:** e15's unit question must be settled before
D-2 is reachable at all — not because the anchor is wrong, but because a posterior expectation
cannot cross a unit boundary. That is a real dependency and it was invisible until both
experiments existed.
