"""e4 -- all six shortlisted submissions, side by side.

e3 compared us against one team. This compares all six, which makes three things
possible that a pairing cannot:

  1. A CONSENSUS crop label by majority vote. Six independent pipelines over the same
     966 parcels is the closest thing to ground truth Sokhda will ever have, and it can
     be tested: does the consensus label separate the withheld optical/C-band witnesses
     better than any single team's map? If yes, the consensus is signal, not an average
     of noise, and our own crop column can finally be scored against something external.

  2. Whether the FIELD agrees on health and yield better than it agrees on crop type.
     Our REPORT already argues the crop label is the weak link. If the health columns
     correlate across teams while the crop columns do not, that is a statement about the
     problem rather than about any one pipeline.

  3. Where we sit: consensus member or outlier, per column.

Every team's file is their published Round 2 deliverable, read-only. Our own submission is
read from results/ and is not modified. Outputs go to post-r2/results/.

Run:  py -3.12 post-r2/experiments/e4_consensus_all.py
"""
import itertools
import os
import sys
from pathlib import Path

os.environ.pop("PROJ_LIB", None)

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from common import RESULTS  # noqa: E402

W = ROOT / "post-r2" / "writeups_submissions"
OUT = ROOT / "post-r2" / "results" / "e4_consensus_all"
OUT.mkdir(parents=True, exist_ok=True)

FILES = {
    "GDHTM":        RESULTS / "submission.csv",
    "CodingBits":   W / "coding_bits" / "submission.csv",
    "8bit":         W / "8_bits" / "submission.csv",
    "Megalodon":    W / "megalodon" / "submission.csv",
    "Orion":        W / "project_orion_team_apes" / "submission.csv",
    "DeepThinkers": W / "deep_thinkers" / "submission_round2.csv",
}
TEAMS = list(FILES)
CROPS = ["Bajra", "Cotton", "Groundnut", "Maize", "Rice"]

LOG = []


def say(t=""):
    print(t)
    LOG.append(t)


def kappa(a, b):
    cats = sorted(set(a) | set(b))
    po = float((a == b).mean())
    pe = sum((a == c).mean() * (b == c).mean() for c in cats)
    return (po - pe) / (1 - pe) if pe < 1 else np.nan


def load():
    crop, health, yld = {}, {}, {}
    for t, p in FILES.items():
        d = pd.read_csv(p).sort_values("farm_id").reset_index(drop=True)
        assert len(d) == 966 and d.farm_id.is_unique, t
        crop[t] = d.set_index("farm_id").crop_type
        health[t] = d.set_index("farm_id").health_index
        yld[t] = d.set_index("farm_id").yield_estimate_to_date
    return pd.DataFrame(crop), pd.DataFrame(health), pd.DataFrame(yld)


def matrix(title, cols, fn, fmt="{:+.3f}"):
    say("=" * 78)
    say(title)
    say("=" * 78)
    say("  " + " " * 13 + "".join(f"{t:>13}" for t in TEAMS))
    for a in TEAMS:
        row = f"  {a:<13}"
        for b in TEAMS:
            row += "            ." if a == b else f"{fmt.format(fn(cols[a], cols[b])):>13}"
        say(row)
    vals = [fn(cols[a], cols[b]) for a, b in itertools.combinations(TEAMS, 2)]
    say(f"  mean off-diagonal: {np.mean(vals):+.3f}   range {min(vals):+.3f} to {max(vals):+.3f}")
    say("")
    return vals


