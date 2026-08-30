"""e3 -- how far do we agree with a competitor on crop type?

Our crop column is the weakest part of the submission and we say so: REPORT 7.1 reports
Cohen's kappa = +0.103 against our own independent rebuild. That is a self-comparison.
Six teams labelled the SAME 966 farms, so an external comparison is possible for the
first time, and one team published theirs:

    notebook  kaggle.com/code/oindrieelmondal/final-submission-for-anrf-aisehack-2-0-round-2
    aux data  kaggle.com/datasets/oindrieelmondal/auxiliary-dataset
    phase 1   kaggle.com/datasets/oindrieelmondal/anrf-2-phase1

They report 50.8% of their own farms carrying crop-type confidence below 0.40, so this is
agreement between two uncertain labellings, not a test against truth. Read it that way:
high agreement is evidence both found the same structure; low agreement bounds how much
either can claim per-farm.

REQUIRES Kaggle credentials. Put a token at ~/.kaggle/kaggle.json
(kaggle.com -> Settings -> API -> Create New Token), then:

    py -3.12 post-r2/experiments/e3_consensus.py

Reads shipped artefacts only; writes to post-r2/results/.
"""
import os
import subprocess
import sys
from pathlib import Path

os.environ.pop("PROJ_LIB", None)

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from common import RESULTS  # noqa: E402

OUT = ROOT / "post-r2" / "results" / "e3_consensus"
DL = OUT / "download"
KERNEL = "oindrieelmondal/final-submission-for-anrf-aisehack-2-0-round-2"


def have_creds():
    return (Path.home() / ".kaggle" / "kaggle.json").exists() or os.environ.get("KAGGLE_USERNAME")


def fetch():
    """Pull the competitor's kernel output. Their submission.csv is an output file."""
    DL.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, "-m", "kaggle", "kernels", "output", KERNEL,
                        "-p", str(DL)], capture_output=True, text=True)
    print(r.stdout or "", r.stderr or "")
    hits = sorted(DL.rglob("*.csv"))
    if not hits:
        raise SystemExit("no CSV in the kernel output -- check the slug or fetch by hand")
    return hits


def pick_submission(paths):
    """The competitor file we want has our five required columns and 966 rows."""
    need = {"farm_id", "crop_type"}
    for p in paths:
        try:
            d = pd.read_csv(p)
        except Exception:
            continue
        if need <= set(d.columns) and len(d) == 966:
            print(f"using {p.name}  ({len(d)} rows)")
            return d
    raise SystemExit(f"none of {[p.name for p in paths]} looks like a 966-row submission")


def kappa(a, b):
    """Cohen's kappa, so the number is comparable to the +0.103 we already report."""
    cats = sorted(set(a) | set(b))
    n = len(a)
    po = float((a == b).sum()) / n
    pe = sum((a == c).mean() * (b == c).mean() for c in cats)
    return (po - pe) / (1 - pe), po


def main():
    if not have_creds():
        print("No Kaggle credentials found.")
        print("  1. kaggle.com -> Settings -> API -> Create New Token")
        print(f"  2. save the file as {Path.home() / '.kaggle' / 'kaggle.json'}")
        print("  3. re-run this script")
        return

    OUT.mkdir(parents=True, exist_ok=True)
    theirs = pick_submission(fetch())
    ours = pd.read_csv(RESULTS / "submission.csv")
    f = pd.read_csv(RESULTS / "farm_features.csv")[["farm_id", "area_ha"]]

    m = (ours[["farm_id", "crop_type"]]
         .merge(theirs[["farm_id", "crop_type"]], on="farm_id", suffixes=("_ours", "_theirs"))
         .merge(f, on="farm_id"))
    print(f"\nmatched {len(m)} farms\n")

    k, po = kappa(m.crop_type_ours.values, m.crop_type_theirs.values)
    print("=" * 70)
    print(f"AGREEMENT     raw {100 * po:.1f}%      Cohen's kappa {k:+.3f}")
    print(f"              our own independent rebuild scored kappa +0.103 (REPORT 7.1)")
    print("=" * 70)

    print("\nconfusion, ours (rows) against theirs (cols), farm counts:")
    print(pd.crosstab(m.crop_type_ours, m.crop_type_theirs).to_string())

    print("\nper-crop: of the farms WE call X, what share do they agree on?")
    for c, g in m.groupby("crop_type_ours"):
        agree = (g.crop_type_theirs == c).mean()
        print(f"  {c:<10} n={len(g):>3}   {100 * agree:>5.1f}%")

    print("\nvillage area share, the level our product is designed to be read at:")
    a = m.groupby("crop_type_ours").area_ha.sum() / m.area_ha.sum() * 100
    b = m.groupby("crop_type_theirs").area_ha.sum() / m.area_ha.sum() * 100
    cmp = pd.DataFrame({"ours %": a, "theirs %": b}).fillna(0)
    cmp["delta"] = cmp["ours %"] - cmp["theirs %"]
    print(cmp.round(2).to_string())
    print(f"\n  mean |delta| across crops: {cmp.delta.abs().mean():.2f} pp")
    print("  A small aggregate delta with a low per-farm kappa is the expected signature")
    print("  of two pipelines that agree on the village mix and not on which farm is which")
    print("  -- exactly the claim REPORT 7.2 already makes about reading level.")

    m.to_csv(OUT / "crop_agreement.csv", index=False)
    print(f"\nwritten: {OUT / 'crop_agreement.csv'}")


if __name__ == "__main__":
    main()
