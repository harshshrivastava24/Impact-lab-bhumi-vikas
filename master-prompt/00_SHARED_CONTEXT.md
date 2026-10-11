# Shared Context for All Build Phases

Read this file before any phase prompt. Every phase prompt assumes it.

## Project

Bhumi Vikas Sahayak: a rule lookup and compliance decision-support tool for the building-permission clerk at the Bhopal Municipal Corporation. The full specification is `SRS_Bhumi_Vikas_Sahayak.md` version 1.2 at the repo root. Requirement IDs (FR-xx, NFR-xx, C-xx) in the phase prompts refer to that document. When a prompt and the SRS disagree, the SRS wins.

Never describe the tool as a chatbot, assistant or conversational agent in code, comments, UI text or README. It is a lookup and compliance tool. The clerk decides; the tool points to the rule.

## Hard constraints (from SRS Section 2.5)

- Public data only. No connection to any government system. No scraping, login or writes to any portal.
- No personal data collected, stored or logged. Free text typed by the clerk is never logged.
- Every result carries the disclaimer: "This is a rule reference, not legal advice. The building-permission clerk decides."
- All arithmetic in application code. No number, rule number or page number may originate from a language model.
- No secrets in source. Configuration by environment variables only. Check before every push.
- MIT licence. Runnable by the department in five documented steps or fewer.
- Single workflow, single user role. Not a citizen portal.

## Stack (default; change only if the whole team agrees)

| Layer | Choice | Reason |
|---|---|---|
| Backend | Python 3.11, FastAPI, Uvicorn | Readable by department staff; no GPU; JSONL handling trivial |
| Frontend | React 18, Vite, TypeScript (strict), Tailwind CSS v4 | Fast to build; static output served by the backend; full frontend stack in `frontend-phases/frontend-phases.md` |
| Drawing | Inline SVG rendered by React | No canvas library; scales cleanly; printable |
| Tests | pytest (backend), Vitest and Playwright (frontend) | Standard |
| Data | JSON and JSONL files in `data/` and `config/` | Corpus update without code change (FR-36) |

Final run steps must be five or fewer, for example: clone, create venv, pip install, npm install and build, run uvicorn.

## Repository layout

```
/
  README.md
  LICENSE                      MIT
  SRS_Bhumi_Vikas_Sahayak.md
  master-prompt/               these prompts
  data/                        bhumi_vikas_rules.jsonl, fulltext_by_page.txt (copied from the track pack)
  resources/                   EN and HI PDFs, sample_questions.md (copied from the track pack)
  config/
    topic_map.json             FR-07
    range_tables.json          FR-13
    amendments.json            FR-24
    exceptions.json            FR-45
    strings.en.json            NFR-11
    strings.hi.json
    settings.json              rule version date (FR-23), thresholds
  eval/
    expectations.json          FR-35, FR-50
    run_eval.py                FR-34
  backend/
    app/                       FastAPI app, routers, services
    tests/
  frontend/
    src/
    dist/                      built output served by backend at /
  logs/                        queries.jsonl (gitignored)
```

## API contract

The frontend is built first against this contract with a mock server. Backend phases implement it exactly. All bodies are JSON. All distances in metres, areas in square metres, money in rupees as integers.

### POST /api/parse
Request: `{ "text": string }`
Response: `{ "language": "en" | "hi", "params": Partial<Params>, "topics": Topic[], "used_inference": boolean }`
Params and Topic types are defined below. Never returns rule numbers or figures.

### POST /api/lookup
Request:
```
{
  "params": {
    "plot_area": number, "road_width": number,
    "use_type": "residential" | "commercial" | "public" | "industrial" | "agricultural",
    "built_up_area"?: number, "height"?: number,
    "development_type"?: "detached" | "semi_detached" | "row",
    "frontage"?: number, "depth"?: number, "floor_to_floor"?: number,
    "existing_developed_area"?: boolean,
    "streets_abutting"?: 1 | 2
  },
  "topics": Topic[],
  "language": "en" | "hi"
}
```
Topic is one of: `front_setback`, `rear_setback`, `side_setback`, `height_limit`, `far`, `ground_coverage`, `application_fee`, `permission_fee`, `permission_validity`, `documents_required`, `plan_check`.

