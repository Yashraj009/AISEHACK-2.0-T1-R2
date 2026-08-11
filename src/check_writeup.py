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
from common import CROPS, RESULTS, ROOT, log

FAILED = []


def check(label, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label:40s} {detail}")
    if not ok:
        FAILED.append(label)


def main():
    w = (ROOT / "docs" / "WRITEUP.md").read_text(encoding="utf8")
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
    check("cotton median yield 0.35 t/ha", abs(cot - 0.35) < 0.02 and "0.35 t/ha" in w,
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
    wit = pd.read_csv(RESULTS / "witness.csv")
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

    print()
    if FAILED:
        print(f"{len(FAILED)} MISMATCH(ES): " + "; ".join(FAILED))
        log("check_writeup", status="FAIL", failed=len(FAILED))
        sys.exit(1)
    print("All writeup claims match the shipped artefacts.")
    log("check_writeup", status="PASS")


if __name__ == "__main__":
    main()
