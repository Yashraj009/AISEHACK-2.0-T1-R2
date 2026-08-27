# How to retrieve each ground-truth source — step by step

Four sources, ordered by **value per hour of your time**. Do them in this order; #1 can
make #4 unnecessary.

Everything you collect feeds one file — `data_aux/ground_truth_vf12.csv` — and one command:

```bash
python src/ingest_ground_truth.py
```

That prints measured accuracy for **both** crop maps (ours and the independent S2+S1 one),
area-weighted, with Cohen's kappa and a majority-class baseline. It's already dry-run tested,
so it will work the moment you have rows.

**Your field sheet is ready:** `data_aux/ground_truth_TEMPLATE.csv` — 100 farms, 20 per
predicted crop, with `farm_id`, `lat`, `lon`, plot area, our prediction, the independent
prediction and our confidence. Fill the `vf12_crop` column, save as
`data_aux/ground_truth_vf12.csv`. Partial is fine — blank rows are skipped and you can
re-run as more arrive.

> **Stratified, not random, and deliberately so.** A random 100 would draw ~47 cotton and
> ~6 maize, and 6 maize can't measure maize accuracy. 20 per class gives every crop enough
> rows; the script re-weights back to the true village shares (Cotton 43.1%, Groundnut
> 31.7%, Rice 10.0%, Bajra 9.3%, Maize 6.0%) when it computes the headline number.
>
> **Fill it in without looking at the `crop_type` column if you can.** It's there so the
> analysis can ask "does our confidence predict correctness?" — not to anchor you. If you
> read our guess first, the accuracy you measure is worth less.

---

## 1. Krishi-DSS — 10 minutes, could answer everything

**Why first:** its published module list advertises *"parcel-level crop maps over different
years"*. If that layer covers Vadodara it gives per-parcel crop **with history**, free,
from the government — and makes the whole VF-12 exercise unnecessary.

**Why I couldn't do it:** it serves an identical 78 kB SPA shell on every path I probed
(`/`, `/api/v1/layers`, `/geoserver/*`). It needs a real browser session.

**Steps**

1. Open <https://krishi-dss.gov.in/> in Chrome.
2. Find the layer/module list — look for **Crop Map**, **Crop Mapping**, **Parcel**, or
   **Field Parcel Segmentation**.
3. Navigate to **Gujarat → Vadodara → Vadodara taluka → Sokhda**, or pan to
   **73.157 E, 22.425 N**.
4. Check three things and tell me the answers:
   - Is there a **crop type per parcel**, or only district/village aggregates?
   - Which **years and seasons** — is kharif 2025 there?
   - Can you **export** (download / GeoJSON / shapefile / CSV)?

**★ The developer-tools trick, which is what actually matters.** Even with no export
button, the map is fetching data from somewhere and you can capture it:

1. Press **F12** → **Network** tab → filter **Fetch/XHR**.
2. Pan/zoom to Sokhda so the map loads tiles.
3. Look for requests returning JSON or `.geojson`, or WMS/WFS `GetFeatureInfo` calls.
4. Right-click a promising one → **Copy → Copy as cURL**, and paste it to me.

With that I can usually pull the layer programmatically for all 966 farms. This single
step is the highest-value thing in this document.

---

## 2. Google ALU / AnthroKrishi API — start now, it has a lead time

**Why:** *arXiv 2507.02972* (Google DeepMind) is farm-level, in-season, pan-India, and its
crop list covers all five of ours. The FAQ confirms the **AMED** endpoint returns crop
predictions for 12 crops plus **"crop prediction confidence, season length, and predicted
crop history"** — field-level, refreshed ~15 days. India-only. **Free, no rate limit.**
"Predicted crop history" is exactly the per-farm history you asked about.

**⚠ One likely blocker, so check it first.** Access requires a **Google Workspace Customer
ID**, which normally means an *organisation* account — not a personal `@gmail.com`. If your
university has Google Workspace, use your institutional address; a supervisor can usually
supply the Customer ID. If not, this route may be closed to you, and it's worth finding
that out in five minutes rather than five days.

**Steps**

1. Read <https://agri.withgoogle.com/faq/>.
2. Create a **Google Cloud project** and **enable billing** (the API is free, but billing
   must be on).
3. Find your **Google Workspace Customer ID**: Google Admin console → *Account settings*.
4. Request allowlisting through the contact route on the site, supplying the Customer ID
   and the authorised email. Say it's for the **ANRF AISEHack 2.0 academic hackathon** and
   that you need **kharif 2025, Vadodara district** — a specific, small, academic ask lands
   better than an open-ended one.
5. Once allowlisted: enable the API in the project, create an API key, send it to me
   **by a private channel, not in this chat**.

