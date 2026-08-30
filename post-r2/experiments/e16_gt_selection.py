"""e16 -- how to spend 100 manual ground-truth lookups. Tests my OWN D-3 proposal.

`ROUND3_DIRECTIONS.md` D-3 proposed re-sorting the staged ground-truth sample by active
learning: pick the farms where Capella and the e14 embedding disagree, where predicted SE is
highest, and where e14 found no corroboration (rice, maize, bajra). The cited evidence was
that spatially explicit active learning reaches 80% accuracy at 97 samples against 169 for
conventional selection.

THAT CITATION IS ABOUT A DIFFERENT JOB. Active learning selects TRAINING labels to improve a
classifier. Our sample does not train anything -- `src/ingest_ground_truth.py` uses it to
MEASURE the accuracy of a map that is already frozen. Those two goals want opposite samples:

  * measuring accuracy wants a sample whose selection is independent of correctness
  * improving a map wants exactly the farms most likely to be wrong

Selecting the hardest farms and then averaging correctness over them estimates the accuracy of
the hard farms, not of the village. So the proposal has to be tested before it is adopted,
and the thing to test is whether it BIASES the number the sample exists to produce.

  T1  Bias and RMSE of the estimated village accuracy, per selection scheme, over many
      synthetic replicates where the truth is known by construction.
  T2  The competing objective: errors DISCOVERED per 100 lookups. This is where active
      learning should win, and if it does the two goals are formally in conflict.
  T3  Can inverse-probability weighting rescue an uncertainty-first sample?
  T4  A hybrid that serves both, and whether its headline stays unbiased.
  T5  Defects in the sample that is actually staged right now.

The synthetic truth is generated so that our label is more often wrong where our confidence is
low -- if correctness were independent of confidence, every scheme would be unbiased and the
test would be vacuous. The strength of that dependence is swept, because the whole question is
how much it matters.

Reads shipped artefacts read-only. Writes to post-r2/results/.

Run:  py -3.12 post-r2/experiments/e16_gt_selection.py
"""
import os
import sys
from pathlib import Path

os.environ.pop("PROJ_LIB", None)

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from common import CROPS, RESULTS, farm_centroids  # noqa: E402

OUT = ROOT / "post-r2" / "results" / "e16_gt_selection"
OUT.mkdir(parents=True, exist_ok=True)
AUX = ROOT / "data_aux"
E14 = ROOT / "post-r2" / "results" / "e14_embeddings" / "farm_embed_pred.csv"

N_BUDGET = 100
N_REP = 400
SEED = 7
LOG = []


def say(t=""):
    print(t)
    LOG.append(t)


def load():
    sub = pd.read_csv(RESULTS / "submission.csv")
    dbg = pd.read_csv(RESULTS / "d4_debug.csv")[["farm_id", "crop_confidence", "area_ha",
                                                 "source"]]
    d = sub.merge(dbg, on="farm_id")
    if E14.exists():
        e = pd.read_csv(E14)[["farm_id", "pred_embed"]]
        d = d.merge(e, on="farm_id", how="left")
        d["embed_disagree"] = (d.pred_embed.notna()
                               & (d.pred_embed != d.crop_type)).astype(float)
    else:
        d["embed_disagree"] = 0.0
    # drop degenerate geometry -- they cannot be found on the ground
    xy = farm_centroids()[d.farm_id.to_numpy() - 1]
    far = np.hypot(xy[:, 0] - np.median(xy[:, 0]), xy[:, 1] - np.median(xy[:, 1])) > 5000
    d = d[~far & (d.area_ha > 1e-4)].reset_index(drop=True)
    return d


def synth_truth(d, rng, strength, base_acc=0.65):
    """Truth where our label is wrong more often at low confidence.

    strength=0 -> correctness independent of confidence (every scheme must be unbiased).
    strength=1 -> strong dependence. The sweep is the point.
    """
    c = d.crop_confidence.to_numpy()
    c = (c - c.mean()) / (c.std() + 1e-9)
    lo = 1 / (1 + np.exp(-strength * c))            # in (0,1), rises with confidence
    p = base_acc + (lo - lo.mean()) * strength * 0.6
    p = np.clip(p, 0.02, 0.98)
    correct = rng.random(len(d)) < p
    truth = d.crop_type.to_numpy().copy()
    wrong = ~correct
    alt = rng.choice(CROPS, size=int(wrong.sum()))
    same = alt == truth[wrong]
    while same.any():                                # ensure a wrong label really differs
        alt[same] = rng.choice(CROPS, size=int(same.sum()))
        same = alt == truth[wrong]
    truth[wrong] = alt
    return truth, correct


