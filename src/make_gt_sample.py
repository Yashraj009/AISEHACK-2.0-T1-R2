"""Build the field-work sheet for manual ground-truth collection.

Manual lookup is the only route to per-farm crop truth (see docs/VALIDATION_SOURCES.md),
so the job is to make it as small and as unbiased as possible.

Design choices that matter:

* STRATIFIED by our predicted crop, not random. A simple random sample of 100 would
  draw ~47 cotton and ~6 maize, and 6 maize cannot measure maize accuracy. Stratifying
  gives every class enough rows to say something, and the per-class results are
  re-weighted back to the true class shares when overall accuracy is computed.
* Includes the INDEPENDENT map's label and our confidence, but the collector should
  ideally not look at them while recording -- they are there so the analysis can
  stratify results afterwards (does agreement predict correctness?), not to anchor
  the person doing the lookup.
* Centroids in plain lat/lon so a parcel can be found in BhuNaksha or any map app.

Run:  python src/make_gt_sample.py [n_per_crop]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import AUX, CROPS, RESULTS, RESULTS_AUX, farm_centroids, log

SEED = 20260806          # fixed so the sample is reproducible and cannot be re-drawn
                         # after seeing an unfavourable result


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 20

    sub = pd.read_csv(RESULTS / "submission.csv")
    dbg = pd.read_csv(RESULTS / "d4_debug.csv")
    d = sub.merge(dbg[["farm_id", "crop_confidence", "area_ha", "source"]], on="farm_id")

    ind_p = RESULTS_AUX / "independent_crop.csv"
    if ind_p.exists():
        d = d.merge(pd.read_csv(ind_p)[["farm_id", "independent_crop"]], on="farm_id",
                    how="left")
    else:
        d["independent_crop"] = ""

    # UTM centroids -> lat/lon for field lookup
    from pyproj import Transformer
    cent = farm_centroids()[d.farm_id.values - 1]
    lon, lat = Transformer.from_crs(32643, 4326, always_xy=True).transform(
        cent[:, 0], cent[:, 1])
    d["lon"], d["lat"] = np.round(lon, 6), np.round(lat, 6)

    # survey numbers from the Gujarat parcel registry (src/fetch_dcs_parcels.py), so
    # the collector can go straight to AnyROR instead of hunting the plot on a map.
    sn = AUX / "farm_to_survey_number.csv"
    if sn.exists():
        d = d.merge(pd.read_csv(sn), on="farm_id", how="left")
        # prefer plots whose registry match is unambiguous -- a 30% overlap means we
        # are not confident WHICH survey number this farm is, and a wrong survey
        # number produces a wrong "truth" label, which is worse than no label
        d = d[d.overlap_frac.fillna(0) >= 0.5]
        print(f"restricted to {len(d)} farms with a confident (>=50%) registry match")

    # DEGENERATE GEOMETRY. Nine parcels are valid FIDs enclosing effectively no ground
    # (0 to 2.3e-7 ha) with centroids up to 835 km away; Orion documented ten. They carry a
    # legitimate row in the submission, but nobody can stand on a parcel of 5e-9 ha, so a
    # lookup spent on one is a lookup lost. One reached the staged field sheet (farm 19).
    n0 = len(d)
    d = d[d.area_ha > 1e-4]
    if len(d) < n0:
        print(f"dropped {n0 - len(d)} degenerate-geometry parcels (area < 1e-4 ha)")

    rng = np.random.default_rng(SEED)
    picks = []
    for c in CROPS:
        pool = d[(d.crop_type == c) & (d.source == "measured")]
        take = min(n_per, len(pool))
        picks.append(pool.iloc[rng.choice(len(pool), take, replace=False)])
    s = pd.concat(picks).sort_values("farm_id").reset_index(drop=True)

    # the blank columns the collector fills in
    s["vf12_crop"] = ""          # crop from Village Form 12 (Rice/Cotton/Maize/Bajra/Groundnut/Other)
    if "fpr_survey_number" not in s:
        s["fpr_survey_number"] = ""
        s["fpr_sub_survey_number"] = ""
        s["overlap_frac"] = np.nan
    s["vf12_season"] = "kharif2025"
    s["notes"] = ""

    cols = ["farm_id", "fpr_survey_number", "fpr_sub_survey_number", "overlap_frac",
            "lat", "lon", "area_ha", "crop_type", "independent_crop",
            "crop_confidence", "vf12_crop", "vf12_season", "notes"]
    out = AUX / "ground_truth_TEMPLATE.csv"
    s[cols].to_csv(out, index=False)

    print(f"wrote {out}  ({len(s)} farms, {n_per} per predicted crop)")
    print("\nfill in `vf12_crop` (and `survey_no` if you have it), keep the rest as-is,")
    print("save as data_aux/ground_truth_vf12.csv, then: python src/ingest_ground_truth.py")
    print("\nsample composition (by OUR predicted crop):")
    print(s.crop_type.value_counts().to_string())
    print(f"\ntrue class shares for re-weighting: "
          f"{ {c: round(100*(d.crop_type==c).mean(), 1) for c in CROPS} }")
    log("gt.sample", n=len(s), per_crop=n_per, seed=SEED)


if __name__ == "__main__":
    main()
