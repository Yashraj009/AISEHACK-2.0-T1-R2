"""Offline bake-off for the candidate fixes, before any of them is shipped.

Each candidate is rebuilt end-to-end into a health index and scored on the SAME
independent witnesses (same-day Sentinel-2 NDVI, Sentinel-1 C-VH), which are not
inputs to anything. A candidate that does not beat the incumbent on evidence does
not get shipped -- that is the whole point of running this before editing d4.

Run:  python src/diagnose_fixes.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CROPS, RESULTS
from d4_submission import HEALTH_W, z

# The incumbent this bake-off compares against is the weighting that was SHIPPED BEFORE
# this pass, pinned as a literal. Importing the live HEALTH_W would make variant "A
# shipped" silently become whatever the current code does -- and once texture was
# dropped, A/D and E/F/I collapsed into duplicates of each other, so the comparison that
# justifies the new weights could no longer be reproduced by the script that produced it.
BASELINE_W = {"level": 0.30, "growth": 0.25, "uniform": 0.20,
              "texture": 0.10, "persist": 0.15}


def rho(a, b):
    a, b = np.asarray(a, "float64"), np.asarray(b, "float64")
    m = np.isfinite(a) & np.isfinite(b)
    return float(spearmanr(a[m], b[m]).statistic) if m.sum() > 10 else np.nan


def build_health(f, crop, parts, weights=BASELINE_W, rank=True):
    """Same combination logic as d4.health_index, but with injectable parts."""
    S = np.zeros(len(f)); W = np.zeros(len(f))
    for k, v in parts.items():
        w = weights.get(k, 0.0)
        if w == 0:
            continue
        ok = np.isfinite(v) & (v != 0)
        S[ok] += w * v[ok]; W[ok] += w
    S = np.where(W > 0, S / np.maximum(W, 1e-9), np.nan)
    out = np.full(len(f), np.nan)
    for c in CROPS:
        m = (crop == c) & np.isfinite(S)
        if m.sum() >= 5:
            if rank:
                out[m] = 100.0 * pd.Series(S[m]).rank(pct=True).values
            else:
                from scipy.stats import norm
                cc = np.median(S[m]); sd = 1.4826 * np.median(np.abs(S[m] - cc))
                out[m] = 100.0 * norm.cdf((S[m] - cc) / (sd if sd > 0 else 1))
        elif m.sum():
            out[m] = 50.0
    return out, S


def main():
    f = pd.read_csv(RESULTS / "farm_features.csv")
    w = pd.read_csv(RESULTS / "witness.csv")
    sub = pd.read_csv(RESULTS / "baseline" / "submission_BASELINE.csv")
    d = f.merge(w, on="farm_id")
    crop = sub.set_index("farm_id").loc[f.farm_id, "crop_type"].values
    ndvi, vh, area = d.s2_ndvi_20251013.values, d.s1_vh_db.values, f.area_ha.values

    print("=" * 78)
    print("1. GROWTH TERM -- which date pair carries real vegetation signal?")
    print("=" * 78)
    g06 = (f.g0_db_20250814 - f.g0_db_20250606).values          # 6.55 deg apart (shipped)
    g19 = (f.g0_db_20250814 - f.g0_db_20250619).values          # 0.076 deg apart
    g19c = g19 - np.nanmedian(g19)                              # common-mode removed
    for name, v in [("d_aug_jun06 (SHIPPED, 6.55deg)", g06),
                    ("d_aug_jun19 (matched, 0.076deg)", g19),
                    ("d_aug_jun19 median-centred", g19c)]:
        print(f"  {name:34s} med {np.nanmedian(v):+6.2f} sd {np.nanstd(v):5.2f} "
              f"| rho_ndvi {rho(v, ndvi):+.3f} rho_vh {rho(v, vh):+.3f} "
              f"rho_area {rho(v, area):+.3f}")
    print(f"  correlation between the two pairs: {rho(g06, g19):+.3f}")

    print()
    print("=" * 78)
    print("2. AREA BIAS -- where does rho(health, area)=+0.086 actually come from?")
    print("=" * 78)
    for c in ["cv_20250814", "cv_20251013", "glcm_resid_20250814",
              "g0_db_20250814", "season_integral", "ktex_20250814"]:
        print(f"  {c:22s} rho_vs_area {rho(f[c], area):+.3f}  "
              f"rho_vs_npix {rho(f[c], f.npix_20251013):+.3f}")
    # sample-size correction on CV: does removing the speckle floor REORDER farms?
    npx = f.npix_20250814.values.astype("float64")
    cv = f.cv_20250814.values
    for L in [3.5, 6.5]:
        cvt = np.sqrt(np.maximum(cv ** 2 - 1.0 / L, 0.0))
        print(f"  ENL-corrected CV (L={L}): rho vs raw CV {rho(cvt, cv):+.4f} "
              f"| rho vs area {rho(cvt, area):+.3f} | n_clipped_to_0 {(cvt == 0).sum()}")

    print()
    print("=" * 78)
    print("3. HEALTH VARIANTS -- scored on witnesses that are not inputs")
    print("=" * 78)
    base_parts = {
        "level":   z(f.g0_db_20250814.values),
        "growth":  z(g06),
        "uniform": -z(f.cv_20250814.values),
        "texture": z(f.glcm_resid_20250814.values),
        "persist": z(f.season_integral.values),
    }
    variants = {"A pre-pass incumbent (rank, jun06)": (dict(base_parts), BASELINE_W, True)}

    p = dict(base_parts); p["growth"] = z(g19c)
    variants["B growth on matched pair"] = (p, BASELINE_W, True)

    p2 = dict(p); p2["uniform"] = -z(np.sqrt(np.maximum(cv ** 2 - 1 / 6.5, 0)))
    variants["C B + ENL-corrected uniform"] = (p2, BASELINE_W, True)

    W3 = {k: v for k, v in BASELINE_W.items() if k != "texture"}
    variants["D B minus inert texture"] = (p, W3, True)

    variants["E B, bounded z (not rank)"] = (p, BASELINE_W, False)
    variants["F B + no texture + bounded z"] = (p, W3, False)

    # level and persist correlate at 0.74 -- 0.45 of the weight on one axis.
    # Rebalance toward the families that carry independent information.
    W4 = {"level": 0.20, "growth": 0.35, "uniform": 0.25, "persist": 0.20}
    variants["G F + rebalanced weights"] = (p, W4, False)

    # growth-only, as the floor: how much do the other families actually add?
    W5 = {"growth": 1.0}
    variants["H growth alone (control)"] = (p, W5, False)

    # --- weights from INTERNAL structure only, never from the witnesses -------
    # Choosing weights by looking at witness correlation would destroy the whole
    # point of holding the witnesses out. So derive them from redundancy alone:
    # a family that duplicates the others is down-weighted, one that carries
    # independent information is up-weighted. Purely a function of the feature
    # matrix, reproducible, and blind to NDVI/VH.
    keys = [k for k in p if k != "texture"]
    Xc = np.column_stack([p[k] for k in keys])
    C = np.abs(pd.DataFrame(Xc).corr(method="spearman").values)
    inv = 1.0 / C.sum(axis=1)                 # redundancy-weighted
    W6 = {k: float(v) for k, v in zip(keys, inv / inv.sum())}
    variants["I decorrelation weights (blind) = SHIPPED"] = (p, W6, False)
    print(f"  [decorrelation weights, derived without witnesses: "
          f"{ {k: round(v, 3) for k, v in W6.items()} }]")

    print(f"  {'variant':34s}{'rho_ndvi':>9}{'rho_vh':>8}{'rho_area':>9}"
          f"{'cv_oct*':>9}{'sd':>7}")
    for name, (parts, W, rank) in variants.items():
        h, _ = build_health(f, crop, parts, W, rank)
        print(f"  {name:34s}{rho(h, ndvi):>+9.3f}{rho(h, vh):>+8.3f}"
              f"{rho(h, area):>+9.3f}{rho(h, f.cv_20251013):>+9.3f}"
              f"{np.nanstd(h):>7.1f}")
    print("  * cv_oct = the INDEPENDENT uniformity test (October CV is not in the index);")
    print("    more negative = 'uniform canopy scores higher' better supported.")


if __name__ == "__main__":
    main()
