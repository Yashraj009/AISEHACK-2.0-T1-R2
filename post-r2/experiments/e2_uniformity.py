"""e2 -- is our uniformity term a signal-to-noise proxy wearing an agronomic label?

Megalodon RETRACTED exactly this finding. They first published that more uniform fields
score higher (rho = -0.53), the sign the rubric expects. Then they found the texture had
been computed on noise-subtracted intensity, which adds variance in proportion to how
near the noise floor a farm sits. Dim farms are near the floor AND unhealthy, so the
statistic was measuring SNR, not agronomy. Corrected it gives rho = +0.02, and all five
structure metrics reverse sign: the best fields are the MORE variable ones (+0.43 once
brightness is partialled out).

Coding Bits report their uniformity term at -0.146 against October greenness -- opposite
in sign to their other three components -- and near-neutral on leave-one-out.

Our `uniform` family is -(within-farm CV) and carries 0.301, the LARGEST weight in our
health index. Our own REPORT 7.1 already says the relationship holds on the date that
feeds the index and fails on an independent one. This asks whether Megalodon's mechanism
is the reason.

Three tests, in order of how damning a failure would be:

  T1  Does CV track brightness? That is the SNR-proxy signature. If dim farms are
      the "non-uniform" ones, the term is measuring the noise floor.
  T2  Does uniform still correlate with an INDEPENDENT witness once brightness is
      partialled out? This is Megalodon's actual test.
  T3  Does the sign flip, as it did for them?

Reads shipped artefacts only; writes to post-r2/results/.

Run:  py -3.12 post-r2/experiments/e2_uniformity.py
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
from common import DATES, RESULTS  # noqa: E402

RESULTS_AUX = RESULTS / "tables"
OUT = ROOT / "post-r2" / "results" / "e2_uniformity"
OUT.mkdir(parents=True, exist_ok=True)

ANCHOR = "20251013"   # the date the deliverable is "as of"


def partial_spearman(x, y, z):
    """Spearman(x, y) with z partialled out, on ranks (Megalodon's framing)."""
    ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
    rx, ry, rz = (stats.rankdata(v[ok]) for v in (x, y, z))
    # residualise both against z, then correlate
    ex = rx - np.polyval(np.polyfit(rz, rx, 1), rz)
    ey = ry - np.polyval(np.polyfit(rz, ry, 1), rz)
    r, p = stats.pearsonr(ex, ey)
    return r, p, int(ok.sum())


def main():
    f = pd.read_csv(RESULTS / "farm_features.csv")
    s = pd.read_csv(RESULTS / "submission.csv")
    w = pd.read_csv(RESULTS_AUX / "witness.csv")
    d = f.merge(s, on="farm_id").merge(w, on="farm_id")

    cv = d[f"cv_{ANCHOR}"].to_numpy(float)
    uniform = -cv                                  # the family as the index uses it
    bright = d[f"g0_db_{ANCHOR}"].to_numpy(float)  # brightness, the confound
    npix = d[f"npix_{ANCHOR}"].to_numpy(float)
    ndvi = d["s2_ndvi_20251013"].to_numpy(float)
    vh = d["s1_vh_db"].to_numpy(float)

    lines = []

    def say(t=""):
        print(t)
        lines.append(t)

    say("=" * 74)
    say("T1  Does CV track brightness?  (the signal-to-noise-proxy signature)")
    say("=" * 74)
    r, p = stats.spearmanr(cv, bright, nan_policy="omit")
    say(f"  rho(CV, gamma0_dB)        = {r:+.3f}   p = {p:.2e}")
    say("     negative => dim farms are the 'non-uniform' ones, i.e. SNR is in the term")
    r2, p2 = stats.spearmanr(cv, npix, nan_policy="omit")
    say(f"  rho(CV, pixel count)      = {r2:+.3f}   p = {p2:.2e}")
    say("     Coding Bits found backscatter rising with plot area (r up to +0.27) purely")
    say("     because larger samples are better determined. Same artefact class.")
    say("")

    say("=" * 74)
    say("T2  Does uniform survive partialling brightness out?  (Megalodon's test)")
    say("=" * 74)
    say(f"  {'witness':<26} {'raw rho':>9} {'partial rho':>13} {'n':>6}")
    for lab, y in (("Sentinel-2 NDVI 13 Oct", ndvi), ("Sentinel-1 VH", vh)):
        ok = np.isfinite(uniform) & np.isfinite(y)
        raw = stats.spearmanr(uniform[ok], y[ok]).statistic
        pr, pp, n = partial_spearman(uniform, y, bright)
        say(f"  {lab:<26} {raw:>+9.3f} {pr:>+13.3f} {n:>6}")
    say("")
    say("  Megalodon: raw -0.53 (published), corrected +0.02, and +0.43 for structure")
    say("  once brightness is partialled out -- a full sign reversal.")
    say("")

    say("=" * 74)
    say("T3  Within crop, where our index actually scores")
    say("=" * 74)
    say(f"  {'crop':<11} {'n':>4} {'raw rho':>9} {'partial rho':>13}")
    for c, g in d.groupby("crop_type"):
        u = -g[f"cv_{ANCHOR}"].to_numpy(float)
        b = g[f"g0_db_{ANCHOR}"].to_numpy(float)
        y = g["s2_ndvi_20251013"].to_numpy(float)
        ok = np.isfinite(u) & np.isfinite(y)
        if ok.sum() < 20:
            continue
        raw = stats.spearmanr(u[ok], y[ok]).statistic
        pr, _, n = partial_spearman(u, y, b)
        say(f"  {c:<11} {n:>4} {raw:>+9.3f} {pr:>+13.3f}")

    (OUT / "report.txt").write_text("\n".join(lines) + "\n", encoding="utf8")
    print(f"\nwritten: {OUT / 'report.txt'}")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------
# T4 -- appended after T1-T3 showed `uniform` is null against both witnesses.
#
# Our weights are w_k proportional to 1 / sum_j |rho(k,j)|: each family is rewarded for
# being UNCORRELATED with the others. The rule is genuinely blind to every witness, which
# is why REPORT 4 defends it -- weights tuned by watching NDVI would convert a held-out
# check into a fitting target.
#
# But independence is not information. A family carrying only noise correlates with
# nothing, so the rule hands it the largest weight. That is what happened: `uniform`
# scores 0.025 mean |rho| against the two witnesses and draws 0.301, the largest weight,
# while `level` scores 0.214 and draws 0.189, the smallest.
#
# This asks what the index would do under alternatives that are STILL blind -- no witness
# may inform a weight, or the reserved check stops being reserved.
# ---------------------------------------------------------------------------

def t4_weighting():
    f = pd.read_csv(RESULTS / "farm_features.csv")
    s = pd.read_csv(RESULTS / "submission.csv")
    w = pd.read_csv(RESULTS_AUX / "witness.csv")
    d = f.merge(s, on="farm_id").merge(w, on="farm_id")

    fam = {"level": d["g0_db_20250814"], "growth": d["d_aug_jun19"],
           "uniform": -d[f"cv_{ANCHOR}"], "persist": d["season_integral"]}

    def zc(v, crop):
        """Robust z within crop, as the shipped index scores."""
        v = pd.Series(v).astype(float)
        out = pd.Series(np.nan, index=v.index)
        for c in crop.unique():
            m = crop == c
            x = v[m]
            med = x.median()
            mad = (x - med).abs().median()
            out[m] = (x - med) / (1.4826 * mad if mad > 0 else 1.0)
        return out.clip(-3.5, 3.5)

    Z = {k: zc(v, d.crop_type) for k, v in fam.items()}

    schemes = {
        "shipped (blind, 1/sum|rho|)": {"growth": .283, "uniform": .301,
                                        "persist": .228, "level": .189},
        "equal": {k: .25 for k in fam},
        "drop uniform, rest equal": {"growth": 1 / 3, "persist": 1 / 3, "level": 1 / 3,
                                     "uniform": 0.0},
        "drop uniform, rest as shipped": {"growth": .283 / .7, "persist": .228 / .7,
                                          "level": .189 / .7, "uniform": 0.0},
    }

    lines = ["", "=" * 74,
             "T4  Would a different -- still blind -- weighting do better?",
             "=" * 74,
             f"  {'scheme':<32}{'rho vs NDVI':>13}{'rho vs S1 VH':>14}"]
    for name, W in schemes.items():
        comp = sum(W[k] * Z[k].fillna(0) for k in fam)
        a = stats.spearmanr(comp, d.s2_ndvi_20251013, nan_policy="omit").statistic
        b = stats.spearmanr(comp, d.s1_vh_db, nan_policy="omit").statistic
        lines.append(f"  {name:<32}{a:>+13.3f}{b:>+14.3f}")
    lines += ["",
              "  Every scheme above is blind: none reads a witness to set a weight.",
              "  The comparison is reported, not used to pick -- picking on this table",
              "  is exactly what would stop the witnesses being independent."]
    txt = "\n".join(lines)
    print(txt)
    with (OUT / "report.txt").open("a", encoding="utf8") as fh:
        fh.write(txt + "\n")


if __name__ == "__main__":
    t4_weighting()
