# Frontend Phases

Two prompts that together replace `01_PHASE1_FRONTEND.md`. Run Phase 1 to completion before starting Phase 2. Both assume `00_SHARED_CONTEXT.md` and the SRS (`SRS_Bhumi_Vikas_Sahayak.md` v1.2). Where this file and the SRS disagree, the SRS wins.

## Stack (fixed for both phases)

| Concern | Choice | Notes |
|---|---|---|
| Language | TypeScript, `strict: true` | No `any` in committed code; API types generated from Zod schemas |
| Framework | React 18 with Vite | Single page, no router needed |
| Styling | Tailwind CSS v4 via `@tailwindcss/vite` | Design tokens in `@theme`; no other CSS framework |
| Validation and API types | Zod | One schema per contract type in `src/api/schemas.ts`; `z.infer` for TS types |
| Forms | React Hook Form with `@hookform/resolvers/zod` | Conditional mandatory fields via `superRefine` |
| Mock API | MSW (Mock Service Worker) | Fixtures from the shared context; same handlers used in tests |
| Icons | `lucide-react` | Every icon paired with text or `aria-label` |
| Fonts | `@fontsource/noto-sans`, `@fontsource/noto-sans-devanagari`, `@fontsource/noto-sans-mono` | Self-hosted; no font CDN calls (NFR-16) |
| Animation (Phase 2 only) | `motion` (the `motion/react` package) | Plus Tailwind transitions for simple cases |
| Tests | Vitest, React Testing Library, `@testing-library/user-event`, Playwright for layout and screenshot checks | |
| Lint | ESLint with `typescript-eslint`, `eslint-plugin-jsx-a11y`; Prettier with `prettier-plugin-tailwindcss` | |

Skills available in this environment and when to use them:

- `ui-ux-pro-max` in Phase 1 step 1 to produce the design system (palette, type scale, spacing, components) for a government counter tool.
- `hallmark` only to sanity-check that the layout does not look like a generic template. The counter workflow wins over novelty; do not adopt a marketing-page macrostructure.
- `web-design-guidelines` at the end of each phase to review the code. Fix every finding or record why not.
- The Open Design MCP may be used to mock the screen visually before coding. It is optional and must not replace the coded implementation.

---

## PHASE 1 PROMPT: UI ONLY

You are building the clerk-facing interface of Bhumi Vikas Sahayak, a rule lookup and compliance decision-support tool used at the Bhopal Municipal Corporation building-permission counter. Never call it a chatbot, assistant or conversational agent in code, comments or UI text. Build the complete static interface, every state, and the to-scale drawing, against a mock API. No animations in this phase: state changes are instant. Phase 2 adds motion on top without restructuring components, so keep component boundaries clean.

### Requirements owned

SRS FR-01 to FR-05 (client side), FR-14 narrow-street input, FR-16 warning display, FR-22 and FR-47 trace display, FR-25 flag display, FR-26 not-found state, FR-28 to FR-33, FR-39 blocked state, FR-41 to FR-49 (rendering and input), FR-51 display. NFR-08 to NFR-11, NFR-22, NFR-23, Section 5.1.

### Step 1: Design system

Run the `ui-ux-pro-max` skill with this brief: "Government building-permission counter tool, Bhopal. Single clerk user, time-pressured, mixed English and Hindi literacy, used on a 1366 x 768 office monitor, also printed. Must feel official, calm and trustworthy, not playful. High contrast, large numerals, accessible." From its output, write the tokens into `src/styles/theme.css` under `@theme`:

- Colours: one primary, neutrals, and semantic colours for conflict, pass, warning (amendment), info. Every text and background pair at 4.5:1 or better; figures at 7:1. Conflict and pass must also differ by icon and pattern, never colour alone.
- Type: Noto Sans for Latin, Noto Sans Devanagari for Hindi, Noto Sans Mono for verbatim rule text. Body 16 px minimum, labels 14 px minimum, figures 28 px, tabular numerals (`font-variant-numeric: tabular-nums`).
- Spacing on a 4 px grid; radius small; shadows minimal.
- Print tokens: black on white, no fills except hatching.

Commit the tokens and a `docs/design-system.md` summarising the choices and the contrast ratios measured.

### Step 2: Project scaffold

