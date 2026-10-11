# SRS Change Prompt: Add Plot Envelope Drawing and Setback Plan Check

You are the senior software architect who authored `SRS_Bhumi_Vikas_Sahayak.md` (SRS-BVS-001, version 1.0). Revise that document to version 1.1 by adding one feature. Preserve the existing structure, numbering and style. Do not rewrite requirements that are unaffected. Keep every rule of the original brief: formal, implementation-neutral language; "shall" for mandatory requirements; atomic, testable, uniquely numbered requirements; never describe the system as a chatbot, assistant or conversational agent; the clerk decides, the tool points to the rule.

## FEATURE TO ADD

**Plot Envelope Drawing and Setback Plan Check.** The Tool shall render a to-scale drawing of the plot with the legally required front, rear and side open spaces marked, so the buildable envelope is visible at a glance. The clerk may then enter a proposed building footprint. Any part of the footprint that crosses a required open-space line shall be highlighted with the exact shortfall in metres and the rule number and PDF page that sets the line. All geometry and arithmetic shall be performed in code from the verified range tables, never by an inference service.

## USER AND SCOPE POSITIONING

- The user is still the single building-permission clerk at the BMC counter. The clerk runs the check; the citizen views the screen and may receive the printout. Do not describe this as a citizen-facing feature or a portal.
- The purpose is to let a plan be corrected before fees are paid and plans are formally submitted. State this benefit in the Introduction and in Appendix A.
- The result is a setback conformity check only. It shall never be labelled "approved", "compliant" or "sanctionable". Specify the exact wording: "No setback conflict found against the checks listed" or "Setback conflict found".

## VERSION 1.1 SCOPE (SUPPORTED CASES)

- Rectangular plot with one road frontage.
- Residential use, building height up to 12.5 m (Rule 56 norms).
- Development types detached, semi-detached and row, derived from Rule 53(1)(i) and Rule 56(3).
- Proposed footprint entered as one rectangle defined by four distances from the plot boundaries (front, rear, left, right), or as footprint width and depth plus front and left offsets.
- Inputs: plot width (frontage) and plot depth in metres, in addition to the existing FR-01 parameters.

## EXPLICITLY UNSUPPORTED IN 1.1 (MUST BE REFUSED WITH A CLEAR MESSAGE)

- Corner plots or plots abutting two or more streets. Record the reason: Rule 56(1)(a) refers to "the street facing the plot" while Rule 65(2) lets the wider street govern height; the Rules do not state clearly which street sets the front open space, so the Tool shall present both readings and defer to the clerk rather than draw.
- Irregular (non-rectangular) plots.
- Non-residential uses and buildings above 12.5 m (Rule 42 Tables 4 and 5 and Rule 57).
- Upload or parsing of drawings, CAD files, PDFs or images of plans. Geometry is entered as numbers only.

## REQUIRED REQUIREMENT CONTENT

Add new functional requirements in a new subsection "3.10 Plot Envelope Drawing and Plan Check", numbered FR-39 onward, each with description, inputs, processing, outputs and acceptance criteria. Cover at least:

