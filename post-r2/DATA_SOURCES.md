# Pricing new data sources before fetching them

`e12_data_ceiling.py`. Three sources were proposed: USDA ERS, OpenWeatherMap, and Google
Earth Engine. All three are tested rather than judged, and the test built to do it prices
every future proposal in one line.

## The screening tool: a resolution ceiling, measured on our own farms

Megalodon reported that a covariate constant within a cell can explain only so much of
farm-to-farm health variation once each crop's mean is removed - 0.226 at 250 m, 0.049 at
1 km, 0.000 at 50 km - and concluded that NASA POWER on a 50 km cell "cannot rank farms at
all". That was their number on their data. We had never measured ours.

**The logic.** If a covariate is constant inside a cell of side L, every farm in that cell
gets the same value, so the most it can possibly explain is the between-cell share of the
variance. Anything within a cell is invisible to it. It is a generous upper bound: it assumes
the covariate is perfectly correlated with whatever the between-cell signal is.

**Measured on the within-crop health residual** for 966 Sokhda farms, village extent
4.1 x 3.6 km:

| cell side | cells used | **ceiling** | what sits at this scale | Megalodon |
|--:|--:|--:|:--|--:|
| 100 m | 589 | **0.685** | Capella; Sentinel-1/2 at 10-20 m | - |
| 250 m | 168 | **0.226** | MODIS; SoilGrids 250 m | **0.226** |
| 500 m | 52 | 0.125 | Dynamic World / WorldCereal aggregated | - |
| 1 km | 17 | 0.041 | SoilGrids 1 km | 0.049 |
| 5 km | 4 | 0.015 | CHIRPS rainfall | - |
| 11 km | 1 | **0.000** | ERA5-Land | - |
| 25 km | 1 | **0.000** | ERA5; most weather APIs | - |
| 50 km | 1 | **0.000** | NASA POWER | **0.000** |

**Our 250 m ceiling is 0.226. Megalodon's is 0.226.** Two teams, different pipelines,
different health indices, identical number - and 0.000 at 50 km on both. That is strong
independent corroboration of the method and of the conclusion, and it is the kind of
convergence §2.4 of the analysis argues is worth more than either team's word alone.

### A bug this caught in my own work

The first run reported a "village extent of 139 x 1110 km", which is impossible for a 3.4 km
village. Nine farms are **degenerate geometry** - valid FIDs enclosing effectively no ground
(areas from 0 to 2.3x10^-7 ha) - and their centroids land up to **835 km** away, stretching
every cell boundary and making the whole curve meaningless. Excluding them gives 4.1 x 3.6 km,
which matches the village.

