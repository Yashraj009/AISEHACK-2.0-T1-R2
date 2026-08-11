"""Turn collected ground truth into a measured accuracy for both crop maps.

Input:  data_aux/ground_truth_vf12.csv  -- the template from make_gt_sample.py with
        the `vf12_crop` column filled in. Rows left blank are ignored, so partial
        collection is fine and the script can be re-run as more rows arrive.

Handles the two things that would otherwise make the number wrong:

1. STRATIFIED RE-WEIGHTING. The sample is 20 per predicted class, but the village is
   ~43% cotton and 6% maize. Unweighted accuracy over that sample would answer "how
   accurate are we on a village that is one-fifth each crop", which is not our
   village.

   The weights must come from the TRUE class shares, not our predicted ones. Per-class
   recall is conditioned on the true class, so weighting it by predicted-class area
   would bias the headline toward whatever the map already over-predicts: if we
   over-call Cotton, Cotton would carry 43% of the weight while true Cotton is a
   smaller share of the village. The true shares are unknown a priori, so they are
   ESTIMATED FROM THE SAMPLE ITSELF (which is what a stratified sample is for), with
   the predicted shares reported alongside for comparison.

2. A CHANCE BASELINE. Accuracy alone is uninterpretable when one class is 47% of the
   area -- always predicting cotton scores 47%. Cohen's kappa and a
   predict-the-majority baseline are reported alongside.

Run:  python src/ingest_ground_truth.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import AUX, CROPS, RESULTS, log

GT = AUX / "ground_truth_vf12.csv"
ALIAS = {"paddy": "Rice", "dhan": "Rice", "chawal": "Rice", "rice": "Rice",
         "kapas": "Cotton", "cotton": "Cotton",
         "makai": "Maize", "corn": "Maize", "maize": "Maize",
         "bajri": "Bajra", "pearl millet": "Bajra", "bajra": "Bajra",
         "mungfali": "Groundnut", "peanut": "Groundnut", "groundnut": "Groundnut"}


def norm(v):
    """Map free-text crop names (English/Gujarati transliteration) onto our five."""
    s = str(v).strip().lower()
    if not s or s in ("nan", "none", ""):
        return None
    for k, c in ALIAS.items():
        if k in s:
            return c
    return "Other"


def kappa(a, b, classes):
    n = len(a)
    po = float((a == b).mean())
    pe = sum((a == c).mean() * (b == c).mean() for c in classes)
    return (po - pe) / (1 - pe) if pe < 1 else np.nan, po


def evaluate(truth, pred, label, weights):
    ok = pd.notna(truth) & pd.notna(pred)
    t, p = truth[ok], pred[ok]
    k, raw = kappa(t.values, p.values, CROPS)

    # per-class recall, then re-weight to the village's real class shares
    per, wsum, acc_w = {}, 0.0, 0.0
    for c in CROPS:
        m = t == c
        if m.sum():
            r = float((p[m] == c).mean())
            per[c] = (r, int(m.sum()))
            w = weights.get(c, 0.0)
            acc_w += w * r
            wsum += w
    acc_w = acc_w / wsum if wsum else np.nan

    print(f"\n  --- {label} ---")
    print(f"    n compared            {ok.sum()}")
    print(f"    raw accuracy          {100*raw:.1f}%")
    print(f"    area-weighted accuracy{100*acc_w:>6.1f}%   <- the honest headline")
    print(f"    Cohen's kappa         {k:+.3f}")
    print("    per-class recall:")
    for c, (r, n) in per.items():
        print(f"      {c:11s} {100*r:5.1f}%  (n={n})")
    return dict(label=label, n=int(ok.sum()), raw=round(raw, 4),
                weighted=round(float(acc_w), 4), kappa=round(float(k), 4))


def main():
    if not GT.exists():
        raise SystemExit(
            f"{GT} not found.\nRun `python src/make_gt_sample.py` first, fill in the\n"
            "`vf12_crop` column, and save it as data_aux/ground_truth_vf12.csv")

    g = pd.read_csv(GT)
    g["truth"] = g["vf12_crop"].map(norm)
    filled = g[g.truth.notna()]
    other = (filled.truth == "Other").sum()
    filled = filled[filled.truth != "Other"]
    print(f"collected rows: {len(filled)} usable"
          f"{f' (+{other} outside our five classes, excluded)' if other else ''}"
          f" of {len(g)} in the sheet")
    if len(filled) < 15:
        print("  ! fewer than 15 rows -- numbers below are indicative only")

    sub = pd.read_csv(RESULTS / "submission.csv")
    m = filled.merge(sub[["farm_id", "crop_type"]], on="farm_id",
                     suffixes=("_sheet", ""))

    # Weights for the headline accuracy: the TRUE class shares.
    # Per-class recall is conditioned on the true class, so it must be weighted by
    # true-class prevalence. We do not know that a priori, so estimate it from the
    # stratified sample: within each predicted class the sampled farms are a random
    # draw, so P(true=c) = sum over predicted classes p of P(pred=p) * P(true=c|pred=p),
    # with the second factor measured in the sample and the first from the map's area
    # shares. This is the standard stratified estimator.
    dbg = pd.read_csv(RESULTS / "d4_debug.csv")
    ar = dbg.groupby("crop_type")["area_ha"].sum()
    pred_share = {c: float(ar.get(c, 0)) / float(ar.sum()) for c in CROPS}
    weights = {c: 0.0 for c in CROPS}
    for pcls in CROPS:
        stratum = m[m.crop_type == pcls]
        if not len(stratum):
            continue
        for c in CROPS:
            weights[c] += pred_share[pcls] * float((stratum.truth == c).mean())
    tot = sum(weights.values()) or 1.0
    weights = {c: v / tot for c, v in weights.items()}

    print("\n" + "=" * 66)
    print("MEASURED ACCURACY AGAINST COLLECTED GROUND TRUTH")
    print("=" * 66)
    print(f"  TRUE class weights, stratified estimate: "
          f"{ {c: round(100*w, 1) for c, w in weights.items()} }")
    print(f"  (our map's predicted area shares:        "
          f"{ {c: round(100*w, 1) for c, w in pred_share.items()} })")
    print("  The headline is weighted by the TRUE shares; weighting by our own")
    print("  predicted shares would bias it toward whatever the map over-predicts.")

    res = [evaluate(m.truth, m.crop_type, "Capella X-band map (shipped)", weights)]

    ind = RESULTS / "independent_crop.csv"
    if ind.exists():
        # the field sheet already carries a stale copy of this column; drop it so the
        # merge does not silently suffix and then read the wrong one
        mm = m.drop(columns=[c for c in m.columns if c.startswith("independent_crop")])
        mi = mm.merge(pd.read_csv(ind)[["farm_id", "independent_crop"]], on="farm_id")
        res.append(evaluate(mi.truth, mi.independent_crop,
                            "Independent S2+S1 map (validator)", weights))

    # majority-class baseline: the number any accuracy claim must beat
    maj = max(weights, key=weights.get)
    base = float((m.truth == maj).mean())
    print(f"\n  baseline -- always predict {maj}: {100*base:.1f}%")

    print("\n  confusion (rows = VF-12 truth, cols = our prediction):")
    print(pd.crosstab(m.truth, m.crop_type).to_string())

    # does our own confidence predict correctness? the actionable question
    if "crop_confidence" in m:
        hi = m.crop_confidence >= m.crop_confidence.median()
        corr = (m.truth == m.crop_type)
        print(f"\n  accuracy on high-confidence half {100*corr[hi].mean():.1f}%"
              f"  vs low-confidence half {100*corr[~hi].mean():.1f}%")

    pd.DataFrame(res).to_csv(RESULTS / "ground_truth_accuracy.csv", index=False)
    for r in res:
        log("gt.accuracy", **r)
    print(f"\n  wrote {RESULTS / 'ground_truth_accuracy.csv'}")
    print("\n  Whatever this says, it goes in the writeup. A measured accuracy that")
    print("  disappoints still beats a submission with no measurement at all.")


if __name__ == "__main__":
    main()
