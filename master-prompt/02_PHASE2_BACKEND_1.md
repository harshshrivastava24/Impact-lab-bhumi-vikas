# Phase 2: Backend 1, Corpus, Retrieval, Computation, Evaluation

Read `00_SHARED_CONTEXT.md` first. Build the deterministic core: load the corpus, hold verified range tables as data, retrieve rules, compute every figure in code, stamp provenance, flag amendments, say "not found" honestly, and prove it with the 17 sample questions. No drawing or geometry in this phase. Serve the Phase 1 frontend from `frontend/dist`.

## SRS requirements owned by this phase

FR-02 (server side, rule-based parsing first; inference optional), FR-03, FR-04, FR-06 to FR-27, FR-34, FR-35, FR-36, FR-37, FR-38, FR-51 (prescribed-percentage branch only). NFR-01, NFR-03 to NFR-07, NFR-12 to NFR-21. Sections 5.2 and 5.3.

## Deliverables

1. `backend/app/` FastAPI application implementing `/api/parse`, `/api/lookup`, `/api/rules/{rule}`, `/api/health`, `/pdf/en`, `/pdf/hi`, and static serving of `frontend/dist` at `/`. `/api/plan-check` returns 501 with a clear message until Phase 3.
2. `config/range_tables.json`, `config/topic_map.json`, `config/amendments.json`, `config/settings.json` as data files. No table value in Python source.
3. `eval/expectations.json` for the 17 sample questions and `eval/run_eval.py` printing per-question pass/fail and a total.
4. `backend/tests/` pytest suite covering every acceptance criterion listed below.
5. Root `README.md` first version, `LICENSE` (MIT), `.gitignore` including `logs/` and `.env`, `.env.example` with the three inference variables empty.

## Step 1: Corpus loading and integrity (FR-06, FR-37, FR-09, FR-10, FR-11)

- Load `data/bhumi_vikas_rules.jsonl` at startup into records with `rule` (string), `title`, `part`, `page_start`, `page_end`, `text`. Refuse to start on a missing file or unparsable line, naming the line number.
- Report at startup: record count, rule numbers found, any gap in 1 to 105. Expect 106 records including `26-B`.
- Header stripping: regex for lines like `Rule 56   M.P. Bhumi Vikas Rules, 2012   78` and `Rule 29-31 ... 49`. Keep the original text for the verbatim view; use the stripped text for sub-rule extraction and search.
- Inserted rules: a data list mapping `12-A`, `17-a`, `25(A)`, `26-A`, `42-A`, `93(a)` to their parent record. `GET /api/rules/42-A` returns the Rule 42 record's pages with the sub-rule text located by its printed heading. Note that 26-A has no heading in the PDF; return the parent with a note.
- Footnotes: preserve markers like `1[` and `]`. Extract footnote blocks (lines beginning with a lone digit followed by "Subs." or "Ins." or "Published") into `footnotes[]` for the citation.
- Sub-rule extraction: given `56` and `(1)(a)`, return the text from that marker to the next sibling marker. Test on 56(1)(a), 56(2)(a), 56(3), 21(2), 21(3)(b), 61 Table 8, 42 Table 4.

## Step 2: Range tables as data (FR-13, NFR-05)

Create `config/range_tables.json`. Each table has an `id`, `rule`, `sub_rule`, `page`, `unit`, `verified_by`, `verified_on`, and `rows[]` with `lower`, `upper`, `lower_inclusive`, `upper_inclusive`, `value`, `label`. Encode the rule wording exactly: "up to 9.0" is upper 9.0 inclusive; "more than 9.0 and up to 12" is lower 9.0 exclusive, upper 12 inclusive; "above 225" is lower 225 exclusive, upper null.

Tables to encode, using the values in the shared context: front_56_1a, rear_56_2a, side_56_3 (as rules with conditions rather than ranges), plot_type_53_1i, far_61_t8, height_42_t4, high_rise_42_t5, app_fee_21_2, perm_fee_21_3b_item1, perm_fee_surcharges_21_3b, perm_fee_high_rise_21_3c, duration_23.

Verification step, not optional: open the English PDF at each page, compare every row, and set `verified_by` to a team member's role (not name) and `verified_on` to today. A row that cannot be read with confidence from the PDF is marked `"uncertain": true` and the lookup must say so in the trace.

## Step 3: Topic map and retrieval (FR-07, FR-08, FR-12)

`config/topic_map.json`: for each topic and use type, the governing rule, sub-rule, table id, and the condition under which it applies (for example height up to 12.5 for Rule 56, otherwise Rule 42). Also map procedural topics: permission_validity to Rule 23; documents_required to Rules 14 and 16; and a `keywords` list per topic for the parser.

Keyword fallback: when no topic applies, rank records by term overlap with the query over stripped text; return up to five candidates with matched excerpts, labelled `candidate: true`. Sample question 12 must return Rule 103 among candidates. Relevance threshold is in `settings.json`; below it return `not_found`.

## Step 4: Deterministic computation (FR-14 to FR-22, FR-51)

Implement one pure function per figure in `backend/app/services/compute.py`, each returning `Figure` with a `trace` string in the FR-22 format, for example `1.25 x 200 = 250 sq m, Rule 61 Table 8 row 1, p. 83`.

