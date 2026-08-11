"""Validate our crop map against ANY external per-parcel crop layer.

Written to run the moment a Krishi-DSS token (or any other source) yields a crop layer,
so no time is lost building the comparison then. It is source-agnostic: give it a table
or a GeoJSON with a crop label and either a farm_id or a geometry, and it answers the
only two questions that matter.

THE ALIGNMENT GATE COMES FIRST, AND IT CAN REFUSE.
The user's condition for trusting an external layer was that it must line up with our
farms properly. So this does not compare labels until geometry has passed: each farm is
matched to the external parcel it overlaps MOST, and any match below `--min-overlap`
(default 0.5) is discarded rather than compared. A label attached to the wrong polygon is
worse than no label, because it produces a confident wrong accuracy.

THE COMPARISON IS THEN CHANCE-CORRECTED.
Raw agreement is meaningless when one class holds 43% of the area -- "always predict
cotton" scores 43%. So Cohen's kappa and a majority-class baseline are always reported
alongside, and per-class lift is shown against that class's own marginal.

WHAT THE RESULT MEANS depends on what the source IS, and the script asks you to say:
  --kind survey  : surveyed ground observation (e.g. Digital Crop Survey) -> ACCURACY
  --kind model   : another model's output -> AGREEMENT between two independent methods
Conflating those two would overclaim, so the wording of the verdict changes with it.

Usage:
  python src/validate_external_layer.py --csv ext.csv --crop-col crop --kind model
  python src/validate_external_layer.py --geojson ext.json --crop-col crop_name --kind survey
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CROPS, FARMS, RESULTS, log

# free-text crop names -> our five classes (English + Gujarati transliterations)
ALIAS = {"paddy": "Rice", "dhan": "Rice", "rice": "Rice",
         "kapas": "Cotton", "cotton": "Cotton",
         "makai": "Maize", "corn": "Maize", "maize": "Maize",
         "bajri": "Bajra", "pearl millet": "Bajra", "bajra": "Bajra", "millet": "Bajra",
         "mungfali": "Groundnut", "peanut": "Groundnut", "groundnut": "Groundnut"}


def norm(v):
    s = str(v).strip().lower()
    if not s or s in ("nan", "none"):
        return None
    for k, c in ALIAS.items():
        if k in s:
            return c
    return "Other"


def spatial_join(ext_gdf, crop_col, min_overlap):
    """Match each farm to the external parcel it overlaps most. Geometry gate."""
    import geopandas as gpd
    farms = gpd.read_file(FARMS).to_crs(32643)
    farms["geometry"] = farms.geometry.make_valid()
    farms["farm_id"] = farms["FID"].astype(int)
    farms["area_m2"] = farms.area

    ext = ext_gdf.to_crs(32643).copy()
    ext["geometry"] = ext.geometry.make_valid()
    ext = ext[[crop_col, "geometry"]].rename(columns={crop_col: "_extcrop"})

    inter = gpd.overlay(farms[["farm_id", "area_m2", "geometry"]], ext,
                        how="intersection", keep_geom_type=False)
    inter["ov"] = inter.area
    best = inter.sort_values("ov").groupby("farm_id").tail(1)
    best["overlap_frac"] = best.ov / best.area_m2

    n_any = len(best)
    good = best[best.overlap_frac >= min_overlap]
    print(f"  ALIGNMENT GATE: {n_any}/{len(farms)} farms touch an external parcel; "
          f"{len(good)} clear the {min_overlap:.0%} overlap bar "
          f"(median overlap {best.overlap_frac.median():.2f})")
    if len(good) < 30:
        raise SystemExit("  REFUSED: too few well-aligned farms to compare. The layers do "
                         "not line up; a comparison here would be noise.")
    return good[["farm_id", "_extcrop", "overlap_frac"]]


def compare(df, kind):
    """df: farm_id, ours, theirs. Chance-corrected, per-class, honest wording."""
    ours, theirs = df.ours.values, df.theirs.values
    po = float((ours == theirs).mean())
    pe = sum((ours == c).mean() * (theirs == c).mean() for c in CROPS)
    kappa = (po - pe) / (1 - pe) if pe < 1 else np.nan
    maj = pd.Series(theirs).value_counts().idxmax()
    base = float((theirs == maj).mean())

    print(f"\n  n compared            {len(df)}")
    print(f"  raw agreement         {100*po:.1f}%")
    print(f"  chance level          {100*pe:.1f}%")
    print(f"  Cohen's kappa         {kappa:+.3f}")
    print(f"  majority baseline     {100*base:.1f}%  (always predict {maj})")

    print("\n  per class (their label as reference):")
    for c in CROPS:
        m = theirs == c
        if m.sum():
            rec = float((ours[m] == c).mean())
            marg = float((ours == c).mean())
            print(f"    {c:11s} recall {100*rec:5.1f}%  our marginal {100*marg:5.1f}%  "
                  f"lift {rec/max(marg,1e-9):4.2f}x   n {int(m.sum()):4d}")

    print("\n  rows = theirs, cols = ours:")
    print(pd.crosstab(theirs, ours).to_string())

    # NaN must not fall through to "substantial": when both maps are entirely one class
    # every comparison below is False, and the chain would have reported an undefined
    # kappa as the strongest possible agreement -- the exact overclaim this module exists
    # to prevent.
    if not np.isfinite(kappa):
        strength = "UNDEFINED (degenerate: one class dominates entirely)"
    else:
        strength = ("negligible" if kappa < 0.2 else "fair" if kappa < 0.4
                    else "moderate" if kappa < 0.6 else "substantial")
    if not np.isfinite(kappa):
        print("
  VERDICT: NO CONCLUSION -- kappa is undefined on this comparison.")
        return dict(n=len(df), raw=round(po, 4), kappa=None,
                    chance=round(pe, 4), baseline=round(base, 4), kind=kind)
    if kind == "survey":
        print(f"\n  VERDICT: measured ACCURACY against surveyed ground observation — "
              f"kappa {kappa:+.3f} ({strength}).")
        print("  This is a real accuracy figure and belongs in the writeup as one.")
    else:
        print(f"\n  VERDICT: AGREEMENT between two independent models — "
              f"kappa {kappa:+.3f} ({strength}).")
        print("  NOT an accuracy: their layer is a model too. Agreement is evidence that")
        print("  two methods converge; disagreement localises where ours is weak.")
    return dict(n=len(df), raw=round(po, 4), kappa=round(float(kappa), 4),
                chance=round(pe, 4), baseline=round(base, 4), kind=kind)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv"); ap.add_argument("--geojson")
    ap.add_argument("--crop-col", required=True)
    ap.add_argument("--id-col", default=None,
                    help="if the source already carries our farm_id, skip the spatial join")
    ap.add_argument("--kind", choices=["survey", "model"], required=True)
    ap.add_argument("--min-overlap", type=float, default=0.5)
    a = ap.parse_args()

    sub = pd.read_csv(RESULTS / "submission.csv")[["farm_id", "crop_type"]]

    print("=" * 72)
    print("EXTERNAL CROP-LAYER VALIDATION")
    print("=" * 72)

    if a.geojson:
        import geopandas as gpd
        ext = gpd.read_file(a.geojson)
        j = spatial_join(ext, a.crop_col, a.min_overlap)
        j["theirs"] = j["_extcrop"].map(norm)
    elif a.csv:
        t = pd.read_csv(a.csv)
        if not a.id_col:
            raise SystemExit("--csv needs --id-col (or use --geojson for a spatial join)")
        j = t.rename(columns={a.id_col: "farm_id", a.crop_col: "_extcrop"})
        j["theirs"] = j["_extcrop"].map(norm)
        print("  (tabular source keyed by farm_id -- no spatial join needed)")
    else:
        raise SystemExit("give --csv or --geojson")

    d = j.merge(sub, on="farm_id").rename(columns={"crop_type": "ours"})
    n_other = int((d.theirs == "Other").sum())
    d = d[d.theirs.notna() & (d.theirs != "Other")]
    if n_other:
        print(f"  {n_other} parcels carry a crop outside our five classes -- excluded")

    res = compare(d, a.kind)
    out = RESULTS / "external_layer_validation.csv"
    pd.DataFrame([res]).to_csv(out, index=False)
    d.to_csv(RESULTS / "external_layer_matched.csv", index=False)
    print(f"\n  wrote {out}")
    log("external_validate", **res)


if __name__ == "__main__":
    main()
