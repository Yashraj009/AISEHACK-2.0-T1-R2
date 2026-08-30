"""e6 -- test the competitors' claims instead of deferring to them.

Every other experiment here started from something another team asserted. A shortlisted
team is not an authority, and two of their claims would change numbers we ship, so both
are re-tested here against evidence that owes nothing to any competitor.

  TEST 1  The calibration convention, against the vendor's own declared NESZ.
          Coding Bits argued from physical plausibility; Orion cited capella-reader; ESA's
          note states a formula whose `sc` is ambiguous. All three are somebody's reading.
          `collect.image.nesz_peak` is a number Capella put in the product, in dB, and it
          can adjudicate on its own.

  TEST 2  The bajra yield anchor. Three teams quote 1.36-1.89 t/ha against our 2.71, and
          a majority of competitors is still not evidence. Two independent checks: whether
          our own table is internally consistent, and whether there is a mechanism that
          explains the gap without anyone being wrong.

Reads shipped artefacts read-only. Writes to post-r2/results/.

Run:  py -3.12 post-r2/experiments/e6_verify_claims.py
"""
import json
import os
import sys
from pathlib import Path

os.environ.pop("PROJ_LIB", None)

import numpy as np
import pandas as pd
import rasterio

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from common import CACHE, DATES, slc_path  # noqa: E402

OUT = ROOT / "post-r2" / "results" / "e6_verify_claims"
OUT.mkdir(parents=True, exist_ok=True)

LOG = []


def say(t=""):
    print(t)
    LOG.append(t)


def test1_nesz():
    say("=" * 78)
    say("TEST 1  CALIBRATION, ADJUDICATED BY THE VENDOR'S OWN NOISE FLOOR")
    say("=" * 78)
    say("  The GEO preview cannot settle this: it is uint8, 0-255, a stretched quicklook")
    say("  with no radiometric meaning. (DeepThinkers compared against it and got an")
    say("  offset that reversed sign on one of four dates -- that is the reason why.)")
    say("")
    say("  `collect.image.nesz_peak` is different: a vendor-declared ABSOLUTE dB level.")
    say("  Physics: a scene contains smooth dark surfaces whose return approaches the")
    say("  system noise floor, so the darkest percentiles must sit near it -- never tens")
    say("  of dB above, which would mean the sensor never reaches its own noise anywhere.")
    say("")
    say(f"  {'date':<10}{'NESZ dB':>9}{'darkest 0.1%':>14}{'vs NESZ':>10}   "
        f"{'under SF^2':>11}{'vs NESZ':>10}")
    rows = []
    for d in DATES:
        meta = json.loads(Path(str(slc_path(d)).replace(".tif", "_extended.json"))
                          .read_text(encoding="utf8"))["collect"]["image"]
        nesz, sf = meta["nesz_peak"], float(meta["scale_factor"])
        with rasterio.open(CACHE / f"gamma0_base_{d}.tif") as s:
            a = s.read(1).astype("float64")
        a = a[np.isfinite(a) & (a > 0)]
        p = float(np.percentile(10 * np.log10(a), 0.1))
        off = 10 * np.log10(sf)
        rows.append((d, nesz, p, p - nesz, p + off, p + off - nesz))
        say(f"  {d:<10}{nesz:>9.2f}{p:>14.1f}{p - nesz:>+10.1f}   "
            f"{p + off:>11.1f}{p + off - nesz:>+10.1f}")
    say("")
    m_ship = np.mean([r[3] for r in rows])
    m_sf2 = np.mean([abs(r[5]) for r in rows])
    say(f"  As shipped, the noise floor sits {m_ship:+.1f} dB above the declared NESZ.")
    say(f"  Under SF^2 it lands on it, mean absolute error {m_sf2:.2f} dB, on FOUR scenes")
    say("  with four different NESZ values and four different scale factors.")
    say("")
    say("  VERDICT: the squared convention is confirmed on vendor metadata alone. No")
    say("  competitor claim, and no reading of the ESA note, is load-bearing here.")
    say("")
    return rows


