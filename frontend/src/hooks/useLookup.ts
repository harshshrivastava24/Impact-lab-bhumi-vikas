import { useCallback, useRef, useState } from 'react';
import { ApiError, api } from '../api/client';
import type {
  Citation,
  Geometry,
  LookupRequest,
  LookupResponse,
  PlanCheckRequest,
  PlanCheckResponse,
} from '../api/schemas';
import { diffRequired, type SideChange } from './usePlanCheck';

/** What the result panel renders: a lookup response, optionally with plan geometry. */
export type ResultView = LookupResponse & { geometry?: Geometry };

export type ResultState =
  | { phase: 'idle' }
  | { phase: 'loading' }
  | { phase: 'done'; view: ResultView; sideChanges: SideChange[] }
  | { phase: 'error'; error: ApiError };

type LastAction =
  | { kind: 'lookup'; req: LookupRequest }
  | { kind: 'plan'; plan: PlanCheckRequest; lookup: LookupRequest | null; fromHeightEdit: boolean };

const citationKey = (c: Citation) => `${c.rule}|${c.sub_rule ?? ''}`;

/**
 * Merge a plan check with a lookup of the other selected topics. A plan check
 * that is blocked or refused is shown on its own so the clerk fixes it first.
 */
export function mergeResults(plan: PlanCheckResponse, lookup: LookupResponse | null): ResultView {
  if (plan.status !== 'answered' || !lookup) return plan;
  if (lookup.status !== 'answered') return { ...lookup, geometry: plan.geometry };
  const seen = new Set<string>();
  // Plan citations first: the drawing and the printed slip are about setbacks.
  const citations = [...plan.citations, ...lookup.citations].filter((c) => {
    const key = citationKey(c);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
  const flagSeen = new Set<string>();
  const amendment_flags = [...lookup.amendment_flags, ...plan.amendment_flags].filter((f) => {
    const key = `${f.date}|${f.rule}`;
    if (flagSeen.has(key)) return false;
    flagSeen.add(key);
    return true;
  });
  return {
    ...lookup,
    figures: [...lookup.figures, ...plan.figures],
    citations,
    amendment_flags,
    used_inference: lookup.used_inference || plan.used_inference,
    geometry: plan.geometry,
  };
}

function toApiError(err: unknown): ApiError {
  return err instanceof ApiError ? err : new ApiError('network', err instanceof Error ? err.message : String(err));
}

export function useLookup() {
  const [state, setState] = useState<ResultState>({ phase: 'idle' });
  const seq = useRef(0);
  const last = useRef<LastAction | null>(null);
  const lastGeometry = useRef<Geometry | undefined>(undefined);

  const run = useCallback(async (action: LastAction) => {
    last.current = action;
    const id = ++seq.current;
    setState({ phase: 'loading' });
    try {
      let view: ResultView;
      let sideChanges: SideChange[] = [];
      if (action.kind === 'lookup') {
        view = await api.lookup(action.req);
      } else {
        const [planResult, lookupResult] = await Promise.allSettled([
          api.planCheck(action.plan),
          action.lookup ? api.lookup(action.lookup) : Promise.resolve(null),
        ]);
        if (planResult.status === 'rejected') throw planResult.reason;
        const plan = planResult.value;
        // A blocked or refused plan check must reach the clerk even if the
        // accompanying lookup failed; otherwise the lookup error decides.
        if (plan.status !== 'answered') view = plan;
        else if (lookupResult.status === 'rejected') throw lookupResult.reason;
        else view = mergeResults(plan, lookupResult.value);
        if (action.fromHeightEdit) sideChanges = diffRequired(lastGeometry.current, view.geometry);
      }
      if (id !== seq.current) return;
      lastGeometry.current = view.geometry;
      setState({ phase: 'done', view, sideChanges });
    } catch (err) {
      if (id === seq.current) setState({ phase: 'error', error: toApiError(err) });
    }
  }, []);

  const runLookup = useCallback((req: LookupRequest) => run({ kind: 'lookup', req }), [run]);
  const runPlan = useCallback(
    (plan: PlanCheckRequest, lookup: LookupRequest | null, fromHeightEdit = false) =>
      run({ kind: 'plan', plan, lookup, fromHeightEdit }),
    [run],
  );
  const retry = useCallback(() => {
    if (last.current) void run(last.current);
  }, [run]);

  return { state, runLookup, runPlan, retry };
}
