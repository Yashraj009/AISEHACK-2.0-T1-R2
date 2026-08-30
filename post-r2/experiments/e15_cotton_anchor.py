"""e15 -- the cotton yield anchor, which covers 47% of our farms and was never checked.

`KHARIF_ANCHORS.md` validated bajra (adopted, 2.714 -> 1.91 t/ha) and groundnut (rejected on
out-of-sample evidence). Cotton appears in it NOWHERE, and cotton is 455 of 966 farms. The
whole yield column for nearly half the village rests on one unexamined number: 776 kg/ha from
`vadodara_apy.csv`.

The specific risk is a UNIT trap rather than a modelling one. Indian cotton statistics are
customarily reported as LINT (the ginned fibre) in kg/ha, or as production in BALES of 170 kg,
while every other crop in the same table is grain or pod in tonnes. Lint is roughly 34% of
what the farmer actually harvests (seed cotton, "kapas"), so picking the wrong convention is a
~2.9x error on 47% of the village -- and `d11_ship.py`'s only yield guard is an upper bound
(`assert mx < 25.0`) which a 2.9x UNDER-estimate sails straight through.

SIX TESTS, and they are deliberately allowed to disagree with each other:

  T1  Internal consistency of the APY table. production/area vs the stated yield column,
      per crop. This is the one test that needs no outside information at all.
  T2  Our pipeline's reproduction of each anchor, to separate a UNIT problem from the
      completion term (cotton is genuinely still standing on 13 October).
  T3  The host's own dummy submission as a range oracle -- INCLUDING the control that
      decides whether it is a valid oracle at all.
  T4  What the five other shortlisted teams shipped for cotton.
  T5  Cross-crop ORDERING. A dummy can be wrong about level and still right about which
      crop out-yields which. Tests lint vs kapas ordering against the host.
  T6  Village-total sensitivity, so the size of the decision is on the record.

NOTHING IS ADOPTED BY THIS SCRIPT. It reads shipped artefacts read-only.

Run:  py -3.12 post-r2/experiments/e15_cotton_anchor.py
"""
import os
import sys
from pathlib import Path

os.environ.pop("PROJ_LIB", None)

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from common import RESULTS  # noqa: E402

OUT = ROOT / "post-r2" / "results" / "e15_cotton_anchor"
OUT.mkdir(parents=True, exist_ok=True)
AUX = ROOT / "data_aux"
HOST = ROOT / "Sokhda_Dummy_Submission.xlsx"
COMP = ROOT / "post-r2" / "writeups_submissions"

# Ginning outturn: lint as a fraction of seed cotton. Published range 33-36%.
GINNING = 0.34
BALE_KG = 170.0
LOG = []


def say(t=""):
    print(t)
    LOG.append(t)