def est_simple(idx, correct):
    return float(correct[idx].mean())


def est_stratified(idx, correct, d):
    """Per-class recall re-weighted by the sample's own estimate of true class shares.

    This is what src/ingest_ground_truth.py does, reproduced here so the test measures the
    estimator we actually ship rather than an idealised one.
    """
    lab = d.crop_type.to_numpy()[idx]
    ok = correct[idx]
    accs, ws = [], []
    for c in CROPS:
        m = lab == c
        if m.sum() == 0:
            continue
        accs.append(ok[m].mean())
        ws.append((d.crop_type == c).mean())        # population predicted share
    return float(np.average(accs, weights=ws))


def pick(scheme, d, rng, n=N_BUDGET):
    N = len(d)
    if scheme == "random":
        return rng.choice(N, n, replace=False)
    if scheme == "stratified":
        out = []
        per = n // len(CROPS)
        for c in CROPS:
            pool = np.flatnonzero(d.crop_type.to_numpy() == c)
            out.append(rng.choice(pool, min(per, len(pool)), replace=False))
        return np.concatenate(out)
    if scheme == "uncertain":
        # the naive D-3 proposal: lowest confidence first, embedding disagreement as a
        # tie-break. Deterministic, so jitter to avoid an identical sample every replicate.
        score = (-d.crop_confidence.to_numpy() + 0.5 * d.embed_disagree.to_numpy()
                 + rng.normal(0, 0.01, N))
        return np.argsort(-score)[:n]
    if scheme == "hybrid":
        # 70 stratified for the headline, 30 targeted at the crops e14 could not corroborate
        head = pick("stratified", d, rng, 70)
        rest = np.setdiff1d(np.arange(N), head)
        tgt = d.crop_type.to_numpy()[rest]
        pool = rest[np.isin(tgt, ["Rice", "Maize", "Bajra"])]
        take = rng.choice(pool, min(30, len(pool)), replace=False)
        return np.concatenate([head, take])
    raise ValueError(scheme)


