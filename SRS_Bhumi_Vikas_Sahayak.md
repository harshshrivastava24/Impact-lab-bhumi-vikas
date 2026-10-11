# Software Requirements Specification

## Bhumi Vikas Sahayak: Building Rule Lookup and Compliance Decision-Support Tool for the Bhopal Municipal Corporation

| Field | Value |
|---|---|
| Document | SRS-BVS-001 |
| Version | 1.1 |
| Date | 11 October 2026 |
| Standard | IEEE Std 830-1998 structure |
| Licence of the described software | MIT |

### Revision History

| Version | Date | Change | Sections affected |
|---|---|---|---|
| 1.0 | 11 October 2026 | Baseline. | All |
| 1.1 | 11 October 2026 | Added Plot Envelope Drawing and Setback Plan Check. | 1.2, 1.3, 2.1, 2.2, 2.5, 2.6, FR-01, FR-05, FR-32, new 3.10 (FR-39 to FR-50), NFR-22 to NFR-25, 5.1, 5.2, 6, A.5, B |

---

## 1. Introduction

### 1.1 Purpose

This document specifies the requirements of Bhumi Vikas Sahayak (hereinafter "the Tool"), a rule lookup and compliance decision-support tool for the building-permission counter of the Bhopal Municipal Corporation (BMC). Its readers are the build team, the Claude Impact Lab jury, and officers of the Government of Madhya Pradesh evaluating the Tool through the Madhya Pradesh State Electronics Development Corporation (MPSeDC).

### 1.2 Scope

The Tool locates the governing provisions of the Madhya Pradesh Bhumi Vikas Rules, 2012 (hereinafter "the Rules") for a set of plot parameters, performs deterministic arithmetic on figures from the rule tables, and presents the result with rule number, verbatim text, PDF page and rule version. It also draws the plot to scale with the required open spaces marked and checks a proposed footprint against them, so that a plan can be corrected at the counter before fees are paid and plans are formally submitted. It supports one workflow for one role: a building-permission clerk at the counter. It is not a citizen portal, does not grant or refuse permission, does not connect to any government system, and does not give legal advice. The clerk decides; the Tool supplies the reference and the figures.

### 1.3 Definitions and Acronyms

| Term | Definition |
|---|---|
| BMC | Bhopal Municipal Corporation, the Authority under Rule 2(5)(b) for building permission within its limits. |
| MPSeDC | Madhya Pradesh State Electronics Development Corporation, the state agency through which the Tool is offered to Government. |
| The Rules | Madhya Pradesh Bhumi Vikas Rules, 2012, English consolidated edition current to 6 March 2025. |
| Corpus | The machine-readable copy of the Rules supplied in the data files (Section 1.4). |
| Setback / open space | Minimum distance between a building and the plot boundary on the front, rear or sides (Rule 56; "M.O.S." in Rule 42). |
| FAR | Floor Area Ratio: total floor area of all floors divided by plot area (Rule 61, Table 8). |
| Ground coverage | Area of land covered by the plinth at ground floor level, as a percentage of plot area (Rule 2(20)). |
| Built-up area | Floor area used as the fee base in Rule 21. |
| High-rise building | A building above the height threshold in Rule 2(38), governed by Rule 42 Table 5. |
| Rule version | The consolidation date of the corpus from which a result was derived. |
| Setback line | The line inside the plot boundary at the required open-space distance, measured perpendicular to that boundary. |
| Buildable envelope | The rectangle bounded by the four setback lines; the area within which a footprint may sit. |
| Footprint | The ground-floor outline of the proposed building, entered as one rectangle. |
| Shortfall | Required open space minus provided open space on a side, in metres; zero when the footprint does not cross the setback line. |
| Inference service | An optional external text-processing API used only for parsing free text and for Hindi rendering of explanatory text. |

### 1.4 References

| Ref | Document |
|---|---|
| R1 | MP Bhumi Vikas Rules 2012, English, consolidated to 6 March 2025. `resources/MP_Bhumi_Vikas_Rules_2012_upto_2025-03-06_EN.pdf`. Source: https://mptownplan.gov.in/NewsPDF/bvn06032025E.pdf. Source of truth. |
| R2 | MP Bhumi Vikas Rules 2012, Hindi, consolidated to 6 March 2025. `resources/MP_Bhumi_Vikas_Rules_2012_upto_2025-03-06_HI.pdf`. Display only. |
| R3 | `data/bhumi_vikas_rules.jsonl`, 106 rule records (rules 1 to 105 and 26-B). |
| R4 | `data/bhumi_vikas_rules_fulltext_by_page.txt`, 108 pages, each starting `===== PDF page N =====`. |
| R6 | `resources/sample_questions.md`, 17 test questions. |
| R7 | Amendment of 28 August 2026 to Rule 2(5)(c), plots up to 500 sq m (TeamLease RegTech notice, read 10 October 2026). Not in corpus. |
| R8 | Track 1 Participant Guide, Claude Impact Lab, Bhopal, 11 October 2026. |

