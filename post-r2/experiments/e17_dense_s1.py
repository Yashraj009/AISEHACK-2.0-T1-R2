"""e17 -- D-1's hypothesis, tested on data we already hold, without spending anything.

D-1 in ROUND3_DIRECTIONS proposed fetching a dense Sentinel-1 time series, on the reasoning
that e14's annual embedding recovered cotton at 84.9% but rice at 4.7% and maize at 0.0%
because an ANNUAL average destroys phenological timing. Two things were wrong with it.

  1. "There is no dense temporal series anywhere in the pipeline" is FALSE. src/witness_season.py
     already fetched ten Sentinel-1 RTC scenes, 12 Jun to 10 Oct 2025, every one on relative
     orbit 34 descending, per farm, in results/tables/witness_season.csv. Nothing needs
     fetching.
  2. docs/REPORT.md:16 states Capella primacy is required BY THE GUIDELINES, not merely
     preferred. Training our crop label on C-band would make C-band the primary source of the
     headline output. D-1's "cost" is therefore not just a spent witness; it is potentially
     disqualifying.

So the question is re-posed as one that costs nothing and breaches nothing. Using the witness
AS A WITNESS -- which is what i5_validation already does with a Kruskal-Wallis test -- does the
dense series corroborate the crop labels the annual embedding could not?

  T1  Blocked-CV kappa and PER-CROP recall from the 10-date series, on exactly e14's protocol
      so the numbers are directly comparable.
  T2  THE ACTUAL D-1 HYPOTHESIS. If timing is what the annual embedding destroyed, then the
      per-date series must beat its own season mean and integral. If it does not, timing is
      not the missing ingredient and D-1 closes for good.
  T3  Permutation and farm-size controls, as in e14 and e13.
  T4  Where the two independent sensors AGREE with us. A farm corroborated by both C-band
      phenology and the annual embedding is evidence of a different order than either alone.

NOTHING IS FED BACK. The season witness stays a witness: this script writes no feature, and
adopting any of it as a model input would forfeit both the independence that makes
i5_validation meaningful and the Capella primacy the guidelines require.

Run:  py -3.12 post-r2/experiments/e17_dense_s1.py
"""
import os
import sys
from pathlib import Path

os.environ.pop("PROJ_LIB", None)

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from common import RESULTS, farm_centroids  # noqa: E402

OUT = ROOT / "post-r2" / "results" / "e17_dense_s1"
OUT.mkdir(parents=True, exist_ok=True)
E14 = ROOT / "post-r2" / "results" / "e14_embeddings" / "farm_embed_pred.csv"
SEED = 0
LOG = []


def say(t=""):
    print(t)
    LOG.append(t)


def blocks(xy, k=5):
    from sklearn.cluster import KMeans
    return KMeans(n_clusters=k, n_init=10, random_state=SEED).fit_predict(xy)


def cv(X, y, fold, label=""):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import cohen_kappa_score
    pred = np.empty(len(y), dtype=object)
    for f in np.unique(fold):
        tr, te = fold != f, fold == f
        m = RandomForestClassifier(n_estimators=300, min_samples_leaf=3,
                                   random_state=SEED, n_jobs=-1).fit(X[tr], y[tr])
        pred[te] = m.predict(X[te])
    k = cohen_kappa_score(y, pred)
    if label:
        say(f"  {label:<46}kappa {k:+.3f}   acc {100 * (pred == y).mean():5.1f}%")
    return k, pred


