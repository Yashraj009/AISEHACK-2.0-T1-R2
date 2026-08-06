"""Authenticated Krishi-DSS client -- reads the bearer token from disk, never from code.

CREDENTIAL HANDLING. The token is a live session credential for a government portal,
tied to a real account. So:

  * it is read from `data_aux/.kdss_token` (gitignored) or the KDSS_TOKEN environment
    variable -- never hardcoded, never printed, never committed;
  * only the first 6 characters are ever echoed, so a log or a screen-share cannot
    leak it;
  * every call here is read-only (GET), and the module refuses to issue anything else.

The public GeoServer WFS used by `fetch_dcs_parcels.py` needs none of this. Only
`cropmapping-api` does, which is why that one is separated out here.

USE MODESTLY. This is an authenticated endpoint on a government service, sized for
interactive use, not bulk extraction. This client requests one village's worth of data,
paces itself, and stops on the first error rather than retrying in a loop.

Setup:
    1. log in at https://krishi-dss.gov.in/
    2. F12 -> Application -> Local Storage -> copy the value of `token`
    3. save it to data_aux/.kdss_token  (one line, no quotes)

Run:  python src/kdss_client.py check      -- verify the token works
      python src/kdss_client.py crops      -- list the crop-mapping catalogue
"""
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import AUX, log

CROPMAP = "https://krishi-dss.gov.in/cropmapping-api"
MASTER = "https://krishi-dss.gov.in/master-api"
TOKEN_FILE = AUX / ".kdss_token"
PAUSE = 0.7          # deliberate pacing between calls


def token():
    import os
    t = os.environ.get("KDSS_TOKEN", "").strip()
    if not t and TOKEN_FILE.exists():
        t = TOKEN_FILE.read_text(encoding="utf8").strip()
    if not t:
        raise SystemExit(
            f"No token.\n"
            f"  1. log in at https://krishi-dss.gov.in/\n"
            f"  2. F12 -> Application -> Local Storage -> copy the `token` value\n"
            f"  3. save it to {TOKEN_FILE} (one line), or set KDSS_TOKEN\n"
            f"The file is gitignored and the token is never printed in full.")
    return t.removeprefix("Bearer ").strip()


def get(url, tok=None):
    """Read-only request. Returns parsed JSON, or raises with a short reason."""
    tok = tok or token()
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {tok}", "Content-Type": "application/json",
        "Accept": "application/json"})
    time.sleep(PAUSE)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read()[:200].decode("utf8", "replace")
        raise SystemExit(f"HTTP {e.code} on {url.split('/')[-1]}: {body}\n"
                         f"(401/403 usually means the token has expired -- log in "
                         f"again and refresh {TOKEN_FILE})")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    tok = token()
    print(f"token loaded: {tok[:6]}... ({len(tok)} chars)")

    if cmd == "check":
        d = get(f"{CROPMAP}/masters/getAllCropMappingList", tok)
        n = len(d.get("data", d) or [])
        print(f"OK -- crop-mapping catalogue reachable, {n} entries")
        print(json.dumps(d, indent=1)[:1200])
        log("kdss.check", ok=True, entries=n)

    elif cmd == "crops":
        d = get(f"{CROPMAP}/masters/getAllCropMappingList", tok)
        rows = d.get("data", d)
        out = AUX / "kdss_crop_catalogue.json"
        out.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf8")
        print(f"wrote {out}")
        for r in (rows or [])[:25]:
            print("  ", r)
        log("kdss.crops", n=len(rows or []))

    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
