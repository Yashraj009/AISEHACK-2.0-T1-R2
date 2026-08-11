"""Pull Gujarat's Farmland Parcel Registry over Sokhda and join it to our 966 farms.

WHAT THIS SOLVES. Ground-truth crop per farm needs Village Form 12, and VF-12 is keyed
by SURVEY NUMBER -- which our farm shapefile does not carry. The documented workaround
was to find each parcel by eye on the BhuNaksha cadastral map, at 3-5 minutes a plot.

Krishi-DSS turns out to expose the registry directly. Its Angular bundle names a
GeoServer at kdss.da.gov.in/geoserver/krishi-dss, WFS is enabled, and layer `24_dcs`
(24 = Gujarat's LGD state code, dcs = Digital Crop Survey) returns per-parcel polygons
carrying `fpr_survey_number`, `fpr_sub_survey_number` and `fpr_unique_code`.

So the survey number for every farm can be read off automatically, and the manual step
collapses to "type this survey number into AnyROR and read the crop".

WHAT IT DOES NOT GIVE. The layer carries geometry and identifiers but NO crop attribute
-- crop per parcel lives behind `cropmapping-api`, which returns 401. So this removes
the hard half of the manual work, not all of it.

Everything here is a public, unauthenticated OGC endpoint. Nothing feeds submission.csv.

Run:  python src/fetch_dcs_parcels.py
"""
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import AUX, FARMS, RESULTS, VILLAGE, log

WFS = "https://kdss.da.gov.in/geoserver/krishi-dss/wfs"
LAYER = "krishi-dss:24_dcs"          # 24 = Gujarat LGD state code
PAGE = 1000


def fetch_parcels(bbox):
    """All registry parcels intersecting the bbox, paged."""
    feats, start, seen = [], 0, set()
    while True:
        # WFS 1.0.0 deliberately: on this server 2.0.0 returns zero features for the
        # same bbox (axis-order handling differs between versions), while 1.0.0 with
        # minx,miny,maxx,maxy works. Verified against a known-populated bbox.
        q = {"service": "WFS", "version": "1.0.0", "request": "GetFeature",
             "typeName": LAYER, "outputFormat": "application/json",
             "srsName": "EPSG:4326", "maxFeatures": PAGE, "startIndex": start,
             "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]},EPSG:4326"}
        url = WFS + "?" + urllib.parse.urlencode(q)
        with urllib.request.urlopen(url, timeout=180) as r:
            d = json.load(r)
        got = d.get("features", [])
        # `startIndex` is a GeoServer vendor extension, not WFS 1.0.0. If a proxy or a
        # different server ignored it, every page would return the same PAGE features,
        # `len(got) < PAGE` would never fire, and this would loop forever appending
        # duplicates at 180 s a request. Stop as soon as a page adds no NEW feature ids.
        new = [g for g in got if g.get("id") not in seen]
        seen.update(g.get("id") for g in got)
        feats += new
        log("dcs.page", start=start, got=len(got), new=len(new), total=len(feats))
        if len(got) < PAGE or not new:
            break
        start += PAGE
    return feats


def main():
    import geopandas as gpd
    from shapely.geometry import shape

    village = gpd.read_file(VILLAGE).to_crs(4326)
    bbox = village.total_bounds                     # minx, miny, maxx, maxy
    feats = fetch_parcels(bbox)
    if not feats:
        raise SystemExit("no parcels returned -- the layer or endpoint may have changed")

    parc = gpd.GeoDataFrame(
        [f["properties"] for f in feats],
        geometry=[shape(f["geometry"]) for f in feats], crs=4326)
    # make_valid first, then drop anything still unusable. The previous expression
    # `notna & is_valid | notna` parses as `(notna & is_valid) | notna` == `notna`,
    # so it filtered nothing and only the make_valid() below saved the overlay.
    parc = parc[parc.geometry.notna()].copy()
    parc["geometry"] = parc.geometry.make_valid()
    parc = parc[~parc.geometry.is_empty]
    log("dcs.fetched", parcels=len(parc),
        with_survey=int(parc["fpr_survey_number"].notna().sum()))

    farms = gpd.read_file(FARMS).to_crs(4326)
    farms["geometry"] = farms.geometry.make_valid()
    farms["farm_id"] = farms["FID"].astype(int)

    # Join by LARGEST OVERLAP, not centroid-in-polygon. The two datasets are digitised
    # independently, so a farm centroid can easily fall in a neighbouring registry
    # parcel; area of intersection is the robust criterion and it also gives us an
    # overlap fraction to report confidence with.
    fu = farms.to_crs(32643)
    pu = parc.to_crs(32643)
    inter = gpd.overlay(fu[["farm_id", "geometry"]], pu, how="intersection",
                        keep_geom_type=False)
    inter["ov_m2"] = inter.area
    best = inter.sort_values("ov_m2").groupby("farm_id").tail(1)

    fu["area_m2"] = fu.area
    out = fu[["farm_id", "area_m2"]].merge(
        best[["farm_id", "ov_m2", "fpr_survey_number", "fpr_sub_survey_number",
              "fpr_unique_code", "fpr_plot_area", "fpr_village_lgd_code"]],
        on="farm_id", how="left")
    out["overlap_frac"] = (out.ov_m2 / out.area_m2).round(3)
    out = out.drop(columns=["ov_m2", "area_m2"])

    matched = out.fpr_survey_number.notna()
    good = matched & (out.overlap_frac >= 0.5)
    p = AUX / "farm_to_survey_number.csv"
    out.to_csv(p, index=False)

    print("\n" + "=" * 68)
    print("FARM -> SURVEY NUMBER (Gujarat Farmland Parcel Registry via Krishi-DSS)")
    print("=" * 68)
    print(f"  registry parcels over the village : {len(parc)}")
    print(f"  farms matched to a parcel         : {matched.sum()} / {len(out)}")
    print(f"  matched with >=50% overlap        : {good.sum()}")
    print(f"  median overlap fraction           : {out.overlap_frac.median():.2f}")
    print(f"\n  wrote {p}")
    print("\n  This replaces the manual BhuNaksha step: the survey number for each farm\n"
          "  is now known, so VF-12 collection is 'type the number into AnyROR and read\n"
          "  the crop' rather than 'find this plot by eye on a cadastral map'.")
    log("dcs.join", matched=int(matched.sum()), good=int(good.sum()),
        parcels=len(parc))


if __name__ == "__main__":
    main()