- Front (FR-14): if road width under 6.0 and `existing_developed_area` is true, value = 6.0 minus road_width / 2, rule 56(1)(b), cite Rule 46 too. If under 6.0 and the flag is absent, return a `conditional` figure with both cases. Otherwise table front_56_1a for height up to 12.5; Rule 42 tables above.
- Rear (FR-15): table rear_56_2a by plot area.
- Side (FR-16): by development type with the Rule 56(3) provisos. Validate the type against plot_type_53_1i on both area and frontage; if out of range, still compute but add a `warning` field citing the 53(1)(i) row. Without a type, return `conditional` with one case per permissible type derived from area and frontage.
- Height (FR-17): Rule 42 Table 4 or 5 by road width and plot size; below 12 m road return 12.5 with the exact FR-17 wording.
- Storey count (FR-18): only when floor_to_floor is given; `derived: true`.
- FAR and floor area (FR-19): far_61_t8; residential 1.25.
- Fees (FR-20): application fee 1.00 per sq m built-up; permission fee by slab; surcharges by use type in code; high-rise branch when height exceeds the Rule 2(38) threshold held in settings.
- Ground coverage (FR-51, prescribed branch only): return the Table 5 or Rules 53, 95, 96 percentage where applicable; otherwise return a figure with `value: null` and the message that the derived figure requires the plan check (Phase 3).
- Computation isolation (FR-21): a test runs the full evaluation with inference disabled and asserts identical numeric output.

## Step 5: Provenance, amendments, not-found, fabrication guard (FR-23 to FR-27)

- Version stamp from `settings.json`: `"consolidated_to": "2025-03-06"`.
- `config/amendments.json` with the 28 August 2026 entry: rule `2(5)(c)`, condition `plot_area <= 500`, `concerns`: "whether separate development permission is needed for plots up to 500 sq m, subject to Development Plan conformity; does not change setback, height, FAR or fee figures", `source_kind: secondary`, source URL from the SRS R7, `applied: false`.
- Flag wording per FR-25: label "potentially relevant amendment".
- Not-found (FR-26): exact string "Not found in MP Bhumi Vikas Rules 2012", zero figures, zero citations.
- Fabrication guard (FR-27): before any response leaves the API, validate every `rule` field against the loaded record numbers plus the inserted-rule list. Strip and log anything else. Unit test with an injected "110".

## Step 6: Parsing and language (FR-02, FR-03)

- Language detection: Devanagari character ratio above a threshold means `hi`.
- Rule-based parser first: regexes for numbers with units in English and Hindi (sq m, वर्ग मीटर, m, मीटर, road, सड़क, plot, प्लॉट), keyword lists per topic from the topic map. Must handle sample questions 1, 8, 10, 14, 15 without inference.
- Optional inference (5.3): if `BVS_INFERENCE_URL` is set, send the text with a strict instruction to return only the Params and Topics JSON; validate the JSON shape; reject any rule numbers or figures; time out at 5 s and fall back to rule-based parsing. Set `used_inference` truthfully.
- `/api/parse` never returns rule numbers, pages or figures.

## Step 7: Audit log and admin (FR-36, FR-38, NFR-17)

- Append one JSON line per `/api/lookup` to `logs/queries.jsonl`: timestamp, params, topics, rules cited, figures returned, version, amendment flags, used_inference. Never the free text.
- Corpus replacement: all file paths from `settings.json`; replacing files and restarting is the only step. Test by adding a 107th record.

## Step 8: Evaluation harness (FR-34, FR-35, NFR-03)

`eval/expectations.json`: one entry per sample question with `question`, `language`, `params` or `text`, `expected_rules[]`, `expected_figures{}` (optional), `expect_not_found` (questions 16, 17), `verification_page`, and a `note` for partial cases (question 4: Rule 28 answers the consequence; the deadline is in the parent Act, not the Rules; pass on Rule 28 citation). `run_eval.py` prints 17 lines and a total and exits non-zero on any failure. Record the result in the README.

## Acceptance checklist

- [ ] Startup reports 106 records, no gaps; a corrupted line fails startup naming the line.
- [ ] `/api/lookup` for the Appendix A params returns front 3.0, rear 2.50, height 12.5, FAR 1.25, floor area 250, fees 250 and 3,000, each with trace, rule and page.
- [ ] Road 9.0 gives 3.0; road 9.1 gives 3.6. Plot 150 gives 1.50; plot 200 gives 2.50.
- [ ] Road 5, existing developed area true, gives 3.5 citing 56(1)(b) and Rule 46.
- [ ] Plot 200, frontage 14, semi-detached returns the Rule 53(1)(i) warning.
- [ ] Plot 200 triggers the amendment flag with process-only wording and `source_kind: secondary`; plot 600 does not.
- [ ] Questions 16 and 17 return not-found with zero citations; question 12 returns Rule 103 among candidates.
- [ ] Injected "Rule 110" is stripped and logged.
- [ ] `GET /api/rules/42-A` returns Rule 42 pages and the 42-A text.
- [ ] Every range-table row has `verified_on` set and a page number.
- [ ] `python eval/run_eval.py` prints 17 lines; at least 15 pass including both not-found cases; the number is in the README.
- [ ] Running the evaluation with inference disabled produces identical figures.
- [ ] `grep -ri "chatbot\|assistant" backend/ README.md` returns nothing; no secrets in the repo.