### 1.5 Overview

Section 2 gives context, user and constraints; Sections 3 and 4 list functional (FR) and non-functional (NFR) requirements; Section 5 defines interfaces; Section 6 traces requirements to jury criteria; appendices give a worked example and known gaps.

---

## 2. Overall Description

### 2.1 Product Perspective

The Tool is a self-contained application that reads a static rule corpus from local files and serves a single-screen interface at the counter. It has no integration with any government system. An optional inference service may be configured for free-text parsing and Hindi rendering; correctness of retrieval, computation and citation shall never depend on it.

```
Clerk --> Query intake (form | parsed text) --> Parameter validation
                                                      |
                                                      v
            Rule corpus (JSONL, page text) --> Rule retrieval --> Table extraction
                                                      |
                                                      v
                                      Deterministic computation (code only)
                                                      |
                                                      v
            Plot geometry --> Envelope drawing and footprint check (code only)
                                                      |
                                                      v
            Amendment register --> Provenance and flagging --> Result display + PDF page link
                                                      |
                                                      v
                                                 Audit log
```

### 2.2 Product Functions

The Tool accepts plot parameters by form or parsed English/Hindi text; retrieves the governing rule with number, title, part, page range and verbatim text; computes setbacks, FAR-derived area, height limit and fees in code from table values; stamps each result with the rule version and flags later amendments; states clearly when the Rules are silent; responds in the query language with rule text always in verbatim English; opens the official PDF at the cited page; draws the plot to scale with setback lines and marks any footprint overlap with its shortfall and rule; runs the 17 sample questions with pass/fail reporting; and lets an administrator load an updated corpus without code change.

### 2.3 User Characteristics

The sole user role is the building-permission clerk at the BMC counter. The clerk answers repetitive questions under a one-minute target, reads English and Hindi with mixed fluency, receives no training before first use, must show the citizen the rule number and text, and retains decision authority. An administrator role exists only for corpus updates, performed by department IT staff following written steps.

### 2.4 Operating Environment

A standard department desktop (Windows 10 or later, or Ubuntu 20.04 or later) or a low-cost server with 4 GB RAM, a current browser, and local access to the data and resources folders. Internet access is required only if an inference service is configured.

### 2.5 Design and Implementation Constraints

| ID | Constraint |
|---|---|
| C-01 | Public data only: R1 to R6 plus any public data named and linked in the README. |
| C-02 | No login to, scraping of, or writes to any live government system. |
| C-03 | No personal data collected, stored or logged. |
| C-04 | Every result carries a disclaimer: rule reference, not legal advice; the clerk decides. |
| C-05 | MIT licence; public repository; readable by department staff. |
| C-06 | Runnable in five documented steps or fewer. |
| C-07 | No secrets in source; configuration by environment variables only. |
| C-08 | Single workflow, single user role; not a citizen portal. |
| C-09 | All arithmetic in application code; no number originates from a language model. |
| C-10 | Plot and footprint geometry entered as numbers only; no ingestion of drawings, CAD files, PDFs or images of plans. |

### 2.6 Assumptions and Dependencies

- A-01: R1 is authoritative where R3 or R4 disagree with it.
- A-02: Page numbers in R3 and R4 are the PDF's own count starting at 1.
- A-03: The Rules prescribe height, not storey count; any storey count shown is derived from a clerk-supplied floor-to-floor height.
- A-04: R2 cannot be parsed; Hindi rule text is shown by displaying R2 pages.
- A-05: The 28 August 2026 amendment text is not in the corpus; the Tool flags it but cannot apply it.
- A-06: The proposed footprint is a single rectangle aligned with the plot boundaries.
- A-07: Open spaces are measured perpendicular to the plot boundary; the road lies along the front boundary.

---

## 3. Functional Requirements

Each requirement is mandatory ("shall"), atomic and testable. Acceptance criteria (AC) define the pass condition.

### 3.1 Query Intake

**FR-01 Structured form input**
The Tool shall provide a form accepting the following parameters: plot area (sq m), road width (m), use type (residential, commercial, public/semi-public, industrial, agricultural), proposed built-up area (sq m), proposed building height (m), development type (detached, semi-detached, row), plot frontage (m), plot depth (m), and optional floor-to-floor height (m). Only plot area, road width and use type shall be mandatory; frontage and depth shall become mandatory when the plan check topic is selected.
AC: Submitting plot area 200, road width 9, use type residential yields a result without further input; selecting plan check without depth produces a field-level prompt.

