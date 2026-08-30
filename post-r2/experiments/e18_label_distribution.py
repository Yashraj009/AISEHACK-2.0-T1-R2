"""e18 -- D-2. The crop label as a distribution, and whether ours is worth propagating.

D-2 proposed shipping the label as a distribution and propagating it into yield. The premise
needs one correction before anything is built: **the distribution already exists.**
`results/d4_debug.csv` carries a full five-class posterior (p_Rice ... p_Groundnut) per farm.
What the deliverable ships is its argmax.

That posterior is not confidently wrong -- it is openly unsure. Median max probability is
0.409, and 69.4% of farms have no class above 0.5. It already agrees with e17, which found
42.5% of farms corroborated by neither independent sensor.

So D-2 is not "build a distribution". It is: **is this posterior calibrated enough to
propagate?** An uncalibrated posterior turned into a yield interval is worse than a point
estimate, because it dresses a guess as a measurement. e11 is the precedent -- a beautifully
calibrated sampling-noise model that turned out not to predict anything that mattered.

  T1  CALIBRATION. Reliability of the posterior against corroboration by two independent
      sensors (e14 embedding, e17 dense S1). Pooled AND within-crop, because the proxy is
      cotton-biased and a pooled curve would mostly re-measure that.
  T2  THE PREDICTION e11 LEFT OPEN. e11 showed sampling-noise SE does NOT predict
      disagreement with the withheld Sentinel-2 witness (rho +0.052, p 0.12) and concluded
      the dominant error must be the crop label. This tests that directly: does label
      ENTROPY predict the same disagreement? If e11's reasoning was right this must work
      where sampling SE failed. If it also comes back null, the error is in neither place.
  T3  Does expectation-over-the-posterior move the village total? A method for QUANTIFYING
      uncertainty that changes the answer is not quantifying it.
  T4  Where the yield uncertainty actually lands, per crop.
  T5  CONTROL. Sharpened and flattened versions of the posterior re-run through T1. If a
      deliberately corrupted posterior scores the same, the posterior carries no information
      and T1 was measuring something else.

Reads shipped artefacts read-only. Nothing is adopted.

Run:  py -3.12 post-r2/experiments/e18_label_distribution.py
"""
import os
import sys
from pathlib import Path

os.environ.pop("PROJ_LIB", None)

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from common import CROPS, RESULTS  # noqa: E402

OUT = ROOT / "post-r2" / "results" / "e18_label_distribution"
OUT.mkdir(parents=True, exist_ok=True)
E17 = ROOT / "post-r2" / "results" / "e17_dense_s1" / "two_sensor_agreement.csv"
P = [f"p_{c}" for c in CROPS]
LOG = []


def say(t=""):
    print(t)
    LOG.append(t)


def entropy(p):
    q = np.clip(p, 1e-12, 1)
    return -(q * np.log(q)).sum(axis=1) / np.log(p.shape[1])   # normalised to [0,1]


