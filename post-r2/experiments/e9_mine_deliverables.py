"""e9 -- mine the competitors' NOTEBOOKS and PDFs, not their writeups.

The five writeups are exhausted. What shipped alongside them is not: four notebooks and
three methodology PDFs, 555,246 characters never opened. A writeup is an argument; a
notebook is the evidence, and it carries what prose omits -- exact constants, the libraries
doing real work, abandoned branches, and the datasets a team actually touched.

Five extractions, each aimed at a question we cannot answer from prose:

  X1  LIBRARY CENSUS      what packages do real work in their pipelines that we do not use?
                          Each is a capability gap and a term to research.
  X2  EXTERNAL DATA       every dataset, API, STAC endpoint and product they touched. The
                          writeups name a few; code names all of them.
  X3  CONSTANT HUNT       every hard-coded number with the line that sets it, cross-tabbed
                          against ours. Where several teams converge on a value we set
                          differently, that is a prior worth testing.
  X4  ABANDONED WORK      commented-out branches, "v2"/"old"/"unused" functions, TODOs.
                          Failed approaches are informative and nobody writes them up.
  X5  METHOD SURFACE      every function they define, as a list of capabilities, diffed
                          against ours.

Read-only over post-r2/writeups_submissions/. Writes to post-r2/results/.

Run:  py -3.12 post-r2/experiments/e9_mine_deliverables.py
"""
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

os.environ.pop("PROJ_LIB", None)

ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "post-r2" / "writeups_submissions"
OUT = ROOT / "post-r2" / "results" / "e9_mine"
OUT.mkdir(parents=True, exist_ok=True)

NB = {
    "8bit": W / "8_bits" / "aisehack_round2_sar_crop_health.ipynb",
    "CodingBits": W / "coding_bits" / "Coding Bits Notebook ANRF AISEHack 2.0 Round 2.ipynb",
    "Megalodon": W / "megalodon" / "AISE2_SAR_R2_Megalodon.ipynb",
    "Orion": W / "project_orion_team_apes" / "sokhda_sar_crop_health.ipynb",
}
PDF = {
    "8bit": W / "8_bits" / "AISEHack2_Round2_Team8bit_Methodology_Report.pdf",
    "CodingBits": W / "coding_bits" / "Coding Bits Report ANRF AISEHack 2.0 Round 2.pdf",
    "Orion": W / "project_orion_team_apes" / "writeup.pdf",
}

# what our own pipeline imports, so the census reports a DIFFERENCE not a list
OURS = set()
for p in (ROOT / "src").glob("*.py"):
    for m in re.finditer(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)",
                         p.read_text(encoding="utf8", errors="ignore"), re.M):
        OURS.add(m.group(1).split(".")[0])

LOG = []


def say(t=""):
    print(t)
    LOG.append(t)


def cells(path):
    """(kind, source) per cell."""
    d = json.loads(path.read_text(encoding="utf8"))
    return [(c.get("cell_type", "code"), "".join(c.get("source", "")))
            for c in d.get("cells", [])]


def code_of(team):
    return "\n".join(s for k, s in cells(NB[team]) if k == "code")


def md_of(team):
    return "\n".join(s for k, s in cells(NB[team]) if k == "markdown")


def x1_libraries(src):
    say("=" * 78)
    say("X1  LIBRARY CENSUS -- what does real work in their code that we do not use")
    say("=" * 78)
    per = {}
    for t, s in src.items():
        mods = set()
        for m in re.finditer(r"^\s*(?:import|from)\s+([A-Za-z_][\w.]*)", s, re.M):
            mods.add(m.group(1).split(".")[0])
        per[t] = mods
    allmods = Counter()
    for t, ms in per.items():
        for m in ms:
            allmods[m] += 1
    stdlib = {"os", "sys", "re", "json", "math", "time", "glob", "pathlib", "warnings",
              "collections", "itertools", "datetime", "shutil", "typing", "subprocess",
              "hashlib", "functools", "random", "zipfile", "io", "traceback", "gc",
              "dataclasses", "textwrap", "copy", "csv", "pprint", "string", "tempfile",
              "urllib", "base64", "contextlib", "operator", "pickle", "logging", "platform",
              "importlib", "inspect", "socket", "getpass", "uuid", "abc", "enum", "struct"}
    say(f"  {'package':<22}{'teams':>7}   who")
    gaps = []
    for m, n in allmods.most_common():
        if m in stdlib:
            continue
        who = ",".join(t for t in src if m in per[t])
        mark = "" if m in OURS else "   <- WE DO NOT USE THIS"
        if m not in OURS:
            gaps.append((m, n, who))
        say(f"  {m:<22}{n:>7}   {who}{mark}")
    say("")
    say(f"  {len(gaps)} packages appear in competitor pipelines and not in ours.")
    say("  Each is either a capability we lack or a dependency they did not need.")
    say("")
    return gaps