**FR-02 Free-text input parsing**
The Tool shall accept a single short text input in English or Hindi and map it to the FR-01 parameter set by extracting numeric values, units and keywords. Parsed values shall be shown in the form for confirmation before lookup. The parsing path shall produce nothing but populated fields and a detected language.
AC: Sample question 14 (Hindi, 200 sq m, 9 m road) populates plot area 200, road width 9, language Hindi.

**FR-03 Language detection**
The Tool shall detect whether the query is English or Hindi from the input text, with a manual override.
AC: Questions 1 to 13 detect English; 14 and 15 detect Hindi.

**FR-04 Parameter validation**
The Tool shall validate each parameter for type and range (plot area 1 to 100,000 sq m; road width 1 to 100 m; height 0 to 150 m; frontage 1 to 500 m) and shall reject invalid values with a field-level message before retrieval.
AC: Road width "-3" is rejected with a message naming the field.

**FR-05 Topic selection**
The Tool shall allow the clerk to select one or more topics: front setback, rear setback, side setback, height limit, FAR and permitted floor area, ground coverage, application fee, permission fee, permission validity, documents required, plan check. When parsed text names a topic, it shall be pre-selected.
AC: Question 10 pre-selects rear setback.

### 3.2 Rule Retrieval

**FR-06 Corpus loading**
The Tool shall load R3 at startup, parse each line into a rule record with fields `rule`, `title`, `part`, `page_start`, `page_end` and `text`, and shall refuse to start if the file is absent or any line fails to parse.
AC: 106 records load; a corrupted line produces a startup error naming the line number.

**FR-07 Topic-to-rule mapping**
The Tool shall hold a configurable mapping from each FR-05 topic and use type to the governing rule number(s) and table identifier(s), stored in a data file rather than in code.
AC: Front setback, residential, height up to 12.5 m maps to Rule 56(1)(a).

**FR-08 Rule retrieval output**
For each governing rule the Tool shall return rule number, title, part, page range and the verbatim text of the relevant sub-rule or table from R3.
AC: Rule 56 returns title "Residential Buildings", part "Part V: General Building Requirements", pages 77 to 80.

**FR-09 Running header removal**
The Tool shall strip lines matching the running header pattern (rule label, "M.P. Bhumi Vikas Rules, 2012", page number) from displayed text while preserving the original text for the verbatim view.
AC: Displayed Rule 56 text contains no line matching `Rule 56 ... 2012 ... 78`.

**FR-10 Inserted-rule resolution**
The Tool shall recognise inserted rules 12-A, 17-a, 25(A), 26-A, 42-A and 93(a) as sections within the preceding rule's record and shall cite them by their printed number with the parent record's page range.
AC: A query on IT plots returns "Rule 42-A" with pages from the Rule 42 record.

**FR-11 Amendment footnote preservation**
The Tool shall retain footnote markers such as `1[` and `]` in verbatim text and shall display the associated footnote where present in the record.
AC: Rule 61 Note (4) shows the `1[200 sq.m.]` marker and the 6 March 2025 footnote.

**FR-12 Keyword fallback**
When no topic mapping applies, the Tool shall perform a ranked full-text search of R3 and shall present up to five candidate rules with matched excerpts, labelled as candidates and not as a computed answer.
AC: Question 12 returns Rule 103 among candidates.

### 3.3 Table Extraction and Computation

**FR-13 Table value lookup**
Each table used for computation shall be held as a structured range table (lower bound, upper bound, value, rule, page) in a data file. Boundaries shall follow the rule text exactly ("up to", "more than", "above").
AC: Road width 9.0 m resolves to Rule 56(1)(a) row 1 (3.0 m); 9.1 m resolves to row 2 (3.6 m).

**FR-14 Front setback computation**
The Tool shall return the minimum front open space from Rule 56(1)(a) for residential buildings up to 12.5 m, and from Rule 42 Tables 4 or 5 otherwise.
AC: 9 m road, residential, height up to 12.5 m returns 3.0 m.

**FR-15 Rear setback computation**
The Tool shall return the minimum rear open space from Rule 56(2)(a) by plot area.
AC: 150 sq m returns 1.50 m; 200 sq m returns 2.50 m.

**FR-16 Side setback computation**
The Tool shall return side open space from Rule 56(3) by development type, height and frontage, stating which proviso applied. Without a development type, it shall derive permissible types from Rule 53(1)(i) and present each case.
AC: 200 sq m, frontage 9 m, semi-detached, height 10 m returns 2.5 m on one side with the proviso cited.

**FR-17 Height limit**
The Tool shall determine maximum height from Rule 42 Table 4 or 5 by road width. Below the smallest entry (12 m), it shall report that Rule 42 does not apply and Rule 56 norms for buildings up to 12.5 m govern.
AC: 9 m road returns "up to 12.5 m under Rule 56; Rule 42 Table 4 requires a 12 m or wider road".

