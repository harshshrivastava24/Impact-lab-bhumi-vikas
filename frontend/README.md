# Bhumi Vikas Sahayak: Frontend (Phase 1, UI only)

Clerk-facing interface for the building-rule lookup and compliance decision-support tool. React 18, TypeScript (strict), Tailwind CSS v4, Vite. Spec: `../SRS_Bhumi_Vikas_Sahayak.md` v1.2 and `../master-prompt/frontend-phases/frontend-phases.md`.

## Run

```bash
cd frontend
npm install
npm run dev:mock      # demo with fixtures, no backend needed: http://localhost:5173
npm run dev           # against the backend at http://127.0.0.1:8000 (proxy for /api and /pdf)
```

Try the worked example: plot area 200, road width 9, built-up area 250, press Look up. For the plan check also enter height 10, Semi-detached, frontage 10, depth 20, footprint 2.4 / 2.5 / 2.5 / 0, press Run plan check.

## Checks

```bash
npm run typecheck && npm run lint && npm test && npm run build
npm run test:e2e      # Playwright in the installed Microsoft Edge at 1366 x 768
```

| Check | Result on 11 Oct 2026 |
|---|---|
| Unit and integration tests (Vitest + MSW) | 67 / 67 pass |
| Browser acceptance tests (Playwright, Edge) | 8 / 8 pass |
| Typecheck, lint (incl. jsx-a11y strict, no literal UI strings) | clean |
| Production bundle | no forbidden words, no fixture data |

## What works

- Form and free-text intake, conditional mandatory fields, error summary, field-level errors.
- Figure cards with rule, PDF page link and calculation trace; conditional cases; Rule 53(1)(i) warning.
- Verbatim English rule text collapsed to the cited sub-rule, footnotes, EN and HI PDF page links.
- Amendment notice above the fold; version stamp; disclaimer on every state.
- Not found, blocked (area mismatch with two resolutions), refused (corner plot, both readings), error with retry.
- To-scale plan drawing: setback lines, envelope, footprint, hatched shortfall labelled with rule and page, exceptions, height re-send with change notice.
- One-page A4 print slip. English and Hindi.

## What does not (yet)

- Demo mode answers only the fixture scenarios; other inputs show a "no fixture" error by design. Real answers need the backend (Phases 2 and 3).
- Hindi strings are machine-drafted and flagged `_review: true` in `config/strings.hi.json`; a Hindi-literate teammate must review them.
- Desktop layout only; the two panes do not stack below about 800 px.
- No animations (Phase 2).

## Contract additions for the backend

Documented in `src/api/schemas.ts`: `Figure.warning`, `Citation.sub_rule_text_en`, `LookupRequest.query_text` (free-text Rules search for not-found), `PlanCheckRequest.resolution`, `Geometry.result_kind` (language-independent conflict flag).

## Regenerate fixtures

`python scripts/make_fixtures.py` rebuilds `src/mocks/fixtures` from `../data`, asserting every cited page against the corpus.
