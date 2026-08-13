"""Verify that every number quoted in the writeup matches the shipped artefacts.

A writeup drifts from its pipeline the moment either is edited, and a judge checking one
number against the CSV is the cheapest way to lose credibility. This asserts the two
agree, so drift fails loudly instead of shipping quietly.

Run:  python src/check_writeup.py
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent))
import d4_submission as D4
from common import CROPS, RESULTS, RESULTS_AUX, ROOT, log

FAILED = []


def check(label, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label:40s} {detail}")
    if not ok:
        FAILED.append(label)


def main():
    # WRITEUP.md (the old flat draft) is gone -- the shipped text now lives across three
    # documents: the mailed report, the Kaggle writeup guide, and the pasteable Kaggle
    # description. A number quoted in any one of them must still match the CSV.
    w = "\n".join((ROOT / "docs" / name).read_text(encoding="utf8") for name in
                  ("REPORT.md", "KAGGLE_WRITEUP.md", "KAGGLE_DESCRIPTION_PASTE.md"))
    sub = pd.read_csv(RESULTS / "submission.csv")
    dbg = pd.read_csv(RESULTS / "d4_debug.csv")
    f = pd.read_csv(RESULTS / "farm_features.csv")

    print("=" * 70)
    print("WRITEUP NUMBERS vs SHIPPED ARTEFACTS")
    print("=" * 70)

    check("966 farms", len(sub) == 966 and "966" in w, f"rows={len(sub)}")

    prov = dbg.source.value_counts()
    for n, key, word in [(895, "measured", "895"),
                         (52, "imputed_spatial_same_crop", "52"),
                         (19, "rfi_flagged", "19")]:
        got = int(prov.get(key, 0))
        check(f"provenance {key}", got == n and word in w, f"{got}")

    cot = float(sub.loc[sub.crop_type == "Cotton", "yield_estimate_to_date"].median())
    check("cotton median yield 0.34 t/ha", abs(cot - 0.34) < 0.01 and "0.34 t/ha" in w,
          f"{cot:.3f}")

    # weights quoted in prose must equal the shipped ones, and the shipped ones must
    # equal what the blind rule derives from the features
    derived = D4.derive_health_weights(f)
    same = all(abs(D4.HEALTH_W[k] - v) < 5e-3 for k, v in derived.items())
    check("HEALTH_W == blind derivation", same,
          str({k: round(v, 3) for k, v in derived.items()}))
    quoted = {k: float(v) for k, v in
              re.findall(r"`(growth|uniform|persist|level)` (0\.\d+)", w)}
    check("writeup quotes the shipped weights",
          bool(quoted) and all(abs(D4.HEALTH_W[k] - v) < 1e-6 for k, v in quoted.items()),
          str(quoted))

    # the completion-sign claim in section 1: all five crops positive
    wit = pd.read_csv(RESULTS_AUX / "witness.csv")
    m = sub.merge(f.drop(columns=["area_ha"], errors="ignore"), on="farm_id")
    m = m.merge(wit, on="farm_id")
    allpos = True
    for c in CROPS:
        g = m[m.crop_type == c]
        ok = np.isfinite(g.d_oct_aug) & np.isfinite(g.s2_ndvi_20251013)
        allpos &= spearmanr(g.d_oct_aug[ok], g.s2_ndvi_20251013[ok]).statistic > 0
    check("completion sign: all 5 crops positive", allpos, "supports the inverted sign")

    worst = max(abs(spearmanr(g.health_index, g.yield_estimate_to_date).statistic)
                for c in CROPS for g in [sub[sub.crop_type == c]] if len(g) > 10)
    check("yield is not a relabelling of health", worst < 0.99, f"max |rho| {worst:.3f}")

    check("crop vocabulary", not (set(sub.crop_type) - set(CROPS)))

    # The writeup now states how we READ the spec -- "yield to date, not a final harvest
    # forecast" -- and quotes the completion constants that implement that reading. If a
    # constant changes, the prose becomes a false description of the shipped column, so
    # assert the quoted numbers against COMPLETION itself.
    quoted_comp = all(f"{v:.2f}" in w for v in set(D4.COMPLETION.values()))
    check("writeup quotes the completion constants", quoted_comp,
          str(D4.COMPLETION))
    # ...and that the column really is scaled by them: the per-crop median must sit at or
    # below the anchor, never above it, or we would be forecasting the harvest.
    apy = pd.read_csv(D4.AUX / "vadodara_apy.csv").set_index("crop")
    never_over = all(
        float(sub.loc[sub.crop_type == c, "yield_estimate_to_date"].median())
        <= float(apy.loc[c, "yield_kg_ha_2022_23"]) / 1000.0 for c in CROPS)
    check("yield is to-date, never above the anchor", never_over,
          "no crop median exceeds its full-season anchor")

    # The matched season-integrated witness. The writeup quotes three signed numbers and
    # calls one of them a contradiction; recompute all three, including the sign, so a
    # later change to the witness or the feature cannot leave the prose asserting the
    # opposite of the data.
    sp = RESULTS_AUX / "witness_season.csv"
    if sp.exists():
        ms = m.merge(pd.read_csv(sp), on="farm_id")
        for c, want in [("Cotton", 0.305), ("Rice", 0.290), ("Bajra", -0.219)]:
            g = ms[ms.crop_type == c]
            ok = np.isfinite(g.season_integral) & np.isfinite(g.s1_vh_season_integral)
            got = float(spearmanr(g.season_integral[ok], g.s1_vh_season_integral[ok]).statistic)
            check(f"matched witness {c}",
                  abs(got - want) < 0.01 and np.sign(got) == np.sign(want)
                  and f"{abs(want):.3f}" in w,
                  f"{got:+.3f} (writeup {want:+.3f})")

    print()
    if FAILED:
        print(f"{len(FAILED)} MISMATCH(ES): " + "; ".join(FAILED))
        log("check_writeup", status="FAIL", failed=len(FAILED))
        sys.exit(1)
    print("All writeup claims match the shipped artefacts.")
    log("check_writeup", status="PASS")


if __name__ == "__main__":
    main()
