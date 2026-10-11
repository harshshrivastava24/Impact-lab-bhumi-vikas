# Bhumi Vikas Sahayak

## Team

- Team name: _to be filled_
- Members: Harsh Shrivastava, _others to be filled_

## Track

Track 1: Bhumi Vikas Sahayak (MP Bhumi Vikas Rules, 2012).

## The one user

The building-permission clerk at the Bhopal Municipal Corporation counter.

## What it does

It looks up the governing rule in the MP Bhumi Vikas Rules 2012 and computes the figures in code, with the rule number, page and calculation trace for each one. The plan check takes a rectangular plot and a proposed footprint. It then works out the required open space on each side, the buildable envelope and any shortfall per side, so the clerk can point to the exact rule at the counter. The clerk decides; every result carries the disclaimer "This is a rule reference, not legal advice. The building-permission clerk decides."

## Run it

1. `git clone <repo-url> && cd Impact-lab-bhumi-vikas`
2. `python -m venv .venv` and activate it (`.venv\Scripts\activate` on Windows, `source .venv/bin/activate` elsewhere)
3. `pip install -r requirements.txt`
4. `cd frontend && npm install && npm run build && cd ..` (skip until the Phase 1 frontend is in the repository)
5. `uvicorn backend.app.main:app --port 8000`, then open http://localhost:8000

Tests: `python -m pytest backend/tests`. Evaluation: `python eval/run_eval.py`.

Copy `.env.example` to `.env` only if you use the optional inference service; the tool runs fully rule-based without it.

## What works

- `POST /api/plan-check` (Phase 3), covering:
  - required front, rear and side open space from Rule 56(1)(a), 56(1)(b), 56(2)(a) and 56(3)
  - buildable envelope, footprint, per-side shortfall and overlap rectangles
  - derived ground coverage (FR-51)
  - the area-mismatch gate with the `use_dimensions` resolution
  - footprint validation
  - refusals for corner plots, non-residential use and heights above 12.5 m
  - the Rule 53(1)(i) development-type warning
  - the exceptions register
  - Hindi labels and messages, with rule references kept in English
  - the optional Hindi trace rendering, labelled "rendering, not official text"
  - audit log entries with geometry inputs and per-side results
- Range tables held as data in `config/range_tables.json`; no table value is in Python source.
- `GET /api/health`, `GET /api/rules/{rule}`, `GET /pdf/en`, `GET /pdf/hi`. The rules and PDF endpoints need the track-pack files in `data/` and `resources/`.

## What does not work yet

Not built yet:
- `POST /api/lookup` and `POST /api/parse` (Phase 2) return 501.
- The Phase 1 frontend and drawing.
- The 17 sample-question runs.

Track-pack data still to be copied in: the corpus `data/bhumi_vikas_rules.jsonl`, the English and Hindi PDFs, and `sample_questions.md`. Until then, plan-check responses carry no citations.

Verification still open:
- Range-table rows are transcribed from the corpus text and still need a row-by-row check against the English PDF (`verified_on` is empty).
- The page for the Rule 2(20) definition and the amendment source URL are unfilled.

Known gaps from the specification (Appendix B):

| Gap | In plain words |
|---|---|
| G-01 | A 28 August 2026 amendment to Rule 2(5)(c) for plots up to 500 sq m is not in the rules text. The tool flags it and does not apply it. |
| G-02 | The Hindi PDF is not machine-readable, so Hindi rule text is shown only by page link. Any Hindi explanation is labelled as a rendering. |
| G-03 | The Rules set height, not number of floors. A floor count is shown only as a derived figure. |
| G-04 | Tables in the source text are flattened. Every table row is hand-checked and every figure links to its PDF page. |
| G-05 | Inserted rules such as 12-A, 26-A and 42-A have no record of their own and are resolved through their parent rule. |
| G-06 | Some sample questions are procedural, with no figure to compute. Only the rule citation is checked for those. |
| G-07 | The Development Plan can override the Rules (Rule 103). Figures here are from the Rules only. |
| G-08 | For corner plots the Rules do not say which street sets the front open space. The plan check refuses and shows both readings. |
| G-09 | Irregular plots and non-rectangular footprints are not modelled. |
| G-10 | Floor-area exclusions in Rule 2 (stairs, parking, services) are not modelled. Floors-by-area is an estimate. |
| G-11 | A drawing looks authoritative, so a table transcription error matters more. Every line carries its rule row and page. |
| G-12 | The Rules do not define an "existing developed area" under Rule 56(1)(b). The clerk must say whether the plot is in one. |
| G-13 | The 2026 amendment is known only from a secondary notice. The flag says so. |

## Accuracy

Sample questions (FR-34): not yet run. The per-question pass/fail table will go here once Phase 2 adds the 17 questions.

Geometry cases (FR-50), from `python eval/run_eval.py`: **17 of 17 pass; zero false "no conflict" results.**

| Case | Description | Result |
|---|---|---|
| G01 | No conflict, A.5 plot with footprint on the setback lines | Pass |
| G02 | A.5 example: front shortfall 0.60, envelope 108.75, footprint 113.25, coverage 54.4 % | Pass |
| G03 | Rear shortfall only | Pass |
| G04 | Left shortfall only | Pass |
| G05 | Right shortfall on a detached plot | Pass |
| G06a, G06b | Road 9.0 m gives 3.0; 9.1 m gives 3.6 | Pass |
| G07a, G07b | Semi-detached height 10.0 m gives 2.5; 10.1 m gives 3.0 | Pass |
| G08 | Road 5.0 m, existing developed area: 3.5 m from 56(1)(b) | Pass |
| G09a, G09b | Area mismatch blocked; resolved with frontage x depth | Pass |
| G10 | Development type outside Rule 53(1)(i) range warns | Pass |
| G11 | Corner plot refused with both readings | Pass |
| G12 | Impossible footprint rejected (HTTP 422) | Pass |
| G13, G14 | Non-residential and height above 12.5 m refused | Pass |

## Extra data used

- 28 August 2026 amendment to Rule 2(5)(c): TeamLease RegTech notice, read 10 October 2026 (SRS reference R7). Secondary source; the link is to be added in `config/amendments.json`.
- Consolidated rules: https://mptownplan.gov.in/NewsPDF/bvn06032025E.pdf (public, read only; the tool makes no connection to it).

## Dependencies and licences

| Package | Licence |
|---|---|
| FastAPI | MIT |
| Starlette | BSD-3-Clause |
| Uvicorn | BSD-3-Clause |
| Pydantic | MIT |
| pytest | MIT |
| HTTPX | BSD-3-Clause |

## Licence

MIT, see `LICENSE`.