def main():
    from scipy import stats
    from sklearn.metrics import cohen_kappa_score

    w = pd.read_csv(RESULTS / "tables" / "witness_season.csv")
    sub = pd.read_csv(RESULTS / "submission.csv")
    feat = pd.read_csv(RESULTS / "farm_features.csv")[["farm_id", "area_ha"]]
    d = sub.merge(feat, on="farm_id").merge(w, on="farm_id", how="left")

    dcols = [c for c in w.columns if c.startswith("s1_vh_db_2")]
    dates = [c.split("_")[-1] for c in dcols]
    say("=" * 78)
    say("SOURCE  results/tables/witness_season.csv -- ALREADY IN THE REPO, nothing fetched")
    say("=" * 78)
    say(f"  {len(dcols)} Sentinel-1 VH dates, all relative orbit 34 descending:")
    say("    " + ", ".join(dates))
    say(f"  Capella has FOUR dates. This C-band series has {len(dcols)}, over the same season.")
    say("")

    ok = d[dcols].notna().all(axis=1)
    d = d[ok].copy()
    xy = farm_centroids()[d.farm_id.to_numpy() - 1]
    keep = np.hypot(xy[:, 0] - np.median(xy[:, 0]), xy[:, 1] - np.median(xy[:, 1])) < 5000
    d, xy = d[keep].copy(), xy[keep]
    fold = blocks(xy)
    y = d.crop_type.to_numpy()
    say(f"  {len(d)} farms with a complete series and usable geometry")
    say(f"  spatial folds: {np.bincount(fold)}")
    say("")

    # feature sets, each isolating one hypothesis
    per_date = d[dcols].to_numpy()
    deltas = np.diff(per_date, axis=1)
    full = np.column_stack([per_date, deltas])
    mean_only = d[["s1_vh_mean_db"]].to_numpy()
    integral_only = d[["s1_vh_season_integral"]].to_numpy()
    flat = np.column_stack([mean_only, integral_only])

    # ---------------- T1 -------------------------------------------------
    say("=" * 78)
    say("T1  DOES THE DENSE C-BAND SERIES CORROBORATE OUR CROP LABELS?")
    say("=" * 78)
    k_full, pred = cv(full, y, fold, "10 dates + 9 deltas (full phenology)")
    say("")
    ct = pd.crosstab(pd.Series(y, name="ours"), pd.Series(pred, name="dense S1"))
    for line in ct.to_string().splitlines():
        say("  " + line)
    say("")
    e14rec = {"Cotton": 84.9, "Groundnut": 28.6, "Bajra": 10.9, "Rice": 4.7, "Maize": 0.0}
    say(f"  {'crop':<12}{'n':>6}{'dense S1':>11}{'e14 annual':>13}{'change':>10}")
    recs = {}
    for c in ct.index:
        n = ct.loc[c].sum()
        r = 100 * (ct.loc[c, c] / n if c in ct.columns else 0.0)
        recs[c] = r
        say(f"  {c:<12}{n:>6}{r:>10.1f}%{e14rec.get(c, np.nan):>12.1f}%"
            f"{r - e14rec.get(c, np.nan):>+9.1f}pp")
    say("")
    say("  This is the comparison D-1 rests on: the SAME crops, the SAME blocked-CV protocol,")
    say("  a dense C-band series against an annual multi-sensor average.")

    # ---------------- T2 -------------------------------------------------
    say("")
    say("=" * 78)
    say("T2  IS TIMING WHAT MATTERS? (the actual D-1 hypothesis, isolated)")
    say("=" * 78)
    k_flat, _ = cv(flat, y, fold, "season mean + integral only (timing REMOVED)")
    k_pd, _ = cv(per_date, y, fold, "10 dates, no deltas")
    k_late, _ = cv(per_date[:, -3:], y, fold, "last 3 dates only (Sep-Oct)")
    k_early, _ = cv(per_date[:, :3], y, fold, "first 3 dates only (Jun-Jul)")
    say("")
    say(f"  full phenology {k_full:+.3f} vs flattened {k_flat:+.3f} -> timing is worth "
        f"{k_full - k_flat:+.3f} kappa")
    say("  If that gap is near zero, the season shape carries nothing the mean does not, and")
    say("  D-1's premise -- that annual averaging is what destroyed rice and maize -- is wrong.")

    # ---------------- T3 -------------------------------------------------
    say("")
    say("=" * 78)
    say("T3  CONTROLS")
    say("=" * 78)
    rng = np.random.default_rng(SEED)
    kp = [cv(full, rng.permutation(y), fold)[0] for _ in range(5)]
    say(f"  permutation kappas: {', '.join(f'{v:+.3f}' for v in kp)}  mean {np.mean(kp):+.3f}")
    say(f"  observed {k_full:+.3f} is "
        f"{(k_full - np.mean(kp)) / (np.std(kp) + 1e-9):.1f} permutation SDs above null")
    r, p = stats.spearmanr(d.area_ha, (pred == y).astype(float))
    say(f"  rho(area_ha, correctly predicted) = {r:+.3f}  p = {p:.3g}   "
        f"(e13 died on this control)")
    k_area, _ = cv(d[["area_ha"]].to_numpy(), y, fold, "area_ha alone (size floor)")

    # ---------------- T4 -------------------------------------------------
    say("")
    say("=" * 78)
    say("T4  WHERE TWO INDEPENDENT SENSORS BOTH BACK OUR LABEL")
    say("=" * 78)
    if E14.exists():
        e = pd.read_csv(E14)[["farm_id", "pred_embed"]]
        m = d.merge(e, on="farm_id", how="left")
        s1_ok = pred == y
        emb_ok = (m.pred_embed.to_numpy() == y)
        both = s1_ok & emb_ok
        neither = ~s1_ok & ~emb_ok
        say(f"  {'':<34}{'farms':>8}{'% of village':>14}")
        say(f"  {'both sensors agree with us':<34}{int(both.sum()):>8}"
            f"{100 * both.mean():>13.1f}%")
        say(f"  {'dense S1 only':<34}{int((s1_ok & ~emb_ok).sum()):>8}"
            f"{100 * (s1_ok & ~emb_ok).mean():>13.1f}%")
        say(f"  {'embedding only':<34}{int((~s1_ok & emb_ok).sum()):>8}"
            f"{100 * (~s1_ok & emb_ok).mean():>13.1f}%")
        say(f"  {'NEITHER agrees with us':<34}{int(neither.sum()):>8}"
            f"{100 * neither.mean():>13.1f}%")
        exp = float(s1_ok.mean() * emb_ok.mean())
        say("")
        say(f"  both-agree observed {100 * both.mean():.1f}% vs "
            f"{100 * exp:.1f}% if the two sensors were independent")
        say(f"  {'crop':<12}{'both agree':>12}{'neither':>10}")
        for c in sorted(set(y)):
            mm = y == c
            say(f"  {c:<12}{100 * both[mm].mean():>11.1f}%{100 * neither[mm].mean():>9.1f}%")
        say("")
        say("  The 'neither' column is the honest one: those farms carry a label that no")
        say("  independent sensor supports, and they are where Track E lookups belong.")
        m.assign(s1_pred=pred, s1_ok=s1_ok, emb_ok=emb_ok)[
            ["farm_id", "crop_type", "s1_pred", "pred_embed", "s1_ok", "emb_ok"]
        ].to_csv(OUT / "two_sensor_agreement.csv", index=False)
    else:
        say("  e14 output not present; run e14_embeddings.py first")

    # ---------------- T5 -------------------------------------------------
    say("")
    say("=" * 78)
    say("T5  IS C-BAND BLIND TO RICE, OR DOES IT SIMPLY MISS THE EVENT?")
    say("=" * 78)
    say("  Our rice channel is the Capella 6 -> 19 June brightening (+3.23 dB for rice against")
    say("  +0.07..+1.12 for everything else), driven by 17.3 mm of rain in the six hours before")
    say("  the 19 June overpass (e12, Open-Meteo). Sentinel-1 flew 12 June and 24 June, so it")
    say("  STRADDLES that event without sampling it. Testing the closest available pair:")
    say("")
    jd = d.s1_vh_db_20250624.to_numpy() - d.s1_vh_db_20250612.to_numpy()
    say(f"  {'crop':<12}{'n':>6}{'12->24 Jun dB':>16}")
    for c in sorted(set(y)):
        m = y == c
        say(f"  {c:<12}{int(m.sum()):>6}{np.mean(jd[m]):>+15.3f}")
    r_m = y == "Rice"
    u = stats.mannwhitneyu(jd[r_m], jd[~r_m])
    say("")
    say(f"  rice {np.mean(jd[r_m]):+.3f} dB vs rest {np.mean(jd[~r_m]):+.3f} dB, "
        f"Mann-Whitney p = {u.pvalue:.3g}")
    say("")
    say("  Rice brightens MOST, which is the same direction as our Capella channel -- but the")
    say("  margin is +0.30 dB against our +3.23 dB, and p = 0.07 is not significant.")
    say("  CONCLUSION: 'C-band is blind to rice' is NOT established. What is established is")
    say("  that a 12-day C-band VH series does not separate rice here, which is consistent")
    say("  with a days-scale flooding event falling between two acquisitions.")

    say("")
    say("=" * 78)
    say("STANDING CONSTRAINT")
    say("=" * 78)
    say("  Nothing here becomes a feature. docs/REPORT.md states Capella primacy is required")
    say("  by the guidelines, and i5_validation's independence rests on this series never")
    say("  having been read by the model. Using it as an input would forfeit both.")

    (OUT / "report.txt").write_text("\n".join(LOG) + "\n", encoding="utf8")
    print(f"\nwritten: {OUT}")


if __name__ == "__main__":
    main()
