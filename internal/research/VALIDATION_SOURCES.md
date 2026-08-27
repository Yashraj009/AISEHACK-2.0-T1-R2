# Ground-Truth Sources for Per-Farm Crop Type — Sokhda, Kharif 2025

Answering: *is there any government or private source that can tell us what was actually grown on each of
these 966 plots — ideally with that plot's history?*

**Short answer: yes, and one of them is close to definitive.** Gujarat's own land record, **Village Form 12**,
is a legal register of the crop grown on each survey number, season by season, year after year. It is
public and online. Three other independent references exist. Ranked below by evidentiary strength.

Research trail: `RESEARCH_LOG_T_U.md` Phase U. Written 2026-08-06.

---

## Tier 1 — Official, per-plot, with history

### U1. ★★★ Gujarat Village Form 12 (VF-12 / 7-12 "Satbara") via AnyROR

**This is the real thing.** The 7/12 extract is Village Form 7 (rights) combined with **Village Form 12,
which is the register of cultivation**: crops grown per survey number, recorded **separately for kharif,
rabi and zaid**, with **area under each crop** and the **irrigation source**, maintained **year on year**
by the village Talati. It is a legal record kept for revenue purposes, not a model output.

That is per-plot crop type *and* per-plot cropping history — exactly what was asked for.

- **Portal:** `anyror.gujarat.gov.in` → "View Land Record – Rural" → District (Vadodara) → Taluka → Village
  (Sokhda) → 7/12 → survey number. Free, no login. Verified live.
- **The missing link — survey numbers.** Our farm shapefile has no survey numbers, only `FID`. Gujarat's
  **BhuNaksha** (`bhunaksha.gujarat.gov.in`) is the **GIS cadastral map showing every survey number's
  boundary polygon**, maintained by the Survey Department and integrated with AnyROR. Spatially join our
  966 farm polygons against the Sokhda cadastral parcels → survey number per farm → VF-12 → crop.
- **Feasibility, honestly:** BhuNaksha exposes a per-village web GIS with PDF export; no documented public
  REST/GeoJSON API. AnyROR is captcha-gated per record. So this is **semi-manual**. A stratified random
  sample of **60–120 plots** is entirely achievable in a day and is statistically ample — at n=100 a 70%
  accuracy carries a ±9 pt confidence interval, which is plenty to state a real number.
- **Caveats to state in the writeup:** VF-12 entries are Talati-recorded and can lag, be generalised, or
  carry the previous season; a survey number may not map 1:1 to a digitised farm polygon (splits, shared
  boundaries). Report the match rate alongside the accuracy.
- ⚠ **Privacy.** 7/12 records carry owner names and are personal land data. Extract **only the crop
  column**, report **only aggregate accuracy**, and publish **no owner names, no survey numbers tied to
  individuals** in a public Kaggle notebook. Use it as a validation set, not as a shipped artefact.

**Why this is worth doing above everything else:** it converts the submission's central weakness —
*"there is no ground truth, so validity can only be argued"* — into *"we obtained the official cultivation
record for a random sample of plots and our crop map is X% accurate."* No other team will have that.

### U2. ★★ Digital Crop Survey (AgriStack), Gujarat

India's Crop Sown Registry: GPS-enabled, plot-by-plot, surveyor-visited crop recording. Active in 17
states, 492 districts, 421k villages; **253 million plots** mapped in the 2024-25 season alone. Gujarat runs
its own DCS app (`gjdcs.agristack.gov.in`).

This is the most authoritative per-plot crop dataset in existence for India — geotagged and season-specific.
**But** states share **village-level aggregates** with the Department of Agriculture via API; per-plot data
is not openly published. Realistic routes: a formal data request, or an academic/hackathon partnership.
Too slow for a 7-day window, but worth one email — and even the **village-level aggregate for Sokhda,
kharif 2025** would independently validate our crop *mix*, which is the quantity the prior pins.

---

## Tier 2 — Independent modelled references at farm level

### U3. ★★★ Google DeepMind ALU / AnthroKrishi — farm-level in-season crop ID for India

This is the highest value-to-effort item after U1, and it is startlingly well matched to our task.

*Deshpande et al., "Farm-Level, In-Season Crop Identification for India", arXiv 2507.02972 (Jun 2025),
Google DeepMind.* Sentinel-1 + Sentinel-2, deep learning, **farm-level**, **in-season**, with an automated
**season-detection algorithm that estimates per-field sowing and harvest dates**. Described as the *first
pan-India, in-season, farm-level crop type data product*. Field boundaries come from the ALU model at 1 m.

Their crop vocabulary contains **every one of our five**: Rice (4,888 GT samples), Cotton (4,365), Corn
(5,499), Groundnut (2,509), Bajra/Pearl Millet (1,732), out of 69,723 ground-truth samples over 2,097
Sentinel-2 L9 cells. Kharif is evaluated separately, and reliable identification is claimed from ~2 months
into the season — so **October 2025 over Sokhda is comfortably inside its operating envelope**.

