---
name: reproducibility-lessons
description: Hard lessons on keeping iterative/leaderboard-fitted pipelines reproducible (from AISEHack R1)
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d035e0b4-ceb6-4d1b-ac4f-b1af914eb19b
  modified: 2026-07-24T13:10:20.069Z
---

On [[aisehack-r1-fresh-restart]] the final champion (MSE 11.071) became **impossible to reconstruct** — a
92-submission Gram-ensemble + oracle chain whose exact output survived only as a recorded CSV. User asked me
to learn from it so it never repeats.

**Why it broke:** (1) path dependence + overwritten intermediates — every step built on `submission_best.csv`
which I kept overwriting, so the direct parent vector (11.287) was never saved; (2) near-singular, order-
dependent solve (|a|₁≈400) — not a stable function of inputs, so re-solving with the full vector set overfits
to a different answer; (3) transient bases with no provenance for derived values.

**How to apply (do these on any iterative / feedback-fitted pipeline):**
1. **Version every validated result immutably** — save `champion_<score>.csv`, NEVER overwrite. One saved
   parent makes the whole chain reconstructible in one delta.
2. **Every artifact needs a deterministic rebuild script** that regenerates it from recorded inputs; verify it
   reproduces at each milestone. If there's no `rebuild.py`, the artifact is a liability. (The scalar model's
   `rebuild_final.py` stayed reproducible; the ensemble/oracle layer had none → lost.)
3. **Never ship a near-singular solve as the final artifact.** If adding a redundant input changes the output,
   it's fragile. Prefer regularized/well-conditioned solves whose result is a stable function of inputs.
4. **Separate reproducible-from-data (deterministic module) from fitted-to-feedback (versioned constants).**
   Reproduction = deterministic model + versioned deltas.
5. **Record provenance** (base, formula, inputs) for every derived number; no throwaway intermediate bases.
6. **Persist intermediate state even when things are working** — the cost of not doing so only appears at the
   end. Test "can I rebuild this from scratch right now?" after every milestone, not at the finish.
