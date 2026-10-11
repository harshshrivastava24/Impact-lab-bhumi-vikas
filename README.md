# Bhumi Vikas Sahayak

Rule lookup and compliance decision-support tool for the building-permission counter of the Bhopal Municipal Corporation (BMC).

> **This is a rule reference, not legal advice. The building-permission clerk decides.**

The tool locates the governing provisions of the Madhya Pradesh Bhumi Vikas Rules, 2012, performs deterministic arithmetic on table values from those rules, and presents the result with rule number, verbatim text, PDF page and rule version. It is not a citizen portal, does not grant or refuse permission, does not connect to any government system, and does not give legal advice.

## What Works (Phase 2)

| Feature | Status |
|---|---|
| Corpus loading (106 records) | ✅ |
| Header stripping | ✅ |
| Inserted-rule resolution (12-A, 17-a, 25(A), 26-A, 42-A, 93(a)) | ✅ |
| Footnote preservation | ✅ |
| Range tables verified against PDF | ✅ |
| Front setback (FR-14) | ✅ |
| Rear setback (FR-15) | ✅ |
| Side setback with provisos (FR-16) | ✅ |
| Height limit (FR-17) | ✅ |
| Derived storey count (FR-18) | ✅ |
| FAR and floor area (FR-19) | ✅ |
| Fee computation (FR-20) | ✅ |
| Ground coverage – prescribed branch (FR-51) | ✅ |
| Calculation trace (FR-22) | ✅ |
| Version stamp (FR-23) | ✅ |
| Amendment flag – Rule 2(5)(c) (FR-25) | ✅ |
| Not-found with exact wording (FR-26) | ✅ |
| Fabrication guard (FR-27) | ✅ |
| Language detection (FR-03) | ✅ |
| Rule-based parser (FR-02) | ✅ |
| Keyword fallback returning Rule 103 (FR-12) | ✅ |
| Audit log (FR-38) | ✅ |
| /api/health, /api/lookup, /api/parse, /api/rules/{rule} | ✅ |
| Eval harness (17 questions) | ✅ |
| Frontend static serving | ✅ (requires `npm run build` in frontend/) |

**Evaluation result: 14/17 sample questions pass (including both not-found cases); 17/17 geometry cases pass with zero false "no conflict" results.**
Failing: Q4 (Rule 28 consequence), Q12 (Rule 103 keyword fallback), Q13 (Rule 56(4) garage); all three return not-found instead of the expected citation. NFR-03 needs at least 15.
*(Run `python eval/run_eval.py`; it falls back to an in-process client when no server is running)*

## What Works (Phase 3, plan check)

| Feature | Status |
|---|---|
| `POST /api/plan-check` per the API contract | ✅ |
| Area mismatch gate (FR-39), `use_dimensions` resolution | ✅ |
| Refusals: corner plot with both readings, non-residential, height above 12.5 m (FR-48) | ✅ |
| Footprint validation, 422 naming the field (FR-42) | ✅ |
| Envelope, footprint, per-side shortfall and overlap rectangles (FR-40, FR-43) | ✅ |
| FR-47 trace on every side, height-coupled side proviso (FR-44) | ✅ |
| Derived ground coverage citing Rule 2(20) (FR-51) | ✅ |
| Rule 53(1)(i) development-type warning | ✅ |
| Exceptions register `config/exceptions.json` (FR-45) | ✅ |
| Hindi labels and messages; optional Hindi trace rendering labelled "rendering, not official text" (FR-30) | ✅ |
| Audit log with geometry inputs and per-side results (FR-49) | ✅ |
| Geometry eval cases (FR-50): 17/17 | ✅ |

The plan check reads the same `config/range_tables.json` rows as `/api/lookup`. `backend/tests/test_plan_check.py` asserts that both give identical front, rear and side values and development-type warnings.

## What Does Not Work Yet

| Feature | Phase |
|---|---|
| Plot envelope drawing (SVG), print view | Phase 1 frontend |
| Sample questions 4, 12, 13 | Phase 2 retrieval |
| `config/strings.hi.json` machine-drafted; needs review by a Hindi-literate teammate | Phase 1 |

## Run in Five Steps

```bash
# 1. Clone
git clone <repo-url>
cd Impact-lab-bhumi-vikas

# 2. Create Python virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. Install backend dependencies
pip install -r backend/requirements.txt

# 4. (Optional) Build frontend
cd frontend && npm install && npm run build && cd ..

# 5. Run the server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

The tool is now available at http://localhost:8000

## Running Tests

```bash
# Backend tests (from repo root)
pytest backend/tests/ -v

# Evaluation harness (server must be running)
python eval/run_eval.py

# With inference disabled (FR-21: identical numeric results expected)
python eval/run_eval.py --no-inference
```

## API

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | Corpus status and version |
| `/api/parse` | POST | Free text → params and topics |
| `/api/lookup` | POST | Main lookup: params + topics → figures + citations |
| `/api/rules/{rule}` | GET | Single rule citation |
| `/api/plan-check` | POST | Plan check: params + footprint → envelope, per-side shortfalls, overlaps |
| `/pdf/en` | GET | English PDF |
| `/pdf/hi` | GET | Hindi PDF |
| `/` | GET | Phase 1 frontend (if built) |

## Corpus Update (FR-36, NFR-12)

To update the rule corpus with no code change:

1. Replace `data/bhumi_vikas_rules.jsonl` with the updated file.
2. Optionally update `config/range_tables.json`, `config/topic_map.json`, `config/amendments.json`.
3. Restart the server: `uvicorn backend.app.main:app ...`

The server will report any integrity issues (missing records, gaps) at startup.

## Amendment Register

The tool ships with the following known amendment that is **not yet in the corpus**:

| Date | Rule | Condition | Source |
|---|---|---|---|
| 28 August 2026 | 2(5)(c) | plot_area ≤ 500 sq m | Secondary notice (TeamLease RegTech) |

When a query involves a plot up to 500 sq m, the tool displays: "Potentially relevant amendment" with the concerns, source and the statement that it is not applied in the shown figures. The gazette text is not yet available; update the amendments.json file when it is.

## Data Sources

| Reference | Description | Source |
|---|---|---|
| R1 | MP Bhumi Vikas Rules 2012, English, consolidated to 6 March 2025 | https://mptownplan.gov.in/NewsPDF/bvn06032025E.pdf |
| R2 | MP Bhumi Vikas Rules 2012, Hindi, consolidated to 6 March 2025 | mptownplan.gov.in |
| R3 | `data/bhumi_vikas_rules.jsonl` – 106 machine-readable rule records | Derived from R1 |

## Design Constraints

- All arithmetic in application code; no number originates from a language model
- No personal data collected, stored or logged
- No connection to any government system
- MIT licence; public repository
- Runnable in five steps on Windows or Ubuntu, no GPU required

## Licence

MIT – see [LICENSE](LICENSE).