def main():
    crop, health, yld = load()
    area = pd.read_csv(RESULTS / "farm_features.csv").set_index("farm_id").area_ha

    # ---- 1. crop type -------------------------------------------------------
    kv = matrix("1.  CROP TYPE -- pairwise Cohen's kappa",
                crop, lambda a, b: kappa(a.values, b.values))
    say("  kappa 0 = chance. Six independent pipelines, same 966 parcels, same 4 scenes.")
    say("")

    # ---- 2. consensus -------------------------------------------------------
    say("=" * 78)
    say("2.  CONSENSUS BY MAJORITY VOTE")
    say("=" * 78)
    mode = crop.mode(axis=1)[0]
    votes = crop.eq(mode, axis=0).sum(axis=1)
    say(f"  {'agreeing teams':<18}{'farms':>8}{'% of farms':>12}{'% of area':>12}")
    for v in range(1, 7):
        m = votes == v
        if m.sum():
            say(f"  {v}/6{'':<15}{m.sum():>8}{100 * m.mean():>11.1f}%"
                f"{100 * area[m.values].sum() / area.sum():>11.1f}%")
    strong = votes >= 4
    say(f"\n  farms where 4+ of 6 teams agree: {strong.sum()} ({100 * strong.mean():.1f}%)")
    say(f"  farms where 5+ agree:            {(votes >= 5).sum()} ({100 * (votes >= 5).mean():.1f}%)")
    say("")
    say("  agreement with the majority label, per team:")
    for t in TEAMS:
        allf = (crop[t] == mode).mean()
        sub = (crop[t][strong] == mode[strong]).mean()
        mark = "  <- us" if t == "GDHTM" else ""
        say(f"    {t:<14} all farms {100 * allf:>5.1f}%   on the {strong.sum()} "
            f"strong-consensus farms {100 * sub:>5.1f}%{mark}")
    say("")

    # ---- 3. does the consensus beat any single team against the witnesses? ---
    say("=" * 78)
    say("3.  IS THE CONSENSUS SIGNAL, OR AN AVERAGE OF NOISE?")
    say("=" * 78)
    wit = pd.read_csv(RESULTS / "tables" / "witness.csv").set_index("farm_id")

    def eps2(lab, idx, col):
        """Kruskal-Wallis effect size, epsilon^2 = (H-k+1)/(n-k).

        Raw H grows with sample size, so it cannot compare a 292-farm subset against a
        966-farm one. epsilon^2 is normalised and can.
        """
        i = idx.intersection(wit.index)
        g = [wit.loc[i, col][lab[i] == c].dropna() for c in CROPS]
        g = [x for x in g if len(x) >= 5]
        if len(g) < 2:
            return np.nan
        n = sum(len(x) for x in g)
        k = len(g)
        return (stats.kruskal(*g).statistic - k + 1) / (n - k)

    say("  Crop separation on two sensors NO pipeline used as input, as effect size.")
    say("  A consensus that is real should separate them better than its members.")
    say(f"  {'labelling':<16}{'n':>6}{'eps2 NDVI':>11}{'eps2 S1 VH':>12}")
    si = mode.index[strong]
    for t_ in TEAMS:
        say(f"  {t_:<16}{966:>6}{eps2(crop[t_], crop.index, 's2_ndvi_20251013'):>11.4f}"
            f"{eps2(crop[t_], crop.index, 's1_vh_db'):>12.4f}"
            f"{'  <- us' if t_ == 'GDHTM' else ''}")
    say(f"  {'CONSENSUS':<16}{966:>6}{eps2(mode, crop.index, 's2_ndvi_20251013'):>11.4f}"
        f"{eps2(mode, crop.index, 's1_vh_db'):>12.4f}")
    say(f"  {'CONSENSUS(4+)':<16}{len(si):>6}{eps2(mode, si, 's2_ndvi_20251013'):>11.4f}"
        f"{eps2(mode, si, 's1_vh_db'):>12.4f}")
    best = max(eps2(crop[t_], crop.index, "s2_ndvi_20251013") for t_ in TEAMS)
    cons = eps2(mode, crop.index, "s2_ndvi_20251013")
    say("")
    say(f"  best individual map: eps2 = {best:.4f}   consensus: eps2 = {cons:.4f}")
    say("  -> " + ("consensus beats every individual map" if cons > best else
                   "the consensus does NOT beat the best individual map. With pairwise"))
    if cons <= best:
        say("     kappa near 0.06, majority voting averages disagreement rather than")
        say("     accumulating evidence, and destroys signal instead of building it.")
    say("")

    # ---- 4. health and yield ------------------------------------------------
    matrix("4.  HEALTH INDEX -- pairwise Spearman",
           health, lambda a, b: stats.spearmanr(a, b, nan_policy="omit").statistic)
    matrix("5.  YIELD TO DATE -- pairwise Spearman",
           yld, lambda a, b: stats.spearmanr(a, b, nan_policy="omit").statistic)

    # ---- 5. village aggregates ---------------------------------------------
    say("=" * 78)
    say("6.  VILLAGE-LEVEL, THE ONLY LEVEL ANYONE AGREES ON")
    say("=" * 78)
    say("  crop-area share, % of 447.5 ha")
    sh = pd.DataFrame({t: (area.groupby(crop[t]).sum() / area.sum() * 100)
                       for t in TEAMS}).reindex(CROPS).fillna(0.0)
    say(sh.round(2).to_string())
    say(f"\n  spread (max-min) per crop, percentage points:")
    for c in CROPS:
        say(f"    {c:<11}{sh.loc[c].max() - sh.loc[c].min():>6.1f} pp"
            f"   (min {sh.loc[c].min():.1f} {sh.loc[c].idxmin()}, "
            f"max {sh.loc[c].max():.1f} {sh.loc[c].idxmax()})")
    say("")
    say("  village production, t = sum(yield x area)")
    prod = {t: float((yld[t] * area).sum()) for t in TEAMS}
    for t, v in sorted(prod.items(), key=lambda kv: kv[1]):
        say(f"    {t:<14}{v:>9.1f} t{'   <- us' if t == 'GDHTM' else ''}")
    say(f"    {'median':<14}{np.median(list(prod.values())):>9.1f} t")
    say(f"    spread: {max(prod.values()) / min(prod.values()):.2f}x")
    say("")
    say("  health index, mean (area-weighted)")
    for t in TEAMS:
        say(f"    {t:<14}{float((health[t] * area).sum() / area.sum()):>9.1f}"
            f"{'   <- us' if t == 'GDHTM' else ''}")

    # ---- 7. why our yield column anti-correlates with the field --------------
    say("")
    say("=" * 78)
    say("7.  YIELD -- how much of each column is just the crop label?")
    say("=" * 78)
    say(f"  {'team':<14}{'eta2 (crop explains)':>22}   per-crop median t/ha, top 3")
    for t_ in TEAMS:
        g = [yld[t_][crop[t_] == c].dropna() for c in crop[t_].unique()]
        k, n = len(g), sum(len(x) for x in g)
        e = (stats.kruskal(*g).statistic - k + 1) / (n - k)
        med = yld[t_].groupby(crop[t_]).median().sort_values(ascending=False)
        say(f"  {t_:<14}{e:>22.3f}   " + " > ".join(med.index[:3])
            + ("   <- us" if t_ == "GDHTM" else ""))
    say("")
    say("  A high eta2 means the column is mostly a per-crop constant, so it inherits")
    say("  the crop map's disagreement. Ours is 0.82: our yield is largely a step")
    say("  function of a label that no two teams agree on.")
    say("")
    say("  per-crop median yield to date, t/ha, each team on its own labels:")
    tab = pd.DataFrame({t_: yld[t_].groupby(crop[t_]).median() for t_ in TEAMS})
    say(tab.reindex(CROPS).round(2).to_string())
    say("")
    say("  Everyone ranks Groundnut at or near the top and Cotton last. We alone rank")
    say("  Bajra top, at 2.57 t/ha against 1.30-1.88 for every other team. Our anchor is")
    say("  Vadodara APY 2022-23, 2714 kg/ha, drawn from a district base of just 7,022 ha")
    say("  (groundnut's base is thinner still at 1,004 ha). Megalodon hit the same problem")
    say("  and fell back to the Gujarat state figure for any crop too thinly sown for a")
    say("  district mean to be stable. A single year off a thin base is exactly the")
    say("  condition under which a district statistic is an outlier.")
    say("")
    say("  This corroborates our own REPORT 7.2, which already flags bajra as the crop")
    say("  whose season-integral term contradicts the witness (rho -0.219). Two")
    say("  independent lines now point at bajra: our own witness, and five other teams.")

    # ---- outputs ------------------------------------------------------------
    out = pd.DataFrame({f"crop_{t}": crop[t] for t in TEAMS})
    out["consensus"] = mode
    out["n_agree"] = votes
    out["gdhtm_matches_consensus"] = (crop["GDHTM"] == mode)
    out.to_csv(OUT / "consensus_crop.csv")
    sh.to_csv(OUT / "village_shares.csv")
    (OUT / "report.txt").write_text("\n".join(LOG) + "\n", encoding="utf8")
    print(f"\nwritten: {OUT}")


if __name__ == "__main__":
    main()
