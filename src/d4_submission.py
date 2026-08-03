"""Stage D4 -- crop type, health index, yield-to-date, and submission.csv.

This is the SUBMITTABLE GATE. Everything after it is improvement on something
already valid; nothing downstream starts until this writes 966 clean rows.

Three steps, each with the constraint that forced its design:

1. CROP  -- soft evidence -> per-farm probabilities -> prior-matched -> argmax.
   Forced by [J3]: in Round 1 a HARD per-pixel crop assignment from SAR scored
   MSE 19354 against 12911 for a flat prior -- 5x WORSE than assigning nothing.
   Single-pol X-band HH genuinely cannot separate five crops confidently, so the
   model must emit probabilities and the class marginals must be pinned to a
   prior rather than inferred freely. We still argmax at the very end because the
   CSV schema demands one crop_type per farm, but the probabilities survive in
   crop_confidence and in the debug table.

2. HEALTH -- crop-relative composite of the feature families that survived QA.
   Scored WITHIN crop, because a healthy groundnut and a healthy cotton have
   completely different backscatter. Excludes ktex [H2] and subcoh [I1], both
   documented negatives.

3. YIELD  -- district yield anchor x relative performance x season completion.
   "to date" is taken literally: on Oct 13 cotton is barely into picking while
   rice is essentially harvested, so the same health score means very different
   accumulated yield.

Run:  python src/d4_submission.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CROPS, DATES, RESULTS, AUX, log

SUB = RESULTS / "submission.csv"
DEBUG = RESULTS / "d4_debug.csv"

# Season completion at the Oct 13 acquisition, as a fraction of the crop's total
# kharif cycle. Gujarat kharif is sown mid-June on the monsoon onset [J8].
# Rice/maize/bajra harvest Sep-Oct -> effectively complete. Cotton picks Oct-Jan,
# so on Oct 13 it is at the very start of harvest. Groundnut lifts Oct-Nov.
COMPLETION = {"Rice": 0.95, "Maize": 0.95, "Bajra": 0.95,
              "Groundnut": 0.75, "Cotton": 0.45}

# Within-village yield spread. Farm-level yield CV inside one village is commonly
# 20-35%; +/-30% at 2 sigma is the conservative end of that. This is the one
# tuning knob in the yield step and it is stated, not buried.
YIELD_SPREAD = 0.30

# Health-index family weights. Module-level so the I5 ablation can perturb them
# without editing the shipped path -- the ablation IS the justification for these
# numbers, so it must exercise the same code the submission uses.
HEALTH_W = {"level": 0.30, "growth": 0.25, "uniform": 0.20,
            "texture": 0.10, "persist": 0.15}

FLOOD_LO, FLOOD_HI = 3.0, 15.0  # [J8] rice flooding band, dB excess over Jun 06
RFI_DB = 15.0                    # [J8] above this, single-date spike is not a crop


def z(v, robust=True):
    """z-score that ignores NaN and (by default) resists the bright tails that
    [J8] showed are endemic on Jun 19. Median/MAD instead of mean/sd."""
    v = np.asarray(v, dtype="float64")
    ok = np.isfinite(v)
    if ok.sum() < 10:
        return np.zeros_like(v)
    if robust:
        c = np.median(v[ok])
        s = 1.4826 * np.median(np.abs(v[ok] - c))
    else:
        c, s = v[ok].mean(), v[ok].std()
    if not np.isfinite(s) or s <= 0:
        return np.zeros_like(v)
    out = np.zeros_like(v)
    out[ok] = np.clip((v[ok] - c) / s, -4, 4)
    return out


def crop_evidence(f):
    """Per-crop evidence scores in z units. Positive = favours that crop.

    Every term is a WITHIN-DATE, BETWEEN-FARM comparison or a within-farm
    temporal difference, so the ~+28 dB absolute calibration offset [J5]/[O1]
    cancels exactly. No absolute dB is ever used.

    The signatures are the ones Round 1 measured against ground truth [J4], read
    across from Sentinel-1 C-band VH to our X-band HH where the mechanism allows.
    """
    flood = (f["g0_db_20250619"] - f["g0_db_20250606"]).values   # [J8] rice channel
    growth = f["d_aug_jun06"].values if "d_aug_jun06" in f else (
        f["g0_db_20250814"] - f["g0_db_20250606"]).values
    aug = f["g0_db_20250814"].values          # peak vegetative biomass
    octl = f["g0_db_20251013"].values         # still standing in October?
    senes = f["d_oct_aug"].values             # + = brighter by Oct (bare/harvested)
    struct = f["glcm_resid_20250814"].values  # canopy texture, size-residualised
    cvv = f["cv_20250814"].values             # within-farm heterogeneity

    zf, zg, za, zo = z(flood), z(growth), z(aug), z(octl)
    zs, zt, zc = z(senes), z(struct), z(cvv)

    # Flooding is the one signature we independently validated [J8], so it gets
    # the largest single weight anywhere in this function. It is also the only
    # mechanism HH polarisation is genuinely good at (double-bounce off water
    # and bunds), which is why it survives single-pol where the others struggle.
    flood_hit = np.clip((flood - FLOOD_LO) / (FLOOD_HI - FLOOD_LO), 0, 1)
    flood_hit = np.where(np.isfinite(flood), flood_hit, 0.0)

    e = {}
    # Rice  -- transplanted into standing water in June, harvested by mid-October.
    e["Rice"] = 2.2 * flood_hit + 0.4 * zf + 0.3 * zs - 0.2 * zo
    # Cotton -- tall, woody, high-biomass, and the only crop still fully standing
    # in October (picking runs Oct-Jan). Highest August volume scattering.
    e["Cotton"] = 0.7 * zo + 0.5 * za + 0.3 * zg + 0.2 * zt - 0.6 * flood_hit
    # Groundnut -- low (~0.4 m) closed canopy on the drier, lighter soils; lifted
    # Oct-Nov so partly still present. Round 1 measured its NDVI coupling as
    # NEGATIVE [J4] -- it sits where the ground is bright and the canopy is thin.
    e["Groundnut"] = 0.5 * zo - 0.5 * za - 0.3 * zt + 0.2 * zg - 0.6 * flood_hit
    # Maize -- tall, high biomass at the August peak, then bare by October.
    e["Maize"] = 0.8 * za + 0.5 * zg + 0.4 * zs - 0.5 * zo - 0.4 * flood_hit
    # Bajra -- Round 1 found NO usable signal for pearl millet in ANY free layer
    # [J4], and the literature splits it only with dual-pol VH/VV. We therefore
    # give it almost no evidence of its own and let the prior place it. Saying so
    # is more honest than inventing a discriminator we cannot defend.
    e["Bajra"] = 0.3 * zs - 0.3 * za - 0.4 * zo - 0.2 * zc - 0.4 * flood_hit
    return e, flood


def fit_prior(P, prior, area, iters=4000, lr=0.35):
    """Bias the log-probabilities until the ARGMAX area shares match `prior`.

    First attempt matched the *soft* mass of each column, which converged fine
    and then did nothing: argmax of weak evidence still collapsed onto the two
    broad classes (rice landed at 1.2% area against a 10.6% prior). The soft
    marginal and the hard marginal are different objects, and the CSV needs the
    hard one, so the hard one is what we constrain.

    Additive bias in log space, multiplicative update on the realised share,
    damped by `lr`. Bias shifts the DECISION BOUNDARY between classes without
    touching the evidence ORDER inside a class -- the farm the physics ranks
    most-rice is still ranked most-rice, we are only choosing how many farms
    that ranking is allowed to claim.

    Weighted by AREA because the prior [J1] is an area share. Weighting by farm
    count instead would silently assume every crop has the same field size.

    Why constrain at all: [J3]. Free argmax on single-pol evidence is exactly
    what scored 5x worse than a flat prior in Round 1.
    """
    L = np.log(np.maximum(P, 1e-12))
    b = np.zeros(P.shape[1])
    A = area / area.sum()
    for _ in range(iters):
        lab = (L + b).argmax(axis=1)
        share = np.array([A[lab == j].sum() for j in range(P.shape[1])])
        # a class that no farm claims gets pushed up until it wins somewhere
        upd = np.log(prior / np.maximum(share, 1e-6))
        b = b + lr * np.clip(upd, -2, 2)
        if np.abs(share - prior).max() < 0.005:
            break
    Q = np.exp(L + b)
    return Q / np.maximum(Q.sum(axis=1, keepdims=True), 1e-12), b


def assign_crop(f, prior_shares):
    e, flood = crop_evidence(f)
    E = np.column_stack([e[c] for c in CROPS])
    E = np.where(np.isfinite(E), E, 0.0)
    # Temperature 1.0: the evidence is already in z units and deliberately weak.
    # A sharper softmax would manufacture confidence the data does not support.
    E -= E.max(axis=1, keepdims=True)
    P = np.exp(E)
    P /= P.sum(axis=1, keepdims=True)

    prior = np.array([prior_shares[c] for c in CROPS], dtype="float64")
    prior = prior / prior.sum()
    area = f["area_ha"].values.astype("float64")
    area = np.where(np.isfinite(area) & (area > 0), area, np.nanmedian(area))
    Q, b = fit_prior(P, prior, area)
    log("d4.prior_bias", **{c: round(float(x), 3) for c, x in zip(CROPS, b)})

    lab = np.array(CROPS)[Q.argmax(axis=1)]
    conf = Q.max(axis=1)
    return lab, conf, Q, flood


def health_index(f, crop):
    """Composite vigour score, 0-100, ranked WITHIN crop.

    Families kept (each independent after the I2 redundancy screen):
      level    -- August backscatter = peak canopy volume
      growth   -- Aug minus the DRY June 06 bare-soil reference. Jun 19 is not
                  usable here: its delta correlates -0.899 with its own level and
                  is 3x noisier, because it carries flooding, not growth [J8].
      uniform  -- within-farm CV. A uniform stand is a healthy stand; patchiness
                  means gaps, waterlogging or pest damage.
      texture  -- size-residualised GLCM entropy [H3]. Raw entropy measured plot
                  AREA (rho 0.95); the residual measures canopy structure.
      persist  -- season integral, i.e. how much canopy was held across the whole
                  series rather than in one lucky date.
    Excluded: ktex [H2] and subcoh [I1], both documented negatives. Including a
    feature we showed to be noise would cost more credibility than it adds signal.
    """
    parts = {
        "level":   z(f["g0_db_20250814"].values),
        "growth":  z((f["g0_db_20250814"] - f["g0_db_20250606"]).values),
        "uniform": -z(f["cv_20250814"].values),
        "texture": z(f["glcm_resid_20250814"].values),
        "persist": z(f["season_integral"].values),
    }
    W = HEALTH_W

    S = np.zeros(len(f))
    Wsum = np.zeros(len(f))
    for k, v in parts.items():
        if k not in W:            # a family the I5 ablation has removed
            continue
        ok = np.isfinite(v) & (v != 0)
        S[ok] += W[k] * v[ok]
        Wsum[ok] += W[k]
    S = np.where(Wsum > 0, S / np.maximum(Wsum, 1e-9), np.nan)

    # Rank within crop: cotton and groundnut differ by ~4 dB for reasons that have
    # nothing to do with health, so a pooled ranking would just re-measure crop.
    out = np.full(len(f), np.nan)
    for c in CROPS:
        m = (crop == c) & np.isfinite(S)
        if m.sum() >= 5:
            r = pd.Series(S[m]).rank(pct=True).values
            out[m] = 100.0 * r
        elif m.sum():
            out[m] = 50.0
    return out, S, parts


YIELD_T_PER_KG = 1e-3      # the submission column is TONNES/ha, see below


def yield_to_date(crop, health, district_yield):
    """TONNES/ha accumulated by the Oct 13 acquisition.

        yield = district_yield(crop) x completion(crop) x (1 + spread x zh) / 1000

    UNIT. The host's `Sokhda_Dummy_Submission.xlsx` carries
    `yield_estimate_to_date` values of 1.24-9.00, and their sample writeup says
    "estimated yield (tonnes/hectare)". The column is therefore t/ha, NOT the
    kg/ha of the APY district source, so the conversion happens here -- once, at
    the single point where the deliverable's unit is decided.

    The district figure is the only yield anchor that exists for this area [O5];
    it sets the LEVEL. SAR cannot measure absolute yield without calibration
    data, so what it contributes is the RELATIVE term -- which farm is doing
    better than its neighbours growing the same crop. Being explicit about that
    split is the honest framing: level from statistics, ranking from SAR.
    """
    out = np.full(len(crop), np.nan)
    for c in CROPS:
        m = crop == c
        if not m.any():
            continue
        # health is a within-crop percentile, so centre it at 50 and rescale to
        # roughly +/-2 sigma at the extremes.
        zh = (health[m] - 50.0) / 25.0
        rel = np.clip(1.0 + YIELD_SPREAD * zh, 0.4, 1.6)
        out[m] = district_yield[c] * COMPLETION[c] * rel * YIELD_T_PER_KG
    return out


def main():
    log("d4.start")
    f = pd.read_csv(RESULTS / "farm_features.csv")
    assert len(f) == 966, f"expected 966 farms, got {len(f)}"

    truth = pd.read_csv(AUX / "sokhda_r1_truth.csv").set_index("crop")
    prior = {c: float(truth.loc[c, "sokhda_share"]) for c in CROPS}
    apy = pd.read_csv(AUX / "vadodara_apy.csv").set_index("crop")
    dyield = {c: float(apy.loc[c, "yield_kg_ha_2022_23"]) for c in CROPS}
    log("d4.prior", **{c: round(prior[c], 4) for c in CROPS})

    crop, conf, Q, flood = assign_crop(f, prior)
    hi, raw, parts = health_index(f, crop)
    yld = yield_to_date(crop, hi, dyield)

    # --- fallbacks. No farm is ever dropped: coverage is 10 rubric points and a
    # missing row fails the required-elements gate outright. Every imputed farm
    # is flagged and counted, and the count goes in the writeup.
    rfi = np.isfinite(flood) & (flood >= RFI_DB)          # [J8] 19 saturating farms
    nosar = f["qc_flag"].astype(str).eq("no_sar_data").values
    bad = nosar | ~np.isfinite(hi)
    src = np.where(rfi, "rfi_flagged", np.where(bad, "imputed_village_median", "measured"))

    for c in CROPS:                      # crop-median health for the unmeasurable
        m = (crop == c)
        med = np.nanmedian(hi[m & ~bad]) if (m & ~bad).any() else 50.0
        hi = np.where(m & bad, med if np.isfinite(med) else 50.0, hi)
    hi = np.where(np.isfinite(hi), hi, 50.0)
    yld2 = yield_to_date(crop, hi, dyield)
    yld = np.where(np.isfinite(yld), yld, yld2)

    sub = pd.DataFrame({
        # The farm shapefile carries ID_1 = 22 for Sokhda, but the host's own
        # Sokhda_Dummy_Submission.xlsx -- presented as "the exact required
        # submission schema" -- uses village_id = 1. There is only one village,
        # so this identifier carries no information either way; we follow the
        # host's schema reference and record the shapefile value in d4_debug.
        "village_id": 1,
        "farm_id": f["farm_id"].values,
        "crop_type": crop,
        "health_index": np.round(hi, 2),
        "yield_estimate_to_date": np.round(yld, 3),   # t/ha, 3 dp: cotton is ~0.35
    })
    validate(sub)
    sub.to_csv(SUB, index=False)

    dbg = sub.copy()
    dbg["shapefile_village_id"] = f["village_id"].values   # ID_1 = 22, kept for traceability
    dbg["area_ha"] = f["area_ha"].values
    dbg["crop_confidence"] = np.round(conf, 4)
    dbg["flood_excess_db"] = np.round(flood, 2)
    dbg["health_raw_z"] = np.round(raw, 4)
    dbg["source"] = src
    for i, c in enumerate(CROPS):
        dbg[f"p_{c}"] = np.round(Q[:, i], 4)
    dbg.to_csv(DEBUG, index=False)

    report(sub, dbg, f, prior)
    log("d4.done", rows=len(sub), rfi=int(rfi.sum()), imputed=int(bad.sum()))


def validate(sub):
    """Hard schema gate. Fails loudly rather than writing a bad CSV -- a silently
    malformed submission is the one failure mode that costs everything."""
    cols = ["village_id", "farm_id", "crop_type", "health_index",
            "yield_estimate_to_date"]
    assert list(sub.columns) == cols, f"columns are {list(sub.columns)}"
    assert len(sub) == 966, f"{len(sub)} rows, expected 966"
    assert sub["farm_id"].is_unique, "duplicate farm_id"
    assert sorted(sub["farm_id"]) == list(range(1, 967)), "farm_id must be 1..966"
    bad = set(sub["crop_type"]) - set(CROPS)
    assert not bad, f"unknown crop_type: {bad}"
    for c in cols:
        assert sub[c].notna().all(), f"NaN in {c}"
    assert sub["health_index"].between(0, 100).all(), "health_index out of 0-100"
    assert (sub["yield_estimate_to_date"] >= 0).all(), "negative yield"
    # UNIT GUARD. The column is tonnes/ha (host dummy: 1.24-9.00). A kg/ha value
    # would sail through every other check here and be wrong by 1000x, which is
    # precisely the failure this gate exists to stop. No kharif crop yields
    # 25 t/ha, so anything above that is a unit error, not a modelling one.
    mx = float(sub["yield_estimate_to_date"].max())
    assert mx < 25.0, f"max yield {mx} t/ha -- looks like kg/ha, unit error"
    assert set(sub["village_id"]) == {1}, "village_id must be 1 (host dummy)"
    log("d4.schema", status="PASS", rows=len(sub), max_yield_t_ha=round(mx, 3))


def report(sub, dbg, f, prior):
    area = dbg.groupby("crop_type")["area_ha"].sum()
    n = sub["crop_type"].value_counts()
    tot = area.sum()
    print("\n=== CROP ASSIGNMENT vs prior ===")
    print(f"{'crop':<11}{'farms':>7}{'area_ha':>10}{'area%':>8}{'prior%':>8}{'conf':>7}")
    for c in CROPS:
        a = area.get(c, 0.0)
        cf = dbg.loc[dbg.crop_type == c, "crop_confidence"].median()
        print(f"{c:<11}{n.get(c,0):>7}{a:>10.1f}{100*a/tot:>8.1f}"
              f"{100*prior[c]:>8.1f}{cf:>7.2f}")
    print(f"\nmedian crop confidence {dbg.crop_confidence.median():.3f} "
          f"-- low BY DESIGN [J3]; hard confident labels are what failed in R1")

    print("\n=== HEALTH INDEX ===")
    print(sub.groupby("crop_type")["health_index"].describe()[
        ["count", "mean", "min", "50%", "max"]].round(1).to_string())

    print("\n=== YIELD TO DATE (TONNES/ha -- host schema unit) ===")
    print(sub.groupby("crop_type")["yield_estimate_to_date"].describe()[
        ["count", "mean", "min", "50%", "max"]].round(3).to_string())

    print("\n=== PROVENANCE ===")
    print(dbg["source"].value_counts().to_string())
    print(f"\nwrote {SUB}")


if __name__ == "__main__":
    main()
