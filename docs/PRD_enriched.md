# PRD — ICP Discovery Engine (MVP → V1.1)

## 0. Vision & Outcomes
Build a **reliable, observable, repeatable** workflow that discovers **net-new, high-fidelity** accounts across three ICPs with **deterministic evidence** and **schema-perfect CSV outputs**, scaling from dozens to **hundreds+** per segment without quality loss.

**Primary KPIs**
- Acceptance (human spot-check) on Confirmed ≥ **90%**.
- NA/EMEA mix **80/20** target per batch (report achieved mix).
- Output schema **100%** conformant to sample headers.
- Evidence coverage: **100%** rows include ≥1 provider-authored URL.
- Cost envelope: ≤ **$X** per 100 accounts (to be baselined in V1).

**Non-goals (MVP)**
- No autonomous multi-agent behaviors; no contact scraping; no CRM writeback.

---

## 1. Users & Jobs-to-be-Done
- **Sales/Marketing Ops**: Export **long, net-new** target lists per ICP.
- **Revenue/Exec**: Weekly rollups (counts, tiers, regional mix, acceptance).
- **Analyst/QA**: Review “Probable/Needs-Confirmation” items and drift alerts.

---

## 2. ICPs (Ground Truth Criteria)
### 2.1 Healthcare EHR Adoption & Training (Provider-led)
- **Must-haves**: Provider org; Active EHR lifecycle (selection/impl/go-live/opt); **VILT** primary; training infrastructure (super users/credentialed trainers/command center).
- **Disqualify**: Payers/pharma/devices; async-only; one-dept pilots; micro practices.

### 2.2 Corporate Academy (Large Enterprise)
- **Must-haves**: Named academy/university; programmatic cohorts; **VILT** modality; size ≥ **7,500** employees (or G2K); evidence of academy ops.
- **Disqualify**: Compliance-only L&D; customer-only academies; higher-ed/government schools.

### 2.3 Professional Training Providers (VILT-Core)
- **Must-haves**: B2B model; **live virtual** training core; public calendar (≥5 sessions/90d); instructor bench (≥5); accreditations (PMI/NEBOSH/etc.).
- **Disqualify**: MOOC/marketplaces; K‑12/test prep; async-only; micro bootcamps; consulting-primary.

(Full scoring matrices in §6.)

---

## 3. Architecture (MVP walking skeleton)
**Pattern:** stateful **workflow** (LangGraph) → deterministic nodes; **MCP-style tools** for external I/O; **evaluator** gates before outputs.

```
seed → harvest → extract → score → dedupe → enrich → output → ledger_upsert
```

**Tools (MCP contracts):**
- `web.search({q, max, site?}) -> [{title,url,snippet}]`
- `web.fetch({url}) -> {status,url,html,text}` (retries, allow-list domains)
- `explorium.enrich({company|domain}) -> {size_range, industry, country, ...}`
- `ledger.load({segment}) -> [org_names]`
- `ledger.upsert([{organization, segment, region, tier, score, evidence_url, notes}])`

**Runtime:** FastAPI (`POST /run`), CSV/TXT outputs, Google Sheets ledger.

---

## 4. Data Contracts (Output Schemas)
### 4.1 Healthcare CSV headers (exact order)
`Organization, Region, Type, Facilities, EHR_Vendor, EHR_Lifecycle_Phase, GoLive_Date, Training_Model, VILT_Evidence, Web_Conferencing, LMS, Tier, Confidence, Evidence_URLs, Notes`

### 4.2 Corporate Academy CSV headers
`Company, HQ_Location, Employee_Count_Range, Revenue_Range, Academy_Name, Academy_URL, Program_Structure, VILT_Evidence, Academy_Scope(Employees/Partners/Dealers), Web_Conferencing, LMS, Scale_Details, Tier, Confidence, Evidence_URLs, Notes`

### 4.3 Professional Training Providers CSV headers
`Company, Website, HQ_Country, Regions_Served(NA/EMEA/Both), Provider_Type, Primary_Tags, B2B_Evidence_URL, VILT_Modality_URL, Web_Conferencing, LMS, VILT_Sessions_90d, VILT_Schedule_URL, Instructor_Bench_Notes, Accreditations, Named_Enterprise_Customers(Y/N), Named_Enterprise_Examples, Tier, Confidence, Evidence_URLs, Notes`

**Notes**
- `Evidence_URLs` supports multiple URLs separated by `|`.
- `Confidence` = numeric 0–100; `Tier` in {Confirmed, Probable, Needs Confirmation}.

---

