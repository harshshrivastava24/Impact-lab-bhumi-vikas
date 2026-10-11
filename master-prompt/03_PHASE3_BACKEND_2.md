# Phase 3: Backend 2, Plan Check Geometry, Exceptions, Hindi, Release

Read `00_SHARED_CONTEXT.md` first. Phase 2 must be complete and its checklist green. This phase adds the plan check engine behind `/api/plan-check`, completes ground coverage, finishes Hindi output, extends the audit log and harness, and prepares the repository for submission.

## SRS requirements owned by this phase

FR-39, FR-40, FR-42 (server validation), FR-43, FR-44, FR-45, FR-46, FR-47, FR-48, FR-49 (server side), FR-50, FR-51 (derived branch), FR-30 (Hindi rendering), FR-38 extension. NFR-10, NFR-22 to NFR-25. Sections 5.2 (`config/exceptions.json`) and 6.

## Deliverables

1. `backend/app/services/geometry.py`: pure functions, no I/O, fully unit-tested.
2. `/api/plan-check` implemented per the contract, including `blocked` and `refused` statuses.
3. `config/exceptions.json`.
4. `eval/expectations.json` extended with at least twelve geometry cases; `run_eval.py` runs them.
5. Hindi explanatory rendering path with the "rendering, not official text" label.
6. Final `README.md`, run steps in five or fewer, what works and what does not, accuracy table, extra data list, team and user.

## Step 1: Input validation and the mismatch gate (FR-39, FR-42, FR-48)

Order of checks, each returning early with the specified status:

1. Mandatory fields for plan check: frontage, depth, development_type, height, footprint with four numbers. Missing: HTTP 422 naming the field.
2. Refusals (FR-48), status `refused` with `message`:
   - `streets_abutting == 2`: message must contain both readings: Rule 56(1)(a) "the street facing the plot" and Rule 65(2) wider street governs height; the Rules do not state which street sets the front open space; the clerk decides. Two paragraphs separated by a blank line.
   - use_type not residential: "Plan check version 1 supports residential buildings only; see Rule 57 for other occupancies."
   - height above 12.5: "Plan check version 1 supports buildings up to 12.5 m; Rule 42 Tables 4 and 5 govern above that."
3. Area mismatch (FR-39): if `abs(frontage * depth - plot_area) / plot_area > 0.02`, return status `blocked`, message "Entered dimensions give N sq m; stated plot area is M sq m", `resolutions: ["correct_inputs", "use_dimensions"]`. If the request carries `resolution: "use_dimensions"`, set plot_area = frontage * depth for every downstream calculation and say so in every trace that uses area.
4. Footprint validity (FR-42): width = frontage minus left minus right; depth = depth minus front minus rear. Reject if either is 0 or negative or if any distance is negative: HTTP 422 with the reason.
5. Development type validation (FR-16 server side, re-used): check plot_type_53_1i on area and frontage; on failure, proceed but add a warning figure citing the row.

## Step 2: Envelope and footprint (FR-40, FR-41 data, FR-51 derived)

Coordinates: origin at the plot's front-left corner, x to the right, y into the plot.

- Required sides from Phase 2 compute functions: front via FR-14 (including the 56(1)(b) branch), rear via FR-15, left and right via FR-16. For semi-detached, the reduced or 3.0 m side is `left` by convention and `right` is 0; for detached both sides are set; for row both are 0. State the convention in the trace.
- Envelope: `x = left_req`, `y = front_req`, `width = frontage - left_req - right_req`, `depth = depth - front_req - rear_req`, `area = width * depth`. Round to 0.01 at the end, not between steps.
- Footprint: `x = left`, `y = front`, `width`, `depth` from Step 1, `area = width * depth`.
- Ground coverage derived (FR-51): `envelope.area / plot_area * 100`, one decimal, labelled "derived from setbacks, not a prescribed percentage", citing Rule 2(20).
- Appendix A.5 must give envelope 7.5 x 14.5 = 108.75 and footprint 7.5 x 15.1 = 113.25 and 54.4 %.

## Step 3: Overlap computation (FR-43, NFR-23, NFR-24)

For each side: `shortfall = max(0, required - provided)`, rounded to 0.01. Build the overlap rectangle for each side with shortfall above 0:

- front: `x = footprint.x, y = footprint.y, width = footprint.width, depth = shortfall`
- rear: `x = footprint.x, y = depth - rear_req, width = footprint.width, depth = shortfall`
- left: `x = footprint.x, y = footprint.y, width = shortfall, depth = footprint.depth`
- right: `x = frontage - right_req, y = footprint.y, width = shortfall, depth = footprint.depth`

Per-side table entries carry `required`, `provided`, `shortfall`, `rule`, `page`, `trace` in the FR-47 format, for example `road width 9.0 m, Rule 56(1)(a) row 1, up to 9.0 m gives 3.0 m, p. 77`.

