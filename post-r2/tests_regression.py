"""Failure-mode regression suite (D-6 / F3). One assertion per bug that got past someone.

Every check here corresponds to a defect that SURVIVED internal consistency checks in a
competent pipeline -- ours or a competitor's. The point is not coverage, it is that each of
these was invisible until someone went looking.

Run:  py -3.12 post-r2/tests_regression.py
"""
import os
import sys
from pathlib import Path

os.environ.pop("PROJ_LIB", None)

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
AUX = ROOT / "data_aux"

BALE_KG = 170.0     # Indian cotton statistics report production in bales of 170 kg lint
GINNING = 0.34      # lint as a fraction of seed cotton (kapas); published range 33-36%


def test_apy_units_are_homogeneous():
    """e15: the cotton row of vadodara_apy.csv is bales-of-lint, the other four are tonnes.

    production/area reproduces the stated yield at ratio 0.91-1.08 for rice, maize, bajra and
    groundnut, and at 5.76 for cotton. Nothing in the pipeline noticed, because the only yield
    guard is an upper bound (`assert mx < 25.0` in d4_submission) and this defect makes cotton
    2.9x too SMALL. It reaches 47% of our farms and 43% of village area.

    This does not assert which convention is right -- e15 tested that and the evidence did not
    decide. It asserts that the inhomogeneity is still there and still known, so that nobody
    later reads 776 kg/ha as directly comparable to bajra's 2714.
    """
    a = pd.read_csv(AUX / "vadodara_apy.csv").set_index("crop")
    ratio = (1000 * a.production_t_2022_23 / a.area_ha_2022_23) / a.yield_kg_ha_2022_23

    others = ratio.drop("Cotton")
    assert others.between(0.85, 1.15).all(), \
        f"a non-cotton crop changed units: {others.to_dict()}"

    assert ratio["Cotton"] > 3.0, \
        "cotton row now looks unit-consistent -- if the source was corrected, re-run e15"

    # and the bales reading must be the one that explains it
    cot = a.loc["Cotton"]
    as_bales = cot.production_t_2022_23 * BALE_KG / cot.area_ha_2022_23
    assert abs(as_bales / cot.yield_kg_ha_2022_23 - 1.0) < 0.10, \
        f"bales reading no longer reconciles: {as_bales:.0f} vs {cot.yield_kg_ha_2022_23}"


def test_yield_units_not_kg_per_ha():
    """d11_ship's guard, kept here so the suite fails loudly rather than only at ship time."""
    y = pd.read_csv(ROOT / "results" / "submission.csv").yield_estimate_to_date
    assert y.max() < 25.0, f"max yield {y.max()} t/ha -- looks like kg/ha, a unit error"
    # ponytail: the matching LOWER bound is deliberately absent. e15 showed cotton at
    # 0.34 t/ha is defensible under the lint convention, so a lower bound here would
    # fire on a value we decided to keep. Add one only if the anchor convention changes.


def test_no_degenerate_parcel_defines_a_grid():
    """e12: nine parcels enclose ~0 ha and their centroids land up to 835 km away.

    They are legitimate rows in the submission. They are NOT legitimate inputs to anything
    spatial -- they stretched the village extent to '139 x 1110 km' and made a whole
    variance curve meaningless. Orion independently documented ten of them.
    """
    sys.path.insert(0, str(ROOT / "src"))
    from common import farm_centroids
    import numpy as np

    xy = farm_centroids()
    d = np.hypot(xy[:, 0] - np.median(xy[:, 0]), xy[:, 1] - np.median(xy[:, 1]))
    n_bad = int((d > 5000).sum())
    assert n_bad < 20, f"{n_bad} parcels >5 km from the village centre -- geometry regressed"
    assert n_bad > 0, "the degenerate parcels vanished -- if they were cleaned, drop the e12 filter"


def test_field_sheet_is_findable_on_the_ground():
    """e16: a degenerate parcel reached the manual field sheet and would waste a lookup.

    make_gt_sample.py filtered on registry-match quality but not on geometry, so farm 19
    (4.8e-09 ha, centroid 835 km out) was staged for someone to go and identify. Seven such
    parcels were in the eligible pool. Manual lookups are the scarcest resource in this
    project -- Track E is blocked on them -- so one wasted row is 1% of the whole budget.
    """
    t = pd.read_csv(AUX / "ground_truth_TEMPLATE.csv")
    bad = t[t.area_ha < 1e-4]
    assert bad.empty, f"degenerate parcels on the field sheet: {bad.farm_id.tolist()}"
    assert t.overlap_frac.fillna(0).ge(0.5).all(), "ambiguous registry match on the sheet"


def test_field_sheet_stays_stratified():
    """e16: stratified selection is unbiased AND gives per-class recall; uncertainty-first
    selection is biased by -12.4pp. If the sheet ever stops being balanced across crops,
    the estimator in ingest_ground_truth.py is no longer the one e16 validated.
    """
    t = pd.read_csv(AUX / "ground_truth_TEMPLATE.csv")
    n = t.crop_type.value_counts()
    assert n.min() >= 0.5 * n.max(), f"field sheet is no longer stratified: {n.to_dict()}"


if __name__ == "__main__":
    fails = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_"):
            continue
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as e:
            fails += 1
            print(f"FAIL  {name}\n        {e}")
    print(f"\n{fails} failing")
    sys.exit(1 if fails else 0)