```
frontend/
  index.html
  vite.config.ts
  tsconfig.json
  src/
    main.tsx  App.tsx
    styles/theme.css  styles/print.css
    api/schemas.ts  api/client.ts
    mocks/handlers.ts  mocks/fixtures/*.json  mocks/browser.ts  mocks/server.ts
    i18n/strings.ts  i18n/useStrings.ts
    components/
      layout/Header.tsx  layout/TwoPane.tsx
      intake/FreeTextParse.tsx  intake/LookupForm.tsx  intake/TopicPicker.tsx  intake/FootprintFields.tsx
      result/ResultPanel.tsx  result/FigureCard.tsx  result/ConditionalCases.tsx
      result/AmendmentFlag.tsx  result/CitationCard.tsx  result/Disclaimer.tsx
      result/states/NotFound.tsx  result/states/Blocked.tsx  result/states/Refused.tsx
      plan/PlanDrawing.tsx  plan/SideTable.tsx  plan/ExceptionsList.tsx  plan/PlanResult.tsx
      print/PrintSlip.tsx
    hooks/useLookup.ts  hooks/usePlanCheck.ts
    lib/geometry.ts  lib/format.ts
  tests/
```

- `npm run dev` starts Vite with MSW enabled when `VITE_USE_MOCK=true`.
- Vite proxy `/api` and `/pdf` to `http://127.0.0.1:8000` when the mock is off.
- Strings load from `config/strings.en.json` and `config/strings.hi.json` at the repo root via a typed loader. No hard-coded UI text in components; a lint rule or test fails on string literals in JSX except punctuation.

### Step 3: API layer

- Zod schemas for every type in the shared context contract: `Params`, `Topic`, `Figure`, `Citation`, `AmendmentFlag`, `LookupResponse`, `PlanCheckRequest`, `PlanCheckResponse`, `ParseResponse`. Parse every response; a schema failure shows a readable error card, never a blank screen.
- `client.ts` exposes `parse`, `lookup`, `planCheck`, `getRule` with typed returns.
- MSW fixtures, with exact figures from the shared context:
  1. Appendix A lookup, English.
  2. Appendix A lookup, Hindi (sample question 14).
  3. Appendix A.5 plan check with front shortfall 0.60.
  4. Same plan check with height 10.5, side space 3.0.
  5. Not found (sample question 16).
  6. Blocked area mismatch (area 230).
  7. Refused corner plot with both readings.
  8. Narrow street 5 m, existing developed area, front 3.5 from 56(1)(b).
  9. Development type out of range warning.

### Step 4: Layout and intake

Two-pane layout from `01_PHASE1_FRONTEND.md`: intake left at about 38 % width, result right. Header shows the product name, the language toggle, and "Rules consolidated to 6 March 2025". No horizontal scroll at 1366 x 768; vertical scroll allowed below the fold.

- `LookupForm` with React Hook Form and a Zod resolver. Mandatory: plot area, road width, use type. When plan check is selected: frontage, depth, development type, height and the four footprint distances become mandatory. When a fee topic is selected: built-up area becomes mandatory. Field-level messages name the field.
- Ranges per FR-04. Numeric inputs use `inputMode="decimal"` and accept only valid numbers.
- Road width under 6 reveals the "existing developed area" yes or no control.
- Streets abutting: 1 or 2. Use type select.
- `FreeTextParse`: text box and Parse button; fills the form from `/api/parse` and highlights filled fields with a static outline. The clerk must press Look up.
- `TopicPicker`: checkboxes; plan check reveals `FootprintFields`.
- Enter in any field submits. Tab order follows visual order.

### Step 5: Result panel

Order per FR-32: figures, drawing when plan check, citations, version stamp, amendment flag, disclaimer, PDF links. Above the fold on load: all figures, first citation, amendment flag.

- `FigureCard`: label in the active language, value at 28 px with unit, rule and page as a link to `/pdf/en#page=N`, a "Show trace" disclosure revealing the trace string. If `derived`, the text "derived, not prescribed by the Rules". If `conditional`, render `ConditionalCases` with one sub-card per case and the text "clerk selects". If a warning is present, show it inline with an icon.
- `AmendmentFlag`: icon plus heading "Potentially relevant amendment", the date, rule, what it concerns, source kind, and "not applied in these figures".
- `CitationCard`: rule number, title, part, page range. Verbatim English text in the mono font with `whitespace-pre` so flattened tables stay aligned, collapsed to the cited sub-rule with an "Expand full rule" disclosure. Footnotes listed below. Buttons "Open EN PDF p. N" and "Open HI PDF p. N". In Hindi mode labels are Hindi and the rule text stays English, with a note that the Hindi PDF page holds the official Hindi text.
- `Disclaimer` on every result and every state.

### Step 6: States