**FR-18 Derived storey count**
The Tool shall compute storey count as floor(height limit / floor-to-floor height) only when the clerk supplies floor-to-floor height, and shall label the figure "derived, not prescribed by the Rules".
AC: Without floor-to-floor height, no storey count is shown and the label explains why.

**FR-19 FAR and permitted floor area**
The Tool shall return FAR from Rule 61 Table 8 by use type and category and shall compute permitted floor area as FAR multiplied by plot area.
AC: Residential, 200 sq m returns FAR 1.25 and 250 sq m.

**FR-20 Fee computation**
The Tool shall compute the application fee under Rule 21(2) and the permission fee under Rule 21(3)(b) or (c) from built-up area and use type, applying the percentage surcharges in items 2 and 4 in code.
AC: Residential, 250 sq m built-up returns application fee Rs 250 and permission fee Rs 3,000 (slab 201 to 300).

**FR-21 Computation isolation**
No numeric value in a result shall originate from an inference service; every number shall be traceable to a table row in FR-13 or to an arithmetic step shown in the result.
AC: Running the evaluation harness with the inference service disabled yields identical numeric results.

**FR-22 Calculation trace**
Each computed figure shall display its formula, inputs, table row and rule reference.
AC: Permitted floor area shows "1.25 x 200 = 250 sq m, Rule 61 Table 8 row 1, p. 83".

### 3.4 Provenance, Versioning and Amendment Flagging

**FR-23 Version stamp**
Every result shall state "Derived from MP Bhumi Vikas Rules 2012, consolidated to 6 March 2025", sourced from a configuration value, not a literal in code.
AC: Changing the configured date changes the stamp without rebuild.

**FR-24 Amendment register**
The Tool shall hold a data file listing known later amendments with date, rule reference, affected condition (for example plot area up to 500 sq m) and source link.
AC: The register ships with the 28 August 2026 entry for Rule 2(5)(c).

**FR-25 Amendment flag**
When a query matches an amendment's affected condition or cites an affected rule, the result shall display a prominent flag: amendment date, rule, source link and the statement that the flagged amendment is not applied in the shown figures.
AC: Plot area 200 sq m triggers the 28 August 2026 flag; 600 sq m does not.

### 3.5 Not-Found Handling

**FR-26 Explicit not-found**
When no topic mapping applies and keyword fallback yields no candidate above the configured relevance threshold, the Tool shall return "Not found in MP Bhumi Vikas Rules 2012" and shall display no rule number, figure or text.
AC: Questions 16 and 17 return not-found with zero citations.

**FR-27 Fabrication guard**
Every rule number in a result shall be validated against the set of 106 record numbers plus the inserted-rule list in FR-10; any other value shall be suppressed and logged.
AC: An injected reference "Rule 110" is removed and an error is logged.

### 3.6 Bilingual Output

**FR-28 Response language**
Labels, explanations and computed-figure descriptions shall be rendered in the detected or selected language.
AC: Question 14 yields Hindi labels; question 1 yields English.

**FR-29 Verbatim English rule text**
Rule text shall always be shown verbatim in English from R3 regardless of response language.
AC: Hindi result for question 14 includes the English Rule 56(1)(a) text unchanged.

**FR-30 Hindi rendering**
Where a Hindi response is required, the Tool shall offer a link to the corresponding page of R2 for the cited rule and may show a Hindi explanatory rendering, labelled "rendering, not official text".
AC: Question 15 result links R2 at page 35 and labels any Hindi paraphrase.

### 3.7 Citation and Display

**FR-31 PDF page link**
Each citation shall open R1 at `page_start` of the cited rule in the browser's PDF viewer, with a second link for R2.
AC: Clicking Rule 21 opens R1 at page 35.

**FR-32 Counter display**
The result screen shall show, in order: computed figures with units, the envelope drawing when plan check is selected, rule citations with verbatim text, version stamp, amendment flag if any, disclaimer (C-04), and PDF links, on one screen without horizontal scrolling at 1366 x 768.
AC: The worked example in Appendix A fits one screen.

**FR-33 Print view**
The Tool shall provide a printable view containing all FR-32 elements.
AC: Print preview of the worked example is one page.

### 3.8 Evaluation Harness

**FR-34 Sample question run**
The Tool shall include a script that runs all 17 questions in R6 against an expectations file (expected rule numbers, expected figures or expected not-found) and prints pass/fail per question and a total.
AC: Running the script prints 17 lines and a summary.

**FR-35 Expectations as data**
Expected answers shall live in a data file with the PDF page used to verify each expectation.
AC: Each of 17 entries has a page number or "not-found".

### 3.9 Administration

**FR-36 Corpus replacement**
An administrator shall be able to replace R1, R2, R3, R4, the topic mapping, the range tables and the amendment register by replacing files and restarting, with no code change.
AC: A corpus with one extra record loads and is retrievable.

