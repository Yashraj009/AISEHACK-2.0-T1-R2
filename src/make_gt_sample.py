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
from common import AUX, CROPS, RESULTS, farm_centroids, log

SEED = 20260806          # fixed so the sample is reproducible and cannot be re-drawn
                         # after seeing an unfavourable result


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 20

    sub = pd.read_csv(RESULTS / "submission.csv")
    dbg = pd.read_csv(RESULTS / "d4_debug.csv")
    d = sub.merge(dbg[["farm_id", "crop_confidence", "area_ha", "source"]], on="farm_id")

    ind_p = RESULTS / "independent_crop.csv"
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

    rng = np.random.default_rng(SEED)
    picks = []
    for c in CROPS:
        pool = d[(d.crop_type == c) & (d.source == "measured")]
        take = min(n_per, len(pool))
        picks.append(pool.iloc[rng.choice(len(pool), take, replace=False)])
    s = pd.concat(picks).sort_values("farm_id").reset_index(drop=True)

    # the blank columns the collector fills in
    s["vf12_crop"] = ""          # crop from Village Form 12 (Rice/Cotton/Maize/Bajra/Groundnut/Other)
    s["survey_no"] = ""          # BhuNaksha survey number, for traceability
    s["vf12_season"] = "kharif2025"
    s["notes"] = ""

    cols = ["farm_id", "lat", "lon", "area_ha", "crop_type", "independent_crop",
            "crop_confidence", "survey_no", "vf12_crop", "vf12_season", "notes"]
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