Response:
```
{
  "status": "answered" | "not_found" | "refused" | "blocked",
  "message"?: string,
  "figures": Figure[],
  "citations": Citation[],
  "version": { "consolidated_to": "2025-03-06", "label": string },
  "amendment_flags": AmendmentFlag[],
  "disclaimer": string,
  "language": "en" | "hi",
  "used_inference": boolean
}
```
Figure: `{ "topic": Topic, "label": string, "value": number | null, "unit": string, "derived": boolean, "conditional": boolean, "trace": string, "rule": string, "page": number, "cases"?: Figure[] }`
Citation: `{ "rule": string, "sub_rule"?: string, "title": string, "part": string, "page_start": number, "page_end": number, "text_en": string, "pdf_en_url": string, "pdf_hi_url": string, "footnotes": string[] }`
AmendmentFlag: `{ "date": string, "rule": string, "concerns": string, "source_url": string, "source_kind": "primary" | "secondary", "applied": false, "note": string }`

### POST /api/plan-check
Request: lookup `params` (frontage, depth, development_type, height mandatory) plus
```
"footprint": { "front": number, "rear": number, "left": number, "right": number }
```
Response: lookup response fields plus
```
"geometry": {
  "plot": { "width": number, "depth": number, "area": number },
  "required": { "front": SideReq, "rear": SideReq, "left": SideReq, "right": SideReq },
  "envelope": { "x": number, "y": number, "width": number, "depth": number, "area": number },
  "footprint": { "x": number, "y": number, "width": number, "depth": number, "area": number },
  "sides": [ { "side": "front"|"rear"|"left"|"right", "required": number, "provided": number, "shortfall": number, "rule": string, "page": number, "trace": string } ],
  "overlaps": [ { "side": string, "x": number, "y": number, "width": number, "depth": number, "shortfall": number } ],
  "result": "No setback conflict found against the checks listed" | "Setback conflict found",
  "checks_performed": string[],
  "not_checked": string,
  "ground_coverage_derived": number,
  "exceptions_available": [ { "id": string, "label": string, "rule": string, "page": number } ]
}
```
SideReq: `{ "value": number, "rule": string, "sub_rule": string, "page": number, "trace": string }`
Coordinates: origin at the front-left corner of the plot, x to the right along the road, y into the plot away from the road.
`status` is `blocked` when FR-39 area mismatch applies, with `message` and `resolutions: ["correct_inputs", "use_dimensions"]`; `refused` for FR-48 cases with the reason in `message`.

### GET /api/rules/{rule}
Returns one Citation for the rule number (string, for example `56` or `26-B`). 404 if not in the corpus.

### GET /api/health
`{ "ok": true, "rules_loaded": 106, "version": "2025-03-06", "inference_configured": boolean }`

### GET /pdf/en, GET /pdf/hi
Serve the PDFs. Frontend opens `/pdf/en#page=N`.

## Verified range-table values

These were read from the corpus text. Phase 2 must re-verify every row against the English PDF page before use and record the page in the table file.