Result string (FR-46): exactly `Setback conflict found` if any shortfall is above 0, otherwise `No setback conflict found against the checks listed`. `checks_performed`: the four side names with their rules. `not_checked`: exactly "Parking, staircase, ventilation shaft, courtyard, fire and structural rules were not checked". A unit test asserts that no response string contains approved, compliant or sanctionable.

## Step 4: Height coupling and exceptions (FR-44, FR-45)

- The frontend re-sends on height change; the backend is stateless. Include in every response `required.left.trace` with the proviso applied, so the frontend can diff old and new. Unit test: semi-detached, frontage 10, height 10.0 gives left 2.5; height 10.1 gives 3.0. Detached, frontage 11, height 7.0 gives 1.5 on one side; 7.1 gives 3.0.
- `config/exceptions.json`: entries `{ "id": "garage_side_rear", "label": "Garage at the rear end of the side open space", "rule": "56(4)", "page": 78 }` and `{ "id": "projections", "label": "Projections governed by Rule 58", "rule": "58", "page": 81 }`. Return them as `exceptions_available`. Selection is a frontend annotation only; the backend never removes an overlap. Narrow streets are computed under FR-14, not listed here.

## Step 5: Hindi rendering and citations (FR-28, FR-30)

- Figure labels, result strings, messages and the not-checked sentence come from `config/strings.hi.json` when `language` is `hi`. Numbers stay in Western digits.
- Citation `text_en` is always the English verbatim text. Add `pdf_hi_url` with the same page number.
- Optional Hindi explanatory rendering of the trace via the inference service, only when configured, returned in a separate field `trace_hi` with `"rendering": true`. The frontend labels it "rendering, not official text". Never translate rule text.

## Step 6: Audit log, print data and harness (FR-38, FR-49, FR-50)

- Log entry for plan check adds `geometry_inputs` (frontage, depth, footprint, development_type, height) and `sides[]`. No free text.
- The print view needs no new endpoint; confirm the response carries everything FR-49 lists.
- Extend `eval/expectations.json` with at least twelve geometry cases, each with inputs, expected sides, expected result string and verification page:
  1. No conflict: A.5 plot with footprint front 3.0, rear 2.5, left 2.5, right 0.
  2. Front shortfall only (the A.5 example, 0.60).
  3. Rear shortfall only.
  4. Left shortfall only.
  5. Right shortfall on a detached plot (both sides required).
  6. Road width exactly 9.0 gives front 3.0; 9.1 gives 3.6.
  7. Semi-detached height exactly 10.0 gives side 2.5; 10.1 gives 3.0.
  8. Road 5.0, existing developed area true, front 3.5 from 56(1)(b).
  9. Area mismatch: frontage 10, depth 20, plot area 230, status blocked.
  10. Development type out of range: plot 200, frontage 14, semi-detached, warning present.
  11. Corner plot: streets_abutting 2, status refused, both readings in message.
  12. Impossible footprint: front 10, rear 10 on depth 20, HTTP 422.
- `run_eval.py` prints the 17 question lines, then the geometry lines, then totals for each group.

## Step 7: Release (C-05, C-06, C-07, NFR-13, NFR-14, NFR-20)

- README sections in this order: team name and members, track, the one user, what it does in three sentences, run it in five steps, what works, what does not (copy Appendix B gaps G-01 to G-13 in plain words), accuracy on the sample questions as a table with per-question pass/fail, geometry cases pass/fail, extra data used with links (the TeamLease notice for the amendment), licence.
- Confirm the five run steps on a clean machine or fresh clone. If a sixth step is needed, remove it.
- Secrets check: `git grep -iE "sk-|api[_-]?key|secret" -- ':!*.md' ':!.env.example'` returns nothing. `.env` is gitignored.
- Dependency licences: list them in the README; all must be permissive.
- Merge to `main` or make the submission branch the default so the jury lands on the README.

## Acceptance checklist

- [ ] Appendix A.5 request returns envelope 108.75, footprint 113.25, front shortfall 0.60 with rule 56(1)(a) page 77, result "Setback conflict found", ground coverage derived 54.4.
- [ ] All four single-side shortfall cases produce the correct overlap rectangle.
- [ ] Threshold cases 9.0 vs 9.1 and 10.0 vs 10.1 produce the expected flips.
- [ ] Road 5.0 existing developed area returns 3.5 citing 56(1)(b) and Rule 46.
- [ ] Area mismatch returns blocked; `use_dimensions` resolution proceeds with area 200 in every trace.
- [ ] Corner plot returns refused with both readings; non-residential and height above 12.5 return refused with the specified messages.
- [ ] Impossible footprint returns 422.
- [ ] No response string contains approved, compliant or sanctionable.
- [ ] Hindi request returns Hindi labels and unchanged English rule text.
- [ ] Log entries for plan check contain geometry inputs and sides and no free text.
- [ ] `python eval/run_eval.py` prints 17 question lines and at least 12 geometry lines; zero false "no conflict" results.
- [ ] README complete; run steps verified on a fresh clone; no secrets; LICENSE present; default branch shows the README.
