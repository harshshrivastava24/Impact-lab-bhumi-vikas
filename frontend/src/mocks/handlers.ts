import { delay, http, HttpResponse } from 'msw';
import type { Citation, LookupRequest, LookupResponse, PlanCheckRequest, PlanCheckResponse, Topic } from '../api/schemas';
import lookupAEnJson from './fixtures/lookup_appendix_a_en.json';
import lookupAHiJson from './fixtures/lookup_appendix_a_hi.json';
import lookupNarrowJson from './fixtures/lookup_narrow_street.json';
import lookupNotFoundJson from './fixtures/lookup_not_found.json';
import lookupTypeWarningJson from './fixtures/lookup_type_warning.json';
import parseAEn from './fixtures/parse_appendix_a_en.json';
import parseEmpty from './fixtures/parse_empty.json';
import parseQ14Hi from './fixtures/parse_q14_hi.json';
import planH10Json from './fixtures/plan_a5_h10.json';
import planH105Json from './fixtures/plan_a5_h10_5.json';
import planBlockedJson from './fixtures/plan_blocked_area.json';
import planRefusedJson from './fixtures/plan_refused_corner.json';

/*
 * Mock API for Phase 1. Fixtures are generated from the real corpus by
 * scripts/make_fixtures.py and hold the SRS Appendix A and A.5 figures.
 * The mock never computes a rule figure: inputs that match no fixture get a
 * 501 so the UI shows an error card instead of an invented number.
 */

type Tagged<T> = T & { _topics?: string[] };

// JSON imports are typed loosely; tests/fixtures.test.ts validates every
// fixture against the Zod schemas, so these casts cannot hide a bad fixture.
const lookupAEn = lookupAEnJson as unknown as LookupResponse;
const lookupAHi = lookupAHiJson as unknown as LookupResponse;
const lookupNarrow = lookupNarrowJson as unknown as LookupResponse;
const lookupNotFound = lookupNotFoundJson as unknown as LookupResponse;
const lookupTypeWarning = lookupTypeWarningJson as unknown as LookupResponse;
const planH10 = planH10Json as unknown as PlanCheckResponse;
const planH105 = planH105Json as unknown as PlanCheckResponse;
const planBlocked = planBlockedJson as unknown as PlanCheckResponse;
const planRefused = planRefusedJson as unknown as PlanCheckResponse;

/** Delay applied to every response so loading states are visible. Tests set it to 0. */
export const mockConfig = { delayMs: 150 };

const noFixture = (what: string) =>
  HttpResponse.json(
    { detail: `Demo mode has no fixture for these ${what}. Try the worked example: plot 200 sq m, road 9 m, residential, built-up 250 sq m.` },
    { status: 501 },
  );

function untag(c: Tagged<Citation>): Citation {
  const rest: Tagged<Citation> = { ...c };
  delete rest._topics;
  return rest;
}

function filterByTopics<T extends LookupResponse>(fixture: T, topics: Topic[]): T {
  const wanted = new Set<string>(topics);
  const figures = fixture.figures.filter((f) => wanted.has(f.topic));
  const citations = (fixture.citations as Tagged<Citation>[])
    .filter((c) => !c._topics || c._topics.some((t) => wanted.has(t)))
    .map(untag);
  return { ...fixture, figures, citations };
}

function stripTags<T extends { citations: Citation[] }>(fixture: T): T {
  return {
    ...fixture,
    citations: (fixture.citations as Tagged<Citation>[]).map(untag),
  };
}

const PLAN_FOOTPRINT = { front: 2.4, rear: 2.5, left: 2.5, right: 0 };

export const handlers = [
  http.post('/api/parse', async ({ request }) => {
    await delay(mockConfig.delayMs);
    const { text } = (await request.json()) as { text: string };
    if (/[ऀ-ॿ]/.test(text) && /200/.test(text) && /9/.test(text)) return HttpResponse.json(parseQ14Hi);
    if (/200/.test(text) && /\b9\s*m/i.test(text)) return HttpResponse.json(parseAEn);
    return HttpResponse.json({ ...parseEmpty, language: /[ऀ-ॿ]/.test(text) ? 'hi' : 'en' });
  }),

  http.post('/api/lookup', async ({ request }) => {
    await delay(mockConfig.delayMs);
    const req = (await request.json()) as LookupRequest;
    const p = req.params;

    if (req.topics.length === 0 && req.query_text) return HttpResponse.json(lookupNotFound);

    if (p.road_width !== undefined && p.road_width < 6 && p.existing_developed_area === true) {
      return HttpResponse.json(filterByTopics(lookupNarrow, req.topics));
    }
    if (p.development_type === 'semi_detached' && p.frontage === 14) {
      return HttpResponse.json(filterByTopics(lookupTypeWarning, req.topics));
    }
    if (p.plot_area === 200 && p.road_width === 9 && p.use_type === 'residential') {
      const fixture = req.language === 'hi' ? lookupAHi : lookupAEn;
      return HttpResponse.json(filterByTopics(fixture, req.topics));
    }
    return noFixture('inputs');
  }),

  http.post('/api/plan-check', async ({ request }) => {
    await delay(mockConfig.delayMs);
    const req = (await request.json()) as PlanCheckRequest;
    const p = req.params;

    if (p.streets_abutting === 2) return HttpResponse.json(planRefused);

    const dimsArea = (p.frontage ?? 0) * (p.depth ?? 0);
    if (req.resolution !== 'use_dimensions' && p.plot_area > 0 && Math.abs(dimsArea - p.plot_area) / p.plot_area > 0.02) {
      return HttpResponse.json(planBlocked);
    }

    const fp = req.footprint;
    const matchesA5 =
      p.frontage === 10 &&
      p.depth === 20 &&
      p.road_width === 9 &&
      p.development_type === 'semi_detached' &&
      fp.front === PLAN_FOOTPRINT.front &&
      fp.rear === PLAN_FOOTPRINT.rear &&
      fp.left === PLAN_FOOTPRINT.left &&
      fp.right === PLAN_FOOTPRINT.right;
    if (matchesA5 && p.height !== undefined && p.height <= 10) return HttpResponse.json(stripTags(planH10));
    if (matchesA5 && p.height !== undefined && p.height > 10 && p.height <= 12.5) return HttpResponse.json(stripTags(planH105));
    return noFixture('plan check inputs');
  }),
];
