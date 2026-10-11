# Design System: Bhumi Vikas Sahayak Counter Interface

Generated with the `ui-ux-pro-max` skill on 11 October 2026 using the query "government public service compliance tool" with dials variance 3, motion 2, density 7, then adapted for a bilingual counter tool. Tokens live in `frontend/src/styles/theme.css`.

## Decisions

| Area | Skill recommendation | Adopted | Reason |
|---|---|---|---|
| Style | Minimalism and Swiss Style | Yes | Functional, high contrast, grid-based; suits a professional tool used all day |
| Pattern | Minimal single column, centred CTA | No | That is a landing-page pattern. The clerk needs intake and result side by side; a two-pane layout is used instead |
| Palette | Navy `#0F172A`, blue `#0369A1`, slate neutrals | Yes | Calm, official, high contrast |
| Semantic colours | Destructive `#DC2626` only | Extended | Added conflict, pass, warning (amendment) and info sets, each with text, stroke and tint |
| Typography | Atkinson Hyperlegible | No | It has no Devanagari. Noto Sans with Noto Sans Devanagari gives matched metrics across English and Hindi, as the stack fixes |
| Motion | Subtle scroll reveal | Deferred | Phase 1 has no animation; Phase 2 adds change-driven motion only |
| Anti-patterns | Ornate design, low contrast, decorative motion, purple gradients | Yes | All avoided |

Supplementary searches applied:

- Form errors: inline error below each field linked by `aria-describedby`, plus a focusable error summary after a failed submit.
- Numbers: thousand separators for rupee amounts, tabular numerals for all figures.

## Type

| Role | Font | Size | Weight |
|---|---|---|---|
| Body | Noto Sans, Devanagari fallback | 16 px, line height 24 | 400 |
| Labels | Noto Sans | 14 px | 600 |
| Figures | Noto Sans, tabular numerals | 28 px | 700 |
| Hindi text | Noto Sans Devanagari | same scale | same |
| Verbatim rule text | Noto Sans Mono, `white-space: pre` | 13 px | 400 |

## Spacing, radius, elevation

4 px grid. Radius 4 to 6 px. One shadow token, 1 px at 6 % opacity. Borders carry structure instead of shadows.

## Measured contrast

Ratios computed with the WCAG 2.x relative luminance formula.

| Pair | Colours | Ratio | Target | Result |
|---|---|---|---|---|
| Body text on background | #020617 on #F8FAFC | 19.28:1 | 4.5:1 | pass |
| Figure value on card | #020617 on #FFFFFF | 20.17:1 | 7:1 | pass |
| Muted text on card | #475569 on #FFFFFF | 7.58:1 | 4.5:1 | pass |
| Muted text on background | #475569 on #F8FAFC | 7.24:1 | 4.5:1 | pass |
| Header text on primary | #FFFFFF on #0F172A | 17.85:1 | 4.5:1 | pass |
| Header muted on primary | #CBD5E1 on #0F172A | 12.02:1 | 4.5:1 | pass |
| Button text on accent | #FFFFFF on #0369A1 | 5.93:1 | 4.5:1 | pass |
| Link on card | #0369A1 on #FFFFFF | 5.93:1 | 4.5:1 | pass |
| Input border on card | #64748B on #FFFFFF | 4.76:1 | 3:1 | pass |
| Focus ring on card | #0369A1 on #FFFFFF | 5.93:1 | 3:1 | pass |
| Conflict text on conflict tint | #991B1B on #FEF2F2 | 7.60:1 | 4.5:1 | pass |
| Conflict stroke on card | #B91C1C on #FFFFFF | 6.47:1 | 3:1 | pass |
| Pass text on pass tint | #166534 on #F0FDF4 | 6.81:1 | 4.5:1 | pass |
| Warning text on warning tint | #7C2D12 on #FFF7ED | 8.83:1 | 4.5:1 | pass |
| Warning border on card | #C2410C on #FFFFFF | 5.18:1 | 3:1 | pass |
| Info text on info tint | #0C4A6E on #F0F9FF | 8.87:1 | 4.5:1 | pass |
| Rule text on code background | #0F172A on #F1F5F9 | 16.30:1 | 4.5:1 | pass |
| Envelope label on envelope fill | #0F172A on #DBEAFE | 14.63:1 | 4.5:1 | pass |

## Meaning never carried by colour alone

| Meaning | Colour | Also shown by |
|---|---|---|
| Setback conflict | Red | Diagonal hatch pattern, "short" label with metres, warning-triangle icon, the words "Setback conflict found" |
| No conflict | Green | Check icon and the exact result sentence |
| Amendment | Orange | Info icon, heading "Potentially relevant amendment" |
| Derived figure | None | The text "derived, not prescribed by the Rules" |

## Print

Black on white. Envelope fill removed; hatching kept. Intake, buttons and disclosures hidden. One A4 page.
