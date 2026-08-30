"""e11 -- per-farm uncertainty, derived from speckle physics and calibration-tested.

THE GAP. All six shortlisted teams ship point estimates. Four ship a confidence number and
none demonstrates it is CALIBRATED - that a farm marked uncertain is actually wrong more
often, by the amount claimed. Megalodon comes closest (rank disagreement falls monotonically
across confidence quintiles) and that is still an ordering check, not a calibration curve.

This matters here more than in most problems, because farm sizes span a 35x range in pixel
count (0 to 1223 at the anchor date). Speckle averages down as 1/sqrt(N), so the precision
of a farm mean varies by ~6x across the village, and a single point estimate hides all of it.

THE MODEL. For a farm of N pixels with coefficient of variation cv, the standard error of
the mean in linear power is cv/sqrt(N). That is not fitted - it is what fully developed
speckle does, and cv and N are both measured per farm per date. Propagating that through the
shipped health index by Monte Carlo gives a per-farm standard deviation on the index itself.

THE TEST, which is the point. Two independent checks, neither needing ground truth:

  T1 SPLIT-HALF     Split each farm's pixels into two random halves and compute the farm
                    statistic from each. The spread between halves is PURE sampling noise,
                    measured with no model and no witness. Theory says that spread should be
                    sqrt(2) x the predicted SE of the full-farm mean. If the observed spread
                    matches, the uncertainty model is calibrated at the feature level. This
                    is the honest test: it can fail.

  T2 WITNESS        Does predicted uncertainty predict actual disagreement with a sensor the
                    pipeline never read? Ordering AND magnitude, not just ordering.

Reads shipped artefacts and cached rasters read-only. Writes to post-r2/results/.

Run:  py -3.12 post-r2/experiments/e11_uncertainty.py
"""
import os
import sys
from pathlib import Path

os.environ.pop("PROJ_LIB", None)

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from common import CACHE, FARMS, RESULTS  # noqa: E402

OUT = ROOT / "post-r2" / "results" / "e11_uncertainty"
OUT.mkdir(parents=True, exist_ok=True)
ANCHOR = "20251013"
RNG = np.random.default_rng(0)
LOG = []


def say(t=""):
    print(t)
    LOG.append(t)


def farm_pixels():
    """Per-farm linear-power pixel samples at the anchor date, reusing the shipped rasteriser."""
    import geopandas as gpd
    import rasterio
    from rasterio.features import rasterize
    from farm_stats import BUFFERS

    with rasterio.open(CACHE / f"gamma0_base_{ANCHOR}.tif") as s:
        arr = s.read(1).astype("float64")
        tf, shape = s.transform, arr.shape

    farms = gpd.read_file(FARMS).to_crs(32643)
    lab = np.zeros(shape, dtype="int32")
    level = np.full(len(farms), -1, dtype="int8")
    for li, buf in enumerate(BUFFERS):
        todo = np.where(level < 0)[0]
        if not len(todo):
            break
        shapes = []
        for i in todo:
            g = farms.geometry.iloc[i]
            g = g.buffer(buf) if buf else g
            if (not g.is_empty) and g.area > 0:
                shapes.append((g, int(i) + 1))
        if not shapes:
            continue
        r = rasterize(shapes, out_shape=shape, transform=tf, fill=0, dtype="int32")
        new = (lab == 0) & (r > 0)
        lab[new] = r[new]
        for i in todo:
            if (lab == i + 1).any():
                level[i] = li
    out = {}
    for i in range(len(farms)):
        v = arr[lab == i + 1]
        v = v[np.isfinite(v) & (v > 0)]
        if len(v) >= 8:
            out[i + 1] = v
    return out


