# Phase 1: Frontend

Read `00_SHARED_CONTEXT.md` first. Build the complete clerk-facing interface against the API contract, running on a mock server, so that backend phases can plug in without UI changes.

## Goal

A single-page interface that a BMC counter clerk can use without training to (a) enter plot parameters by form or short free text, (b) see computed figures with rule citations, (c) run a plan check and see the to-scale drawing, (d) open the official PDF at the cited page, and (e) print a one-page slip. Everything in English and Hindi.

## SRS requirements owned by this phase

FR-01, FR-02 (client side only: send text to `/api/parse`, populate the form, require confirmation), FR-03 (manual language override), FR-04 (client-side validation mirroring the ranges), FR-05, FR-28, FR-29, FR-30, FR-31, FR-32, FR-33, FR-41, FR-42 (input and client validation), FR-43 (rendering of overlaps), FR-44 (re-request on height change and show the notice), FR-45 (exception selection UI and annotation), FR-46 (render wording exactly as returned), FR-47 (trace display), FR-48 (render refusal), FR-49 (print view). NFR-08, NFR-09, NFR-10, NFR-11, NFR-22, NFR-23, 5.1.

## Deliverables

1. `frontend/` Vite + React + TypeScript project with `npm run build` producing `frontend/dist`.
2. `frontend/mock/server.ts` (or a Vite plugin) serving the API contract with fixture responses for: the Appendix A lookup, the Appendix A.5 plan check, a `not_found` response (sample question 16), a `blocked` response (area mismatch), a `refused` response (corner plot), and a Hindi lookup (sample question 14). Fixtures must use the exact figures from the shared context.
3. `config/strings.en.json` and `config/strings.hi.json` with every interface string. No hard-coded UI text in components. Hindi strings written in plain Devanagari by a Hindi-literate teammate; mark any machine-drafted string with a `"_review": true` flag for later checking.
4. Vitest tests for: form validation ranges, language toggle, figure rendering with trace, SVG geometry mapping, overlap hatching, refusal and blocked states, print view presence of all FR-32 elements.
5. A short `frontend/README.md`: how to run with mock, how to run against the real backend.

## Screen layout (FR-32, 5.1)

One page, 1366 x 768 minimum, no horizontal scrolling, vertical scrolling allowed below the fold.

```
+------------------------------------------------------------------+
| Bhumi Vikas Sahayak          [EN | हिन्दी]   Rules consolidated to 6 Mar 2025 |
+------------------------------+-----------------------------------+
| INTAKE                       | RESULT                            |
| [ free text box ] [Parse]    | Figures (large, with unit, rule,  |
| Plot area* | Road width*     |   page link, trace toggle)        |
| Use type*  | Built-up area   | Amendment flag (icon + text)      |
| Height     | Dev type        | Drawing (when plan check)         |
| Frontage   | Depth           | Per-side table                    |
| Floor-to-floor               | Citations (collapsed to sub-rule, |
| Topics: [x] front [x] rear.. |   expandable; verbatim English;   |
| Plan check: footprint        |   footnotes; EN/HI PDF links)     |
|   front rear left right      | Disclaimer                        |
| [Look up]  [Plan check]      | [Print]                           |
+------------------------------+-----------------------------------+
```

Above the fold on load of a result: all figures, the first citation, the amendment flag if any.

## Form behaviour (FR-01, FR-04, FR-05)

- Mandatory for lookup: plot area, road width, use type. Mandatory when plan check is selected: frontage, depth, development type, height, all four footprint distances. Mandatory when a fee topic is selected: built-up area. Show field-level prompts naming the field; never submit with a missing mandatory field.
- Validation ranges: plot area 1 to 100,000; road width 1 to 100; height 0 to 150; frontage and depth 1 to 500. Reject negatives and non-numbers inline.
- When road width is under 6, show the "existing developed area" yes/no control (FR-14).
- Streets abutting: default 1; selecting 2 makes plan check send `streets_abutting: 2` and the UI renders the refusal returned.
- Topics are checkboxes. Parsed text may pre-select topics. Plan check is a topic that reveals the footprint fields.
- Free-text parse: send to `/api/parse`, fill fields with returned params, highlight filled fields, require the clerk to press Look up. Show a banner if `used_inference` is false and parsing was partial.

