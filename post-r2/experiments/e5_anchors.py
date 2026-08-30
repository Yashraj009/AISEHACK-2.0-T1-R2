"""e5 -- the yield anchors, and whether fixing bajra puts us back in the field.

e4 found our yield column negatively correlated with three of five teams -- the only team
in that position -- and traced it to two things:

  1. 82% of our yield variance is the crop label alone (eta^2 = 0.820), so the column
     inherits the crop map's disagreement wholesale.
  2. Our per-crop ORDERING is inverted: we alone rank bajra top.

Our anchors come from `data_aux/vadodara_apy.csv`, Vadodara 2022-23. Bajra's yield there is
2,714 kg/ha off a district area base of just 7,022 ha (2.5% of the five-crop area);
groundnut's base is thinner still at 1,004 ha (0.35%).

`data_aux/SOURCES.md` already contains a RETRACTED section conceding that this table is
"a bad prior for this village" for exactly the thin-base crops -- but that retraction was
applied to the AREA prior only. We kept using the same table's YIELDS as anchors for the
same thin crops. That is the inconsistency this experiment tests.

Megalodon stated the rule we lack: a district figure is only usable where the district
sows enough of the crop for the mean to be stable, and otherwise the state figure is the
honest fallback.

The falsifiable question: if the bajra anchor alone is corrected to the external consensus,
does our yield column stop anti-correlating with the rest of the field? Because the anchor
is a per-crop multiplicative constant, this needs no pipeline rerun -- it is one scalar per
crop, applied exactly.

Reads shipped artefacts read-only. Writes to post-r2/results/. Nothing in results/ or
docs/ is modified.

Run:  py -3.12 post-r2/experiments/e5_anchors.py
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
from common import RESULTS  # noqa: E402

W = ROOT / "post-r2" / "writeups_submissions"
OUT = ROOT / "post-r2" / "results" / "e5_anchors"
OUT.mkdir(parents=True, exist_ok=True)

OTHERS = {
    "CodingBits":   W / "coding_bits" / "submission.csv",
    "8bit":         W / "8_bits" / "submission.csv",
    "Megalodon":    W / "megalodon" / "submission.csv",
    "Orion":        W / "project_orion_team_apes" / "submission.csv",
    "DeepThinkers": W / "deep_thinkers" / "submission_round2.csv",
}

# Full-season t/ha as each team states it in its own writeup, with the source named.
# Cotton is deliberately excluded from the comparison: the teams quote it in two different
# units (lint vs kapas, ~34% ginning outturn), so the numbers are not comparable as printed.
EXTERNAL = {
    #                     Bajra  Groundnut  Maize   Rice
    "Orion (GJ 1st Adv Est 24-25)":      dict(Bajra=1.79, Groundnut=3.03, Maize=3.11, Rice=2.54),
    "DeepThinkers (GJ 3rd Adv Est 25-26)": dict(Bajra=1.36, Groundnut=2.73, Maize=2.03, Rice=1.74),
    "Megalodon (Vadodara post-2014 rec)": dict(Bajra=1.89, Groundnut=1.94, Rice=2.00),
}
COMPLETION = {"Rice": 0.95, "Maize": 0.95, "Bajra": 0.95, "Groundnut": 0.75, "Cotton": 0.45}

LOG = []


def say(t=""):
    print(t)
    LOG.append(t)


def main():
    apy = pd.read_csv(ROOT / "data_aux" / "vadodara_apy.csv").set_index("crop")
    ours_full = (apy.yield_kg_ha_2022_23 / 1000.0)

    say("=" * 78)
    say("1.  OUR ANCHOR AGAINST THREE INDEPENDENTLY SOURCED GOVERNMENT STATISTICS")
    say("=" * 78)
    say("  full-season t/ha. Cotton omitted: teams quote lint and kapas, not comparable.")
    say(f"  {'crop':<11}{'OURS':>8}{'base ha':>10}" +
        "".join(f"{k.split(' (')[0]:>15}" for k in EXTERNAL) + f"{'ext median':>12}{'ours vs':>10}")
    fix = {}
    for c in ["Bajra", "Groundnut", "Maize", "Rice"]:
        vals = [v[c] for v in EXTERNAL.values() if c in v]
        med = float(np.median(vals))
        o = float(ours_full[c])
        fix[c] = med
        row = (f"  {c:<11}{o:>8.2f}{int(apy.area_ha_2022_23[c]):>10,}" +
               "".join(f"{v.get(c, float('nan')):>15.2f}" for v in EXTERNAL.values()) +
               f"{med:>12.2f}{100 * (o / med - 1):>+9.0f}%")
        say(row)
    say("")
    say("  Bajra is the outlier: +52% above the external median, off a 7,022 ha base.")
    say("  Everything else sits within 15% of it. Cotton, checked separately, is fine:")
    say("  our 0.776 t/ha lint is ~2.28 t/ha kapas at a 34% ginning outturn, against")
    say("  Orion's 2.45 and Megalodon's 2.10 kapas.")
    say("")

    say("=" * 78)
    say("2.  THE RULE WE LACK, AND WHAT IT WOULD HAVE CAUGHT")
    say("=" * 78)
    say("  Megalodon: a district yield is usable only where the district sows enough of")
    say("  the crop for the mean to be stable; otherwise fall back to the state figure.")
    say("")
    say(f"  {'crop':<11}{'district base ha':>18}{'% of 5-crop area':>19}   district mean usable?")
    for c in ["Cotton", "Rice", "Maize", "Bajra", "Groundnut"]:
        a = int(apy.area_ha_2022_23[c])
        sh = 100 * float(apy.area_share_of_5crops[c])
        ok = "yes" if a >= 20000 else "NO -- fall back to state"
        say(f"  {c:<11}{a:>18,}{sh:>18.2f}%   {ok}")
    say("")
    say("  A 20,000 ha threshold is one defensible choice and must be declared, not tuned.")
    say("  It flags bajra and groundnut -- the same two crops SOURCES.md already retracted")
    say("  an AREA claim about. We applied that retraction to the area prior and not to the")
    say("  yield anchor drawn from the same rows of the same table.")
    say("")

    # ---- 3. does correcting bajra put us back in the field? -----------------
    say("=" * 78)
    say("3.  DOES CORRECTING BAJRA ALONE FIX THE ANTI-CORRELATION?")
    say("=" * 78)
    sub = pd.read_csv(RESULTS / "submission.csv").set_index("farm_id")
    scale = fix["Bajra"] / float(ours_full["Bajra"])
    say(f"  anchor 2.714 -> {fix['Bajra']:.2f} t/ha, a scalar of {scale:.4f} on bajra farms only.")
    say(f"  bajra median yield to date {COMPLETION['Bajra'] * float(ours_full['Bajra']):.2f}"
        f" -> {COMPLETION['Bajra'] * fix['Bajra']:.2f} t/ha")

    corrected = sub.yield_estimate_to_date.copy()
    corrected[sub.crop_type == "Bajra"] *= scale

    say("")
    say(f"  {'vs team':<15}{'shipped rho':>13}{'corrected rho':>15}{'change':>10}")
    deltas = []
    for t, p in OTHERS.items():
        o = pd.read_csv(p).set_index("farm_id").yield_estimate_to_date
        a = stats.spearmanr(sub.yield_estimate_to_date, o, nan_policy="omit").statistic
        b = stats.spearmanr(corrected, o, nan_policy="omit").statistic
        deltas.append(b - a)
        say(f"  {t:<15}{a:>+13.3f}{b:>+15.3f}{b - a:>+10.3f}")
    say(f"  {'mean':<15}{'':>13}{'':>15}{np.mean(deltas):>+10.3f}")
    say("")

    # the witness our own report says bajra contradicts
    wit = ROOT / "results" / "tables" / "witness_season.csv"
    if wit.exists():
        ws = pd.read_csv(wit).set_index("farm_id")
        col = [c for c in ws.columns if "s1" in c.lower() or "vh" in c.lower()]
        if col:
            bj = sub.index[sub.crop_type == "Bajra"].intersection(ws.index)
            r = stats.spearmanr(sub.loc[bj, "yield_estimate_to_date"],
                                ws.loc[bj, col[0]], nan_policy="omit").statistic
            say(f"  Note: rescaling one crop by a positive scalar cannot change that crop's")
            say(f"  WITHIN-crop rank, so the bajra witness contradiction (REPORT 7.2) is")
            say(f"  untouched by this fix: rho stays {r:+.3f}. The anchor sets the LEVEL;")
            say(f"  the witness disagreement is about the within-crop ORDERING. Two separate")
            say(f"  defects, both real, and only one of them is fixed here.")
    say("")

    say("=" * 78)
    say("4.  EFFECT ON THE VILLAGE TOTAL")
    say("=" * 78)
    area = pd.read_csv(RESULTS / "farm_features.csv").set_index("farm_id").area_ha
    a0 = float((sub.yield_estimate_to_date * area).sum())
    a1 = float((corrected * area).sum())
    say(f"  shipped     {a0:8.1f} t")
    say(f"  corrected   {a1:8.1f} t   ({100 * (a1 / a0 - 1):+.1f}%)")
    say(f"  Megalodon   {578.3:8.1f} t     (the team we already agree with to 3%)")
    say("")
    say("  Bajra is 9.45% of area, so a 34% cut to its anchor moves the village total by")
    say(f"  {100 * (a1 / a0 - 1):+.1f}%. The correction is real but small at aggregate level --")
    say("  the same pattern as the calibration fix in e1, and for the same reason: this")
    say("  product is built from ranks and shares, so level errors stay contained.")

    pd.DataFrame({"farm_id": sub.index, "crop_type": sub.crop_type,
                  "yield_shipped": sub.yield_estimate_to_date,
                  "yield_anchor_corrected": corrected}).to_csv(
        OUT / "yield_anchor_corrected.csv", index=False)
    (OUT / "report.txt").write_text("\n".join(LOG) + "\n", encoding="utf8")
    print(f"\nwritten: {OUT}")


if __name__ == "__main__":
    main()