- **Access:** `agri.withgoogle.com` — Agricultural Landscape Understanding **Research API**, explicitly
  scoped to "researchers / academia". Requires an application. Partners already include IIT Bombay and the
  Government of India.
- **What it would give us:** an independent per-farm label for our exact 966 plots, in our exact season,
  from *different sensors and a different method* — plus per-field sowing/harvest dates, which would
  independently validate the §D season-completion term.
- **Framing:** this is a *reference*, not ground truth — it is a model. But agreement between two
  independent methods on different sensors is strong evidence, and disagreement is informative.
- **Action: apply today.** Even if access does not arrive in time, citing the paper as the state of the art
  and positioning our X-band approach against it strengthens the writeup.

### U4. ★★ Krishi-DSS (Government of India)

`krishi-dss.gov.in`, launched 16 Aug 2024 — the national geospatial decision-support platform for
agriculture. Its published module list includes **"parcel-level crop maps over different years"** and
**field parcel segmentation**. If that layer is browsable for Vadodara, it is *per-parcel crop with
history*, from the government, for free.

The landing page is a JavaScript application and did not yield its layer catalogue to a simple fetch, so
**this needs ten minutes of manual browsing to settle** — highest value-to-effort of anything unverified on
this list. Check it before investing in the manual VF-12 route.

---

## Tier 3 — Independent cross-checks we can build ourselves, today, with no permission

### U5. ★★★ A Sentinel-2 + Sentinel-1 phenology classifier — the pragmatic best move

Fully in our control, no gatekeeper, and it is the strongest *self-serve* independent opinion available.

Evidence for the design: S1+S2 fusion reaches **80–96% overall accuracy** on smallholder systems in
Central/South Asia, with **S1 particularly effective for structurally distinct crops such as cotton** and
S2 improving the more diverse classes; monthly temporal aggregation beats coarser binning by 1–3 points.
For our AOI, Jun–Nov gives roughly 15–20 usable S2 dates plus dense S1 — an order of magnitude more
temporal information than four X-band scenes.

Build it as a **deliberately independent second opinion** on the 966 farms, then report the confusion
matrix against the Capella map. Note it cannot be trained without labels either — so pair it with U1's
sample as the training/validation set, or run it unsupervised (cluster → assign via the same prior) and
report agreement.

**Important framing for the rubric:** this must be presented as *validation*, never as an input. Capella
stays primary. Done that way, it converts the submission's weakest area (Validity, 20 pts) into its second
strongest.

### U6. Existing witnesses — already done, keep them

Same-day Sentinel-2 (13 Oct 2025, 0.003% cloud) and Sentinel-1 RTC VH (10 Oct). Already showing the crop
classes separating in the agronomically correct order. This remains the single strongest existing result.

---

## Tier 4 — Aggregate statistics (yield side)

### U7. PMFBY Crop Cutting Experiments — the missing *yield* validator

The submission currently has **no independent check on the yield column at all** — the district APY anchor
is an input, so comparing against it is circular. PMFBY (crop insurance) runs **Crop Cutting Experiments**
that produce measured yields at the insurance-unit level (village or village-cluster), season by season,
crop by crop, published through the PMFBY/Krishi Rakshak portals.

For Sokhda, kharif 2025, a CCE yield for even one or two of our five crops would give the first genuinely
external check on the yield deliverable. Worth 20 minutes on the portal.

### U8. Gujarat DoA / APY / ICRISAT DLD

District and taluka statistics — already in use as the yield anchor. Not a validator, by construction.

---

## Recommended plan

**Do today, in this order:**

1. **Krishi-DSS** (10 min) — if the parcel-level crop layer covers Vadodara, it may answer the whole
   question for free. Check first because it is cheap and could make U1 unnecessary.
2. **Apply for the Google ALU Research API** (20 min) — long lead time, so start the clock now.
3. **PMFBY CCE for Sokhda / Vadodara kharif 2025** (20 min) — the only route to validating yield.
4. **BhuNaksha → AnyROR VF-12 sample** (half a day) — the definitive per-plot answer. Target 60–120 plots,
   stratified across our five predicted classes so the confusion matrix is balanced. Crop column only;
   no owner data leaves the machine.
5. **S2/S1 independent classifier** (1 day) — the self-serve fallback that needs nobody's permission, and
   which is worth building regardless because it also strengthens the writeup.

**Expected outcome.** With U1 at n≈100 plus U5, the writeup's validation section changes from *"no ground
truth exists, so here are consistency arguments"* to *"we obtained the official cultivation record for a
random sample and measured our accuracy; an independent optical-radar classifier agrees at X%."* That is
the difference between arguing for validity and demonstrating it — and Validity is 20 points.

**One caution.** If VF-12 says our accuracy is poor, that must be reported. It would still be a better
submission than one with no measurement at all, and the rubric rewards checks capable of failing. Decide
in advance that the number gets published whichever way it lands.