**FR-37 Corpus integrity check**
On startup the Tool shall report record count, rule numbers found, and any gap in sequence 1 to 105.
AC: Removing Rule 50 produces a startup warning naming Rule 50.

**FR-38 Audit log**
The Tool shall append to a local log, per query: timestamp, parameters, topics, rules cited, figures returned, version stamp, amendment flags, and whether the inference service was used. Free text typed by the clerk shall not be logged.
AC: Log entry for the worked example contains no name, phone number or address field.

### 3.10 Plot Envelope Drawing and Plan Check

Version 1.1 supports a rectangular plot with one road frontage, residential use, height up to 12.5 m, and the three Rule 53 development types. Geometry is entered as numbers (C-10).

**FR-39 Plot geometry input and consistency check**
Inputs: plot frontage and depth in metres, each validated in the range 1 to 500 m. Processing: compare frontage x depth with the stated plot area. Output: warning "Entered dimensions give N sq m; stated plot area is M sq m" when the difference exceeds 2 %; the check proceeds on the entered dimensions.
AC: 10 x 20 with area 200 gives no warning; with area 230 it gives the warning.

**FR-40 Envelope computation**
Inputs: FR-39 geometry, road width, plot area, development type, proposed height. Processing: required open space per side from the FR-13 range tables (front Rule 56(1)(a), rear 56(2)(a), sides 56(3) with 53(1)(i) for permissible types). Output: four required distances with rule, sub-rule and page, and envelope width, depth and area.
AC: Appendix A.5 inputs give front 3.0 m, rear 2.5 m, sides 2.5 m and 0 m, envelope 7.5 x 14.5 m, 108.75 sq m.

**FR-41 To-scale drawing**
The Tool shall render a vector drawing with the plot boundary, road edge at the bottom, each setback line labelled with distance and rule, the buildable envelope with its dimensions and area, and a scale bar, legible at 1366 x 768 without zoom.
AC: Four labelled setback lines and one envelope label are visible for the A.5 case.

**FR-42 Footprint input**
The clerk shall enter the footprint as one rectangle, by four distances from the plot boundaries or by width, depth, front offset and left offset. A footprint extending outside the plot shall be rejected.
AC: Front 2.4, rear 3.1, left 1.0, right 1.5 on a 10 x 20 m plot is accepted; left 11 is rejected.

**FR-43 Overlap computation and marking**
Per side, shortfall = max(0, required minus provided), by rectangle arithmetic only. Output: a per-side table of required, provided, shortfall, rule and page, and the overlap drawn hatched with a numeric label.
AC: Provided 2.4 m against required 3.0 m shows a 0.60 m hatched strip labelled "0.60 m short, Rule 56(1)(a), p. 77".

**FR-44 Height-coupled redraw**
When proposed height crosses a Rule 56(3) threshold (7 m detached with frontage under 12 m; 10 m semi-detached with frontage up to 10 m), the side open space and drawing shall update and a notice shall state old value, new value and proviso.
AC: Height 10 m to 10.5 m in the A.5 case changes the side space from 2.5 m to 3.0 m with the notice shown.

**FR-45 Exceptions register**
The Tool shall display beside the result a selectable list drawn from `config/exceptions.json`: garage at the rear end of the side open space (Rule 56(4)); projections governed by Rule 58; existing streets under 6 m where Rule 56(1)(b) and Rule 46 apply. Selecting an exception shall not remove the overlap from the drawing; it shall annotate it "clerk-marked exception, see Rule N".
AC: Selecting the garage exception keeps the hatched region and adds the annotation citing Rule 56(4).

**FR-46 Result wording and limitation statement**
The result shall read exactly "No setback conflict found against the checks listed" or "Setback conflict found", followed by the list of checks performed and the statement "Parking, staircase, ventilation shaft, courtyard, fire and structural rules were not checked", and the C-04 disclaimer. The words "approved", "compliant" and "sanctionable" shall not appear.
AC: Both outcomes show the limitation statement; a text search of the result for the three prohibited words finds none.

**FR-47 Setback trace display**
Each setback line shall show the range-table row used, in the FR-22 format.
AC: Front line shows "road width 9.0 m, Rule 56(1)(a) row 1, up to 9.0 m gives 3.0 m, p. 77".

**FR-48 Unsupported-case refusal**
The Tool shall refuse to draw for plots abutting two or more streets, irregular plots, non-residential uses and heights above 12.5 m, stating the reason. For corner plots the reason shall say that Rule 56(1)(a) refers to "the street facing the plot" while Rule 65(2) lets the wider street govern height, that the Rules do not state which street sets the front open space, and shall present both readings.
AC: Selecting "two streets" produces the corner-plot reason and no drawing.

**FR-49 Plan check print and audit**
The FR-33 print view shall include the drawing and per-side table. The FR-38 log entry shall include geometry inputs and per-side results, with no personal data.
AC: Print preview of A.5 is one page; the log entry holds the four shortfall values.

