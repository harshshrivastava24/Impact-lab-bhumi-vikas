# SRS Generation Prompt: Bhumi Vikas Sahayak

You are a senior software architect and business analyst. Write a complete Software Requirements Specification (SRS) following the IEEE 830 structure for the system described below. Write it in formal, implementation-neutral language. Do not describe the system as a chatbot, assistant, or conversational agent anywhere in the document. Describe it as a rule lookup and compliance decision-support tool.

## System Name

**Bhumi Vikas Sahayak:** Building Rule Lookup and Compliance Decision-Support Tool for the Bhopal Municipal Corporation.

## Context

Every building in Bhopal must comply with the Madhya Pradesh Bhumi Vikas Rules, 2012. The rulebook is 108 pages with 105 numbered rules plus rule 26-B. The most-requested figures (fees, setbacks, floor-area limits, floor counts) sit in tables spread across the document. The rules are amended periodically. The consolidated copy is current to 6 March 2025. A further amendment to Rule 2(5)(c) for plots up to 500 sq m was issued on 28 August 2026 and is not included in the consolidated copy.

## Primary User

A building-permission clerk at the Bhopal Municipal Corporation counter. A citizen presents plot details in person (for example: 200 sq m plot on a 9 m road) and asks about front setback, permitted floors, and applicable fees. The clerk must produce a correct answer within one minute, cite the rule number, and show the citizen the exact rule text. The clerk makes the decision; the tool supplies the rule reference and computed figures.

## Core Capabilities the SRS Must Cover

1. **Structured query intake:** the clerk enters plot parameters (plot area, road width, zone/use type, proposed floors, etc.) through a form, or types a short natural-language query in English or Hindi. Treat the natural-language path as an input parsing feature that maps to the same structured parameters, not as a dialogue.
2. **Rule retrieval:** locate the governing rule(s) in the corpus and return rule number, title, part, PDF page range, and the verbatim source text.
3. **Deterministic computation:** all arithmetic (fees, areas, floor counts, setback distances, FAR/ground coverage) is performed in code from the retrieved table values, never by a language model.
4. **Provenance and versioning:** every result states the rule version it was derived from (consolidated to 6 March 2025) and flags when a later amendment (28 August 2026, Rule 2(5)(c)) may affect the answer.
5. **Explicit non-answer:** when the rules do not cover the question, the tool returns a clear "not found in rules" result and never fabricates a rule or figure.
6. **Bilingual output:** the result is returned in the language of the query (English or Hindi), with the verbatim rule text always shown in English from the source of truth, and a Hindi rendering where available.
7. **Citation display:** the clerk can open the referenced PDF page to verify the rule text against the official document.
8. **Accuracy evaluation:** a built-in or scripted test harness runs the 17 sample questions (including two the rules do not answer) and reports pass/fail per question.

## Data Sources (Public Data Only)

| File | Description |
|------|-------------|
| `data/bhumi_vikas_rules.jsonl` | 106 lines, one rule per line with rule number, title, part, PDF page range, full text. |
| `data/bhumi_vikas_rules_fulltext_by_page.txt` | Full English text, pages marked with `===== PDF page N =====`. |
| `resources/MP_Bhumi_Vikas_Rules_2012_upto_2025-03-06_EN.pdf` | Official English PDF, the source of truth. |
| `resources/MP_Bhumi_Vikas_Rules_2012_upto_2025-03-06_HI.pdf` | Official Hindi PDF; its font makes extracted text unusable, so it is displayed, not parsed. |
| `resources/sample_questions.md` | 17 test questions. |

**Data quirks to capture as requirements:**

- Running page headers embedded in text.
- Flattened tables with column spacing preserved.
- Footnote markers like `1[` denoting amendments.
- Inserted rules (12-A, 17-a, 25(A), 26-A, 42-A, 93(a)) embedded inside the preceding rule's text; only 26-B has its own record.

## Constraints

- No connection to any live government system; no scraping, login, or writes to any portal.
- No personal data collected or stored.
- Output must not be presented as legal advice; every result carries a disclaimer that the clerk decides.
- Open source under the MIT licence; the code is offered to the Government of Madhya Pradesh via MPSeDC and must be readable and runnable by the department in five steps or fewer.
- No API keys or secrets in source code; configuration via environment variables.
- Single workflow, single user role. It is not a citizen portal.

## Required SRS Sections

1. **Introduction:** purpose, scope, definitions and acronyms (FAR, setback, ground coverage, MPSeDC, BMC, etc.), references, overview.
2. **Overall description:** product perspective, product functions, user characteristics (clerk with limited time and mixed English/Hindi literacy), operating environment, design and implementation constraints, assumptions and dependencies.
3. **Functional requirements:** numbered FR-xx, each with description, inputs, processing, outputs, and acceptance criteria. Cover query intake, parameter validation, rule retrieval, table extraction, computation, provenance, versioning and amendment flagging, not-found handling, bilingual output, citation and PDF page linking, result display for the counter, evaluation harness, and administrator tasks such as loading an updated rule corpus.
4. **Non-functional requirements:** numbered NFR-xx with measurable targets. Cover response time (end-to-end result within a stated number of seconds so the clerk meets the one-minute target), accuracy (target pass rate on sample questions, zero fabricated rules), reliability, availability for counter hours, usability (first-use without training, minimal clicks per query), localisation, maintainability (corpus update without code change), portability (runs on a standard department desktop or low-cost server), security (no secrets in code, no personal data, no outbound calls to government systems), auditability (log of query, rule cited, version used), offline or degraded-mode behaviour if any external inference service is unavailable, and licensing.
5. **External interface requirements:** user interface, data file interfaces, any optional external inference API interface with the explicit rule that computation and citation never depend on it for correctness.
6. **Traceability matrix** mapping each functional requirement to the jury criteria: rule number and text shown on every answer; "not found" when rules are silent; table figures correct; measured accuracy on sample questions.
7. **Appendices:** the worked example (200 sq m plot, 9 m road) showing expected inputs, retrieved rules, computed outputs, and displayed citation; list of known gaps (28 August 2026 amendment not in corpus, Hindi PDF not machine-readable).

## Style

Use "shall" for mandatory requirements. Each requirement must be atomic, testable, and uniquely numbered. Use tables where they aid clarity. Keep the document between 2,500 and 4,000 words.

---

## Notes on How the Prompt Was Shaped

- Natural-language entry is positioned as input parsing that feeds a structured form, with deterministic computation and citation as the core. That keeps the document reading as a lookup and compliance tool.
- Jury criteria are baked in through the traceability matrix section, so the SRS output doubles as a checklist for your demo and README.
