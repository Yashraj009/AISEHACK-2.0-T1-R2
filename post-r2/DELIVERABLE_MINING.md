# Mining the competitors' deliverables, not their writeups

`e9_mine_deliverables.py`. The five writeups were exhausted after §1-12 of
`COMPETITOR_ANALYSIS_R2.md`. What shipped *alongside* them was not: four notebooks and three
methodology PDFs, **555,246 characters never opened**.

A writeup is an argument. A notebook is the evidence, and it carries what prose omits.

| source | code | prose + PDF |
|:--|--:|--:|
| Orion | 213,137 | 20,881 |
| Coding Bits | 135,090 | 13,051 |
| 8bit | 122,953 | 38,989 |
| Megalodon | 6,301 | 4,853 |

---

## 1. The external-data census: there is no edge to copy

Every dataset, endpoint and product touched by any competitor pipeline, extracted from code
rather than prose:

| dataset | who |
|:--|:--|
| Sentinel-2 L2A (Element84 `earth-search`, MS Planetary Computer) | Coding Bits, Orion, 8bit |
| Copernicus DEM 30 m (`copernicus-dem-30m.s3.amazonaws.com`) | 8bit |
| NASA POWER (`power.larc.nasa.gov`) | 8bit |
| Open-Meteo archive (`archive-api.open-meteo.com`) | Coding Bits |
| APY / advance estimates | Megalodon, Orion |

**Nobody used Sentinel-1.** We are the only team of six with a C-band witness, and the only
one with a season-integrated one. The external-data advantage we already have is larger than
anything visible here to copy.

**Consequence for Round 3:** a new-dataset edge cannot come from imitating this field. It has
to come from sources none of the six touched. Two candidates identified and not yet tested:

- **Kharif-season-separated district statistics.** `data.gov.in` catalog
  *Area, Production and Yield of Major crops of Gujarat State*, resource
  `66e33662-6f0b-4bd9-8771-5a33f8ff6cdd`, described as **"season wise and year wise"** - which
  is precisely the annual-vs-kharif defect §10.2 identified in our bajra anchor. The ICRISAT
  District Level Database (560 districts, 1990-2015, kharif/rabi split) is the multi-year
  companion that would fix the thin-base instability. **Blocked:** the shared public demo API
  key returns HTTP 429; a free personal key from `data.gov.in` is needed.
- **ESA WorldCereal 10 m (2021)** - global maize / cereals / active-cropland maps at 10 m,
  which clears the ~250 m resolution floor Megalodon showed any covariate must beat to rank
  farms at all. Four years stale and rotation-sensitive, so it is a hypothesis, not an input.

## 2. A competitor's code corrected one of our own conclusions

Coding Bits' notebook carries this comment:

```
# gcps= alone fits a 2nd-order polynomial. SRC_METHOD='GCP_TPS' interpolates every GCP;
# METHOD='GCP_TPS' is accepted and silently IGNORED by GDAL.
```

**This falsifies part 3 of the e8 verdict.** §12 concluded that GDAL auto-selects order 3
with 225 GCPs, that this overfits our lattice, and that forcing order 2 was "the cheapest
win" at 0.46 m. If `gcps=` already fits order 2, there is nothing to force and no 0.46 m to
recover.

We could not settle it directly - `osgeo` is not installed here, and an attempted marker-warp
test produced an empty raster, so its apparent 564 m offset was the corner of an all-zeros
array and is not a measurement. What we can measure says the question does not matter:

| fit | in-sample RMSE | LOO median (§12) |
|:--|--:|--:|
| order 1 | 8.14 m | 5.62 m |
| order 2 | **7.06 m** | **2.93 m** |
| order 3 | 6.71 m | 3.00 m |

Order 2 and order 3 differ by 0.07 m on held-out points. **Recommendation withdrawn:** there
is no meaningful gain in forcing the polynomial order either way. The TPS finding from §12
stands unchanged - it halves the residual and its p95 tail - and now comes with the trap:

> **`METHOD='GCP_TPS'` is silently ignored. The correct key is `SRC_METHOD='GCP_TPS'`.**

A silent no-op is exactly the failure class that survives every internal consistency check,
which is the F3 argument in miniature. Worth an assertion if we ever adopt the spline.

## 3. Orion's real argument against our central design choice

Their writeup says the Round 1 shares are unstable. Their **code comments** give the actual
agronomic reasoning, which is much stronger and was never published:

```
#   - Gujarat kharif 2025 sowing (the season these scenes image): groundnut 20.41 and
#     cotton 20.35 lakh ha, paddy 7.17, maize 2.64, bajra 1.53.
#   - Vadodara's field-crop profile is paddy/cotton/maize; Gujarat's groundnut area is
#     concentrated in Saurashtra, not the central zone.
#   - Vadodara ranks 1st in Gujarat for maize yield, 2nd for cotton yield.
#   - Round 1 found real bajra area in Vadodara district to be close to zero.
CROP_MIX_REFERENCE = {"Rice": 0.26, "Cotton": 0.32, "Maize": 0.18, "Bajra": 0.08,
                      "Groundnut": 0.16}
```

Set against ours:

| crop | **ours (R1)** | Orion's external reference | gap |
|:--|--:|--:|--:|
| Cotton | 43.2% | 32% | +11.2 |
| **Groundnut** | **30.8%** | **16%** | **+14.8** |
| Rice | 10.6% | 26% | -15.4 |
| Bajra | 9.5% | 8% | +1.5 |
| **Maize** | **6.0%** | **18%** | **-12.0** |

Two of their claims bear directly on our two most disputed shares:

- **Groundnut is a Saurashtra crop, not a central-Gujarat one.** We put it at 30.8% of
  Sokhda - our second-largest class.