def x2_external(src, md):
    say("=" * 78)
    say("X2  EXTERNAL DATA -- every dataset, endpoint and product they touched")
    say("=" * 78)
    pats = {
        "STAC / catalog": r"(?:stac|STAC|planetarycomputer|earth-search|element84|earthsearch)[\w\-./:]*",
        "Sentinel": r"(?:sentinel|SENTINEL|S1|S2)[\-_]?\w*",
        "Copernicus DEM": r"(?:copernicus|COP30|COP90|glo-30|glo30|nasadem|srtm|SRTM)\w*",
        "soil": r"(?:soilgrids|SoilGrids|HWSD|NBSS|isric|ISRIC)\w*",
        "weather": r"(?:open-meteo|openmeteo|CHIRPS|chirps|NASA\s*POWER|nasapower|era5|ERA5|imd|IMD)\w*",
        "landcover": r"(?:worldcover|WorldCover|dynamicworld|DynamicWorld|esa_cci|GLAD)\w*",
        "thermal / LST": r"(?:landsat|LANDSAT|LST|MODIS|modis)\w*",
        "govt statistics": r"(?:APY|apy\.csv|advance\s*estimate|DES|agricoop|data\.gov)\w*",
        "urls": r"https?://[\w\-./?=&%:+]+",
    }
    for lab, p in pats.items():
        hits = Counter()
        for t in src:
            for m in re.finditer(p, src[t] + "\n" + md.get(t, "")):
                hits[(m.group(0)[:70], t)] += 1
        if not hits:
            continue
        say(f"  --- {lab} ---")
        seen = defaultdict(set)
        for (tok, t), _ in hits.most_common():
            seen[tok].add(t)
        for tok, teams in sorted(seen.items(), key=lambda kv: -len(kv[1]))[:14]:
            say(f"    {tok:<62} {','.join(sorted(teams))}")
        say("")


def x3_constants(src):
    say("=" * 78)
    say("X3  CONSTANT HUNT -- named numeric constants, by team")
    say("=" * 78)
    say("  Module-level ALL_CAPS assignments and dict literals of numbers: the parameters a")
    say("  team chose. Where several converge on a value we set differently, that is a prior")
    say("  worth testing; where they all differ, the parameter probably does not matter.")
    say("")
    for t, s in src.items():
        say(f"  --- {t} ---")
        n = 0
        for m in re.finditer(r"^([A-Z][A-Z0-9_]{2,})\s*=\s*(.{0,110})", s, re.M):
            say(f"    {m.group(1):<28} = {m.group(2).rstrip()}")
            n += 1
            if n > 44:
                say("    ... truncated")
                break
        if n == 0:
            say("    (no module-level ALL_CAPS constants -- values are inline)")
        say("")


def x4_abandoned(src):
    say("=" * 78)
    say("X4  ABANDONED WORK -- what they tried and did not ship")
    say("=" * 78)
    pats = [(r"^\s*#\s*(?:def|from|import|[a-z_]+\s*=)\s*.{0,90}", "commented-out code"),
            (r"(?:TODO|FIXME|XXX|HACK|NOTE:)\s*.{0,90}", "marker"),
            (r"^\s*def\s+(\w*(?:_v2|_v3|_old|_unused|_deprecated|_alt|_test)\w*)", "alt version"),
            (r"(?:did not|didn't|rejected|abandoned|does not work|doesn't work|"
             r"failed|discarded|not used|unused|no improvement|no better)[^\n]{0,90}", "prose")]
    for t, s in src.items():
        say(f"  --- {t} ---")
        n = 0
        for p, lab in pats:
            for m in re.finditer(p, s, re.M | re.I):
                txt = " ".join(m.group(0).split())[:104]
                if len(txt) < 12:
                    continue
                say(f"    [{lab:<17}] {txt}")
                n += 1
                if n > 26:
                    break
            if n > 26:
                say("    ... truncated")
                break
        if n == 0:
            say("    (nothing found)")
        say("")


def x5_methods(src):
    say("=" * 78)
    say("X5  METHOD SURFACE -- every function they define")
    say("=" * 78)
    ourfn = set()
    for p in (ROOT / "src").glob("*.py"):
        for m in re.finditer(r"^def\s+(\w+)", p.read_text(encoding="utf8", errors="ignore"), re.M):
            ourfn.add(m.group(1).lower())
    for t, s in src.items():
        fns = re.findall(r"^\s*def\s+(\w+)\s*\(", s, re.M)
        say(f"  --- {t} ({len(fns)} functions) ---")
        say("    " + ", ".join(sorted(set(fns))[:60]))
        say("")
    say(f"  ours: {len(ourfn)} functions across src/")
    say("")


def main():
    src = {t: code_of(t) for t in NB}
    md = {t: md_of(t) for t in NB}

    try:
        import pymupdf
        for t, p in PDF.items():
            with pymupdf.open(p) as doc:
                md[t] = md.get(t, "") + "\n" + "\n".join(pg.get_text() for pg in doc)
    except Exception as e:                                    # noqa: BLE001
        say(f"  (PDF text unavailable: {e})")

    say("=" * 78)
    say("SOURCE INVENTORY")
    say("=" * 78)
    for t in NB:
        say(f"  {t:<13} code {len(src[t]):>8,} chars   prose+pdf {len(md[t]):>8,} chars")
    say("")

    gaps = x1_libraries(src)
    x2_external(src, md)
    x3_constants(src)
    x4_abandoned(src)
    x5_methods(src)

    say("=" * 78)
    say("WHAT TO CHASE, from this pass alone")
    say("=" * 78)
    say("  Packages in their pipelines and not in ours:")
    for m, n, who in gaps[:20]:
        say(f"    {m:<20} used by {n} team(s): {who}")
    say("")
    say("  Nothing above is adopted here. Each is a hypothesis for the next experiment,")
    say("  and gets tested on our own data before it is believed.")

    (OUT / "report.txt").write_text("\n".join(LOG) + "\n", encoding="utf8")
    for t in src:
        (OUT / f"code_{t}.txt").write_text(src[t], encoding="utf8")
        (OUT / f"prose_{t}.txt").write_text(md[t], encoding="utf8")
    print(f"\nwritten: {OUT}")


if __name__ == "__main__":
    main()
