# Handoff prompt for the Round 3 chat

Paste everything below the line as the first message in the new chat.

---

I am Team GDHTM in the ANRF AISEHack 2.0 competition (SAR crop health & yield estimation,
Sokhda village, Gujarat, 966 farms). Rounds 1 and 2 are complete and we are shortlisted in the
final 6. Round 3 is an in-person working sprint in Goa on 2–3 September; I will tell you its
format later in this chat. **Do not start any Round 3 work until I do.**

Working directory: `C:\Users\sorat\Downloads\AISEHack_R2_SAR_Crop\AISEHACK-2.0-T1-R2`

## Your first task: read the project, in this order, then stop and report

Read these yourself — do not ask me to summarise them, and do not spawn subagents.

**1. Start here — this is the compressed state of everything:**
- `post-r2/SPRINT_BRIEF.md` — the single most important file. Adversarial Q&A, the eleven
  closed ideas, four shipped defects, four R3 scenarios, measured portability debt.
- `post-r2/README.md` — index of all 18 post-R2 experiments with their verdicts.

**2. Round 1 context (what carried forward):**
- `internal/research/R1_CONTEXT.md`
- `internal/research/R1_TRANSFER_CONCLUSIONS.md`
- `data_aux/sokhda_r1_truth.csv` — R1 fixed this village's crop-area shares. Treat it as the
  crop-mix prior, **not** the district APY table.

**3. Round 2 — what we built and why:**
- `docs/REPORT.md` — the method, end to end. Note §1: Capella X-band is the **required primary
  source** per the guidelines; Sentinel-1/2 are witnesses only and never enter a shipped number.
- `internal/MASTER_PLAN.md` and `internal/RESEARCH_LOG.md` — stage-by-stage decisions.
- `data_aux/SOURCES.md` — every external input, with caveats and one retraction.
- `src/` (33 files) — `common.py`, `prep_r2.py`, `farm_stats.py`, `d4_submission.py`,
  `witness.py`, `witness_season.py`, `i5_validation.py`, `d11_ship.py` are the spine.

**4. Post-R2 competitive analysis and experiments:**
- `post-r2/COMPETITOR_ANALYSIS_R2.md` — teardown of all five other shortlisted writeups.
- `post-r2/KHARIF_ANCHORS.md`, `UNCERTAINTY.md`, `DATA_SOURCES.md`,
  `LABEL_CORROBORATION.md`, `LABEL_DISTRIBUTION.md`, `GROUND_TRUTH_SELECTION.md`
- `post-r2/ROUND3_DIRECTIONS.md` — four directions, three rejected by their own tests.
- `post-r2/experiments/e1..e18*.py` — every experiment, each documenting what would kill it.

## Then report back

Give me a short summary of: what we shipped in R2, the strongest claims we can defend, the
known defects, and what is already closed. Then **wait** — I will tell you what Round 3 is.

## Standing rules — these override default behaviour

1. **The R2 submission is frozen.** `results/submission.csv` must stay md5
   `89b0e4e2aef63ace4989fc0a44590ee5`. Verify it before and after any change. Nothing has
   modified a shipped number since R2 and nothing should without me saying so.
2. **Never commit until I explicitly tell you to.** Stage and report; I review first.
   ~22 changes are currently pending and uncommitted, deliberately.
3. **Never add a `Co-Authored-By: Claude` trailer** to any commit, in any project.
4. **Test in depth before adopting anything.** This is the rule the whole post-R2 pass was
   built on. Other teams' published ideas can be wrong, published papers can be about a
   different objective, and my own proposals have been wrong three times out of four. Every
   claim needs a control that could fail. If a test fails its own control, discard the test and
   say so.
5. **Privacy:** 7 of 12 land records carry owner names. Extract the crop column only, report
   aggregate accuracy only, never publish owner names or individual-linked survey numbers.
   `ground_truth_vf12.csv` and `.kdss_token` stay gitignored.

## Facts you will otherwise re-derive or get wrong

- **Round 1's official score was MSE 11.071, not 0.000.** The crop shares are an estimate.
- **Capella SLC calibration:** β⁰ = scale_factor² · |z|². We ship scale_factor (not squared) —
  a known defect, verified against the vendor's `nesz_peak`, deliberately not applied to the
  frozen submission. It changes 8 of 966 labels.
- **Cotton yield is lint**, not seed cotton (×2.94 for kapas). Every official source reports it
  this way. Tested and the conversion was rejected.
- **Ground truth is blocked.** Krishi-DSS needs an API we don't have; AnyROR needs a person.
  Assume no ground truth will arrive.
- **The headline claim:** two independent sensor stacks back our cotton labels on 78.8% of
  farms, and 42.5% of the village is backed by neither — almost entirely rice, maize and bajra.
  We are the only team that has measured where its own map is unsupported.
- **Do not re-propose** dense Sentinel-1, Dynamic World filtering, WorldCereal crop type,
  Quegan-Yu speckle filtering, any covariate coarser than 1 km, AlphaEarth as a label source, or
  propagating the label posterior into yield. All tested, all closed, reasons in §3 of the brief.

## Two outstanding items

- Three credentials (data.gov.in, USDA ERS, GEE client secret) were pasted into the previous
  chat and need rotating. They live in `~/.config/aisehack/`, outside the repo.
- `post-r2/sprint_brief.html` is built but unpublished (an artifact publish was blocked).
