"""e13 -- Google Earth Engine, priced against our own ceiling before anything is adopted.

e12 established the screening rule: a covariate constant within a cell of side L can explain
at most 0.685 of within-crop health variation at 100 m, 0.226 at 250 m, and 0.000 beyond
about 11 km. GEE is a catalogue, not a dataset, so only its 10 m products clear that bar.

Three are tested, each against a question we actually have:

  T1  DYNAMIC WORLD 10 m, Jun-Oct 2025 -- contemporaneous with our SAR.
      THE GAP IT FILLS: we have no non-crop screen. Orion removes 37 parcels / 21.2 ha
      before clustering ("any-date mean > -10 dB, or CoV > 2.0") and we remove none. A
      farm polygon containing a building, a pond or a stand of trees still gets a crop
      label and a health score from us today.

  T2  WORLDCEREAL 2021 temporarycrops + maize.
      A 2021 product cannot label a 2025 crop -- rotation moves maize every year. So it is
      tested the only way it can honestly be used: `temporarycrops` as a STABLE cropland
      mask, and `maize` only as a weak prior whose agreement with our labels must beat
      chance to mean anything.

  T3  WORLDCEREAL irrigation.
      Unanticipated and relevant: KHARIF_ANCHORS.md turned on irrigated summer bajra
      yielding 1.6x rainfed kharif bajra. If irrigated parcels are identifiable here, that
      is a per-farm handle on the very mechanism the anchor correction rests on.

NOTHING IS ADOPTED HERE. Each test can fail, and a ceiling is an upper bound rather than a
promise -- Megalodon fetched ten SoilGrids properties against 0.226 of headroom and rejected
all of them on measurement.

Auth: uses the existing refresh token in ~/.config/earthengine/credentials with GCP project
472723809152. No credential is read from or written to this repo.

Run:  py -3.12 post-r2/experiments/e13_gee.py
"""
import os
import sys
from pathlib import Path

os.environ.pop("PROJ_LIB", None)

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from common import FARMS, RESULTS  # noqa: E402

OUT = ROOT / "post-r2" / "results" / "e13_gee"
OUT.mkdir(parents=True, exist_ok=True)
CACHE = OUT / "farm_gee.csv"
PROJECT = "472723809152"
BATCH = 120
LOG = []


def say(t=""):
    print(t)
    LOG.append(t)


def fetch():
    """Per-farm zonal means for the three 10 m products. Cached after the first run."""
    if CACHE.exists():
        return pd.read_csv(CACHE)
    import ee
    import geopandas as gpd
    ee.Initialize(project=PROJECT)

    farms = gpd.read_file(FARMS).to_crs(4326)
    fid = farms["FID"].astype(int).to_numpy()

    aoi = ee.Geometry.Rectangle(list(farms.total_bounds))

    # Dynamic World: modal class and mean crop probability over the kharif window
    dw = (ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
          .filterBounds(aoi).filterDate("2025-06-01", "2025-10-31"))
    dw_img = ee.Image.cat(
        dw.select("label").mode().rename("dw_mode"),
        dw.select("crops").mean().rename("dw_crops"),
        dw.select("built").mean().rename("dw_built"),
        dw.select("water").mean().rename("dw_water"),
        dw.select("trees").mean().rename("dw_trees"))

    wc = ee.ImageCollection("ESA/WorldCereal/2021/MODELS/v100")

    def wc_band(product, name):
        c = wc.filter(ee.Filter.eq("product", product)).select("classification")
        return ee.Image(c.mosaic()).rename(name)

    img = ee.Image.cat(dw_img,
                       wc_band("temporarycrops", "wc_crop"),
                       wc_band("maize", "wc_maize"),
                       wc_band("irrigation", "wc_irrig"))

    rows = []
    for i in range(0, len(farms), BATCH):
        sl = farms.iloc[i:i + BATCH]
        feats = [ee.Feature(ee.Geometry(g.__geo_interface__), {"fid": int(f)})
                 for g, f in zip(sl.geometry, fid[i:i + BATCH])]
        fc = ee.FeatureCollection(feats)
        red = img.reduceRegions(collection=fc, reducer=ee.Reducer.mean(), scale=10)
        for ft in red.getInfo()["features"]:
            rows.append(ft["properties"])
        print(f"  fetched {min(i + BATCH, len(farms))}/{len(farms)}")
    d = pd.DataFrame(rows).rename(columns={"fid": "farm_id"})
    d.to_csv(CACHE, index=False)
    return d


DW_CLASS = {0: "water", 1: "trees", 2: "grass", 3: "flooded_veg", 4: "crops",
            5: "shrub_scrub", 6: "built", 7: "bare", 8: "snow_ice"}