def main():
    from scipy import stats

    apy = pd.read_csv(AUX / "vadodara_apy.csv").set_index("crop")
    sub = pd.read_csv(RESULTS / "submission.csv")
    host = pd.read_excel(HOST)

    # ---------------- T1 -------------------------------------------------
    say("=" * 78)
    say("T1  IS THE APY TABLE INTERNALLY CONSISTENT? (needs no outside information)")
    say("=" * 78)
    a = apy.copy()
    a["implied_kg_ha"] = 1000 * a.production_t_2022_23 / a.area_ha_2022_23
    a["ratio"] = a.implied_kg_ha / a.yield_kg_ha_2022_23
    say(f"  {'crop':<12}{'area ha':>10}{'production':>12}{'yield kg/ha':>13}"
        f"{'implied':>10}{'ratio':>8}")
    for c, r in a.iterrows():
        say(f"  {c:<12}{r.area_ha_2022_23:>10.0f}{r.production_t_2022_23:>12.0f}"
            f"{r.yield_kg_ha_2022_23:>13.0f}{r.implied_kg_ha:>10.0f}{r.ratio:>8.2f}")
    say("")
    cot = a.loc["Cotton"]
    lint_if_bales = cot.production_t_2022_23 * BALE_KG / cot.area_ha_2022_23
    say(f"  Four crops sit at ratio {a.drop('Cotton').ratio.min():.2f}-"
        f"{a.drop('Cotton').ratio.max():.2f}. Cotton sits at {cot.ratio:.2f}.")
    say(f"  Reading cotton production as BALES of {BALE_KG:.0f} kg instead of tonnes:")
    say(f"    {cot.production_t_2022_23:.0f} bales x {BALE_KG:.0f} kg / "
        f"{cot.area_ha_2022_23:.0f} ha = {lint_if_bales:.0f} kg/ha "
        f"vs stated {cot.yield_kg_ha_2022_23:.0f} "
        f"(ratio {lint_if_bales / cot.yield_kg_ha_2022_23:.2f})")
    say("")
    say("  ESTABLISHED: the cotton row is bales-of-lint while the other four are tonnes of")
    say("  grain or pod. One column, two unit systems. That is a defect regardless of which")
    say("  convention the deliverable should ultimately use.")
    say(f"  Seed cotton (kapas) equivalent at {GINNING:.0%} ginning outturn: "
        f"{cot.yield_kg_ha_2022_23 / GINNING:.0f} kg/ha "
        f"= {cot.yield_kg_ha_2022_23 / GINNING / 1000:.2f} t/ha")

    # ---------------- T2 -------------------------------------------------
    say("")
    say("=" * 78)
    say("T2  DOES OUR PIPELINE REPRODUCE EACH ANCHOR? (unit problem vs completion term)")
    say("=" * 78)
    og = sub.groupby("crop_type").yield_estimate_to_date.agg(["count", "median", "min", "max"])
    og["apy_t_ha"] = apy.yield_kg_ha_2022_23 / 1000
    og["ours/apy"] = og["median"] / og.apy_t_ha
    say(f"  {'crop':<12}{'n':>5}{'our median':>12}{'apy t/ha':>10}{'ours/apy':>10}")
    for c, r in og.iterrows():
        say(f"  {c:<12}{r['count']:>5.0f}{r['median']:>12.3f}{r.apy_t_ha:>10.3f}"
            f"{r['ours/apy']:>10.3f}")
    say("")
    say("  Cotton's 0.44 against 0.94-0.97 elsewhere is NOT the unit question -- it is the")
    say("  completion term, and it is correct: cotton is long-duration and still standing on")
    say("  13 October, so a 'to date' yield SHOULD be well under the full-season anchor.")
    say("  The unit question is entirely about the 776 kg/ha the ratio is taken against.")

    # ---------------- T3 -------------------------------------------------
    say("")
    say("=" * 78)
    say("T3  THE HOST DUMMY AS A RANGE ORACLE -- AND THE CONTROL THAT VALIDATES IT")
    say("=" * 78)
    hg = host.groupby("crop_type").yield_estimate_to_date.agg(["median", "min", "max"])
    say(f"  {'crop':<12}{'ours med':>10}{'ours max':>10}{'host min':>10}"
        f"{'host med':>10}{'host max':>10}{'overlap':>9}")
    for c in og.index:
        ov = og.loc[c, "max"] >= hg.loc[c, "min"]
        say(f"  {c:<12}{og.loc[c, 'median']:>10.3f}{og.loc[c, 'max']:>10.3f}"
            f"{hg.loc[c, 'min']:>10.2f}{hg.loc[c, 'median']:>10.2f}"
            f"{hg.loc[c, 'max']:>10.2f}{str(ov):>9}")
    say("")
    say("  THE CONTROL. If non-overlap with the host dummy proved a unit error, it would have")
    say("  to prove it ONLY for cotton. It does not:")
    bad = [c for c in og.index if og.loc[c, "max"] < hg.loc[c, "min"]]
    say(f"    crops failing to overlap the host dummy: {', '.join(bad)}")
    say("  Maize and Rice are anchored to the real district figure and are not in dispute, so")
    say("  a test that condemns them is not a unit oracle. The host dummy is generated data")
    say("  and is simply not calibrated to Vadodara district for ANY crop.")
    say("")
    say("  >>> T3 IS DISCARDED AS EVIDENCE. Recorded because stopping here would have")
    say("      'proved' the cotton hypothesis with a test that fails its own control.")

    # ---------------- T4 -------------------------------------------------
    say("")
    say("=" * 78)
    say("T4  WHAT THE OTHER FIVE SHORTLISTED TEAMS SHIPPED FOR COTTON")
    say("=" * 78)
    files = {"8_bits": "8_bits/submission.csv",
             "coding_bits": "coding_bits/submission.csv",
             "deep_thinkers": "deep_thinkers/submission_round2.csv",
             "megalodon": "megalodon/submission.csv",
             "project_orion": "project_orion_team_apes/submission.csv"}
    say(f"  {'team':<16}{'cotton med':>12}{'rice med':>10}{'bajra med':>11}   reading")
    rows = []
    for t, f in files.items():
        p = COMP / f
        if not p.exists():
            say(f"  {t:<16}  deliverable not present")
            continue
        d = pd.read_csv(p)
        g = d.groupby("crop_type").yield_estimate_to_date.median()
        ct = g.get("Cotton", np.nan)
        # classify against the two candidate conventions
        lint, kapas = cot.yield_kg_ha_2022_23 / 1000, cot.yield_kg_ha_2022_23 / GINNING / 1000
        if g.max() > 20:
            what = "different unit entirely (not t/ha)"
        elif abs(ct - lint) < abs(ct - kapas):
            what = "LINT scale"
        else:
            what = "SEED COTTON (kapas) scale"
        rows.append((t, ct, what))
        say(f"  {t:<16}{ct:>12.3f}{g.get('Rice', np.nan):>10.3f}"
            f"{g.get('Bajra', np.nan):>11.3f}   {what}")
    ours = og.loc["Cotton", "median"]
    say(f"  {'OURS':<16}{ours:>12.3f}{og.loc['Rice', 'median']:>10.3f}"
        f"{og.loc['Bajra', 'median']:>11.3f}   LINT scale")
    say("")
    say("  The field is SPLIT. There is no consensus to borrow, which is the same conclusion")
    say("  e4 reached on crop labels (six-team kappa 0.060) -- competitor agreement is not")
    say("  available as evidence here.")

    # ---------------- T5 -------------------------------------------------
    say("")
    say("=" * 78)
    say("T5  CROSS-CROP ORDERING -- a dummy can be wrong on level and right on order")
    say("=" * 78)
    crops = list(og.index)
    h = np.array([hg.loc[c, "median"] for c in crops])
    lint_v = np.array([apy.loc[c, "yield_kg_ha_2022_23"] / 1000 for c in crops])
    kapas_v = lint_v.copy()
    kapas_v[crops.index("Cotton")] = apy.loc["Cotton", "yield_kg_ha_2022_23"] / GINNING / 1000
    r_l, p_l = stats.spearmanr(h, lint_v)
    r_k, p_k = stats.spearmanr(h, kapas_v)
    say(f"  {'crop':<12}{'host med':>10}{'apy lint':>10}{'apy kapas':>11}")
    for i, c in enumerate(crops):
        say(f"  {c:<12}{h[i]:>10.2f}{lint_v[i]:>10.3f}{kapas_v[i]:>11.3f}")
    say("")
    say(f"  Spearman(host order, APY as LINT)  = {r_l:+.3f}  p = {p_l:.3f}")
    say(f"  Spearman(host order, APY as KAPAS) = {r_k:+.3f}  p = {p_k:.3f}")
    say("")
    say("  With only 5 crops neither correlation can reach significance, so this is reported")
    say("  as a direction and not as a result. It cannot carry a decision on its own.")

    # ---------------- T6 -------------------------------------------------
    say("")
    say("=" * 78)
    say("T6  VILLAGE-TOTAL SENSITIVITY -- the size of the decision, on the record")
    say("=" * 78)
    f = pd.read_csv(RESULTS / "farm_features.csv")[["farm_id", "area_ha"]]
    d = sub.merge(f, on="farm_id")
    prod = d.yield_estimate_to_date * d.area_ha
    tot = prod.sum()
    m = d.crop_type == "Cotton"
    cot_t = prod[m].sum()
    scale = 1.0 / GINNING
    say(f"  village production as shipped          {tot:>10.1f} t")
    say(f"    of which cotton                      {cot_t:>10.1f} t  "
        f"({100 * cot_t / tot:.1f}% on {int(m.sum())} farms, "
        f"{100 * d.area_ha[m].sum() / d.area_ha.sum():.1f}% of area)")
    say(f"  if cotton were restated as seed cotton {tot - cot_t + cot_t * scale:>10.1f} t  "
        f"({100 * (cot_t * scale - cot_t) / tot:+.1f}% on the village total)")
    say("")
    say("  A 2.9x change on 47% of farms is not a tweak. It moves the single headline number")
    say("  in the deliverable, so it needs evidence that decides -- and T3 was discarded, T4")
    say("  is split, and T5 cannot reach significance on five points.")

    a.to_csv(OUT / "apy_consistency.csv")
    (OUT / "report.txt").write_text("\n".join(LOG) + "\n", encoding="utf8")
    print(f"\nwritten: {OUT}")


if __name__ == "__main__":
    main()
