"""e12 -- a screening test for ANY gridded covariate, before we go and fetch it.

Megalodon measured that a covariate which is CONSTANT within a cell can explain only so much
of the farm-to-farm variation in health once each crop's mean is removed: 0.226 of the
variance at 250 m, 0.049 at 1 km, and 0.000 at 50 km. Their conclusion was that NASA POWER,
on a 50 km cell against a 3.4 km village, "cannot rank farms at all".

That is their number on their data. Ours has never been measured, and it is the single most
useful screening tool available, because it prices EVERY proposed gridded dataset in one shot
- weather APIs, soil grids, land-cover products, reanalysis - without fetching any of them.

THE LOGIC. If a covariate is constant inside a cell of side L, then every farm in that cell
receives the same value. The most it can possibly explain is the BETWEEN-CELL share of the
variance. Anything within a cell is invisible to it. So partition the farms into cells of
side L and compute

    ceiling(L) = between-cell variance / total variance     (of within-crop health residual)

This is an upper bound and a generous one: it assumes the covariate is perfectly correlated
with whatever the between-cell signal is. A real dataset does worse.

Also tested here: WEATHER, which is the one class of covariate that is not being proposed for
spatial ranking. A single village sees one weather stream, so its value is temporal - the
rain event on 19 June is what makes our rice signature work. That is tested separately,
because a spatial ceiling of zero does not make weather useless, it makes it useful for a
different purpose.

Reads shipped artefacts read-only. Writes to post-r2/results/.

Run:  py -3.12 post-r2/experiments/e12_data_ceiling.py
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

os.environ.pop("PROJ_LIB", None)

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from common import DATES, RESULTS, farm_centroids  # noqa: E402

OUT = ROOT / "post-r2" / "results" / "e12_data_ceiling"
OUT.mkdir(parents=True, exist_ok=True)
LOG = []


def say(t=""):
    print(t)
    LOG.append(t)


def ceiling_curve():
    say("=" * 78)
    say("1.  THE RESOLUTION CEILING, MEASURED ON OUR OWN FARMS")
    say("=" * 78)
    s = pd.read_csv(RESULTS / "submission.csv")
    xy = farm_centroids()
    s = s.assign(x=xy[s.farm_id.to_numpy() - 1, 0], y=xy[s.farm_id.to_numpy() - 1, 1])

    # Drop degenerate-geometry parcels before gridding. Nine farms are valid FIDs enclosing
    # effectively no ground (0 to 2.3e-7 ha) and their centroids land up to 835 km away,
    # which would stretch every cell boundary and make the whole curve meaningless. They
    # still carry a row in the submission -- they just cannot define a spatial grid.
    # (Orion independently documented ten such parcels at < 1e-6 ha.)
    dist = np.hypot(s.x - s.x.median(), s.y - s.y.median())
    bad = dist > 5000
    say(f"  excluded {int(bad.sum())} degenerate parcels (centroid >5 km out, area ~0)")
    s = s[~bad].copy()

    # work on the WITHIN-CROP residual: the index is a within-crop score, so a covariate
    # that merely separates crops is not adding anything the crop label does not already give
    s["resid"] = s.health_index - s.groupby("crop_type").health_index.transform("mean")
    v_tot = s.resid.var()

    say(f"  966 farms, village extent {(s.x.max() - s.x.min()) / 1000:.1f} x "
        f"{(s.y.max() - s.y.min()) / 1000:.1f} km")
    say(f"  variance of the within-crop health residual: {v_tot:.2f}")
    say("")
    say(f"  {'cell side':>12}{'cells used':>12}{'ceiling':>10}   what sits at this scale")
    notes = {100: "Capella farm-scale; Sentinel-1/2 at 10-20 m",
             250: "MODIS 250 m; SoilGrids 250 m",
             500: "Dynamic World / WorldCereal aggregated",
             1000: "SoilGrids 1 km; CHIRPS 5 km is coarser still",
             5000: "CHIRPS rainfall",
             11000: "ERA5-Land reanalysis (~9-11 km)",
             25000: "ERA5 (~25 km); most weather APIs",
             50000: "NASA POWER (~50 km)"}
    rows = []
    for L in (100, 250, 500, 1000, 5000, 11000, 25000, 50000):
        cx = np.floor(s.x / L).astype(int)
        cy = np.floor(s.y / L).astype(int)
        key = cx.astype(str) + "_" + cy.astype(str)
        grp = s.groupby(key).resid
        # between-cell variance share, weighted by cell membership
        cm = grp.transform("mean")
        ceil = float(cm.var() / v_tot) if v_tot > 0 else np.nan
        n = key.nunique()
        rows.append((L, n, ceil))
        say(f"  {L:>9} m {n:>12}{ceil:>10.3f}   {notes.get(L, '')}")
    say("")
    say("  Read this as: a covariate constant within a cell of that size can explain AT MOST")
    say("  this share of farm-to-farm health variation, and only if it is perfectly")
    say("  correlated with the between-cell signal. A real dataset does worse.")
    say("")
    d = pd.DataFrame(rows, columns=["cell_m", "n_cells", "ceiling"])
    d.to_csv(OUT / "ceiling.csv", index=False)
    return d


def verdicts(d):
    say("=" * 78)
    say("2.  PRICING THE PROPOSED DATA SOURCES AGAINST IT")
    say("=" * 78)
    c = dict(zip(d.cell_m, d.ceiling))

    def at(m):
        ks = sorted(c)
        for k in ks:
            if m <= k:
                return c[k]
        return c[ks[-1]]

    say(f"  {'source':<34}{'native cell':>13}{'ceiling':>9}   verdict")
    src = [
        ("USDA ERS ARMS", None, "US farm FINANCES, 16 US states. Wrong continent and subject"),
        ("OpenWeatherMap (history)", 25000, None),
        ("NASA POWER (we use it)", 50000, None),
        ("CHIRPS rainfall", 5000, None),
        ("ERA5-Land reanalysis", 11000, None),
        ("SoilGrids 250 m", 250, None),
        ("ESA WorldCereal 10 m", 100, None),
        ("Dynamic World 10 m", 100, None),
        ("Sentinel-1 / Sentinel-2", 100, None),
        ("Capella (what we ship)", 100, None),
    ]
    for name, cell, note in src:
        if cell is None:
            say(f"  {name:<34}{'n/a':>13}{'n/a':>9}   {note}")
            continue
        cl = at(cell)
        v = ("USELESS for ranking farms" if cl < 0.02 else
             "marginal" if cl < 0.10 else
             "could matter" if cl < 0.30 else "farm-scale")
        say(f"  {name:<34}{cell:>10} m {cl:>9.3f}   {v}")
    say("")
    say("  Every weather/reanalysis product lands in the same place: its cell is larger than")
    say("  the village, so it takes ONE value for all 966 farms and its spatial ceiling is")
    say("  exactly zero. That is not a judgement about weather, it is arithmetic.")
    say("")


def weather_timing():
    say("=" * 78)
    say("3.  WHERE WEATHER IS ACTUALLY USEFUL: TIMING, NOT RANKING")
    say("=" * 78)
    say("  A spatial ceiling of zero does not make weather useless. Our rice signature is the")
    say("  6->19 June brightening (+3.23 dB for rice vs +0.07..+1.12 for everything else),")
    say("  and both Coding Bits and Megalodon report 19 June as a rain day (12.5 mm in the")
    say("  preceding six hours; 21.9 mm on the day). The MECHANISM of our own crop map")
    say("  depends on a weather fact.")
    say("")
    say("  So the question worth asking of a weather API is not 'can it rank farms' (no) but")
    say("  'can it pin the rain to the acquisition hour'. Capella overpasses:")
    for d, t in zip(DATES, ["07:25", "02:14", "03:11", "02:26"]):
        say(f"    {d}  {t} UTC")
    say("")
    say("  Open-Meteo's archive gives HOURLY precipitation free and without a key, which is")
    say("  what Coding Bits used. OpenWeatherMap's history endpoint is paid and no better")
    say("  resolved for this purpose. Testing Open-Meteo now.")
    say("")
    lat, lon = 22.43, 73.18
    url = ("https://archive-api.open-meteo.com/v1/archive?"
           f"latitude={lat}&longitude={lon}&start_date=2025-06-04&end_date=2025-06-20"
           "&hourly=precipitation&timezone=UTC")
    try:
        with urllib.request.urlopen(url, timeout=45) as r:
            j = json.loads(r.read())
        h = pd.DataFrame({"t": pd.to_datetime(j["hourly"]["time"]),
                          "mm": j["hourly"]["precipitation"]})
        say(f"  fetched {len(h)} hourly records, 4-20 June 2025")
        for d, hh in (("2025-06-06", 7), ("2025-06-19", 2)):
            ts = pd.Timestamp(d) + pd.Timedelta(hours=hh)
            pre24 = h[(h.t > ts - pd.Timedelta(hours=24)) & (h.t <= ts)].mm.sum()
            pre6 = h[(h.t > ts - pd.Timedelta(hours=6)) & (h.t <= ts)].mm.sum()
            day = h[h.t.dt.date == pd.Timestamp(d).date()].mm.sum()
            say(f"    {d} {hh:02d}:00 UTC  ->  6 h before {pre6:6.1f} mm   "
                f"24 h before {pre24:6.1f} mm   whole day {day:6.1f} mm")
        say("")
        say("  This is the fact our rice channel rests on, fetched independently rather than")
        say("  taken from a competitor's writeup.")
    except Exception as e:                                    # noqa: BLE001
        say(f"  Open-Meteo unavailable here: {e}")
        say("  (the test stands; it just needs network)")
    say("")


def main():
    d = ceiling_curve()
    verdicts(d)
    weather_timing()
    say("=" * 78)
    say("CONCLUSION")
    say("=" * 78)
    say("  Anything on a cell larger than the village is arithmetically incapable of ranking")
    say("  farms within it. That prices out every weather and reanalysis product for the")
    say("  ranking job in one line, and it is measured on our own farms rather than borrowed.")
    say("  What remains worth pursuing is 10 m products - and their value has to be shown,")
    say("  not assumed, because a ceiling is an upper bound and not a promise.")
    (OUT / "report.txt").write_text("\n".join(LOG) + "\n", encoding="utf8")
    print(f"\nwritten: {OUT}")


if __name__ == "__main__":
    main()