**FR-50 Geometry test cases**
`eval/expectations.json` shall hold at least six geometry cases: no conflict; single-side shortfall; height-coupled change; area warning; corner-plot refusal; the A.5 example. The FR-34 script shall run and report them.
AC: The script prints six geometry lines in addition to the 17 sample questions.

---

## 4. Non-Functional Requirements

| ID | Category | Requirement | Target / Verification |
|---|---|---|---|
| NFR-01 | Response time | End-to-end result for a form query | 3 s or less at the 95th percentile on the Section 2.4 desktop |
| NFR-02 | Response time | Free-text parse to populated form | 8 s or less with inference service; 3 s or less with local parsing |
| NFR-03 | Accuracy | Pass rate on R6 via FR-34 | At least 15 of 17, including both not-found cases |
| NFR-04 | Accuracy | Fabricated rule numbers or figures | Zero across the harness and 50 random form queries |
| NFR-05 | Accuracy | Table values match R1 | 100 % of range-table rows checked against the PDF page |
| NFR-06 | Reliability | Unhandled errors visible to the clerk | None in a 200-query soak run |
| NFR-07 | Availability | Counter hours 10:30 to 17:30, Monday to Saturday | At least 99 % over one week; no external dependency in local operation |
| NFR-08 | Usability | First use without training | 3 untrained testers complete the worked example in 60 s or less |
| NFR-09 | Usability | Interaction cost | 4 clicks or entries or fewer from blank form to result |
| NFR-10 | Localisation | Hindi labels and messages | 100 % of interface strings in both languages, in a resource file |
| NFR-11 | Maintainability | Corpus or table update | Zero code changes; documented in README |
| NFR-13 | Portability | Install | 5 documented steps or fewer on Windows and Ubuntu; runs without GPU |
| NFR-14 | Security | Secrets | None in repository; pre-push check for key patterns |
| NFR-15 | Security | Personal data | None collected, stored or logged (FR-38) |
| NFR-16 | Security | Outbound traffic | No connection to any government domain; only the configured inference endpoint, if any |
| NFR-17 | Auditability | Log content | One FR-38 entry per query; append-only JSONL |
| NFR-18 | Degraded mode | Inference service unavailable | Form path, retrieval, computation, citation and English output remain fully functional; a banner states that free-text parsing and Hindi rendering are unavailable |
| NFR-19 | Degraded mode | Fail-safe | Inference timeout 5 s or less, after which the form path is offered |
| NFR-20 | Licensing | Licence file and dependencies | MIT LICENSE present; all dependencies permissively licensed |
| NFR-21 | Disclaimer | Legal position | Disclaimer (C-04) on 100 % of results and prints |
| NFR-22 | Response time | Envelope drawing render after inputs complete | 1 s or less |
| NFR-23 | Precision | Geometry arithmetic and display | Computed to 0.01 m; displayed to two decimals |
| NFR-24 | Accuracy | False "no conflict" results on FR-50 geometry cases | Zero |
| NFR-25 | Traceability | Numeric labels in the drawing | 100 % traceable to a range-table row or a displayed arithmetic step |

---

## 5. External Interface Requirements

### 5.1 User Interface

- Single page: form, free-text box, topic selector, and a result panel laid out per FR-32.
- Language toggle (English / Hindi) always visible.
- Keyboard-only operation; Enter submits.
- Minimum font 14 px; computed figures 20 px or larger.
- Colour is never the sole carrier of meaning; the amendment flag uses icon and text; overlaps use hatching plus a numeric label.
- Drawing panel beside the per-side table when plan check is selected; all geometry entered by keyboard in numeric fields.

### 5.2 Data File Interfaces

| File | Direction | Format | Contract |
|---|---|---|---|
| `data/bhumi_vikas_rules.jsonl` | Read | JSONL, UTF-8 | Fields per Section 1.3 "Rule record"; `rule` is a string |
| `data/bhumi_vikas_rules_fulltext_by_page.txt` | Read | UTF-8 text | Page delimiter `===== PDF page N =====` |
| `resources/*.pdf` | Read, served to browser | PDF | Opened at page via `#page=N` fragment |
| `config/topic_map.json` | Read | JSON | Topic and use type to rule reference(s) and table id |
| `config/range_tables.json` | Read | JSON | Table id to rows {lower, upper, inclusive flags, value, unit, rule, page} |
| `config/amendments.json` | Read | JSON | {date, rule, condition, source_url, note} |
| `config/exceptions.json` | Read | JSON | {id, label, rule, page, note} for the FR-45 exceptions register |
| `config/strings.en.json`, `config/strings.hi.json` | Read | JSON | Interface strings |
| `eval/expectations.json` | Read | JSON | Per question: expected rules, figures or not-found, verification page |
| `logs/queries.jsonl` | Append | JSONL | FR-38 fields |

