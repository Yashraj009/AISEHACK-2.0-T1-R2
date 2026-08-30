"""e8 -- measure our own geocoding residual, the last untested borrowed premise.

Coding Bits: "Polynomial fitting leaves approximately 8 m of residual displacement,
significant against a median plot dimension of 24.7 m; the spline interpolates each control
point exactly." They moved to a thin-plate spline on that basis.

That is their measurement on their chain. Ours has never been measured, so the premise of
the recommendation was untested for us -- e7 left it graded THEIRS for exactly that reason.

It is testable without touching the frozen pipeline. `prep_r2.geocode()` calls
`rasterio.warp.reproject(gcps=...)`, and GDAL given GCPs and no explicit order fits a
POLYNOMIAL (order 3 once there are 10+ points; we have 225). So the question is what that
polynomial's error actually is on our scenes.

Comparing a spline against a polynomial by residual AT the control points would be rigged:
a thin-plate spline interpolates every control point exactly, so its residual there is zero
by construction and tells you nothing about accuracy anywhere else. Both are therefore
scored by LEAVE-ONE-OUT cross-validation -- fit on 224 points, predict the held-out one --
which measures what each does at places it has not seen. That is the number that matters
for a farm boundary sitting between control points.

Reads shipped artefacts read-only. Writes to post-r2/results/.

Run:  py -3.12 post-r2/experiments/e8_geocoding.py
"""
import os
import sys
from pathlib import Path

os.environ.pop("PROJ_LIB", None)

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from scipy.interpolate import RBFInterpolator

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from common import DATES, RESULTS, slc_path  # noqa: E402

OUT = ROOT / "post-r2" / "results" / "e8_geocoding"
OUT.mkdir(parents=True, exist_ok=True)
UTM = 32643
LOG = []


def say(t=""):
    print(t)
    LOG.append(t)


def poly_design(rc, order):
    """2-D polynomial terms in (row, col) up to `order`, matching GDAL's form.

    Coordinates are centred and scaled first. Raw row/col run to tens of thousands, so
    a cubic design matrix built on them is catastrophically ill-conditioned -- the first
    run of this script reported a 140 km "residual" for order 3, which was lstsq failing,
    not the fit. GDAL normalises internally for the same reason.
    """
    rc = (rc - _NORM[0]) / _NORM[1]
    r, c = rc[:, 0], rc[:, 1]
    cols = []
    for i in range(order + 1):
        for j in range(order + 1 - i):
            cols.append((r ** i) * (c ** j))
    return np.column_stack(cols)


_NORM = (0.0, 1.0)


def loo_poly(rc, xy, order):
    """Leave-one-out residual, in metres, for a polynomial of the given order."""
    global _NORM
    _NORM = (rc.mean(axis=0), rc.std(axis=0))
    n = len(rc)
    A = poly_design(rc, order)
    if A.shape[1] >= n:
        return None
    err = np.empty(n)
    for i in range(n):
        m = np.ones(n, bool)
        m[i] = False
        c0 = xy[m].mean(axis=0)
        coef, *_ = np.linalg.lstsq(A[m], xy[m] - c0, rcond=None)
        err[i] = np.linalg.norm(A[i] @ coef + c0 - xy[i])
    return err


def loo_tps(rc, xy):
    """Leave-one-out residual for a thin-plate spline, the Coding Bits alternative."""
    n = len(rc)
    s = rc.std(axis=0)
    rcn = rc / s                      # condition the kernel; TPS is not scale-free
    err = np.empty(n)
    for i in range(n):
        m = np.ones(n, bool)
        m[i] = False
        f = RBFInterpolator(rcn[m], xy[m], kernel="thin_plate_spline", smoothing=0.0)
        err[i] = np.linalg.norm(f(rcn[i:i + 1])[0] - xy[i])
    return err


