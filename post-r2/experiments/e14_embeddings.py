"""e14 -- AlphaEarth / Satellite Embedding v1, tested against the ONE thing that limits us.

WHY THIS AND NOT ANOTHER LAND-COVER PRODUCT. Three independent measurements now agree that
our limiting error is the crop label, not measurement noise: sampling noise is 15.9% of
between-farm signal (e11), yield is eta^2 = 0.820 explained by the label (e4), and six teams'
labels agree at kappa = 0.060 (e4). e13 then showed that a 10 m *categorical* product fails on
our geometry -- Dynamic World's modal class is half a farm-size detector at 0.18 ha.

The Satellite Embedding dataset is the one product that is 10 m, contemporaneous (2025), and
CONTINUOUS -- 64 float bands per pixel encoding a whole year of Sentinel-1, Sentinel-2,
Landsat, DEM and climate. A mean over 18 pixels of a continuous vector is a well-posed
quantity; a mode over 18 pixels of a categorical raster is not. That is the specific reason
this is worth a test after e13 rejected Dynamic World.

INDEPENDENCE. Our crop labels come from Capella X-band HH alone. The embedding sees no
Capella. Agreement between the two is genuine cross-sensor corroboration, and it is the first
such evidence available to us -- the six-team consensus (e4) supplied none.

CIRCULARITY, STATED UP FRONT. The 2025 embedding ingests Sentinel-2 2025, which contains our
withheld witness (s2_ndvi_20251013). So the witness cannot score anything derived from these
embeddings. That test is deliberately omitted rather than reported.

  T1  Does the embedding carry crop-label information at all?
      Spatially BLOCKED 5-fold CV (KMeans on centroids, so folds are geographic blocks and no
      fold can win by memorising a neighbourhood). Metric is Cohen's kappa, not raw accuracy
      -- e13's WorldCereal test is the cautionary case, where 91.6% raw hid kappa = -0.010.

  T2  THE e13 CONTROL, RUN AGAIN. Is any apparent skill really farm size? Dynamic World looked
      strong until area was matched. Same trap checked here: kappa within area deciles, plus a
      size-only classifier as a floor.

  T3  Label permutation control. Anything the pipeline can "learn" from shuffled labels is CV
      leakage, not signal.

  T4  Within-crop health residual. e12 priced a 10 m covariate's ceiling at 0.685. How much of
      that does the embedding actually reach? A ceiling is an upper bound, not a promise.

NOTHING IS ADOPTED HERE. This decides only whether direction #1 for Round 3 is real.

Run:  py -3.12 post-r2/experiments/e14_embeddings.py
"""
import os
import sys
from pathlib import Path

os.environ.pop("PROJ_LIB", None)

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from common import FARMS, RESULTS, farm_centroids  # noqa: E402

OUT = ROOT / "post-r2" / "results" / "e14_embeddings"
OUT.mkdir(parents=True, exist_ok=True)
CACHE = OUT / "farm_embed.csv"
PROJECT = "472723809152"
BATCH = 60
BANDS = [f"A{i:02d}" for i in range(64)]
SEED = 0
LOG = []


def say(t=""):
    print(t)
    LOG.append(t)


def fetch():
    if CACHE.exists():
        return pd.read_csv(CACHE)
    import ee
    import geopandas as gpd
    ee.Initialize(project=PROJECT)

    farms = gpd.read_file(FARMS).to_crs(4326)
    fid = farms["FID"].astype(int).to_numpy()
    aoi = ee.Geometry.Rectangle(list(farms.total_bounds))
    img = ee.Image(ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL")
                   .filterDate("2025-01-01", "2026-01-01").filterBounds(aoi).mosaic())

    rows = []
    for i in range(0, len(farms), BATCH):
        sl = farms.iloc[i:i + BATCH]
        feats = [ee.Feature(ee.Geometry(g.__geo_interface__), {"fid": int(f)})
                 for g, f in zip(sl.geometry, fid[i:i + BATCH])]
        red = img.reduceRegions(collection=ee.FeatureCollection(feats),
                                reducer=ee.Reducer.mean(), scale=10)
        rows += [ft["properties"] for ft in red.getInfo()["features"]]
        print(f"  fetched {min(i + BATCH, len(farms))}/{len(farms)}")
    d = pd.DataFrame(rows).rename(columns={"fid": "farm_id"})
    d.to_csv(CACHE, index=False)
    return d


