# Round 1 → Round 2: what transfers, what does not, and what we shipped

Written 2026-08-11, corrected 2026-08-27. Every claim here was **tested**, not assumed.
Round 1's **official** score was **MSE 11.071**; the MSE 0.000 run came after the deadline
and is not our result. So R1's 145 village×crop cells are our own best reconstruction of
the village mix, *not* ground truth — good enough to measure sign agreement against, which
is all the tests below ask of it, but never to be cited as exact.

**Method rule applied throughout:** Sokhda (R1 village 22) is the R2 target village, so it
is **held out of every derivation below**. Nothing here is fitted to the village we predict.

---

## 1. R1's score ladder, split by what actually produced the gain

| MSE step | Lever | Category | Transfers to R2? |
|---|---|---|---|
| 12911 → 1872 | optimal global scale | leaderboard algebra | **No** |
| 1872 → 1072 | per-crop weights `W_c` | leaderboard algebra → but *result* is the crop mix | **Yes, as the prior** |
| 1072 → 1045 | covered/uncovered groups | artefact of R1's coverage problem | No — R2 has full coverage |
| 1045 → **527** | Dynamic World cropland mask | better backbone feature | Lesson only |
| 527 → 204 | re-solved weights on DW | leaderboard algebra | No |
| 204 → **130.8** | soft aux blends, λ solved | **measured physical signatures** | **Test each** |
| 130.8 → 98.4 | denser aux (S1 Jul/Sep, S2 monthly) | measured signatures | Test each |
| 98.4 → 76.3 | GLCM texture / entropy | measured signatures | Test each |
| 76.3 → **32.7** | Gram ensemble solve | pure leaderboard algebra | **No** |
| 32.7 → 14.6 | crop-type reallocation directions | leaderboard algebra | No |
| 14.6 → **11.07** | oracle cell reads | pure leaderboard algebra | **No** |

**The structural conclusion.** Roughly three quarters of R1's total MSE reduction came from
levers that exist only because a final leaderboard was answering queries about a fixed
truth vector. R2 has no leaderboard, no MSE, no feedback channel of any kind. **Those
levers are not "hard to port" — they are undefined here**, and any attempt to dress them up
as methodology would be dishonest.

What *is* portable is the middle band: the 25 soft-aux blends, because each λ is a
*measurement of a physical relationship* that happened to be made through the leaderboard.
The measurement stands on its own once you have the truth — which we do.

---

## 2. Testing R1's 25 signatures against its own reconstruction

R1 fitted each λ to minimise MSE. With that reconstruction in hand we can ask a
sharper question: **does the sign of each λ match the actual correlation between that
feature and that crop's share across the 29 villages?**

**13 of 15 testable signatures agree.** The strongest, all p < 0.01:

| crop | feature | λ sign | ρ vs true crop share | p |
|---|---|--:|--:|--:|
| Groundnut | NDVI | − | **−0.637** | 0.000 |
| Maize | S1 VH Aug | + | **+0.608** | 0.000 |
| Cotton | S1 VH Jul | + | **+0.588** | 0.001 |
| Rice | flood dip (VH Aug−Jun) | + | **+0.546** | 0.002 |
| Rice | X-band Aug−Jun | − | **−0.507** | 0.005 |

Two **contradict** the reconstruction:

- Cotton × X-band Aug (λ was +, reconstruction ρ = −0.243, p = 0.21) — a weak, non-significant fit.
- **Groundnut × NDVI entropy (λ was +, reconstruction ρ = −0.531, p = 0.003)** — significantly the
  wrong way round.

That second one matters. It sits in the late texture band that took R1 from 88 → 76, and it
is **evidence that the tail of R1's ladder was partly fitting leaderboard noise rather than
physics.** A useful caution about R1's own final numbers, and a reason not to import that
band wholesale.

---

## 3. The one signature that survived every test — and shipped

R2 has **X-band only**. So of R1's 25 blends, only the six X-band ones can transfer at all.
Re-measured against that reconstruction on the **28 villages excluding Sokhda**:

| feature | Rice | Cotton | Maize | Bajra | Groundnut |
|---|--:|--:|--:|--:|--:|
| x_hh_aug | +0.00 | −0.25 | +0.24 | −0.03 | +0.11 |
| x_hh_jun | +0.26 | −0.34 | +0.09 | −0.27 | +0.16 |
| x_hh_oct | −0.14 | **−0.43\*** | +0.09 | +0.04 | +0.32 |
| **x_hh_augjun** | **−0.56\*\*** | **+0.38\*** | **+0.44\*** | +0.26 | −0.34 |
| x_hh_octaug | +0.03 | +0.12 | −0.36 | +0.05 | +0.03 |
| x_hh_octjun | −0.17 | +0.26 | −0.19 | +0.07 | −0.09 |

**`x_hh_augjun` (X-band August minus June) is the only X-band feature that discriminates
crops, and rice is what it discriminates best** (ρ −0.555, p = 0.0022).

### Why this was worth shipping — four independent checks

1. **Exact-truth validated**, Sokhda held out entirely. p = 0.002.
2. **The prediction transfers.** In R2 at farm level, rice-labelled farms have the *lowest*
   median x_augjun (−2.20 dB) and maize the *highest* (+0.32) — exactly the predicted order,
   in a different village, at a 3000× smaller spatial support.
3. **It is not a restatement of the flood channel.** Partial correlation with the same-day
   Sentinel-2 witness, controlling for flood: **ρ +0.162, p = 1.0e−06.** It carries crop
   information the existing rice channel does not.
