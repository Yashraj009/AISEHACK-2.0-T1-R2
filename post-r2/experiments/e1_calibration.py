"""e1 -- what does the calibration correction actually do to the submission?

Two shortlisted teams form brightness with the scale factor SQUARED:

    Coding Bits   sigma0 = (SF * |A|)^2 * sin(theta)
    Project Orion beta0  = |I+jQ|^2 * SF^2, citing capella-reader's
                           `beta0_complex = SF * DN`

We ship `beta0 = SF * |z|^2`. Our median gamma0 is +7.2 to +9.3 dB, which would mean a
field returning five times the power it receives; under SF^2 the same rasters read
-18.2 to -19.8 dB, against Coding Bits' -20.2 and Orion's -21.5.

The correction is exactly one multiply by SF per date, because the scale factor is a
per-SCENE constant. So the whole submission can be rebuilt without touching a raster:
scale the per-date linear power, re-derive the temporal block exactly as farm_stats.py
does, and re-run the real d4_submission.main() against the corrected frame.

Nothing here writes to results/ or docs/. The shipped Round 2 artefacts are read-only
inputs; every output lands in post-r2/results/.

Run:  py -3.12 post-r2/experiments/e1_calibration.py
"""
import os
import sys
from pathlib import Path

os.environ.pop("PROJ_LIB", None)

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import common
from common import DATES, RESULTS

OUT = ROOT / "post-r2" / "results" / "e1_calibration"
OUT.mkdir(parents=True, exist_ok=True)

# Scale factors, read from each scene's own metadata rather than hard-coded, so this
# stays correct if the dataset is ever re-issued.
def scale_factors():
    import json
    sf = {}
    for d in DATES:
        p = common.slc_path(d)
        meta = json.loads(Path(str(p).replace(".tif", "_extended.json")).read_text(encoding="utf8"))
        sf[d] = float(meta["collect"]["image"]["scale_factor"])
    return sf


def correct(f, sf):
    """Apply beta0 = SF^2|z|^2 instead of SF|z|^2, and re-derive everything downstream.

    Per-date power is multiplied by SF; dB gains 10log10(SF). CV, the K-distribution
    texture and the pixel counts are all ratios or counts, so a scalar gain leaves them
    untouched -- which is exactly why most of the health index survives this.
    """
    g = f.copy()
    for d in DATES:
        g[f"g0_lin_{d}"] = f[f"g0_lin_{d}"] * sf[d]
        g[f"g0_db_{d}"] = f[f"g0_db_{d}"] + 10.0 * np.log10(sf[d])

    # re-derive the temporal block exactly as src/farm_stats.py does
    db = g[[f"g0_db_{d}" for d in DATES]].values
    lin = g[[f"g0_lin_{d}" for d in DATES]].values
    g["d_aug_jun19"] = db[:, 2] - db[:, 1]
    g["d_oct_aug"] = db[:, 3] - db[:, 2]
    g["d_oct_jun"] = db[:, 3] - db[:, 0]
    jun = np.nanmean(db[:, :2], axis=1)
    g["jun_baseline_db"] = jun
    g["ref_aug"] = db[:, 2] - jun
    g["ref_oct"] = db[:, 3] - jun
    g["temporal_cv"] = np.nanstd(lin, axis=1) / np.nanmean(lin, axis=1)
    g["temporal_range_db"] = np.nanmax(db, axis=1) - np.nanmin(db, axis=1)
    doy = np.array([157, 170, 226, 286], dtype="float64")
    g["season_integral"] = np.trapezoid(lin, doy, axis=1)
    return g


def rebuild(frame):
    """Run the SHIPPED d4_submission.main() against a corrected feature frame.

    The stage is not edited. Its two module-level path constants are redirected so it
    reads our frame and writes into post-r2/, leaving results/ untouched.
    """
    stage = OUT / "stage"
    stage.mkdir(exist_ok=True)
    frame.to_csv(stage / "farm_features.csv", index=False)

    import d4_submission as d4
    d4.RESULTS = stage
    d4.OUTPUT = stage
    d4.SUB = stage / "submission.csv"
    d4.DEBUG = stage / "d4_debug.csv"
    d4.main()
    return pd.read_csv(stage / "submission.csv")


def main():
    sf = scale_factors()
    print("scale factors, and the dB each date is inflated by as shipped:")
    for d in DATES:
        print(f"  {d}   SF={sf[d]:.6e}   inflation +{-10 * np.log10(sf[d]):.2f} dB")
    spread = 10 * np.log10(max(sf.values()) / min(sf.values()))
    print(f"  spread across dates: {max(sf.values()) / min(sf.values()):.3f}x = {spread:.2f} dB")
    print("  -> that spread is the part that does NOT cancel in a cross-date difference\n")

    f = pd.read_csv(RESULTS / "farm_features.csv")
    g = correct(f, sf)
    g.to_csv(OUT / "farm_features_calibrated.csv", index=False)

    shipped = pd.read_csv(RESULTS / "submission.csv")
    rebuilt = rebuild(g)
    m = shipped.merge(rebuilt, on="farm_id", suffixes=("_ship", "_cal"))
    assert len(m) == 966, len(m)

    print("=" * 72)
    print("EFFECT ON THE SUBMISSION")
    print("=" * 72)

    same = (m.crop_type_ship == m.crop_type_cal).sum()
    print(f"\ncrop_type      {same}/966 unchanged ({100 * same / 966:.1f}%)")
    if same < 966:
        ch = m[m.crop_type_ship != m.crop_type_cal]
        print("  reassignments:")
        for (a, b), k in ch.groupby(["crop_type_ship", "crop_type_cal"]).size().items():
            print(f"    {a:<10} -> {b:<10} {k:>3}")

    for col in ("health_index", "yield_estimate_to_date"):
        a, b = m[f"{col}_ship"], m[f"{col}_cal"]
        d = (b - a).abs()
        rho = spearmanr(a, b).statistic
        print(f"\n{col}")
        print(f"  Spearman(shipped, calibrated) = {rho:.4f}")
        print(f"  |delta|  median {d.median():.3f}   p90 {d.quantile(.9):.3f}   max {d.max():.3f}")
        r = (a.rank() - b.rank()).abs()
        print(f"  rank shift: median {r.median():.0f}, >50 ranks {(r > 50).sum()}, "
              f"> 100 ranks {(r > 100).sum()}")

    ship_t = float((shipped.yield_estimate_to_date * 0 + 1).sum())  # placeholder guard
    print("\nvillage production, t (area-weighted sum yield*area):")
    ar = pd.read_csv(RESULTS / "farm_features.csv")[["farm_id", "area_ha"]]
    for lab, sub in (("shipped", shipped), ("calibrated", rebuilt)):
        j = sub.merge(ar, on="farm_id")
        print(f"  {lab:<11} {(j.yield_estimate_to_date * j.area_ha).sum():8.1f} t")

    m.to_csv(OUT / "submission_diff.csv", index=False)
    print(f"\nwritten: {OUT}")
    print("NOTE: results/submission.csv is untouched -- this is a parallel rebuild.")


if __name__ == "__main__":
    main()
