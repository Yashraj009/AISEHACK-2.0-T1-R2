"""Prove the staged Kaggle dataset actually works before anyone uploads 174 MB.

Simulates the Kaggle layout exactly: the dataset mounted under a stand-in
/kaggle/input/<slug>, and the notebook run from a stand-in /kaggle/working that
contains none of the project. Then runs the notebook's own root-discovery logic
against it and reads the data through `common`.

If this passes, the only remaining upload risks are human (wrong file, dataset not
attached), which is what UPLOAD_CHECKLIST.md is for.

Run:  python src/verify_upload_package.py
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT

PROBE = '''
import sys
from pathlib import Path
KIN = Path(sys.argv[1])

def _find_root():
    here = Path.cwd()
    cands = [here, here.parent]
    if KIN.exists():
        cands += sorted(KIN.glob("*"))
    for c in cands:
        if (c / "src" / "common.py").exists():
            return c
        for sub in sorted(c.glob("*")):
            if (sub / "src" / "common.py").exists():
                return sub
    raise SystemExit("ROOT NOT FOUND")

ROOT = _find_root()
sys.path.insert(0, str(ROOT / "src"))
import common, pandas as pd
assert common.FARMS.exists(), "shapefile missing from the dataset"
sub = pd.read_csv(common.RESULTS / "submission.csv")
assert len(sub) == 966, f"submission has {len(sub)} rows"
tifs = list((common.RESULTS / "cache").glob("*.tif"))
assert len(tifs) >= 24, f"only {len(tifs)} cached rasters"
print("ROOT:", ROOT.name)
print("farms shapefile: OK")
print("submission rows:", len(sub))
print("cached rasters:", len(tifs))
print("PACKAGE VERIFIED")
'''


def main():
    pkg = ROOT / "upload" / "kaggle_dataset"
    if not pkg.exists():
        raise SystemExit("run src/make_upload_package.py first")

    tmp = Path(tempfile.mkdtemp(prefix="kagverify_"))
    try:
        inp = tmp / "input" / "aisehack-r2-sokhda-pipeline"
        work = tmp / "working"
        work.mkdir(parents=True)
        # copytree, not a link: this must prove the FILES are sufficient, and a link
        # would quietly let it read the original repo instead of the staged package
        shutil.copytree(pkg, inp)

        probe = work / "_probe.py"
        probe.write_text(PROBE, encoding="utf8")
        r = subprocess.run([sys.executable, "-W", "ignore", str(probe),
                            str(tmp / "input")],
                           cwd=str(work), capture_output=True, text=True)
        print("=" * 62)
        print("KAGGLE PACKAGE VERIFICATION (isolated copy, foreign cwd)")
        print("=" * 62)
        print(r.stdout.strip() or r.stderr.strip()[:900])
        if r.returncode != 0:
            raise SystemExit("PACKAGE IS NOT SELF-SUFFICIENT -- do not upload yet")
        print()
        print("  The dataset is self-sufficient: discovery found it from a foreign")
        print("  working directory and every file the pipeline needs was present.")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