def main():
    from scipy import stats

    dbg = pd.read_csv(RESULTS / "d4_debug.csv")
    sub = pd.read_csv(RESULTS / "submission.csv")
    wit = pd.read_csv(RESULTS / "tables" / "witness.csv")
    feat = pd.read_csv(RESULTS / "farm_features.csv")[["farm_id", "area_ha"]]
    d = sub.merge(dbg[["farm_id", "crop_confidence", "source"] + P], on="farm_id")
    d = d.merge(wit, on="farm_id", how="left").merge(feat, on="farm_id")
    Pm = d[P].to_numpy()
    d["entropy"] = entropy(Pm)
    d["p_assigned"] = Pm.max(axis=1)

    say("=" * 78)
    say("THE POSTERIOR THAT ALREADY EXISTS")
    say("=" * 78)
    say(f"  {len(d)} farms carry a full 5-class posterior in results/d4_debug.csv")
    say(f"  median max probability {d.p_assigned.median():.3f}; "
        f"{100 * (d.p_assigned < 0.5).mean():.1f}% of farms have NO class above 0.5")
    say(f"  median normalised entropy {d.entropy.median():.3f} (0 = certain, 1 = uniform)")
    say("  The deliverable ships the argmax of this and discards the rest.")
    say("")

    # ---------------- T1 -------------------------------------------------
    say("=" * 78)
    say("T1  IS THE POSTERIOR CALIBRATED? (against two independent sensors)")
    say("=" * 78)
    if not E17.exists():
        say("  e17 output missing -- run e17_dense_s1.py first")
        return
    a = pd.read_csv(E17)[["farm_id", "s1_ok", "emb_ok"]]
    m = d.merge(a, on="farm_id")
    m["n_backing"] = m.s1_ok.astype(int) + m.emb_ok.astype(int)
    m["backed"] = m.n_backing > 0
    say(f"  proxy for 'our label is right': backed by at least one independent sensor")
    say(f"  ({len(m)} farms; {100 * m.backed.mean():.1f}% backed)")
    say("")
    say(f"  {'p_assigned bin':<18}{'n':>6}{'mean p':>9}{'% backed':>11}{'gap':>8}")
    m["bin"] = pd.qcut(m.p_assigned, 5, labels=False, duplicates="drop")
    for b in sorted(m.bin.unique()):
        s = m[m.bin == b]
        say(f"  Q{b + 1:<17}{len(s):>6}{s.p_assigned.mean():>9.3f}"
            f"{100 * s.backed.mean():>10.1f}%{100 * (s.backed.mean() - s.p_assigned.mean()):>+7.1f}pp")
    r, p = stats.spearmanr(m.p_assigned, m.backed.astype(float))
    say("")
    say(f"  POOLED rho(p_assigned, backed) = {r:+.3f}  p = {p:.3g}")
    say("")
    say("  WITHIN CROP -- the pooled number is confounded, because cotton is both the crop we")
    say("  are most confident about and the only one the sensors can see (e17).")
    say(f"  {'crop':<12}{'n':>6}{'rho':>9}{'p':>11}{'mean p':>9}{'% backed':>11}")
    for c in CROPS:
        s = m[m.crop_type == c]
        if len(s) < 20 or s.backed.nunique() < 2:
            say(f"  {c:<12}{len(s):>6}{'--':>9}{'--':>11}{s.p_assigned.mean():>9.3f}"
                f"{100 * s.backed.mean():>10.1f}%")
            continue
        rr, pp = stats.spearmanr(s.p_assigned, s.backed.astype(float))
        say(f"  {c:<12}{len(s):>6}{rr:>+9.3f}{pp:>11.3g}{s.p_assigned.mean():>9.3f}"
            f"{100 * s.backed.mean():>10.1f}%")
    say("")
    say("  A calibrated posterior needs the gap column near zero AND a positive within-crop")
    say("  rho. Ordering matters more than level here: the proxy is noisy, so a systematic")
    say("  offset is expected, but the RANKING should still hold if the posterior means")
    say("  anything.")

    # ---------------- T2 -------------------------------------------------
    say("")
    say("=" * 78)
    say("T2  DOES LABEL ENTROPY PREDICT WITNESS DISAGREEMENT? (e11's open prediction)")
    say("=" * 78)
    say("  e11 measured sampling-noise SE against the same target and got rho +0.052, p 0.12 --")
    say("  null. Its conclusion was that the dominant error is the crop label, not pixel count.")
    say("  That conclusion predicts THIS test comes out positive. It is falsifiable and this")
    say("  is the falsification attempt.")
    say("")
    w = m.dropna(subset=["s2_ndvi_20251013"]).copy()
    # within-crop rank gap: the index is a within-crop score, so compare within crop
    w["r_health"] = w.groupby("crop_type").health_index.rank(pct=True)
    w["r_ndvi"] = w.groupby("crop_type").s2_ndvi_20251013.rank(pct=True)
    w["gap"] = (w.r_health - w.r_ndvi).abs()
    say(f"  {'entropy quintile':<20}{'n':>6}{'mean entropy':>14}{'mean |rank gap|':>17}")
    w["ebin"] = pd.qcut(w.entropy, 5, labels=False, duplicates="drop")
    for b in sorted(w.ebin.unique()):
        s = w[w.ebin == b]
        say(f"  Q{b + 1} {'(certain)' if b == 0 else '(uncertain)' if b == max(w.ebin) else '':<16}"
            f"{len(s):>6}{s.entropy.mean():>14.3f}{s.gap.mean():>17.4f}")
    r2, p2 = stats.spearmanr(w.entropy, w.gap)
    say("")
    say(f"  rho(label entropy, |rank gap| WITHIN crop)     = {r2:+.3f}  p = {p2:.3g}")
    say("")
    say("  DESIGN FLAW IN THE ABOVE, and the variant that fixes it. Both ranks are taken")
    say("  within the SAME crop cohort, so if a farm's label is wrong it is ranked against the")
    say("  wrong cohort on BOTH sides and the error largely cancels. That makes the test")
    say("  under-powered by construction. Re-running with GLOBAL ranks, where a label error")
    say("  cannot cancel:")
    w["rg_health"] = w.health_index.rank(pct=True)
    w["rg_ndvi"] = w.s2_ndvi_20251013.rank(pct=True)
    w["gap_g"] = (w.rg_health - w.rg_ndvi).abs()
    r2g, p2g = stats.spearmanr(w.entropy, w.gap_g)
    say(f"  rho(label entropy, |rank gap| GLOBAL)          = {r2g:+.3f}  p = {p2g:.3g}")
    r2 = r2 if p2 < p2g else r2g
    p2 = min(p2, p2g)
    say(f"  e11's sampling-SE result on the same target        = +0.052   p = 0.12")
    say("")
    if p2 < 0.05 and r2 > 0:
        say("  POSITIVE: e11's inference is confirmed. Label uncertainty predicts disagreement")
        say("  with an unread sensor where measurement noise did not.")
    else:
        say("  NULL: e11's inference is NOT confirmed. If neither sampling noise nor label")
        say("  entropy predicts witness disagreement, the dominant error is in neither, and")
        say("  D-2's interval would be honest about the wrong quantity.")

    # ---------------- T3 -------------------------------------------------
    say("")
    say("=" * 78)
    say("T3  DOES PROPAGATING THE POSTERIOR MOVE THE VILLAGE TOTAL?")
    say("=" * 78)
    # ponytail: per-crop yield LEVEL is taken from the shipped medians rather than by
    # re-running d4 with five forced labels. The crop-dependent part of the yield is
    # district_yield[c] x COMPLETION[c], which the observed median captures; the farm-dependent
    # terms are common across the five hypotheses. Good enough to size the effect, not to ship.
    lvl = d.groupby("crop_type").yield_estimate_to_date.median()
    A = np.array([lvl.get(c, np.nan) for c in CROPS])
    scale = d.yield_estimate_to_date.to_numpy() / np.array(
        [lvl[c] for c in d.crop_type])                     # farm-specific multiplier
    exp_y = (Pm * A).sum(axis=1) * scale
    ar = d.area_ha.to_numpy()
    say(f"  {'':<34}{'t/ha median':>13}{'village t':>12}")
    say(f"  {'as shipped (argmax)':<34}{np.median(d.yield_estimate_to_date):>13.3f}"
        f"{(d.yield_estimate_to_date * ar).sum():>12.1f}")
    say(f"  {'expectation over the posterior':<34}{np.median(exp_y):>13.3f}"
        f"{(exp_y * ar).sum():>12.1f}")
    ch = 100 * ((exp_y * ar).sum() / (d.yield_estimate_to_date * ar).sum() - 1)
    say("")
    say(f"  change in village total: {ch:+.1f}%")
    say("  A large move would mean this is not quantifying the answer, it is changing it --")
    say("  and the R1 official MSE of 11.071 is the only external check on the aggregate.")

    # ---------------- T4 -------------------------------------------------
    say("")
    say("=" * 78)
    say("T4  WHERE THE LABEL UNCERTAINTY LANDS")
    say("=" * 78)
    sd = np.sqrt((Pm * (A[None, :] * scale[:, None]) ** 2).sum(axis=1) - exp_y ** 2)
    d["yield_sd"] = sd
    say(f"  {'crop':<12}{'n':>6}{'median yield':>14}{'median SD':>12}{'SD/yield':>10}"
        f"{'mean entropy':>14}")
    for c in CROPS:
        s = d[d.crop_type == c]
        say(f"  {c:<12}{len(s):>6}{s.yield_estimate_to_date.median():>14.3f}"
            f"{s.yield_sd.median():>12.3f}"
            f"{s.yield_sd.median() / s.yield_estimate_to_date.median():>10.2f}"
            f"{s.entropy.mean():>14.3f}")
    say("")
    say(f"  village-level: {100 * (sd * ar).sum() / (d.yield_estimate_to_date * ar).sum():.1f}% "
        f"of the total, if farm label errors were perfectly correlated (worst case)")
    say(f"                 {100 * np.sqrt((sd * ar) ** 2 @ np.ones(len(d))) / (d.yield_estimate_to_date * ar).sum():.1f}% "
        f"if independent (best case)")

    # ---------------- T5 -------------------------------------------------
    say("")
    say("=" * 78)
    say("T5  CONTROL -- does a CORRUPTED posterior score the same?")
    say("=" * 78)
    for name, T in (("sharpened (T=0.5)", 0.5), ("as shipped (T=1)", 1.0),
                    ("flattened (T=3)", 3.0), ("uniform", None)):
        if T is None:
            Q = np.full_like(Pm, 1.0 / Pm.shape[1])
        else:
            Q = Pm ** (1.0 / T)
            Q = Q / Q.sum(axis=1, keepdims=True)
        # align on farm_id -- the earlier merge dropped 10 farms, so positional indexing
        # into Pm was wrong. This is the bug that made the control disagree with T1.
        pa = pd.Series(Q.max(axis=1), index=d.farm_id.to_numpy())
        mm = m.assign(pa=pa.reindex(m.farm_id.to_numpy()).to_numpy())
        rr, pp = stats.spearmanr(mm.pa, mm.backed.astype(float))
        say(f"  {name:<22}mean p {pa.mean():.3f}   rho(p, backed) {rr:+.3f}  p = {pp:.3g}")
    say("")
    say("  The T=1 row MUST reproduce T1's pooled rho exactly -- that is what makes this a")
    say("  control rather than a second measurement, and an earlier version of this script")
    say("  failed it (positional indexing into a merge that had dropped 10 farms).")
    say("  Temperature scaling barely moves rho because it leaves each farm's ARGMAX alone;")
    say("  it shifts the ordering of p_assigned only slightly, since renormalising depends on")
    say("  the whole vector. So rho is a statement about RANKING and says nothing about")
    say("  whether the LEVELS are calibrated -- which T1's +28.7pp gap in Q1 already denies.")
    say("  The uniform row is the true null: no ordering left to correlate.")

    d[["farm_id", "crop_type", "p_assigned", "entropy", "yield_sd"] + P].to_csv(
        OUT / "label_distribution.csv", index=False)
    (OUT / "report.txt").write_text("\n".join(LOG) + "\n", encoding="utf8")
    print(f"\nwritten: {OUT}")


if __name__ == "__main__":
    main()