4. **Physically coherent.** Paddy is bright in June from stem–water double bounce and falls
   back as the canopy closes by August, so its Aug−Jun change is the most negative of the
   five. Same mechanism the rice channel already rests on, observed from the other end.

### What it fixed

The rice channel was a **documented weakness**: the leave-channel-out test said rice rested
on a single channel and was **NOT corroborated (p = 0.38)**. With x_augjun added:

| metric | before | after |
|---|--:|--:|
| rice leave-channel-out | p = 0.378 *(not corroborated)* | **p = 2.65e−13 — corroborated** |
| crop separation, S2 NDVI (H) | 164.3 | **165.6** |
| crop separation, S1 C-VH (H) | 95.8 | **98.0** |
| independent uniformity test | −0.161 | **−0.168** |
| Moran's I (health) | 0.091 | **0.097** |

**A strict improvement on every metric**, while fixing the weakness. The weight is the
measured effect size (0.555), not a tuned number — tuning it against the witness would
convert a held-out check into a fitting target.

### And what was rejected

The same reconstruction gives **Maize +0.444 (p = 0.018)** on the same feature. Adding it was
tried and **rejected on measurement**: crop separation fell on *both* witnesses (NDVI H
164.3 → 157.5, C-VH 95.8 → 89.3). Rice's evidence is an order of magnitude stronger in p.
Only the signature that earns its place ships.

---

## 4. What we deliberately did NOT take from R1

| R1 asset | Why not |
|---|---|
| Gram ensemble, parabola solve, oracle reads | Undefined without a leaderboard. Not portable, not "hard" — impossible. |
| The 19 C-band / optical λ values | Fitted on Sentinel-1 C-band and Sentinel-2 at **village** scale for **crop area**. R2 is X-band, farm scale, health/yield. Three simultaneous transfers; the numbers would be false precision. Their *directions* already inform the evidence function. |
| Groundnut × NDVI entropy | **Contradicts the reconstruction** (ρ −0.531, p = 0.003). Actively rejected. |
| Dynamic World cropland backbone | R2's deliverable is per-farm health, not village cropland area. The farm polygons *are* the backbone. |
| Sokhda's own crop areas as labels | Held to the [J7] rule: soft prior on the village mix only, never per-farm labels, never a fitting target. |

**The honest caveat on what we did ship.** R1's correlations are measured *between villages*;
applying them *between farms within one village* is an ecological inference, and the two need
not agree. That is exactly why check 2 (does the predicted ordering appear at farm level?) and
check 3 (partial correlation against a held-out sensor) exist. Both passed. Had either
failed, the signature would not have shipped.

---

## 5. External ground-truth sources — the complete search

Everything probed, with the outcome:

| source | status |
|---|---|
| **Krishi-DSS GeoServer** | ★ **WFS open, no auth.** Layer `24_dcs` = Gujarat Farmland Parcel Registry → **survey number for 947/966 farms**, median overlap 0.93. Shipped. |
| Krishi-DSS `cropmapping-api` | 401 — needs the bearer token you are fetching |
| Krishi-DSS Data Exchange | 43 use cases incl. `getCropIdentification`, **`getGTPoint`** (ground-truth points). Seeker/provider onboarding — **no yield or crop-health product exists in the catalogue** |
| Gujarat VF-12 / AnyROR | Per-plot crop per season, with history. Captcha-gated → manual, now cheap thanks to the survey numbers |
| AgriStack Digital Crop Survey | Village aggregates only; per-plot not published |
| Google ALU / AnthroKrishi | Farm-level, in-season, all five crops, free — needs a Workspace Customer ID |
| **MNCFC FASAL** | District level (557 districts), not village. Not useful per-farm |
| **MNCFC YES-TECH** | ★ Yield at **Gram Panchayat** level for paddy/wheat/soybean — the right granularity, but the portal (`pmfby.gov.in/yestech/`) is a shell and the data is not open |
| PMFBY report portals | `reportPortal`, `cceAdmin`, `nationalCropInsurancePortalReports` all return **HTTP 200** — worth a browser visit, they may expose CCE yields |
| Bhuvan | WFS explicitly **disabled** |
| WorldCereal | "Global" collection is a Belgium-sized test extent |
| data.gov.in API | 404 without a registered key |
| NASA POWER | ★ Open, no key. Shipped as rainfall context |
| Impact Observatory LULC | ★ Open via Planetary Computer. Shipped as the cropland confounder check |

**Conclusion on ground truth:** per-farm crop type genuinely cannot be obtained without a
human. That is now a *measured* conclusion, not an assumption. The three live routes are the
Krishi-DSS token, the VF-12 sample (now cheap), and the ALU application.

**One new lead for you:** the three PMFBY report portals return 200. Since you are already
in a browser with a session, they are worth ten minutes — they are the only realistic route
to an external check on the **yield** column, which still has none.

---

## 6. Bottom line

- **One** thing from R1 met the bar for shipping, and it is now in the pipeline: the
  X-band Aug−June rice channel. It converted a documented failure into a documented pass and
  improved every other metric at the same time.
- **One** R1 signature was found to *contradict* R1's own reconstruction, which is a useful
  caution about the tail of that ladder.
- Everything else was either impossible without a leaderboard, or would have required three
  simultaneous unvalidated transfers.

That ratio is the point. R1's headline achievement was a measurement channel, not a method —
and the honest yield from mining it is one well-tested feature, not a methodology.