- `NotFound`: large message "Not found in MP Bhumi Vikas Rules 2012" in the active language, no figures and no citations, disclaimer shown.
- `Blocked`: the message and two buttons, "Correct inputs" focuses the plot area field, "Use dimensions as plot area" re-sends with the resolution.
- `Refused`: message verbatim; corner-plot message rendered as two paragraphs.
- Loading: disable the submit button and show "Looking up" text. No spinner animation in this phase.
- Network or schema error: a readable error card with a retry button.

### Step 7: Plan drawing

`PlanDrawing` is an inline SVG with `role="img"` and an `aria-label` summarising the result. Pure geometry helpers live in `lib/geometry.ts` and are unit-tested.

- One scale factor fits the plot into the panel with a 10 % margin. API coordinates: origin front-left, x right, y away from the road. Flip y so the road sits at the bottom of the SVG.
- Draw order: road band with width label; plot boundary with width and depth labels; four setback lines with labels such as "front 3.00 m, R56(1)(a)"; envelope rectangle with light fill and "7.50 x 14.50 m, 108.75 sq m"; footprint outline with "7.50 x 15.10 m, 113.25 sq m"; overlap rectangles with a diagonal hatch `<pattern>` and a label "0.60 m short, R56(1)(a), p. 77"; scale bar of 1 m or 5 m.
- Labels never overlap: place them outside the shape when space is under 24 px.
- `SideTable`: required, provided, shortfall, rule, page for each side.
- `PlanResult`: the exact result string from the API, the `checks_performed` list, the `not_checked` sentence. The words approved, compliant and sanctionable never appear anywhere in the UI.
- `ExceptionsList`: checkboxes from `exceptions_available`. Selecting one keeps the hatch and adds "clerk-marked exception, see Rule N" on the overlap.
- Height edit after a plan check re-sends the request. If a side value changed, show a static notice "Side open space changed from 2.50 m to 3.00 m" built from the old and new responses.

### Step 8: Print

`styles/print.css` with `@media print` and `PrintSlip` fitting one A4 page: figures, drawing, side table, first citation sub-rule text, version stamp, amendment flag, disclaimer, PDF page numbers as text. Hide intake, buttons and disclosures.

### Step 9: Accessibility and review

- Keyboard-only path for the full Appendix A and A.5 flows.
- Visible focus ring on every interactive element.
- `aria-live="polite"` region announces "Result ready" and the result status.
- Run the `web-design-guidelines` skill on `frontend/src/**/*.tsx`. Fix every finding.

### Phase 1 acceptance

- [ ] `npm run typecheck`, `npm run lint`, `npm test`, `npm run build` all pass.
- [ ] Appendix A fixture: five figures and the Rule 56(1)(a) citation visible without scrolling at 1366 x 768 (Playwright screenshot test).
- [ ] Lookup for Appendix A takes 4 or fewer entries from a blank form; plan check A.5 takes 12 or fewer.
- [ ] A.5 fixture draws envelope 7.50 x 14.50 and footprint 7.50 x 15.10 with a hatched 0.60 m front strip labelled with rule and page.
- [ ] Height 10.5 fixture shows the side-space notice.
- [ ] Not found, blocked, refused, narrow street and type warning fixtures render as specified.
- [ ] Hindi fixture shows Hindi labels with unchanged English rule text, in Noto Sans Devanagari.
- [ ] Print preview is one A4 page with every FR-32 element.
- [ ] Built bundle contains none of: chatbot, assistant, approved, compliant, sanctionable.
- [ ] No network requests other than `/api` and `/pdf` (checked in Playwright).
- [ ] `web-design-guidelines` review has no open findings.

---

## PHASE 2 PROMPT: ANIMATIONS, INTERACTIONS AND POLISH

Phase 1 is complete and green. Add motion and interaction polish that helps the clerk see what changed, without slowing the one-minute counter workflow. Do not restructure components or change any data, wording or layout from Phase 1. Every animation must be removable by `prefers-reduced-motion` without losing information.

### Principles

1. **Motion explains change, never decorates.** Animate only when something appeared, changed or needs attention.
2. **Never animate a number through intermediate values.** Fees, distances and areas are legal figures; a count-up would show values that are not in the Rules. Numbers swap with a crossfade.
3. **Never delay readability.** A figure must be readable within 200 ms of the response arriving. No animation blocks input.
4. **Short and calm.** 120 to 250 ms for most transitions, ease-out on enter, ease-in on exit. No bounce, no elastic, no infinite loops, no shake.
5. **Transform and opacity only.** No animated width, height or top on large elements except through `motion` layout animations; no layout thrash.
6. **Reduced motion.** With `prefers-reduced-motion: reduce`, every transition becomes an instant change or an opacity fade of 80 ms or less.
7. **Print has no motion.**