def main():
    d = load()
    say("=" * 78)
    say("POPULATION")
    say("=" * 78)
    say(f"  {len(d)} farms after dropping degenerate geometry")
    say(f"  crop mix: " + ", ".join(f"{c} {(d.crop_type == c).sum()}" for c in CROPS))
    say(f"  embedding disagrees with us on {100 * d.embed_disagree.mean():.1f}% of farms")
    say(f"  budget under test: {N_BUDGET} manual lookups, {N_REP} synthetic replicates")
    say("")

    # ---------------- T1 / T3 --------------------------------------------
    say("=" * 78)
    say("T1  DOES THE SELECTION SCHEME BIAS THE ACCURACY ESTIMATE?")
    say("=" * 78)
    say("  strength = how strongly our correctness depends on our own confidence.")
    say("  At strength 0 every scheme MUST be unbiased -- that is the control.")
    say("")
    rows = []
    for strength in (0.0, 0.5, 1.0, 1.5):
        rng = np.random.default_rng(SEED)
        acc = {k: [] for k in ("random", "stratified", "uncertain", "uncertain_ipw",
                               "hybrid")}
        true = []
        for _ in range(N_REP):
            truth, correct = synth_truth(d, rng, strength)
            true.append(correct.mean())
            for s in ("random", "stratified", "uncertain", "hybrid"):
                idx = pick(s, d, rng)
                if s == "stratified":
                    acc[s].append(est_stratified(idx, correct, d))
                elif s == "hybrid":
                    acc[s].append(est_stratified(idx[:70], correct, d))
                else:
                    acc[s].append(est_simple(idx, correct))
                if s == "uncertain":
                    # T3: inverse-probability weighting. Selection is deterministic in
                    # confidence, so weight each drawn farm by 1/(its selection propensity),
                    # approximated by the confidence decile's sampling fraction.
                    dec = pd.qcut(d.crop_confidence, 10, labels=False, duplicates="drop")
                    sel = np.zeros(len(d), bool)
                    sel[idx] = True
                    frac = pd.Series(sel).groupby(dec).mean()
                    w = 1.0 / frac.reindex(dec[idx]).to_numpy()
                    w = np.where(np.isfinite(w), w, 0.0)
                    acc["uncertain_ipw"].append(
                        float(np.average(correct[idx], weights=w)) if w.sum() > 0 else np.nan)
        tr = np.mean(true)
        say(f"  --- dependence strength {strength:.1f}   true village accuracy "
            f"{100 * tr:.1f}%")
        say(f"  {'scheme':<20}{'mean est':>10}{'bias':>9}{'RMSE':>9}")
        for s in ("random", "stratified", "uncertain", "uncertain_ipw", "hybrid"):
            a = np.array(acc[s], float)
            bias = np.nanmean(a) - tr
            rmse = float(np.sqrt(np.nanmean((a - np.array(true)) ** 2)))
            rows.append((strength, s, np.nanmean(a), bias, rmse))
            say(f"  {s:<20}{100 * np.nanmean(a):>9.1f}%{100 * bias:>+8.1f}pp"
                f"{100 * rmse:>8.1f}pp")
        say("")
    pd.DataFrame(rows, columns=["strength", "scheme", "mean_est", "bias", "rmse"]).to_csv(
        OUT / "bias.csv", index=False)

    # ---------------- T2 -------------------------------------------------
    say("=" * 78)
    say("T2  THE COMPETING OBJECTIVE -- errors FOUND per 100 lookups")
    say("=" * 78)
    rng = np.random.default_rng(SEED)
    found = {k: [] for k in ("random", "stratified", "uncertain", "hybrid")}
    for _ in range(N_REP):
        _, correct = synth_truth(d, rng, 1.0)
        for s in found:
            found[s].append(int((~correct[pick(s, d, rng)]).sum())
                            if s != "hybrid" else int((~correct[pick(s, d, rng)]).sum()))
    say(f"  {'scheme':<20}{'errors found / 100':>20}")
    for s in ("random", "stratified", "uncertain", "hybrid"):
        say(f"  {s:<20}{np.mean(found[s]):>20.1f}")
    say("")
    say("  If uncertainty-first wins here and loses T1, the two goals are formally in")
    say("  conflict and one sample cannot serve both without being split.")

    # ---------------- T5 -------------------------------------------------
    say("")
    say("=" * 78)
    say("T5  DEFECTS IN THE SAMPLE THAT IS STAGED RIGHT NOW")
    say("=" * 78)
    t = pd.read_csv(AUX / "ground_truth_TEMPLATE.csv")
    deg = t[t.area_ha < 1e-4]
    say(f"  staged rows: {len(t)}, filled: {int(t.vf12_crop.notna().sum())}")
    say(f"  stratification: {dict(t.crop_type.value_counts())}")
    say(f"  degenerate-geometry rows (area < 1e-4 ha): {len(deg)} "
        f"-> farm_id {deg.farm_id.tolist()}")
    say("    e12 found nine such parcels village-wide; one reached the field sheet. A parcel")
    say("    enclosing ~0 ha cannot be found on the ground, so that lookup is wasted.")
    xy = farm_centroids()[t.farm_id.to_numpy() - 1]
    far = np.hypot(xy[:, 0] - np.median(xy[:, 0]), xy[:, 1] - np.median(xy[:, 1])) > 5000
    say(f"  rows whose centroid is >5 km from the village: {int(far.sum())} "
        f"-> farm_id {t.farm_id[far].tolist()}")
    say(f"  rows with an ambiguous registry match (<0.5): "
        f"{int((t.overlap_frac.fillna(0) < 0.5).sum())}")
    say(f"  agreement with the independent map: {100 * (t.crop_type == t.independent_crop).mean():.0f}%")

    (OUT / "report.txt").write_text("\n".join(LOG) + "\n", encoding="utf8")
    print(f"\nwritten: {OUT}")


if __name__ == "__main__":
    main()