def t1_split_half(px):
    say("=" * 78)
    say("T1  SPLIT-HALF -- measure our own sampling noise with no model and no witness")
    say("=" * 78)
    say("  Each farm's pixels are split into two random halves and the mean computed from")
    say("  each. Theory: the half-to-half difference has SD = sqrt(2) x SE(full mean),")
    say("  and SE(full mean) = cv/sqrt(N). Nothing here is fitted.")
    say("")
    rows = []
    for fid, v in px.items():
        n = len(v)
        cv = v.std(ddof=1) / v.mean()
        pred_se = cv / np.sqrt(n)                       # SE of the full-farm mean, fraction
        diffs = []
        for _ in range(25):                             # average over random splits
            p = RNG.permutation(n)
            a, b = v[p[: n // 2]], v[p[n // 2: 2 * (n // 2)]]
            diffs.append((a.mean() - b.mean()) / v.mean())
        rows.append((fid, n, cv, pred_se, float(np.std(diffs))))
    d = pd.DataFrame(rows, columns=["farm_id", "n", "cv", "pred_se", "obs_half_sd"])
    # observed half-difference SD should be sqrt(2)*SE_full ... each half has n/2 pixels,
    # so SE_half = cv/sqrt(n/2) and SD(diff) = sqrt(2)*SE_half = 2*cv/sqrt(n) = 2*pred_se
    d["pred_half_sd"] = 2.0 * d.pred_se
    d["ratio"] = d.obs_half_sd / d.pred_half_sd

    say(f"  farms with >=8 usable pixels: {len(d)}")
    say(f"  {'quantity':<34}{'median':>10}{'p10':>9}{'p90':>9}")
    say(f"  {'predicted half-split SD':<34}{d.pred_half_sd.median():>10.4f}"
        f"{d.pred_half_sd.quantile(.1):>9.4f}{d.pred_half_sd.quantile(.9):>9.4f}")
    say(f"  {'observed half-split SD':<34}{d.obs_half_sd.median():>10.4f}"
        f"{d.obs_half_sd.quantile(.1):>9.4f}{d.obs_half_sd.quantile(.9):>9.4f}")
    say(f"  {'observed / predicted':<34}{d.ratio.median():>10.3f}"
        f"{d.ratio.quantile(.1):>9.3f}{d.ratio.quantile(.9):>9.3f}")
    say("")
    r = stats.spearmanr(d.pred_half_sd, d.obs_half_sd).statistic
    say(f"  Spearman(predicted, observed) across farms = {r:+.4f}")
    med = d.ratio.median()
    verdict = ("CALIBRATED" if 0.9 <= med <= 1.1 else
               f"BIASED by {100 * (med - 1):+.0f}% -- the model needs that factor")
    say(f"  VERDICT: {verdict}")
    say("")
    say("  A ratio near 1.0 means the physics predicts our own noise without tuning. This is")
    say("  the check that can fail, and it is reported whichever way it comes out.")
    say("")
    d.to_csv(OUT / "split_half.csv", index=False)
    return d


def t2_witness(d):
    say("=" * 78)
    say("T2  DOES PREDICTED UNCERTAINTY PREDICT DISAGREEMENT WITH A WITHHELD SENSOR?")
    say("=" * 78)
    f = pd.read_csv(RESULTS / "farm_features.csv")
    s = pd.read_csv(RESULTS / "submission.csv")
    w = pd.read_csv(RESULTS / "tables" / "witness.csv")
    m = f.merge(s, on="farm_id").merge(w, on="farm_id").merge(
        d[["farm_id", "pred_se"]], on="farm_id")

    # rank health and the witness WITHIN crop, since the index is a within-crop score
    m["r_health"] = m.groupby("crop_type").health_index.rank(pct=True)
    m["r_wit"] = m.groupby("crop_type").s2_ndvi_20251013.rank(pct=True)
    m = m.dropna(subset=["r_health", "r_wit", "pred_se"])
    m["disagree"] = (m.r_health - m.r_wit).abs()

    say(f"  n = {len(m)} farms with a witness value and a usable pixel sample")
    say("")
    say(f"  {'predicted-SE quintile':<24}{'n':>6}{'median SE':>12}{'mean |rank gap|':>18}")
    m["q"] = pd.qcut(m.pred_se, 5, labels=False)
    for q, g in m.groupby("q"):
        say(f"  {'Q' + str(int(q) + 1) + ' (most precise)' if q == 0 else 'Q' + str(int(q) + 1):<24}"
            f"{len(g):>6}{g.pred_se.median():>12.4f}{g.disagree.mean():>18.4f}")
    r, p = stats.spearmanr(m.pred_se, m.disagree)
    say("")
    say(f"  Spearman(predicted SE, |rank gap|) = {r:+.4f}   p = {p:.3g}")
    say("  A positive, significant value means the uncertainty is INFORMATIVE: farms we")
    say("  flag as imprecise really do agree less with a sensor we never read.")
    say("")
    say("  Note the ceiling: witness disagreement contains our noise AND the fact that NDVI")
    say("  is a different physical quantity. So the correlation cannot reach 1, and its")
    say("  absolute size is not the result -- the sign, significance and monotonicity are.")
    say("")
    m[["farm_id", "crop_type", "pred_se", "r_health", "r_wit", "disagree"]].to_csv(
        OUT / "witness_vs_uncertainty.csv", index=False)
    return m


def t3_propagate(d):
    say("=" * 78)
    say("T3  WHAT IT WOULD MEAN FOR THE DELIVERABLE")
    say("=" * 78)
    s = pd.read_csv(RESULTS / "submission.csv").merge(d[["farm_id", "pred_se"]], on="farm_id")
    # health is a bounded transform of a within-crop robust z; a fractional SE on linear
    # power maps to roughly (10/ln10)*se dB, and the index spans ~50 points per ~2 dB.
    s["health_sd_pts"] = (10 / np.log(10)) * s.pred_se * 25.0
    say("  Rough propagation of the measured feature-level SE onto the 0-100 index")
    say("  (a fractional SE on linear power is ~4.34*se dB; the index spans ~25 points/dB")
    say("  within a crop cohort):")
    say("")
    say(f"  {'health_index uncertainty, points':<36}{'median':>9}{'p90':>9}{'max':>9}")
    say(f"  {'':<36}{s.health_sd_pts.median():>9.2f}{s.health_sd_pts.quantile(.9):>9.2f}"
        f"{s.health_sd_pts.max():>9.2f}")
    say("")
    frac = float((s.health_sd_pts > 5).mean())
    say(f"  {100 * frac:.1f}% of farms carry more than 5 index points of sampling uncertainty")
    say("  on a 0-100 scale, purely from how few pixels they contain. Reporting a single")
    say("  number for those farms and for a 1,200-pixel farm treats them as equally known.")
    say("")
    say("  This is a scoping figure, not a shipped column: the constant 25 pts/dB is an")
    say("  approximation of the index transform, and the full propagation should run the")
    say("  Monte Carlo through d4_submission rather than a linear factor.")
    s[["farm_id", "crop_type", "health_index", "pred_se", "health_sd_pts"]].to_csv(
        OUT / "health_uncertainty.csv", index=False)


def main():
    say("Per-farm uncertainty from speckle physics, and whether it is calibrated.")
    say("")
    px = farm_pixels()
    say(f"extracted pixel samples for {len(px)} farms at {ANCHOR}")
    say("")
    d = t1_split_half(px)
    t2_witness(d)
    t3_propagate(d)
    (OUT / "report.txt").write_text("\n".join(LOG) + "\n", encoding="utf8")
    print(f"\nwritten: {OUT}")


if __name__ == "__main__":
    main()