### Implementation

- Add `motion` and create `src/motion/tokens.ts` with named durations (`fast 120`, `base 180`, `slow 250`, `draw 320`) and easings. No literal durations elsewhere.
- `src/motion/useReducedMotion.ts` wraps `useReducedMotion` from `motion/react`; every animated component reads it.
- Wrap the app in `<MotionConfig reducedMotion="user">`.

### Interactions to add

| Where | Trigger | Motion | Duration |
|---|---|---|---|
| Result panel | New response | Panel fades in; figure cards stagger 30 ms each, max 5 staggered | base |
| Figure value | Value changes between responses | Old value fades out, new value fades in; card border highlights once | fast |
| Figure card | Value unchanged | No motion | none |
| Trace and "Expand full rule" disclosures | Toggle | Height via `motion` layout animation, content fade | base |
| Amendment flag | First appearance | Slide down 8 px and fade in; icon does not pulse | base |
| Parse fill | Fields filled from free text | Field background highlight fades out | 1000 ms fade-out, starts after 300 ms |
| Form errors | Validation fails | Message fades in; focus moves to first error | fast |
| Submit | Request in flight longer than 300 ms | Show skeleton cards with a subtle shimmer; none if faster | shimmer 1.2 s loop, stops on response |
| Language toggle | Switch | Text crossfade; no layout animation | fast |
| States (not found, blocked, refused) | Appear | Fade in; not found icon scales from 0.96 to 1 | base |
| Focus ring | Focus | Ring fades in | fast |
| Buttons | Press | Scale to 0.98 on press only | fast |

### Drawing animation

On a new plan-check response:

1. Plot boundary and road appear instantly.
2. Setback lines draw in using `pathLength` from 0 to 1, front first then rear, left and right, 40 ms apart.
3. Envelope fill fades in after the lines.
4. Footprint outline fades in.
5. Overlap hatch fades in; the overlap label and its row in the side table get one highlight pulse, then rest.
6. Total sequence 600 ms or less; everything legible after 400 ms.

On a height change that alters a side value:

- The affected setback line and envelope edge move to the new position with a layout transition (slow). Labels update with a crossfade.
- The side-space notice slides in and stays until the next lookup.
- Other elements stay still.

On exception selection: the "clerk-marked exception" annotation fades in; the hatch stays.

With reduced motion: the final drawing renders immediately; only opacity fades of 80 ms or less.

### Micro-interactions and polish

- Hover and focus states for every button, link, checkbox and disclosure, using Tailwind `transition-colors` at `fast`.
- PDF links show an external-document icon; on hover the page number underlines.
- Copy button on each citation copies the rule number, sub-rule, page and verbatim text; a toast "Copied" fades in and out (`aria-live`).
- Keyboard shortcuts: `Ctrl+Enter` submits, `Ctrl+P` opens print, `Alt+L` toggles language. Show them in a small help popover opened by `?`.
- Empty state before the first lookup: a short static instruction with the worked example as a one-click "Try the example" button that fills the form.
- Scroll the result panel to top on each new response; move focus to the result heading.

### Performance budget

- Added JavaScript from `motion` and polish code 40 KB gzipped or less; lazy-load the drawing animations with the plan check.
- No frame drops below 50 fps on a mid-range office PC during the drawing sequence (Chrome performance panel, 4x CPU throttle).
- First result interaction-to-figure-visible unchanged from Phase 1 within 50 ms.

### Accessibility checks for motion

- `aria-live` announcements fire when data arrives, not when animation ends.
- No content is hidden until an animation completes; screen readers get the final state immediately.
- Nothing flashes more than three times per second.

### Phase 2 acceptance

- [ ] All Phase 1 tests still pass unchanged.
- [ ] With `prefers-reduced-motion: reduce` emulated in Playwright, the A.5 drawing is complete in the first frame after the response.
- [ ] No number on screen ever shows a value other than the old or new response value (test with a frame-by-frame Playwright capture during a fee change).
- [ ] Drawing sequence completes within 600 ms; figures readable within 200 ms of response.
- [ ] Skeleton appears only when the mock delay exceeds 300 ms.
- [ ] Bundle size increase within budget (report from `vite build`).
- [ ] Keyboard shortcuts work and are listed in the help popover in both languages.
- [ ] Print output identical to Phase 1.
- [ ] `web-design-guidelines` review re-run with no open findings.