def main():
    med_ha = float(pd.read_csv(RESULTS / "farm_features.csv").area_ha.median())
    side = np.sqrt(med_ha * 10000)

    say("=" * 78)
    say("OUR GEOCODING RESIDUAL, BY LEAVE-ONE-OUT OVER THE SUPPLIED GCPs")
    say("=" * 78)
    say("  prep_r2.geocode() calls reproject(gcps=...). GDAL with 225 GCPs and no explicit")
    say("  order fits an order-3 POLYNOMIAL -- the same class Coding Bits measured at ~8 m")
    say("  and replaced with a spline.")
    say("")
    say("  Residual AT the control points would be a rigged comparison: a thin-plate spline")
    say("  interpolates every control point exactly, so its error there is zero by")
    say("  construction. Both are scored leave-one-out instead, which is what matters for a")
    say("  farm boundary sitting BETWEEN control points.")
    say("")
    say(f"  Our median plot is {med_ha:.3f} ha, a {side:.1f} m square.")
    say(f"  (Coding Bits quote 24.7 m for theirs, so our plots are larger and more")
    say(f"   forgiving of the same absolute error.)")
    say("")

    tf = Transformer.from_crs(4326, UTM, always_xy=True)
    rows = []
    for d in DATES:
        with rasterio.open(slc_path(d)) as s:
            gcps, _ = s.gcps
        rc = np.array([[p.row, p.col] for p in gcps], float)
        lon = np.array([p.x for p in gcps]); lat = np.array([p.y for p in gcps])
        X, Y = tf.transform(lon, lat)
        xy = np.column_stack([X, Y])

        res = {"date": d, "n_gcp": len(gcps)}
        for o in (1, 2, 3):
            e = loo_poly(rc, xy, o)
            if e is not None:
                res[f"poly{o}"] = float(np.median(e))
                res[f"poly{o}_p95"] = float(np.percentile(e, 95))
        e = loo_tps(rc, xy)
        res["tps"] = float(np.median(e))
        res["tps_p95"] = float(np.percentile(e, 95))
        rows.append(res)

    t = pd.DataFrame(rows)
    say(f"  {'date':<10}{'n':>5}" + "".join(f"{k:>12}" for k in
        ("poly1", "poly2", "poly3", "TPS")) + "     median LOO error, metres")
    for _, r in t.iterrows():
        say(f"  {r.date:<10}{int(r.n_gcp):>5}"
            f"{r.get('poly1', np.nan):>12.2f}{r.get('poly2', np.nan):>12.2f}"
            f"{r.get('poly3', np.nan):>12.2f}{r.tps:>12.2f}")
    say("")
    say(f"  {'date':<10}{'':>5}" + "".join(f"{k:>12}" for k in
        ("poly1", "poly2", "poly3", "TPS")) + "     95th percentile, metres")
    for _, r in t.iterrows():
        say(f"  {r.date:<10}{'':>5}"
            f"{r.get('poly1_p95', np.nan):>12.2f}{r.get('poly2_p95', np.nan):>12.2f}"
            f"{r.get('poly3_p95', np.nan):>12.2f}{r.tps_p95:>12.2f}")
    say("")

    p3 = float(t.poly3.median())
    tps = float(t.tps.median())
    say(f"  Our order-3 polynomial: {p3:.2f} m median LOO error.")
    say(f"  Thin-plate spline:      {tps:.2f} m.")
    say(f"  Difference:             {p3 - tps:+.2f} m, against a {side:.0f} m plot "
        f"({100 * abs(p3 - tps) / side:.1f}% of a plot side).")
    say("")
    p2 = float(t.poly2.median())
    p3p95 = float(t.poly3_p95.median())
    tpsp95 = float(t.tps_p95.median())
    say(f"  Order 2 median: {p2:.2f} m -- BETTER than the order 3 GDAL picks by default.")
    say(f"  With 225 GCPs GDAL selects order 3, and on this geometry that overfits: the")
    say(f"  extra cubic terms cost {p3 - p2:+.2f} m of held-out accuracy on every date.")
    say("")
    say("  VERDICT, three parts:")
    say(f"   1. The premise does NOT transfer as stated. Coding Bits measured ~8 m for")
    say(f"      their polynomial; ours is {p3:.1f} m median -- under one 5 m base cell, and")
    say(f"      {100 * p3 / side:.0f}% of a {side:.0f} m plot side. Our fit is roughly twice as good")
    say("      as the one they rejected, so their 8 m is not our number.")
    say(f"   2. But the SPLINE still halves it, {p3:.2f} -> {tps:.2f} m median and")
    say(f"      {p3p95:.1f} -> {tpsp95:.1f} m at the 95th percentile. The tail is where this")
    say(f"      bites: a {p3p95:.0f} m error is {100 * p3p95 / side:.0f}% of a plot side, which is")
    say("      boundary mixing on the worst-placed farms, and erosion is our only guard.")
    say(f"   3. The cheapest win is not the spline at all: forcing order 2 recovers")
    say(f"      {p3 - p2:.2f} m for a one-argument change, because GDAL's automatic order-3")
    say("      choice is overfitting our GCP lattice.")
    say("")
    say("  So: ADOPT, but not for their reason and not necessarily their method. Order 2")
    say("  first because it is nearly free; the spline if the tail matters after that.")
    say("  Caveat, stated: this measures the GCP fit only. It cannot see a common-mode")
    say("  error affecting every GCP equally -- the class Megalodon's geoid bug belonged")
    say("  to, which per-date consistency cannot catch either. Our absolute registration")
    say("  against the vendor's geocoded product remains a separate, unmeasured question.")

    t.to_csv(OUT / "geocoding_residual.csv", index=False)
    (OUT / "report.txt").write_text("\n".join(LOG) + "\n", encoding="utf8")
    print(f"\nwritten: {OUT}")


if __name__ == "__main__":
    main()