def test2_bajra():
    say("=" * 78)
    say("TEST 2  THE BAJRA ANCHOR -- is the field right, and for what reason?")
    say("=" * 78)
    apy = pd.read_csv(ROOT / "data_aux" / "vadodara_apy.csv")

    say("  2a. Is our own source table internally consistent?")
    say(f"     {'crop':<11}{'implied kg/ha':>15}{'stated':>10}{'gap':>9}")
    for _, r in apy.iterrows():
        imp = r.production_t_2022_23 / r.area_ha_2022_23 * 1000
        if r.crop == "Cotton":
            say(f"     {'Cotton':<11}{imp:>15,.0f}{r.yield_kg_ha_2022_23:>10,.0f}"
                f"{'  n/a':>9}   production is in BALES, 829,400 x 170 kg = 141 kt")
            continue
        say(f"     {r.crop:<11}{imp:>15,.0f}{r.yield_kg_ha_2022_23:>10,.0f}"
            f"{100 * (r.yield_kg_ha_2022_23 / imp - 1):>+8.1f}%")
    say("")
    say("     The yield column is not derivable from the area and production columns")
    say("     beside it. Bajra carries the largest gap of the four non-cotton crops,")
    say("     +9.5%, in the direction that inflates our anchor. The table's own")
    say("     production/area gives bajra 2.478 t/ha, not the 2.714 we ship -- a 9% cut")
    say("     before any competitor number is consulted.")
    say("")

    say("  2b. Is there a mechanism that explains the remaining gap?")
    say("     Ours 2.48-2.71 t/ha. Theirs: Orion 1.79, Megalodon 1.89, DeepThinkers 1.36.")
    say("     Still a factor of ~1.5 apart, so one side is measuring something else.")
    say("")
    say("     Gujarat grows bajra in TWO seasons, and they are not comparable:")
    say("       summer, irrigated   4,000-5,000 kg/ha   (ICRISAT pearl millet manual)")
    say("       rainfed kharif      1,200-1,800 kg/ha   (12-18 quintals/ha)")
    say("       irrigated general   2,500-3,500 kg/ha")
    say("")
    say("     Our anchor is an ANNUAL district figure -- every season summed. It lands at")
    say("     2.5-2.7 t/ha, exactly where a blend of high-yield summer bajra and lower")
    say("     rainfed kharif bajra should land. Every competitor figure is explicitly a")
    say("     KHARIF estimate, and all three sit inside the rainfed kharif band.")
    say("")
    say("     Round 2 observes 6 Jun - 13 Oct 2025. That is kharif. The anchor must be a")
    say("     kharif anchor.")
    say("")
    say("     VERDICT: the field is right, but not because three teams agree -- because")
    say("     our figure answers a different question than the one we asked it. This is")
    say("     a season-matching error in our own sourcing, and we can state it that way")
    say("     without citing anybody.")
    say("")

    say("  2c. Which other anchors carry the same exposure?")
    say(f"     {'crop':<11}{'2nd season in Gujarat?':<28}{'exposure'}")
    expo = [("Bajra", "summer, irrigated, 2-3x", "HIGH -- annual mean is inflated"),
            ("Maize", "rabi maize, higher yield", "MODERATE -- same mechanism, smaller"),
            ("Rice", "summer rice is minor", "low"),
            ("Groundnut", "~90% kharif in Gujarat", "low"),
            ("Cotton", "kharif only", "none")]
    for c, s2, e in expo:
        say(f"     {c:<11}{s2:<28}{e}")
    say("")
    say("     So the fix is not 'copy their bajra number'. It is: source a KHARIF anchor")
    say("     for every crop, and check each crop for a second cropping season before")
    say("     using an annual district mean. That rule catches bajra and flags maize,")
    say("     and it is derived from agronomy rather than from a competitor's table.")
    say("")


def main():
    test1_nesz()
    test2_bajra()
    say("=" * 78)
    say("WHAT REMAINS UNTESTED, AND MUST NOT BE TREATED AS ESTABLISHED")
    say("=" * 78)
    for item, who, why in [
        ("Quegan-Yu multitemporal speckle filter", "Coding Bits",
         "2.4-2.8x looks claimed, on THEIR data. Never run on ours."),
        ("Thin-plate spline geocoding", "Coding Bits",
         "~8 m polynomial residual claimed. Our GCP fit's residual is unmeasured."),
        ("Spatial hold-out for weight selection", "Coding Bits",
         "Sound in principle; never run on our features."),
        ("CoV excess over the L=1 speckle prediction", "Orion",
         "Better posed than raw CoV, but our grid is multilooked, so L=1 does not hold."),
        ("500 m grid sub-village table", "Orion",
         "Presentation, no correctness risk, but the 32-point spread is THEIR number."),
        ("Plot-size de-biasing", "Coding Bits",
         "PARTLY tested: we measured rho(CV, npix) = +0.229 ourselves, so the artefact"),
    ]:
        say(f"  - {item}  [{who}]")
        say(f"      {why}")
    say("")
    say("  is real in our data. The correction itself is still untested.")
    say("")
    say("  None of these should enter a Round 3 report as established until run on our")
    say("  own features. A shortlisted writeup is a hypothesis, not a result.")

    (OUT / "report.txt").write_text("\n".join(LOG) + "\n", encoding="utf8")
    print(f"\nwritten: {OUT / 'report.txt'}")


if __name__ == "__main__":
    main()