Orion independently documented the same defect ("ten parcels are degenerate geometry - valid
FIDs enclosing effectively no ground, < 10^-6 ha"). We find nine. They still carry a row in
the submission; they simply cannot define a spatial grid.

---

## Verdict 1 - USDA ERS: dead end, tested

The key works and the API responds. The data is about something else.

| endpoint | returns |
|:--|:--|
| `/arms/state` | 16 **US** states - Arkansas, California, Florida, Georgia... |
| `/arms/report` | *Farm Business Balance Sheet*, *Income Statement*, *Financial Ratios* |
| `/arms/year` | 1996-2024 |

ARMS is the **Agricultural Resource Management Survey**: US farm **finances**, US states only.
Wrong continent, wrong subject, and no biophysical variable at any resolution. Every other
documented ERS endpoint 404s.

**Not usable.** If a USDA product is wanted for India, the relevant agency is FAS (Foreign
Agricultural Service - PSD Online, Crop Explorer), not ERS - but those are country- and
state-level, which the ceiling table prices at 0.000.

## Verdict 2 - OpenWeatherMap: useless for ranking, and unnecessary for timing

**For ranking farms: arithmetically impossible.** OpenWeatherMap history resolves at roughly
25 km. Sokhda is 4 km across, so the entire village sits in one cell and receives one value
for all 966 farms. Ceiling **0.000**. This is not a judgement about weather - it is the same
arithmetic that prices out NASA POWER, ERA5 and every other reanalysis product.

**But weather is not useless, it is useful for a different job.** Our rice channel is the
6 -> 19 June brightening (+3.23 dB for rice against +0.07 to +1.12 for every other crop), and
that mechanism depends on a *weather fact*: that one date is dry and the other is wet.

Fetched independently from **Open-Meteo's archive** - hourly, free, no key - against the
actual Capella overpass times:

| acquisition | 6 h before | 24 h before | whole day |
|:--|--:|--:|--:|
| **6 Jun, 07:00 UTC** | **0.0 mm** | 0.1 mm | 0.0 mm |
| **19 Jun, 02:00 UTC** | **17.3 mm** | 29.0 mm | 7.4 mm |

A clean dry/wet contrast between exactly the two dates our rice signature uses, verified from
a source neither we nor any competitor's writeup supplied. It corroborates Coding Bits
(12.5 mm in the preceding six hours) and Megalodon (21.9 mm on the day) - same event, small
differences from grid and product.

**So: adopt hourly weather for acquisition-time context, and use Open-Meteo, not
OpenWeatherMap.** Open-Meteo is free, needs no key, gives hourly precipitation, and is what
Coding Bits used. OWM's history endpoint is paid and no better resolved for this purpose.
There is no reason to add a paid dependency for a strictly worse version of a free one.

*Value already banked:* this converts "19 June was a rain day, per two competitors" into a
fact we measured ourselves, at the overpass hour, which is exactly the standard §10 demanded
of the calibration finding.

## Verdict 3 - Google Earth Engine: the only proposal that clears the ceiling

GEE is a catalogue, not a dataset, so it must be priced product by product:

| GEE product | native cell | ceiling | worth pursuing? |
|:--|--:|--:|:--|
| **ESA WorldCereal 10 m** | 10 m | 0.685 | **yes** - independent crop reference |
| **Dynamic World 10 m** | 10 m | 0.685 | **yes** - near-real-time land cover |
| Sentinel-1 / Sentinel-2 | 10-20 m | 0.685 | already used, via Planetary Computer |
| SoilGrids 250 m | 250 m | 0.226 | Megalodon fetched ten properties and **rejected** them on measurement |
| CHIRPS | 5 km | 0.015 | no |
| ERA5 / ERA5-Land | 11-25 km | 0.000 | no |

Only the 10 m products clear the ceiling, and **a ceiling is an upper bound, not a promise** -
Megalodon's SoilGrids result is the cautionary case: 0.226 of headroom, ten properties
fetched, and rejected on measurement anyway.

**Two caveats before anyone spends time on it:**

1. **GEE needs a Google account and a registered cloud project.** That is an interactive
   authentication step, so it needs a person, like Track E.
2. **WorldCereal is a 2021 product** and we image kharif 2025. Crop rotation means a
   2021 maize map is not a 2025 maize map. Its *stable* layers - temporary-crop extent,
   active cropland - transfer better than its crop-type layers, and that is how it should be
   tested: as a cropland mask and a non-crop screen, not as a crop label.

### GEE was authenticated and the tests were run

`e13_gee.py`. The existing refresh token worked once the GCP project was corrected to
`472723809152`; Dynamic World returned 20 images over Sokhda for Jun-Oct 2025, and
WorldCereal 2021 offered four products (`temporarycrops`, `maize`, `wintercereals`,
`irrigation`). Per-farm zonal means at 10 m for all 966 parcels.

**T1 - Dynamic World non-crop screen: REJECTED, and this is the important one.**

The headline looked strong: 247 parcels (16.6% of area) have a modal 2025 land cover that is
not crops or grass - 91 built, 70 shrub, 50 flooded vegetation, 36 trees - and our health
index scores them 48.3 against 52.0 for the rest. We have no non-crop screen at all, where
Orion removes 37 parcels, so this looked like a clean capability gap being filled.

It does not survive testing.

| | non-crop | crop |
|:--|--:|--:|
| median area | **0.179 ha** | **0.357 ha** |
| median 10 m pixels per parcel | ~18 | ~36 |

`rho(area, non-crop) = -0.286`, Mann-Whitney `p = 5.7e-19`. The flag is **half a farm-size
detector**. A 0.164 ha parcel - the median for "built" and "trees" - is about 4x4 pixels at
10 m, so boundary pixels carrying the neighbouring road, farmstead or tree line dominate the
mode. And the modal label is a weak winner: for "built" parcels the built probability is only
0.411 with crops still at 0.203.

Matching on area decile collapses the health difference from -7.34 to **-3.39**, and the sign
**flips** in the top three deciles (+10.14, +5.76, +20.98). A contamination signal that
reverses with farm size is not a contamination signal.

**Adopting this would have removed 16.6% of the village's area for being small.** The
resolution ceiling said 10 m clears the bar; it did not say a 10 m product survives a 0.27 ha
parcel. **A ceiling is necessary, not sufficient.**

**What is defensible is much narrower.** Ten farms are flagged by *both* our own SAR rule
(Orion's: any-date mean > -10 dB or CoV > 2.0, mapped onto our uncalibrated scale) and by
Dynamic World - 10 against 6 expected by chance. Those ten are 0.60% of area, median 0.190 ha,
and **our health index already scores them at a median of 1.1 against a village median of
50.7**. Two independent sensors agree they are not fields, and our pipeline already ranks them
at the very bottom without being told.

*Recommendation:* ship them as a **flag**, not a filter. They are already handled numerically;
what is missing is that they still enter the crop-share accounting and the village aggregate
as though they were farms.

**T2 - WorldCereal maize: no information, exactly as predicted.**

Raw agreement 91.6%, **Cohen's kappa -0.010**. Ours 42 maize farms, WorldCereal 24. A 2021
maize map says nothing about 2025 labels, which is what crop rotation predicts - this was
called before the test ran and the test agreed. The 91.6% raw figure is the trap: it is high
only because both maps call almost everything not-maize, which is why kappa exists.

`temporarycrops` is more usable as a stable cropland mask: median 59, with 53.2% of farms
above 50.

**T3 - WorldCereal irrigation: a weak, wrong-signed signal.**

| relationship | rho | p |
|:--|--:|--:|
| irrigation vs our health index | +0.056 | 0.115 |
| irrigation vs NDVI 13 Oct (withheld) | **-0.167** | **2.4e-06** |
| irrigation vs our yield | +0.050 | 0.16 |

Irrigated-flagged parcels are significantly *less* green on 13 October. That is the opposite
of the naive expectation, though it is consistent with the seasonal story in
`KHARIF_ANCHORS.md` - parcels irrigated for a *summer* crop may sit fallow or late in kharif.
It is a coherent story and a weak correlation, so it is recorded as an open lead and not used.

### GEE verdict

Authenticated, three products tested, **nothing adopted except a ten-farm flag**. The
resolution ceiling correctly identified which products were worth fetching, and the depth
test then rejected the most promising-looking of them for a reason the ceiling could not see:
our parcels are too small for a 10 m modal class to be trustworthy.

That is the rule this whole exercise keeps re-learning - a source can clear every screen and
still fail on the specific geometry of this problem.

---

## The general rule this establishes

**Anything on a cell larger than the village is arithmetically incapable of ranking farms
inside it.** That single line prices out every weather API, every reanalysis product and
every country-level statistic for the ranking job, without fetching any of them.

Coarse data still has two legitimate uses, and both are about *level* or *timing* rather than
*ranking*:

- **temporal context** - the rain event that makes our rice channel work (verified above)
- **aggregate anchors** - district yield statistics, which set a level and are never asked to
  rank (see `KHARIF_ANCHORS.md`)

Applied to the three proposals: **one dead end, one replaced by a free better alternative,
one genuinely worth pursuing but gated on an interactive login and needing its own test.**