## Figure cards (FR-22, FR-28, FR-47)

Each figure: value at 20 px or larger, unit, label in the active language, rule and page as a link to `/pdf/en#page=N`, a "show trace" toggle revealing the trace string. If `derived` is true show the label "derived, not prescribed by the Rules". If `conditional` is true, render each case in `cases` as a sub-card and the text "clerk selects".

## Citations (FR-29, FR-30, FR-31)

Always verbatim English `text_en`, monospace or preserved whitespace so flattened tables stay aligned. Footnote markers kept. Collapsed to the cited sub-rule with an "expand full rule" control. Two buttons: "Open EN PDF p. N", "Open HI PDF p. N". In Hindi mode labels are Hindi, the rule text stays English, and a note says the Hindi PDF page is the official Hindi text.

## Drawing (FR-41, FR-43, FR-44, FR-45, NFR-22, NFR-23)

Inline SVG. Map metres to pixels with a single scale factor fitting the plot into the panel with a 10 % margin. Coordinates from the API: origin front-left, x right, y away from the road. Render in this order:

1. Road band along the bottom edge, labelled with road width.
2. Plot boundary rectangle with width and depth labels.
3. Four setback lines, each labelled "front 3.00 m, R56(1)(a)" style; label text from the API `rule` and `value`.
4. Buildable envelope rectangle, light fill, labelled with width x depth and area.
5. Footprint rectangle, outline only, labelled with width x depth and area.
6. Overlap rectangles from `overlaps`, diagonal hatch pattern plus a text label "0.60 m short, R56(1)(a), p. 77". Never colour alone.
7. Scale bar, 1 m or 5 m depending on plot size.
8. Exception annotations: when the clerk selects an exception from `exceptions_available`, keep the hatch and add the text "clerk-marked exception, see Rule N" to the overlap.

Height change: when the clerk edits height after a plan check, re-send the request and, if any required side value changed, show a notice "Side open space changed from 2.50 m to 3.00 m, Rule 56(3)(ii) proviso no longer applies" built from the old and new API values.

All displayed distances to two decimals. Drawing re-renders in under 1 s after a response.

## States (FR-26, FR-39, FR-46, FR-48)

- `answered`: render as above.
- `not_found`: large message "Not found in MP Bhumi Vikas Rules 2012" in the active language, no figures, no citations, disclaimer still shown.
- `blocked`: show `message` and two buttons for `resolutions`: "Correct inputs" (focus the form) and "Use dimensions as plot area" (re-send with the flag).
- `refused`: show `message` verbatim. For the corner-plot case the message contains both readings; render as two paragraphs.
- Plan check result line uses the exact string from the API. Below it, the `checks_performed` list and the `not_checked` sentence. Never add words like approved or compliant anywhere in the UI.

## Print view (FR-33, FR-49)

A print stylesheet that fits one A4 page: figures, drawing, per-side table, first citation sub-rule text, version stamp, amendment flag, disclaimer, PDF page references as text. Hide the intake panel.

## Accessibility and usability (NFR-08, NFR-09, NFR-10, 5.1)

- Keyboard-only path: Tab order follows the layout; Enter in any field triggers Look up.
- Lookup in 4 or fewer entries from a blank form for the Appendix A case; plan check in 12 or fewer.
- Minimum font 14 px. Colour never the sole carrier of meaning.
- Language toggle always visible; switching re-renders labels without re-fetching.

## Acceptance checklist

- [ ] Appendix A fixture renders five figures and the Rule 56(1)(a) citation above the fold at 1366 x 768.
- [ ] Appendix A.5 fixture draws envelope 7.5 x 14.5 and footprint 7.5 x 15.1 with a hatched 0.60 m front strip labelled with rule and page.
- [ ] Changing height from 10 to 10.5 in the mock produces the side-space notice.
- [ ] Sample question 16 fixture shows the not-found state with zero citations.
- [ ] Hindi fixture shows Hindi labels with the English rule text unchanged.
- [ ] Blocked and refused fixtures render as specified.
- [ ] Print preview is one page containing every FR-32 element.
- [ ] A text search of the built bundle finds none of: chatbot, assistant, approved, compliant, sanctionable.
- [ ] `npm test` passes; `npm run build` succeeds; no API keys anywhere.