## 5. Pipeline I/O (per node)
- **seed**: inputs: `segment, region, targetcount`; outputs: `seeds[]({title,url})`.
- **harvest**: fetch pages; emit `candidates[]({organization, evidence:{provider_org, ehr_activity|academy_exists|calendar, vilt_present, training_program/instructor_bench, large_scale, evidence_url}, region})`.
- **extract**: normalize org names, detect EHR vendor/academy name/calendar URLs (regex/entity rules).
- **score**: apply per-ICP matrix (§6); compute `{score,tier,missing}`.
- **dedupe**: remove orgs in `ledger.load(segment)`; within-run unique by org.
- **enrich**: Explorium to confirm size/region and boost `large_scale`/HQ fields.
- **output**: format CSV per schema; compute NA/EMEA mix; write TXT summary.
- **ledger_upsert**: append `{org, segment, region, tier, score, first_added, last_validated, evidence_url, notes}`.

---

## 6. Scoring Matrices (weights)
### 6.1 Healthcare (100 pts)
- Provider organization (hospital/IDN/AMC) ………………… **+5**
- **EHR lifecycle active** (selection/impl/go-live/opt) …… **+40** (MUST)
- **VILT present** (explicit live virtual training) ………… **+30** (MUST)
- Training infrastructure (super users/CT/command center) … **+15**
- Large scale (multi-hospital, >10k staff) ………………… **+5**
- **Tier mapping**: ≥90 & all MUST → Confirmed; 70–89 → Probable; else Needs Confirmation.

### 6.2 Corporate (100 pts)
- **Named academy/university exists** ……………………… **+50** (MUST)
- Company size ≥7,500 or G2K ……………………………… **+10** (MUST)
- Programmatic cohorts/learning paths ……………………… **+15**
- **VILT modality** documented (virtual classroom) ……… **+15** (MUST)
- Awards/recognition (Top 125/CLO/ATD) ………………… **+5..15**
- External scope (partners/dealers) ………………………… **+5**
- Mapping: same thresholds.

### 6.3 Providers (100 pts)
- **B2B focus** (for organizations) ………………………… **+20** (MUST)
- **VILT core** (front-and-center) …………………………… **+25** (MUST)
- **Public calendar ≥5 sessions/90d** ……………………… **+20** (MUST)
- **Instructor bench ≥5** (site or LinkedIn) ………………… **+15** (MUST)
- Accreditations (PMI/NEBOSH/etc.) ……………………… **+10**
- Enterprise client logos/cases ……………………………… **+10**
- Geo reach (NA/EMEA/Both) ………………………………… **+5**
- Mapping: same thresholds.
- **Red flags (exclude)**: MOOC/marketplaces; K‑12; async-only; micro-ops; consulting-primary.

---

## 7. Query Libraries (seed sets, expand in code)
### 7.1 Healthcare
- `"Epic go-live" AND training AND hospital 2024..2026`
- `site:beckershospitalreview.com ("go-live" AND training)`
- `<Hospital Name> "credentialed trainer" | "super user" | "command center"`
- `("EHR implementation" OR "switch to Epic") AND ("virtual training" OR "live online")`

### 7.2 Corporate
- `"launches corporate university" 2023..2026`
- `inurl:academy.[company].com OR inurl:universityof`
- `"Training Top 125" winners 2024..2026` + company verification
- `site:cornerstoneondemand.com case study "academy"` (repeat for LMS vendors)

### 7.3 Providers
- `site:*.com (inurl:schedule OR inurl:calendar) "virtual" "instructor-led"`
- `"Authorized Training Partner" (PMI|CompTIA|NEBOSH) "virtual"`
- `"live online" "upcoming courses" -"udemy" -"coursera" -"edx"`

---

## 8. Evaluations (release gates)
- **Dataset**: `/evals/data/icp_eval_set_v1.csv` (20 golds). Add 30 more in V1.1.
- **Evaluators**:
  - `schema_completeness`: required headers populated per ICP.
  - `evidence_support`: page text contains key claim terms (regex/heuristics).
  - `tier_mapping`: score thresholds respected; MUST-haves present for Confirmed.
- **Thresholds (MVP)**: schema 100%; evidence ≥90%; tier mapping 100%.
- **Process**: every PR → run evals; if fail → block merge. Add LangSmith Align Evals when available.

---

## 9. Observability, Errors, Security
- **Tracing**: per-node latency, tokens/cost; include `batch_id`, `segment`, `region`.
- **Logs**: JSON; redact secrets/PII; include URL allow/deny decisions.
- **Errors**: `web.fetch` retries (3), exponential backoff; circuit-break on 5xx.
- **Security**: Domain allow-list; strip JavaScript; ignore forms; **no** tool execution from page data.
- **Secrets**: env-only (OpenAI, Explorium, Google SA); never in logs.

---

## 10. Regional Logic
`NA_target = ceil(N*0.8)`, `EMEA_target = N - NA_target`. If thin supply, backfill; report achieved mix in TXT summary.

---

## 11. Roadmap
- **MVP (this sprint)**: Healthcare loop + eval gates + ledger + CSV.
- **V1.1**: Corporate & Providers flows, schema-complete outputs, expanded libraries.
- **V1.2**: Observability (LangSmith), domain allow-list, stronger extractors.
- **V2**: Scheduling, Google Drive export, optional Prompt Flow parity.