def blocks(xy, k=5):
    """Geographic folds. Random folds would let a farm be predicted by its own neighbours."""
    from sklearn.cluster import KMeans
    return KMeans(n_clusters=k, n_init=10, random_state=SEED).fit_predict(xy)


def cv_kappa(X, y, fold, label=""):
    """Spatially blocked CV. Returns (kappa, accuracy, majority baseline, predictions)."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import cohen_kappa_score
    pred = np.empty(len(y), dtype=object)
    for f in np.unique(fold):
        tr, te = fold != f, fold == f
        m = RandomForestClassifier(n_estimators=300, min_samples_leaf=3,
                                   random_state=SEED, n_jobs=-1).fit(X[tr], y[tr])
        pred[te] = m.predict(X[te])
    k = cohen_kappa_score(y, pred)
    acc = float((pred == y).mean())
    base = float(pd.Series(y).value_counts(normalize=True).max())
    if label:
        say(f"  {label:<44}kappa {k:+.3f}   acc {100 * acc:5.1f}%   "
            f"majority {100 * base:5.1f}%")
    return k, acc, base, pred


def main():
    from scipy import stats
    from sklearn.metrics import cohen_kappa_score
    from sklearn.model_selection import cross_val_predict, PredefinedSplit
    from sklearn.ensemble import RandomForestRegressor

    g = fetch()
    s = pd.read_csv(RESULTS / "submission.csv")
    f = pd.read_csv(RESULTS / "farm_features.csv")
    d = s.merge(f, on="farm_id").merge(g, on="farm_id", how="left")

    have = d[BANDS].notna().all(axis=1)
    say("=" * 78)
    say("SOURCE  GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL, 2025, 64 bands, 10 m")
    say("=" * 78)
    say(f"  {int(have.sum())}/{len(d)} farms returned a complete 64-vector")
    say(f"  embedding component SD across farms: median "
        f"{d.loc[have, BANDS].std().median():.4f}")
    say("  (a constant embedding would mean the village is one texture and nothing can be")
    say("   ranked inside it -- that is the first way this test can fail)")
    say("")

    d = d[have].copy()
    xy = farm_centroids()[d.farm_id.to_numpy() - 1]
    keep = np.hypot(xy[:, 0] - np.median(xy[:, 0]), xy[:, 1] - np.median(xy[:, 1])) < 5000
    say(f"  excluded {int((~keep).sum())} degenerate-geometry parcels (e12)")
    d, xy = d[keep].copy(), xy[keep]
    fold = blocks(xy)
    say(f"  spatial folds: {np.bincount(fold)} farms per geographic block")
    say("")

    X = d[BANDS].to_numpy()
    y = d.crop_type.to_numpy()

    # ---------------- T1 -------------------------------------------------
    say("=" * 78)
    say("T1  DOES THE EMBEDDING CARRY OUR CROP LABEL? (spatially blocked)")
    say("=" * 78)
    k_emb, _, base, pred = cv_kappa(X, y, fold, "64-band embedding")
    cv_kappa(d[["area_ha"]].to_numpy(), y, fold, "area_ha alone (size floor)")
    sar = [c for c in f.columns
           if c.startswith(("g0_db", "cv_", "d_", "temporal")) and c in d]
    cv_kappa(d[sar].to_numpy(), y, fold, "our own Capella features (self-check)")
    say("")
    say("  crop mix: " + ", ".join(f"{k} {v}" for k, v in d.crop_type.value_counts().items()))
    say("")
    say("  Reading: our own features MUST score high -- the labels were made from them, so a")
    say("  low self-check would mean the CV is broken. The embedding's kappa is the result:")
    say("  it is predicting Capella-derived labels from a sensor stack that never saw Capella,")
    say("  across held-out geographic blocks.")

    # ---------------- T1b ------------------------------------------------
    say("")
    say("-" * 78)
    say("T1b  WHERE the agreement lives -- per-crop, because a pooled kappa hides this")
    say("-" * 78)
    ct = pd.crosstab(pd.Series(y, name="ours"), pd.Series(pred, name="embedding"))
    for line in ct.to_string().splitlines():
        say("  " + line)
    say("")
    say(f"  {'crop':<12}{'n':>6}{'recall':>9}")
    for c in ct.index:
        n = ct.loc[c].sum()
        rec = ct.loc[c, c] / n if c in ct.columns else 0.0
        say(f"  {c:<12}{n:>6}{100 * rec:>8.1f}%")
    say("")
    say("  The literature prediction, set before this was run: Sentinel-1 monsoon phenology")
    say("  separates cotton best, while the cereal/legume group overlaps heavily. If the")
    say("  agreement is concentrated in one crop, the pooled kappa is not a licence to treat")
    say("  the embedding as a label source for the others.")

    # ---------------- T2 -------------------------------------------------
    say("")
    say("=" * 78)
    say("T2  IS IT REALLY FARM SIZE? (the control that killed Dynamic World in e13)")
    say("=" * 78)
    r, p = stats.spearmanr(d.area_ha, (pred == y).astype(float))
    say(f"  rho(area_ha, correctly predicted) = {r:+.3f}  p = {p:.3g}")
    say(f"  {'area decile':<14}{'n':>5}{'kappa':>9}{'median ha':>12}")
    dec = pd.qcut(d.area_ha, 10, labels=False, duplicates="drop")
    ks = []
    for q in sorted(pd.unique(dec)):
        m = (dec == q).to_numpy()
        kq = cohen_kappa_score(y[m], pred[m]) if len(np.unique(y[m])) > 1 else np.nan
        ks.append(kq)
        say(f"  {q + 1:<14}{int(m.sum()):>5}{kq:>9.3f}{d.area_ha[m].median():>12.3f}")
    say("")
    say(f"  kappa spread across deciles: {np.nanmin(ks):+.3f} to {np.nanmax(ks):+.3f}")
    say("  In e13 the Dynamic World effect COLLAPSED and changed SIGN across these deciles.")
    say("  If kappa holds up in the smallest deciles, this is not a size artefact.")

    # ---------------- T3 -------------------------------------------------
    say("")
    say("=" * 78)
    say("T3  PERMUTATION CONTROL -- can the pipeline 'learn' shuffled labels?")
    say("=" * 78)
    rng = np.random.default_rng(SEED)
    kp = [cv_kappa(X, rng.permutation(y), fold)[0] for _ in range(5)]
    say(f"  kappa on 5 label permutations: {', '.join(f'{v:+.3f}' for v in kp)}")
    say(f"  mean {np.mean(kp):+.3f}  (must sit at 0; anything above is CV leakage)")
    say(f"  observed {k_emb:+.3f} is "
        f"{(k_emb - np.mean(kp)) / (np.std(kp) + 1e-9):.1f} permutation SDs above the null")

    # ---------------- T4 -------------------------------------------------
    say("")
    say("=" * 78)
    say("T4  WITHIN-CROP HEALTH RESIDUAL -- how much of the 0.685 ceiling is real?")
    say("=" * 78)
    resid = (d.health_index
             - d.groupby("crop_type").health_index.transform("mean")).to_numpy()
    yp = cross_val_predict(RandomForestRegressor(n_estimators=300, min_samples_leaf=5,
                                                 random_state=SEED, n_jobs=-1),
                           X, resid, cv=PredefinedSplit(fold), n_jobs=1)
    r2 = 1 - np.sum((resid - yp) ** 2) / np.sum((resid - resid.mean()) ** 2)
    rr, pp = stats.spearmanr(yp, resid)
    say(f"  out-of-block R^2 = {r2:+.3f}   rho = {rr:+.3f}  p = {pp:.3g}")
    say("  e12 ceiling for a 10 m covariate: 0.685 (an upper bound, and a generous one)")
    say("")
    say("  NOT tested here: anything scored against s2_ndvi_20251013. The 2025 embedding")
    say("  ingests Sentinel-2 2025, so the withheld witness sits inside its inputs. Using it")
    say("  would be circular, and the number would look good for the wrong reason.")

    d[["farm_id", "crop_type"]].assign(pred_embed=pred).to_csv(
        OUT / "farm_embed_pred.csv", index=False)
    (OUT / "report.txt").write_text("\n".join(LOG) + "\n", encoding="utf8")
    print(f"\nwritten: {OUT}")


if __name__ == "__main__":
    main()
