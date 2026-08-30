"""e10 -- rebuild the yield anchors from KHARIF-only, multi-year district statistics.

e6 established the defect by mechanism rather than by copying anyone: our anchors come from
`data_aux/vadodara_apy.csv`, which is an ANNUAL district figure, applied to a deliverable
that observes 6 Jun - 13 Oct 2025. That is kharif. Gujarat grows bajra in two seasons and
they are not comparable -- summer irrigated bajra runs 4,000-5,000 kg/ha against 1,200-1,800
rainfed kharif -- so an all-season mean lands high, which is exactly where ours sits (+52%
above the external median, off a district base of only 7,022 ha).

Two independent problems, one fix each:

  SEASON     an annual mean answers a different question than a kharif deliverable asks.
             -> filter to Season == Kharif.
  THIN BASE  a single district-year off 7,022 ha (bajra) or 1,004 ha (groundnut) is
             unstable by construction.
             -> average over many years, and report the spread so the instability is visible
                rather than assumed away.

Source: data.gov.in resource 35be999b-0208-4354-b557-f6ca9a5355de,
"District-wise, season-wise crop production statistics from 1997", 246,091 records,
fields State_Name / District_Name / Crop_Year / Season / Crop / Area / Production.

This is a NEW external dataset: the census in e9 confirmed no competitor used it, and it is
the only source found that separates kharif from the annual figure at district level.

Nothing is adopted here. The script reports what the kharif anchors would be, what changes,
and by how much -- the shipped submission is not touched.

Needs a free data.gov.in API key at ~/.config/aisehack/datagovin.key

Run:  py -3.12 post-r2/experiments/e10_kharif_anchors.py
"""
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

os.environ.pop("PROJ_LIB", None)

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from common import RESULTS  # noqa: E402

OUT = ROOT / "post-r2" / "results" / "e10_kharif_anchors"
OUT.mkdir(parents=True, exist_ok=True)
CACHE = OUT / "vadodara_season_crops.csv"
RID = "35be999b-0208-4354-b557-f6ca9a5355de"
KEYFILE = Path.home() / ".config" / "aisehack" / "datagovin.key"

# Their spellings differ from ours; map onto the submission vocabulary.
CROPMAP = {"Rice": "Rice", "Cotton(lint)": "Cotton", "Maize": "Maize",
           "Bajra": "Bajra", "Groundnut": "Groundnut"}
COMPLETION = {"Rice": 0.95, "Maize": 0.95, "Bajra": 0.95, "Groundnut": 0.75, "Cotton": 0.45}

LOG = []


def say(t=""):
    print(t)
    LOG.append(t)


def fetch_gujarat():
    """Page the API for every Gujarat record. Cached, so it is pulled once."""
    if CACHE.exists():
        return pd.read_csv(CACHE)
    key = KEYFILE.read_text(encoding="utf8").strip()
    rows, off, lim = [], 0, 250   # 1000 times out on this endpoint; 250 is reliable
    while True:
        q = urllib.parse.urlencode({"api-key": key, "format": "json", "limit": lim,
                                    "offset": off, "filters[state_name]": "Gujarat",
                                    "filters[district_name]": "VADODARA"})
        with urllib.request.urlopen(f"https://api.data.gov.in/resource/{RID}?{q}",
                                    timeout=60) as r:
            d = json.loads(r.read())
        recs = d.get("records", [])
        rows += recs
        if len(recs) < lim:
            break
        off += lim
        if off > 40000:
            break
    df = pd.DataFrame(rows)
    df.to_csv(CACHE, index=False)
    return df