1. Plot geometry input and validation, including a consistency check that width x depth equals the stated plot area within 2 %, with a warning when it does not.
2. Envelope computation: required open space per side from the existing range tables (Rule 56(1)(a) by road width, 56(2)(a) by plot area, 56(3) by development type, height and frontage), each value carrying rule, sub-rule and PDF page.
3. To-scale drawing: plot boundary, road edge, each setback line labelled with its distance and rule, the resulting buildable envelope with its dimensions and area. Scale bar and north-free orientation (road at bottom). Legible at 1366 x 768.
4. Footprint input and overlap computation: per side, required gap, provided gap, shortfall (required minus provided, zero if none), and the overlap region drawn in a distinct pattern with a numeric label. Rectangle arithmetic only.
5. Coupled-constraint redraw: when proposed height changes across the Rule 56(3) thresholds (7 m for detached, 10 m for semi-detached), the side open space and drawing shall update and the change shall be announced in text.
6. Exceptions register shown beside the result and selectable by the clerk, so legal designs are not flagged as violations: garage at the rear end of the side open space (Rule 56(4)); projections governed by Rule 58; narrow existing streets under Rule 56(1)(b) and Rule 46. Selecting an exception shall not remove the overlap from the drawing; it shall annotate it as "clerk-marked exception, see Rule N".
7. Result wording and limitation statement: list of checks performed; statement that parking, staircase, ventilation shaft, courtyard, fire and structural rules were not checked; the standard disclaimer.
8. Trace display: for each setback line, the table row used, exactly as in FR-22.
9. Unsupported-case refusal per the list above, with the reason text.
10. Print view of the drawing and per-side table, extending FR-33.
11. Audit logging of geometry inputs and per-side results, extending FR-38, with no personal data.
12. Harness extension: at least six geometry test cases in `eval/expectations.json`, including one with no conflict, one with a single-side shortfall, one triggering the height-coupled side-space change, one with the area consistency warning, one corner plot refusal, and the worked example from Appendix A.

Add or amend non-functional requirements as needed, numbered NFR-22 onward, covering at least: drawing render time (target 1 s or less after inputs), geometry precision (0.01 m, displayed to two decimals), zero false "no conflict" results on the harness geometry cases, and a requirement that every numeric label in the drawing is traceable to a range-table row or an arithmetic step.

## UPDATES TO EXISTING SECTIONS

- 1.2 Scope: one sentence adding the plan check, positioned as a pre-submission conformity check run by the clerk.
- 1.3 Definitions: add "buildable envelope", "footprint", "shortfall", "setback line".
- 2.1 Product Perspective: add the drawing and plan-check box to the flow diagram after deterministic computation.
- 2.2 Product Functions: add one clause.
- 2.5 Constraints: add C-10, geometry entered as numbers only, no drawing file ingestion.
- 2.6 Assumptions: add that the footprint is a single rectangle and that open spaces are measured perpendicular to the boundary.
- FR-01: add plot width and depth as optional parameters that become mandatory when the plan check is requested.
- FR-05: add topic "plan check".
- FR-32 Counter display: add the drawing to the display order.
- 5.1 User Interface: describe the drawing panel, colour-independent marking of overlaps (hatching plus text), and keyboard entry of all geometry.
- 5.2 Data File Interfaces: add `config/exceptions.json` for the exceptions register.
- 6 Traceability Matrix: add rows for the new FRs. Map the plan check primarily to J3 (table figures correct) and J1 (rule shown on every answer), and the refusal and limitation statement to J2.
- Appendix A: extend the worked example with plot width 10 m, depth 20 m, semi-detached, height 10 m, frontage 10 m, so the side open space is 2.5 m on one side under the Rule 56(3)(ii) proviso and row type is nil. Show the envelope arithmetic as a table: buildable width 7.5 m, buildable depth 14.5 m (20 minus 3.0 front minus 2.5 rear), envelope area 108.75 sq m. Then show a proposed footprint with front gap 2.4 m and state the result: front shortfall 0.6 m, Rule 56(1)(a) row 1, page 77. Note that FAR 1.25 gives 250 sq m total floor area, which with a 108.75 sq m footprint yields a derived figure of 2.3 floors by area, labelled derived and subject to Rule 2 exclusions from floor area.
- Appendix B Known Gaps: add corner-plot ambiguity, irregular plots, exclusions from FAR area not modelled, and the risk that a drawing is more persuasive than a number so transcription errors in range tables carry higher consequence.

## CHANGE LOG

Add a short "Revision History" table after the document header with version 1.0 (11 October 2026, baseline) and version 1.1 (same date, plan check added), listing the affected sections.

## STYLE AND LENGTH

Keep the whole document under 5,000 words after the change. If needed, tighten existing prose rather than cutting requirements. Output the complete revised document, not a diff.