| Table | Rule, page | Rows |
|---|---|---|
| Front open space, residential up to 12.5 m | 56(1)(a), p. 77 | road up to 9.0: 3.0; more than 9 up to 12: 3.6; more than 12 up to 18: 4.5; above 18: 6.0 |
| Narrow street | 56(1)(b), p. 77 | existing developed areas, street under 6.0 m: building line 6.0 m from street centre line |
| Rear open space | 56(2)(a), p. 78 | plot up to 40: nil; above 40 up to 150: 1.50; above 150 up to 225: 2.50; above 225: 3.00 |
| Side open space | 56(3), p. 78 | detached: 3.0 both sides, one side may be 1.5 if height up to 7 m and frontage under 12 m; semi-detached: 3.0 one side, may be 2.5 if height up to 10 m and frontage up to 10 m; row: nil |
| Plot size and frontage by type | 53(1)(i), p. 70 | detached: above 225 sq m, frontage above 12; semi-detached: 125 to 225, frontage 8 to 12; row: 50 to 225, frontage 4.5 to 12 |
| FAR | 61 Table 8, p. 83 | residential 1.25; commercial 2.50 city centre, 2.00 sub-city, 1.75 community, 1.50 local shopping, 1.25 convenience; public/semi-public 1.00; industrial per Rule 48 |
| Height above 12.5 m up to 30 m | 42 Table 4, p. 58 | road 12 m and above, plot 1000, frontage 18, FAR 1.5, height up to 18, front MOS 7.5, sides/rear 6.0; road 18, plot 1500, frontage 21, FAR 1.75, up to 24, 9.0, 6.0; road 24, plot 2000, frontage 30, FAR 2.0, up to 30, 12.0, 7.5 |
| High rise | 42 Table 5, p. 59 | road 30: plot 2500, frontage 30, FAR 2.25, GC 30 %, up to 45 m, front 15, sides 7.5; road 36: 3000, 40, 2.50, 30 %, up to 60, 18, 9; road 45: 3500, 45, 2.75, 30 %, up to 75, 21, 9; road 60: 4000, 50, 3.0, 30 %, up to 90, 24, 10; road 75: 4500, 60, 3.0, 30 %, above 90, 30, 12 |
| Application fee | 21(2), p. 35 | development permission Rs 5000 per hectare or part; building permission Rs 1.00 per sq m built-up area; non-refundable |
| Permission fee, residential, not high rise | 21(3)(b) item 1, p. 36 | built-up 0 to 75: 750; 76 to 125: 1,250; 126 to 200: 2,000; 201 to 300: 3,000; 301 to 400: 4,000; 401 to 600: 6,000; 601 to 750: 7,500; 751 to 1,000: 10,000; 1,001 to 1,250: 12,500; 1,251 to 1,500: 15,000; 1,501 to 2,000: 20,000; 2,001 to 2,500: 25,000; above 2,500: 50,000 |
| Permission fee surcharges | 21(3)(b) items 2 to 9, p. 36 to 37 | commercial, shops, factory: item 1 plus 50 %; factory admin block: item 1; shop-cum-residence: item 1 plus 50 %; cinema: Rs 15,000 up to 800 seats, Rs 25,000 above; social, charitable, educational and unspecified: item 1; external alteration not adding area: Rs 500; alteration in proposed plan up to 10 %: Rs 500, above 10 %: fresh application; revalidation: 10 % of original permission fee |
| Permission fee, high rise | 21(3)(c), p. 37 | residential Rs 10 per sq m built-up; commercial plus 100 %; shop-cum-residence plus 50 % |
| Duration of sanction | 23, p. 41 | valid 3 years; revalidation two consecutive terms of 1 year; 5 year limit not relaxed; no lapse once execution begins |

## Worked example used as the first acceptance test (SRS Appendix A)

Plot 200 sq m, road 9 m, residential, built-up 250: front 3.0, rear 2.50, height up to 12.5 m (Rule 42 Table 4 needs 12 m road), FAR 1.25, floor area 250, application fee 250, permission fee 3,000, amendment flag for 28 August 2026 shown as potentially relevant and not applied.
Plan check extension: frontage 10, depth 20, semi-detached, height 10, footprint front 2.4, rear 2.5, left 2.5, right 0: envelope 7.5 x 14.5 = 108.75; footprint 7.5 x 15.1 = 113.25; front shortfall 0.60; result "Setback conflict found"; ground coverage derived 54.4 %.

## Definition of done for every phase

- All acceptance criteria of the listed FRs pass and are covered by an automated test.
- `python eval/run_eval.py` runs without error (even if some cases fail in early phases) and prints per-case pass/fail.
- No secrets, no personal data, no outbound calls except the configured inference endpoint.
- README updated with what works and what does not.
- Commit on a feature branch; do not force-push.
