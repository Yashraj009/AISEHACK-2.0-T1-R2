"""e7 -- run the remaining borrowed ideas on our own features before believing them.

e6 graded every recommendation. Three were left at THEIRS: sound-sounding, never tested
here. Two of them could change the health index, so they are tested now. The third is a
claim about our own geocoding that we had simply never measured.

  T1  PLOT-SIZE DE-BIASING  [Coding Bits]
      They found backscatter rising with plot area (r up to +0.27) purely because larger
      samples are better determined, regressed every feature on log(area) and removed the
      trend. We already know the artefact exists here -- rho(CV, npix) = +0.229 (e2) --
      but "the artefact is real" and "removing it helps" are different claims.

  T2  SPATIAL HOLD-OUT FOR WEIGHTS  [Coding Bits]
      They select weights on the western half of the village and report on the eastern
      half, and used it to REJECT their own data-driven optimum. Our weights are blind,
      which is a different defence and a weaker one: e2 showed the blind rule is
      anti-correlated with informativeness (Spearman -0.200) yet still beat every
      alternative on the full sample. That could be a real property or a full-sample
      artefact. A hold-out is the way to tell.

  T3  GEOCODING RESIDUAL  [Coding Bits]
      They report a polynomial fit leaving ~8 m residual against a 24.7 m median plot,
      and moved to a thin-plate spline. That is their measurement on their chain. Ours has
      never been measured, so the premise of the recommendation is untested for us.

Reads shipped artefacts read-only. Writes to post-r2/results/.

Run:  py -3.12 post-r2/experiments/e7_test_theirs.py
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
from common import RESULTS, farm_centroids  # noqa: E402

OUT = ROOT / "post-r2" / "results" / "e7_test_theirs"
OUT.mkdir(parents=True, exist_ok=True)
ANCHOR = "20251013"
LOG = []


def say(t=""):
    print(t)
    LOG.append(t)


def load():
    f = pd.read_csv(RESULTS / "farm_features.csv")
    s = pd.read_csv(RESULTS / "submission.csv")
    w = pd.read_csv(RESULTS / "tables" / "witness.csv")
    return f.merge(s, on="farm_id").merge(w, on="farm_id")


def families(d):
    return {"level": d["g0_db_20250814"].to_numpy(float),
            "growth": d["d_aug_jun19"].to_numpy(float),
            "uniform": -d[f"cv_{ANCHOR}"].to_numpy(float),
            "persist": d["season_integral"].to_numpy(float)}


def zc(v, crop):
    """Robust z within crop, as the shipped index scores."""
    v = pd.Series(v).astype(float)
    out = pd.Series(np.nan, index=v.index)
    for c in pd.unique(crop):
        m = (crop == c).to_numpy()
        x = v[m]
        med = x.median()
        mad = (x - med).abs().median()
        out[m] = (x - med) / (1.4826 * mad if mad > 0 else 1.0)
    return out.clip(-3.5, 3.5)


def blind_weights(fam):
    """w_k proportional to 1 / sum_j |rho(k,j)| -- the shipped rule, recomputed."""
    ks = list(fam)
    inv = {}
    for a in ks:
        s = 0.0
        for b in ks:
            if a == b:
                continue
            m = np.isfinite(fam[a]) & np.isfinite(fam[b])
            s += abs(stats.spearmanr(fam[a][m], fam[b][m]).statistic)
        inv[a] = 1.0 / s if s > 0 else 0.0
    tot = sum(inv.values())
    return {k: v / tot for k, v in inv.items()}


def score(fam, W, crop):
    Z = {k: zc(v, crop) for k, v in fam.items()}
    return sum(W[k] * Z[k].fillna(0) for k in fam)


def rho(a, b):
    return stats.spearmanr(a, b, nan_policy="omit").statistic


def t1_debias(d):
    say("=" * 78)
    say("T1  PLOT-SIZE DE-BIASING  [Coding Bits]")
    say("=" * 78)
    fam = families(d)
    la = np.log(d["area_ha"].to_numpy(float))
    say("  Correlation of each family with log(plot area), before and after removing")
    say("  the fitted trend. Coding Bits report residual area correlation < 0.001.")
    say(f"  {'family':<9}{'rho vs log(area)':>18}{'after de-bias':>16}")
    deb = {}
    for k, v in fam.items():
        m = np.isfinite(v) & np.isfinite(la)
        r0 = stats.spearmanr(v[m], la[m]).statistic
        res = v.copy()
        res[m] = v[m] - np.polyval(np.polyfit(la[m], v[m], 1), la[m])
        deb[k] = res
        r1 = stats.spearmanr(res[m], la[m]).statistic
        say(f"  {k:<9}{r0:>+18.3f}{r1:>+16.3f}")
    say("")
    say("  Does removing it improve the index against the two withheld witnesses?")
    W = {"growth": .283, "uniform": .301, "persist": .228, "level": .189}
    a0 = score(fam, W, d.crop_type)
    a1 = score(deb, W, d.crop_type)
    say(f"  {'index':<22}{'rho vs NDVI':>13}{'rho vs S1 VH':>14}")
    for lab, v in (("shipped", a0), ("plot-size de-biased", a1)):
        say(f"  {lab:<22}{rho(v, d.s2_ndvi_20251013):>+13.3f}{rho(v, d.s1_vh_db):>+14.3f}")
    say("")
    d0n, d1n = rho(a0, d.s2_ndvi_20251013), rho(a1, d.s2_ndvi_20251013)
    d0v, d1v = rho(a0, d.s1_vh_db), rho(a1, d.s1_vh_db)
    better = (d1n > d0n) and (d1v > d0v)
    say(f"  VERDICT: de-biasing {'HELPS on both witnesses' if better else
        'does NOT improve the index on both witnesses'}"
        f" ({d1n - d0n:+.3f} NDVI, {d1v - d0v:+.3f} S1).")
    say("  The area artefact is real in our data (e2: rho(CV, npix) = +0.229), but the")
    say("  correction is a separate claim and this is the test of it.")
    say("")
    return deb


def t2_holdout(d):
    say("=" * 78)
    say("T2  SPATIAL HOLD-OUT FOR WEIGHTS  [Coding Bits]")
    say("=" * 78)
    xy = farm_centroids()
    east = xy[d.farm_id.to_numpy() - 1, 0] > np.median(xy[:, 0])
    say(f"  Village split on the easting median: west n={(~east).sum()}, east n={east.sum()}.")
    say("  Weights are derived on ONE half and scored on the OTHER, so the reported")
    say("  number never saw the data that produced the weights.")
    say("")
    fam = families(d)
    shipped = {"growth": .283, "uniform": .301, "persist": .228, "level": .189}
    equal = {k: .25 for k in fam}

    for train_lab, tr in (("west", ~east), ("east", east)):
        te = ~tr
        famtr = {k: v[tr] for k, v in fam.items()}
        Wtr = blind_weights(famtr)
        say(f"  weights derived on the {train_lab} half: "
            + ", ".join(f"{k} {Wtr[k]:.3f}" for k in fam))
        famte = {k: v[te] for k, v in fam.items()}
        crop_te = d.crop_type[te].reset_index(drop=True)
        nd = d.s2_ndvi_20251013[te].reset_index(drop=True)
        vh = d.s1_vh_db[te].reset_index(drop=True)
        say(f"    scored on the held-out {'east' if train_lab == 'west' else 'west'} half:")
        say(f"      {'weighting':<26}{'rho NDVI':>10}{'rho S1 VH':>11}")
        for lab, W in (("derived on the other half", Wtr),
                       ("shipped (full-sample blind)", shipped),
                       ("equal", equal)):
            v = score(famte, W, crop_te)
            say(f"      {lab:<26}{rho(v, nd):>+10.3f}{rho(v, vh):>+11.3f}")
        say("")
    say("  Coding Bits used this to REJECT their own data-driven optimum: it improved the")
    say("  held-out half by 0.0006, within noise, while their physical prior improved both")
    say("  halves independently. The question here is whether our blind rule is stable")
    say("  when it can only see half the village.")
    say("")


def t3_geocoding(d):
    say("=" * 78)
    say("T3  GEOCODING RESIDUAL  [Coding Bits]")
    say("=" * 78)
    say("  Their claim: a polynomial GCP fit leaves ~8 m residual against a 24.7 m median")
    say("  plot dimension, which is why they moved to a thin-plate spline.")
    say("")
    med = float(np.sqrt(d.area_ha.median() * 10000))
    say(f"  Our median plot is {d.area_ha.median():.3f} ha, i.e. a {med:.1f} m square -")
    say(f"  close to their 24.7 m, so the geometry of the problem is the same.")
    say("")
    say("  What we can say without reprocessing: our chain resamples by AVERAGE onto a")
    say("  5 m base grid, so a residual of their size would be 1.6 base pixels and would")
    say("  mix neighbouring fields at the boundary. We erode before sampling, which is")
    say("  the mitigation, but the residual itself has never been measured on our fit.")
    say("")
    say("  STATUS: still THEIRS. Measuring it needs the GCP fit residuals out of")
    say("  prep_r2.py's geocoding step, which is a code change, not an analysis. Flagged")
    say("  as the one borrowed claim whose PREMISE remains untested for our pipeline.")
    say("")


def main():
    d = load()
    t1_debias(d)
    t2_holdout(d)
    t3_geocoding(d)
    (OUT / "report.txt").write_text("\n".join(LOG) + "\n", encoding="utf8")
    print(f"\nwritten: {OUT / 'report.txt'}")


if __name__ == "__main__":
    main()