**Even if access never arrives**, citing the paper and positioning our X-band approach
against the state of the art strengthens the writeup. That costs nothing.

---

## 3. PMFBY Crop Cutting Experiments — the only route to validating *yield*

**Why this matters more than it looks:** the submission currently has **zero** independent
check on the yield column. The district APY figure is an *input*, so comparing against it is
circular. CCEs are physically measured yields at insurance-unit (village or cluster) level,
by season and crop.

**Steps**

1. Open <https://pmfby.gov.in/>.
2. Look under **Reports** / **Yield Data** / **Statistics**, or the National Crop Insurance
   Portal linked from there. Operational guidelines state that *"last 10 years yield data at
   notified level"* is uploaded to the portal, so historical yield by notified unit should
   be published somewhere.
3. Filter: **Gujarat → Vadodara → Kharif 2025** (fall back to 2024 or 2023 if 2025 isn't
   published yet — even a prior year gives a plausibility band).
4. Record, per crop: **notified unit**, **crop**, **season**, **year**, **yield kg/ha**.
5. Also try the **Krishi Rakshak** portal and the state Directorate of Agriculture site.

**What I do with it:** compare against our village aggregate — Bajra 2.55, Maize 2.19,
Groundnut 1.90, Rice 1.60, Cotton 0.35 t/ha. Even one crop matching within a sensible band
converts "anchored to district statistics" into "validated against measured yields".

⚠ Note the unit trap: **cotton is usually reported as lint, not seed cotton** — a factor of
~3. Record exactly what the source says.

---

## 4. BhuNaksha → AnyROR VF-12 — the definitive per-farm answer

**Why:** Village Form 12 is a **legal register of the crop grown on each survey number**,
recorded separately for kharif/rabi/zaid, with area per crop and irrigation source,
maintained year on year by the village Talati. Per-plot crop **and** history. Free.

**Why it's last:** it's the most manual. Budget ~3–5 minutes per plot; 100 plots is roughly
half a day. Do #1 first — it may make this unnecessary.

**The hard part is the join.** Our polygons have no survey numbers, so you need
farm → survey number → VF-12.

**Steps**

1. **Find the survey number for a farm.** Open BhuNaksha for Gujarat (reachable via the
   AnyROR portal — note `bhunaksha.gujarat.gov.in` did not resolve for me, so go through
   <https://anyror.gujarat.gov.in/> rather than direct). Select **Vadodara → Vadodara →
   Sokhda**. The cadastral map draws every survey-number parcel.
2. Locate the plot using the **`lat`/`lon` from the field sheet**. Cross-check the shape
   against `results/figures/cover.png`, which shows the same parcels.
3. Read off the **survey number**; record it in `survey_no`.
4. **Get the crop.** On AnyROR → *View Land Record – Rural* → District **Vadodara**, Taluka
   **Vadodara**, Village **Sokhda**, record type **7/12**, enter the survey number, solve
   the captcha.
5. In the **Village Form 12 / crop details** section, find the **kharif 2025** row and
   record the crop in `vf12_crop`.
6. Repeat. Work down the sheet in order — it's already stratified, so **stopping early is
   fine** as long as you don't skip around, which would reintroduce bias.

**Free-text is fine.** The ingester maps Gujarati/English variants automatically — *paddy,
dhan, kapas, makai, bajri, mungfali* all resolve correctly. Anything outside our five
classes is recorded as `Other` and excluded, with the count reported.

### ⚠ Privacy — please follow this

7/12 extracts carry **owner names**. They are personal land records.

- Record **only** the crop column (and survey number for traceability).
- **Never** put owner names, or survey numbers tied to individuals, in the public Kaggle
  notebook or writeup.
- Report **aggregate accuracy only**.
- Keep `ground_truth_vf12.csv` out of the public repo — add it to `.gitignore`.

The validation is fully served by aggregate numbers, so there's no cost to being strict here.

---

## What to send me

| source | what to send |
|---|---|
| Krishi-DSS | Answers to the three questions, and **the "Copy as cURL" from the Network tab** if you find a data request |
| ALU API | Whether the Workspace Customer ID is available; the API key privately once allowlisted |
| PMFBY | Crop, unit, season, year, yield kg/ha — a screenshot or paste is fine |
| VF-12 | `data_aux/ground_truth_vf12.csv` with `vf12_crop` filled in, even partially |

## One thing to agree before you start

Decide **now** that the number gets published whichever way it lands. If VF-12 says our map
is poor, that goes in the writeup — a measured accuracy that disappoints still beats a
submission with no measurement, and the rubric explicitly rewards checks capable of failing.
Deciding this in advance is what stops it becoming a temptation later.