### 5.3 Optional Inference Service Interface

- Endpoint, model and key supplied only through environment variables (`BVS_INFERENCE_URL`, `BVS_INFERENCE_KEY`, `BVS_INFERENCE_MODEL`).
- Permitted uses: mapping free text to FR-01 parameters and FR-05 topics; rendering Hindi explanatory labels.
- Prohibited uses: producing any rule number, page number, table value, fee, distance, area or storey count. Service output shall be parsed into typed fields and validated by FR-04 and FR-27 before use.
- Absence or failure degrades only per NFR-18 and NFR-19.

---

## 6. Traceability Matrix

Jury criteria for Track 1 (R8): J1 rule number and text shown on every answer; J2 "not found" when the Rules are silent, never an invented rule; J3 table figures correct; J4 measured accuracy on sample questions.

| Requirement | J1 | J2 | J3 | J4 |
|---|---|---|---|---|
| FR-06 Corpus loading | X | | | |
| FR-07 Topic-to-rule mapping | X | | X | |
| FR-08 Rule retrieval output | X | | | X |
| FR-09 Header removal | X | | | |
| FR-10 Inserted-rule resolution | X | X | | |
| FR-11 Footnote preservation | X | | X | |
| FR-12 Keyword fallback | X | X | | |
| FR-13 Table value lookup | | | X | X |
| FR-14 to FR-20 Computation | | | X | X |
| FR-21 Computation isolation | | X | X | |
| FR-22 Calculation trace | X | | X | |
| FR-23 Version stamp | X | | | |
| FR-24, FR-25 Amendment register and flag | X | | X | |
| FR-26 Explicit not-found | | X | | X |
| FR-27 Fabrication guard | | X | | |
| FR-29 Verbatim English text | X | | | |
| FR-31 PDF page link | X | | X | |
| FR-32 Counter display | X | X | | |
| FR-34, FR-35 Evaluation harness | | X | X | X |
| FR-36, FR-37 Corpus admin and integrity | X | X | | |
| FR-38 Audit log | X | | | X |
| FR-40, FR-41, FR-43, FR-47 Envelope, drawing, overlap, trace | X | | X | |
| FR-39, FR-42, FR-44 Geometry input and coupled redraw | | | X | X |
| FR-45 Exceptions register | X | X | | |
| FR-46, FR-48 Result wording, limitation, refusal | X | X | | |
| FR-49, FR-50 Plan check print, audit, test cases | X | | X | X |
| NFR-03, NFR-04, NFR-05 | | X | X | X |
| NFR-24, NFR-25 Geometry accuracy and traceability | X | | X | X |
| NFR-18 Degraded mode | X | X | X | |

---

## Appendix A. Worked Example: 200 sq m Residential Plot on a 9 m Road

### A.1 Inputs

| Parameter | Value | Source |
|---|---|---|
| Plot area | 200 sq m | Citizen |
| Road width | 9.0 m | Citizen |
| Use type | Residential | Citizen |
| Proposed built-up area | 250 sq m | Clerk entry (equal to FAR maximum) |
| Proposed height | Up to 12.5 m | Default |
| Frontage, development type, floor-to-floor height | Not supplied | Shown as conditional |
| Language | Hindi (sample question 14) or English | Detected |

### A.2 Retrieved Rules

| Topic | Rule | Title (Part) | PDF pages |
|---|---|---|---|
| Front setback | 56(1)(a) | Residential Buildings (V) | 77 |
| Rear setback | 56(2)(a) | Residential Buildings (V) | 78 |
| Side setback | 56(3); 53(1)(i) | Residential Buildings (V); Size of plots (IV) | 78; 70 |
| Height limit | 65(1); 42 Table 4 | Height limit (V); Provisions above 12.5 m (IV) | 85; 58 |
| FAR | 61 Table 8 | Floor Area Ratio (V) | 83 |
| Fees | 21(2)(ii); 21(3)(b) item 1 | Fees (III) | 35 to 37 |

### A.3 Computed Outputs

| Figure | Value | Trace |
|---|---|---|
| Front open space | 3.0 m | Rule 56(1)(a) row 1, "Up to 9.0 meters" gives 3.0 m |
| Rear open space | 2.50 m | Rule 56(2)(a) row 3, "Above 150 and up to 225.00" gives 2.50 m |
| Side open space | Conditional | Rule 53(1)(i): 200 sq m permits semi-detached (125 to 225) or row type (50 to 225). Semi-detached: 3.0 m on one side, reducible to 2.5 m if height is 10 m or less and frontage is 10 m or less (Rule 56(3)(ii)). Row type: nil (Rule 56(3)(iii)). Clerk selects. |
| Maximum height | 12.5 m | Rule 42 Table 4 begins at 12 m road width; 9 m is below it, so Rule 56 norms for buildings up to 12.5 m govern |
| Storey count | Not prescribed | Shown only if floor-to-floor height is entered (FR-18) |
| FAR | 1.25 | Rule 61 Table 8 row 1 |
| Permitted floor area | 250 sq m | 1.25 x 200 |
| Application fee | Rs 250 | Rule 21(2)(ii): Rs 1.00 x 250 sq m |
| Permission fee | Rs 3,000 | Rule 21(3)(b) item 1, slab 201 to 300 sq m |