def main():
    g = fetch()
    say("=" * 78)
    say("SOURCE")
    say("=" * 78)
    say(f"  per-farm zonal means for {len(g)} farms at 10 m")
    say("  Dynamic World Jun-Oct 2025 (20 images, contemporaneous with our SAR)")
    say("  WorldCereal 2021 v100: temporarycrops, maize, irrigation")
    say("")

    s = pd.read_csv(RESULTS / "submission.csv")
    f = pd.read_csv(RESULTS / "farm_features.csv")
    w = pd.read_csv(RESULTS / "tables" / "witness.csv")
    d = s.merge(f, on="farm_id").merge(w, on="farm_id").merge(g, on="farm_id", how="left")

    # ---------------- T1 -------------------------------------------------
    say("=" * 78)
    say("T1  DYNAMIC WORLD -- do we carry non-crop parcels we never screened?")
    say("=" * 78)
    if "dw_mode" not in d or d.dw_mode.isna().all():
        say("  no Dynamic World values returned")
    else:
        d["dw_label"] = d.dw_mode.round().map(DW_CLASS)
        vc = d.dw_label.value_counts()
        say(f"  {'modal DW class':<16}{'farms':>7}{'% area':>9}{'our median NDVI':>18}")
        for k, n in vc.items():
            sub = d[d.dw_label == k]
            say(f"  {str(k):<16}{n:>7}{100 * sub.area_ha.sum() / d.area_ha.sum():>8.1f}%"
                f"{sub.s2_ndvi_20251013.median():>18.3f}")
        noncrop = d[~d.dw_label.isin(["crops", "grass"]) & d.dw_label.notna()]
        say("")
        say(f"  parcels whose modal 2025 land cover is NOT crops/grass: {len(noncrop)}"
            f" ({100 * noncrop.area_ha.sum() / d.area_ha.sum():.1f}% of area)")
        say(f"  Orion screened 37 parcels / 21.2 ha on a SAR-only rule. We screen none.")
        if len(noncrop) > 3:
            say("")
            say(f"  {'':<22}{'non-crop':>11}{'rest':>11}")
            for col, lab in (("s2_ndvi_20251013", "NDVI 13 Oct"),
                             ("g0_db_20251013", "gamma0 dB"),
                             ("cv_20251013", "within-farm CV"),
                             ("health_index", "our health index")):
                say(f"  {lab:<22}{noncrop[col].median():>11.3f}"
                    f"{d[~d.index.isin(noncrop.index)][col].median():>11.3f}")
            say("")
            say("  If these parcels look different on a sensor we never read, they are")
            say("  contaminating a health index that assumes every parcel is a field.")

    # ---------------- T2 -------------------------------------------------
    say("")
    say("=" * 78)
    say("T2  WORLDCEREAL 2021 -- cropland mask, and maize as a weak prior")
    say("=" * 78)
    if "wc_crop" not in d or d.wc_crop.isna().all():
        say("  no WorldCereal values returned")
    else:
        say(f"  temporarycrops (100 = cropland): median {d.wc_crop.median():.1f}, "
            f"{100 * (d.wc_crop > 50).mean():.1f}% of farms above 50")
        say(f"  irrigation     : median {d.wc_irrig.median():.1f}, "
            f"{100 * (d.wc_irrig > 50).mean():.1f}% above 50")
        say(f"  maize          : median {d.wc_maize.median():.1f}, "
            f"{100 * (d.wc_maize > 50).mean():.1f}% above 50")
        say("")
        m = d.dropna(subset=["wc_maize"])
        ours = (m.crop_type == "Maize")
        theirs = (m.wc_maize > 50)
        if theirs.sum() > 0 and ours.sum() > 0:
            po = float((ours == theirs).mean())
            pe = float(ours.mean() * theirs.mean() + (1 - ours.mean()) * (1 - theirs.mean()))
            k = (po - pe) / (1 - pe) if pe < 1 else np.nan
            say(f"  maize agreement: raw {100 * po:.1f}%, Cohen's kappa {k:+.3f}")
            say(f"    ours {int(ours.sum())} maize farms, WorldCereal {int(theirs.sum())}")
            say("    kappa near 0 means a 2021 maize map says nothing about our 2025 labels,")
            say("    which is what crop rotation predicts. It is a check, not a failure.")
        else:
            say("  WorldCereal flags no maize in this village, so no agreement test is possible.")

    # ---------------- T3 -------------------------------------------------
    say("")
    say("=" * 78)
    say("T3  IRRIGATION -- a per-farm handle on the anchor mechanism?")
    say("=" * 78)
    if "wc_irrig" in d and d.wc_irrig.notna().any() and d.wc_irrig.std() > 0:
        from scipy import stats
        for col, lab in (("health_index", "our health index"),
                         ("s2_ndvi_20251013", "NDVI 13 Oct (withheld)"),
                         ("yield_estimate_to_date", "our yield")):
            r, p = stats.spearmanr(d.wc_irrig, d[col], nan_policy="omit")
            say(f"  rho(irrigation, {lab:<26}) = {r:+.3f}  p = {p:.3g}")
        say("")
        say("  KHARIF_ANCHORS.md rests on irrigated summer bajra yielding 1.6x rainfed")
        say("  kharif bajra. A per-farm irrigation flag would let that mechanism be applied")
        say("  per parcel rather than per crop -- IF it varies here and tracks something.")
    else:
        say("  irrigation layer is constant or absent across the village -- no signal to use.")

    d_out = [c for c in ("farm_id", "crop_type", "health_index", "dw_mode", "dw_crops",
                         "dw_built", "dw_water", "dw_trees", "wc_crop", "wc_maize",
                         "wc_irrig") if c in d]
    d[d_out].to_csv(OUT / "farm_gee_joined.csv", index=False)
    (OUT / "report.txt").write_text("\n".join(LOG) + "\n", encoding="utf8")
    print(f"\nwritten: {OUT}")


if __name__ == "__main__":
    main()