def main():
    if not KEYFILE.exists():
        say(f"No data.gov.in key at {KEYFILE}. Get a free one at data.gov.in and save it there.")
        return

    df = fetch_gujarat()
    say("=" * 78)
    say("1.  SOURCE")
    say("=" * 78)
    say(f"  data.gov.in {RID}")
    say(f"  Gujarat records: {len(df):,}")
    if df.empty:
        say("  nothing returned -- check the key or the filter")
        return
    dcol = "district_name" if "district_name" in df else "District_Name"
    scol = "season" if "season" in df else "Season"
    ccol = "crop" if "crop" in df else "Crop"
    ycol = "crop_year" if "crop_year" in df else "Crop_Year"
    acol = [c for c in df.columns if c.startswith("area")][0]
    pcol = [c for c in df.columns if c.startswith("production")][0]

    df[scol] = df[scol].astype(str).str.strip()
    df[dcol] = df[dcol].astype(str).str.strip().str.upper()
    say(f"  years {df[ycol].min()}-{df[ycol].max()}   seasons: "
        f"{sorted(df[scol].unique())}")
    say(f"  districts: {df[dcol].nunique()}")

    vad = df[df[dcol].str.contains("VADODARA|BARODA", na=False)]
    say(f"  Vadodara records: {len(vad)}")
    say("")

    for name, sub in (("VADODARA", vad), ("GUJARAT (all districts)", df)):
        say("=" * 78)
        say(f"2.  KHARIF-ONLY, MULTI-YEAR -- {name}")
        say("=" * 78)
        k = sub[sub[scol].str.lower().str.startswith("kharif")].copy()
        k[acol] = pd.to_numeric(k[acol], errors="coerce")
        k[pcol] = pd.to_numeric(k[pcol], errors="coerce")
        say(f"  {'crop':<11}{'yrs':>5}{'median t/ha':>13}{'mean':>8}{'p25':>8}{'p75':>8}"
            f"{'tot area ha':>14}")
        res = {}
        for raw, ours in CROPMAP.items():
            g = k[k[ccol].astype(str).str.strip() == raw]
            if g.empty:
                say(f"  {ours:<11}{'-':>5}   (no kharif rows under name '{raw}')")
                continue
            per = g.groupby(ycol).apply(
                lambda x: x[pcol].sum() / x[acol].sum() if x[acol].sum() > 0 else np.nan,
                include_groups=False).dropna()
            if per.empty:
                continue
            res[ours] = float(per.median())
            say(f"  {ours:<11}{len(per):>5}{per.median():>13.2f}{per.mean():>8.2f}"
                f"{per.quantile(.25):>8.2f}{per.quantile(.75):>8.2f}"
                f"{g[acol].sum():>14,.0f}")
        say("")
        if name == "VADODARA":
            vad_k = res
        else:
            guj_k = res

    say("=" * 78)
    say("3.  THE ANCHOR TABLE, THREE WAYS")
    say("=" * 78)
    apy = pd.read_csv(ROOT / "data_aux" / "vadodara_apy.csv").set_index("crop")
    ext = {"Bajra": 1.79, "Groundnut": 2.73, "Maize": 2.57, "Rice": 2.00}  # e6 competitor median
    say(f"  {'crop':<11}{'OURS (annual)':>15}{'kharif Vadodara':>18}{'kharif Gujarat':>16}"
        f"{'competitor med':>16}")
    for c in ("Bajra", "Groundnut", "Maize", "Rice"):
        o = float(apy.yield_kg_ha_2022_23[c]) / 1000
        say(f"  {c:<11}{o:>15.2f}{vad_k.get(c, np.nan):>18.2f}{guj_k.get(c, np.nan):>16.2f}"
            f"{ext.get(c, np.nan):>16.2f}")
    say("")
    say("  Cotton omitted: the source reports cotton in BALES and teams quote lint or kapas")
    say("  interchangeably, so the numbers are not comparable without a stated conversion.")
    say("")

    # ---- what it would do to the shipped column -----------------------------
    say("=" * 78)
    say("4.  EFFECT IF ADOPTED (not applied -- Round 2 stays frozen)")
    say("=" * 78)
    sub = pd.read_csv(RESULTS / "submission.csv").set_index("farm_id")
    area = pd.read_csv(RESULTS / "farm_features.csv").set_index("farm_id").area_ha
    base = float((sub.yield_estimate_to_date * area).sum())
    corr = sub.yield_estimate_to_date.copy()
    say(f"  {'crop':<11}{'shipped anchor':>16}{'kharif anchor':>15}{'scalar':>9}")
    for c in ("Bajra", "Groundnut", "Maize", "Rice"):
        new = vad_k.get(c)
        if new is None or not np.isfinite(new):
            continue
        old = float(apy.yield_kg_ha_2022_23[c]) / 1000
        s = new / old
        corr[sub.crop_type == c] *= s
        say(f"  {c:<11}{old:>16.2f}{new:>15.2f}{s:>9.3f}")
    v = float((corr * area).sum())
    say("")
    say(f"  village production   {base:.1f} t  ->  {v:.1f} t   ({100 * (v / base - 1):+.1f}%)")
    say(f"  Megalodon 578.3 t, DeepThinkers 634.9 t, Orion 1001.6 t, Coding Bits 1268.0 t")
    say("")
    say("  Rescaling a crop by a positive scalar cannot change that crop's WITHIN-crop rank,")
    say("  so the health index and every within-crop ordering are untouched. This corrects a")
    say("  LEVEL, which is the only thing an anchor sets.")

    pd.DataFrame({"farm_id": sub.index, "crop_type": sub.crop_type,
                  "yield_shipped": sub.yield_estimate_to_date,
                  "yield_kharif_anchor": corr}).to_csv(OUT / "yield_kharif.csv", index=False)
    (OUT / "report.txt").write_text("\n".join(LOG) + "\n", encoding="utf8")
    print(f"\nwritten: {OUT}")


if __name__ == "__main__":
    main()