- **Round 1 found bajra near zero in Vadodara.** We ship 9.5%.

This is not settled, and it is uncomfortable, because our own `data_aux/SOURCES.md` carries a
**RETRACTED** section that went the *other* way: it once argued groundnut was essentially
absent from the district (1,004 ha, 0.35%), then retracted that in favour of the Round 1
figure of 31%. So we have already litigated this once and concluded R1 was right.

Three positions now exist on Sokhda's groundnut:

| source | groundnut share | basis |
|:--|--:|:--|
| Vadodara APY 2022-23 | 0.35% | one district-year, 1,004 ha base |
| Orion's reference | 16% | state sowing + agro-zone reasoning |
| **our Round 1 fit** | **30.8%** | whole-village reconstruction, MSE 11.071 |

A single village may legitimately differ from its district and its agro-zone, which is the
whole premise of dasymetric mapping - but "may differ" is not evidence.

**Tested on our two withheld witnesses**, 13 October:

| our label | n | NDVI | S1 VH dB | crop-calendar expectation |
|:--|--:|--:|--:|:--|
| Cotton | 455 | **0.374** | -14.19 | standing, greenest |
| Groundnut | 221 | **0.295** | -14.95 | standing, lifted Oct-Nov |
| Bajra | 149 | 0.255 | -14.71 | off field by late Sep |
| Rice | 86 | 0.234 | -15.71 | draining / harvest |
| Maize | 55 | **0.199** | -15.77 | harvested Sep-Oct |

Cotton tops both sensors as the only crop still standing, maize bottoms them as the earliest
harvested, and **groundnut separates from bajra in exactly the direction the calendar demands**
(0.295 vs 0.255, Mann-Whitney p = 6.4x10^-5). Within the tier-2 group, agronomy predicts
Bajra < Maize < Groundnut and we observe Maize < Bajra < Groundnut - groundnut on top as
predicted, maize and bajra transposed.

**What this does and does not establish, stated carefully.** It shows our groundnut class
carries real signal on sensors the pipeline never read: it is not an arbitrary residual
allocation. It does **not** validate the *share*. Orion's objection is about how much
groundnut Sokhda has (30.8% vs 16%), and a class can behave correctly while being over- or
under-allocated. Nothing in our possession can settle 30.8% against 16% - which is precisely
why real ground truth (Track E) is the highest-value item on the Round 3 plan, and why it is
worth saying so rather than treating this test as a win.

## 4. Quality gates and constants worth testing against ours

From the constant hunt. These are **hypotheses**, not adoptions.

| constant | team | ours | note |
|:--|:--|:--|:--|
| `NESZ_MARGIN_DB = 3.0` | Orion | none | they gate farms on clearing the declared noise floor by 3 dB. We only discovered `nesz_peak` in e6 and use it nowhere |
| `MIN_CORE_PX = 60` | Orion | none | below this "the farm-mean is too noisy to trust on its own" |
| `MIN_VALID_DATES = 3` | Orion | none | |
| `MIN_DATE_COVERAGE = 0.50` | Orion | none | a date counts for a farm only above this valid-pixel fraction |
| `ERODE_MAX_M = 4.0`, `ERODE_FRACTION = 0.25` | Orion | fixed ladder | proportional erosion rather than a fixed buffer |
| `W_WET = 0.10` | Coding Bits | n/a | annotated *"PHYSICS PRIOR - deliberately not the sweep's argmax"* |
| `SEASON = {Bajra: complete, Maize: complete, Groundnut: complete, ...}` | Orion | `COMPLETION` dict | their crop calendar as a categorical, ours as a fraction |

**The NESZ gate is the most interesting.** e6 used `nesz_peak` to adjudicate our calibration
and then dropped it. Orion uses it operationally as a per-farm quality gate. We have 12-23% of
AOI pixels near the noise floor by our own reckoning, and no gate on it.

## 5. What they tried and did not ship

Prose omits failures; code preserves them.

- **Coding Bits** annotate a rejected calibration convention inline
  (`# ours = sf^2|A|^2 sin(th), so the competing convention is RAW/sf`) - they tested ours
  explicitly and recorded it in code, not just in the writeup.
- **Coding Bits**: *"NOTE: the optimum sits at the edge of the grid - the sweep spans 0 to 1,
  so this..."* - an edge-of-grid optimum they flagged rather than adopted.
- **Coding Bits**: *"did not replicate, reported anyway."*
- **Orion**: *"NOTE: no reserved scene cleared the gate, so this audit runs against the..."*
  Their writeup presents an 18 October reserved scene as the headline validation. The code
  note suggests the reserved-scene gate did not always pass. **Worth reading in full before
  citing their reserved-scene discipline as a model** - it may be weaker than published.
- **Orion**: *"note: CoV = std/mean of linear power. For fully-developed speckle at L looks
  the expected..."* - independently confirms the L-dependence that made their CoV-excess
  formulation fail on our 4-5 look grid (§10.3).

---

## What this pass changes

1. **One of our recommendations is withdrawn** (force polynomial order 2 - immaterial).
2. **One trap recorded** (`METHOD='GCP_TPS'` is a silent no-op).
3. **One live threat to our largest design choice** - Orion's agronomic case against our
   groundnut and bajra shares, which is stronger in their code than in their writeup, and
   which we can test on witnesses we already hold.
4. **One capability gap with a concrete fix** - a NESZ-based per-farm quality gate.
5. **Two untested external datasets** - kharif-season district statistics (blocked on a free
   API key) and ESA WorldCereal 10 m.
6. **Confirmation that no external-data edge is available by imitation** - nobody used
   Sentinel-1, and we already do.

Nothing above is adopted. Every item is a hypothesis with a named test.
