"""Stage D11 -- the final gate before submission.

One script, run last. It answers exactly one question: is what we are about to
upload complete, and does it match the host's own schema reference byte for byte
where it has to?

Everything here is checked against `Sokhda_Dummy_Submission.xlsx` -- the host's
file, not our assumptions about it. That file already caught a 1000x unit error
[R1] that every internal check passed, so it is the authority on schema.

Run:  python src/d11_ship.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CROPS, RESULTS, log

ROOT = Path(__file__).resolve().parent.parent
HOST = ROOT / "Sokhda_Dummy_Submission.xlsx"

# The five deliverables the brief asks for. Missing one is a zero on that
# rubric line no matter how good the model is, so they are checked as data.
DELIVERABLES = {
    "submission.csv": RESULTS / "submission.csv",
    "writeup (<=4 pages)": ROOT / "docs" / "WRITEUP.md",
    "public notebook": ROOT / "notebooks" / "I9_pipeline.ipynb",
    "cover image": RESULTS / "figures" / "cover.png",
    # the two maps the Round 2 guidelines require BY NAME, not just "some gallery figure"
    "required health map": RESULTS / "figures" / "gallery_01_health_index_map.png",
    "required yield map": RESULTS / "figures" / "gallery_02_yield_to_date_map.png",
}

CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}{'  ' + detail if detail else ''}")
    return ok


def main():
    log("d11.start")
    sub = pd.read_csv(RESULTS / "submission.csv")
    host = pd.read_excel(HOST)

    print("\n" + "=" * 68 + "\n1. SCHEMA vs the host's own dummy submission\n" + "=" * 68)
    check("column names + order identical", list(sub.columns) == list(host.columns),
          f"{list(sub.columns)}")
    check("row count identical", len(sub) == len(host), f"{len(sub)} rows")
    check("farm_id set identical", set(sub.farm_id) == set(host.farm_id),
          f"{sub.farm_id.min()}-{sub.farm_id.max()}")
    check("farm_id unique", sub.farm_id.is_unique)
    check("village_id identical", set(sub.village_id) == set(host.village_id),
          f"village_id={sorted(set(sub.village_id))}")
    check("crop vocabulary within ours", set(sub.crop_type) <= set(CROPS),
          f"{sorted(set(sub.crop_type))}")
    check("no nulls anywhere", int(sub.isna().sum().sum()) == 0)

    print("\n" + "=" * 68 + "\n2. VALUE RANGES\n" + "=" * 68)
    h, y = sub.health_index, sub.yield_estimate_to_date
    check("health_index in 0-100", h.between(0, 100).all(), f"{h.min():.2f}-{h.max():.2f}")
    # UNIT GUARD, the one that matters. The host dummy runs 1.24-9.00, so the
    # column is t/ha. A kg/ha value passes every other check on this page and is
    # wrong by 1000x -- this line is the only thing standing between us and that.
    check("yield is t/ha not kg/ha", y.max() < 25.0,
          f"max {y.max():.3f} t/ha (host dummy max {host.yield_estimate_to_date.max():.2f})")
    check("yield non-negative", (y >= 0).all(), f"min {y.min():.3f}")

    print("\n" + "=" * 68 + "\n3. DELIVERABLES PRESENT\n" + "=" * 68)
    for name, p in DELIVERABLES.items():
        check(name, p.exists(), f"{p.stat().st_size // 1024} KB" if p.exists() else "MISSING")
    gal = sorted((RESULTS / "figures").glob("gallery_*.png"))
    check("gallery has >=6 figures", len(gal) >= 6, f"{len(gal)} figures")

    print("\n" + "=" * 68 + "\n4. CONTENT SANITY\n" + "=" * 68)
    words = len((ROOT / "docs" / "WRITEUP.md").read_text(encoding="utf-8").split())
    # ~650 words/page at this formatting; 4 pages is the hard cap in the brief.
    check("writeup under 4 pages", words < 2600, f"{words} words ~ {words / 650:.1f} pages")
    nb = (ROOT / "notebooks" / "I9_pipeline.ipynb").read_text(encoding="utf-8")
    check("notebook has no stored errors", '"output_type": "error"' not in nb)

    n_fail = sum(1 for _, ok, _ in CHECKS if not ok)
    print("\n" + "=" * 68)
    print(f"  {len(CHECKS) - n_fail}/{len(CHECKS)} passed")
    log("d11.done", checks=len(CHECKS), failed=n_fail,
        status="READY" if n_fail == 0 else "BLOCKED")
    if n_fail:
        print("  NOT READY -- fix the above before uploading.")
        sys.exit(1)
    print("  READY TO SUBMIT.")
    print("=" * 68)


if __name__ == "__main__":
    main()