### A.4 Displayed Citation and Flags

- Verbatim English text of Rule 56(1)(a) including the four-row table, with links "Open EN PDF p. 77" and "Open HI PDF p. 77".
- Version stamp: "Derived from MP Bhumi Vikas Rules 2012, consolidated to 6 March 2025."
- Amendment flag: "28 August 2026 amendment to Rule 2(5)(c) concerns plots up to 500 sq m. This plot is 200 sq m. The amendment text is not in this corpus and is not applied here. Source: R7."
- Disclaimer: "This is a rule reference, not legal advice. The building-permission clerk decides."

### A.5 Plan Check Extension

The clerk adds frontage 10 m, depth 20 m, semi-detached, height 10 m. Rule 56(3)(ii) gives 3.0 m on one side, reduced to 2.5 m because height and frontage are both 10 m or less; the other side is nil. The citizen can correct the plan at the counter before paying fees.

| Envelope step | Value | Trace |
|---|---|---|
| Buildable width | 7.5 m | 10 minus 2.5 side (Rule 56(3)(ii), p. 78) minus 0 other side |
| Buildable depth | 14.5 m | 20 minus 3.0 front (Rule 56(1)(a), p. 77) minus 2.5 rear (Rule 56(2)(a), p. 78) |
| Envelope area | 108.75 sq m | 7.5 x 14.5 |

Proposed footprint entered as distances from the boundaries: front 2.4 m, rear 2.5 m, left 2.5 m, right 0 m.

| Side | Required | Provided | Shortfall | Rule, page |
|---|---|---|---|---|
| Front | 3.00 m | 2.40 m | 0.60 m | 56(1)(a) row 1, p. 77 |
| Rear | 2.50 m | 2.50 m | 0.00 m | 56(2)(a) row 3, p. 78 |
| Left | 2.50 m | 2.50 m | 0.00 m | 56(3)(ii) proviso, p. 78 |
| Right | 0.00 m | 0.00 m | 0.00 m | 56(3)(ii), p. 78 |

Result: "Setback conflict found", with a hatched and labelled 0.60 m strip along the front, then the limitation statement and disclaimer. Derived note: FAR 1.25 gives 250 sq m; against a 108.75 sq m footprint that is 2.3 floors by area, labelled "derived" and subject to the unmodelled Rule 2 exclusions from floor area.

---

## Appendix B. Known Gaps

| ID | Gap | Impact | Mitigation |
|---|---|---|---|
| G-01 | The 28 August 2026 amendment to Rule 2(5)(c) is not in the corpus. | Results for plots up to 500 sq m may be superseded. | FR-24 and FR-25 flag it; administrator loads the text via FR-36 when available. |
| G-02 | Hindi PDF (R2) is not machine-readable. | No verbatim Hindi rule text. | Display R2 page by link (FR-30); Hindi explanatory rendering labelled as such. |
| G-03 | The Rules prescribe height, not storey count. | Citizens ask "how many floors". | FR-18 derived figure with explicit label. |
| G-04 | Tables are flattened text. | Risk of wrong figure. | Range tables hand-verified against R1 (NFR-05); PDF link on every figure. |
| G-05 | Inserted rules 12-A, 17-a, 25(A), 26-A, 42-A and 93(a) have no own record. | Retrieval by printed number may fail. | FR-10 resolution list. |
| G-06 | Sample questions 4, 6, 7, 9 and 13 are procedural and have no computable figure. | Harness checks rule citation only. | FR-35 expectations allow a rule-only pass. |
| G-07 | Development Plan provisions take precedence (Rule 103) and may differ from the Rules. | Figures are rule-based only. | Disclaimer; Rule 103 cited when the Development Plan is mentioned. |
| G-08 | Corner plots: the Rules do not state which street sets the front open space. | No drawing for corner plots. | FR-48 refusal with both readings shown. |
| G-09 | Irregular plots and non-rectangular footprints are not modelled. | Plan check limited to rectangles. | FR-48 refusal; future version. |
| G-10 | Rule 2 exclusions from floor area (stairs, parking, services) are not modelled. | Floors-by-area figure is an estimate. | Labelled "derived" in A.5; FAR shown separately. |
| G-11 | A drawing is more persuasive than a number; a range-table transcription error carries higher consequence. | Wrong line drawn with confidence. | NFR-05 row verification; FR-47 trace on every line; PDF link beside the drawing. |

*End of document.*
