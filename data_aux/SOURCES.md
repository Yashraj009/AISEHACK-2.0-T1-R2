# Auxiliary data — provenance

All auxiliary data must be **open and freely available to all** (competition rule, [E1]), and Capella SAR
must remain the primary dataset — these inputs refine, they do not replace.

## `vadodara_apy.csv` — district crop area, production, yield

**Source:** Directorate of Agriculture, Government of Gujarat (2024), reproduced as Tables 1–3 in
Parmar, K. & Bhatt, B. (2025), *Evaluating agricultural patterns and crop shifts in Vadodara-Chhotaudepur
District of Gujarat, India*, International Journal of Agriculture and Food Science 7(5): 55–61.
DOI: `10.33545/2664844X.2025.v7.i5a.380` — open access.

**Year:** 2022–23 (the most recent official district-level figures published in that series).

Areas converted from the paper's `'00 ha`; production from `'00 MT`. `area_share_of_5crops` is renormalised
over the five competition crops only (Rice, Cotton, Maize, Bajra, Groundnut), because the district also
grows tur, wheat, castor, tobacco and jowar which are outside our label set.

| crop | area (ha) | yield (kg/ha) | share of the 5 crops |
|---|---|---|---|
| Cotton | 185,479 | 776 | **65.3%** |
| Rice | 49,818 | 1,690 | 17.5% |
| Maize | 40,794 | 2,312 | 14.4% |
| Bajra | 7,022 | 2,714 | 2.5% |
| Groundnut | 1,004 | 2,514 | **0.35%** |

### Caveats — state these in the writeup

1. **"Vadodara-Chhotaudepur" is the combined district.** Chhotaudepur was carved out of Vadodara in 2013;
   this series reports them together, so it covers a larger and more tribal/upland area than modern Vadodara
   district alone. Sokhda sits in the western alluvial plain.
2. **2022–23, not the 2025 kharif we observe.** Used as a *prior on the crop mix*, never as truth. The
   direction of recent change is known from state-level 2025 sowing figures [E6]: groundnut acreage rose
   sharply statewide that year.
3. **Cotton yield (776 kg/ha) is lint**, not seed cotton — do not compare it to the cereal yields directly.
4. This is a **district** figure and Sokhda is **one village**. Its true mix legitimately differs. Applied
   as a soft prior, not a hard quota [E6].

### ⚠ RETRACTED — the groundnut claim was wrong. See `sokhda_r1_truth.csv`.

This section previously argued that **groundnut is essentially absent** from the district (1,004 ha, 0.35%
of the five-crop area, collapsed from 13,000 ha in 1997–98), and that this **contradicted** the
Round-1-derived prior in [A5] which had groundnut at **31%** of Sokhda. It concluded that losing the R1
artefacts was "an escape".

**That conclusion is retracted [J2].** The R1 repository was recovered on 2026-08-02 and contains
**measured ground truth for Sokhda** (= R1 village 22, polygon 1173.68 ha vs our 1174.1 ha):

| crop | Sokhda ha | share |
|---|---|---|
| Cotton | 297.08 | **43.0%** |
| Groundnut | 213.93 | **31.0%** |
| Rice | 73.33 | 10.6% |
| Bajra | 65.12 | 9.4% |
| Maize | 41.42 | 6.0% |

Groundnut is **31.0%** of Sokhda's cropped area — the [A5] figure was right to the decimal. The district
APY table is a **bad prior for this village**: it is 2022–23, it merges Vadodara with tribal/upland
Chhotaudepur, and Gujarat groundnut sowing hit **125% of normal in kharif 2025** (DeshGujarat, Sep 2025).
Caveat 4 above ("district ≠ village, apply as a soft prior") was the correct caveat; the error was letting
the district number overrule a village-level measurement.

**Use `sokhda_r1_truth.csv` as the crop-mix prior, not this table.** The APY table is retained only for its
**yield** column (kg/ha), which is the district-level anchor the yield step needs and which no
village-level source provides.

## Not fetched, deliberately

- **Copernicus GLO-30 DEM** — skipped. The AOI's best-fit terrain slope is **0.020°**, so local incidence
  deviates from scene incidence by ~0.02° against a 0.43° within-scene and 6.55° between-date spread [H5].
  A DEM would change nothing measurable. TWI drops with it.
- **Sentinel-2 NDVI / Sentinel-1 VH** — reserved for **validation only** (§4 of `MASTER_PLAN.md`), fetched
  at the validation stage, never used as model inputs.
