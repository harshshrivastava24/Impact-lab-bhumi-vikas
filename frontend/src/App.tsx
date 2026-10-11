import { useRef, useState } from 'react';
import type { Params, Side } from './api/schemas';
import { LookupForm, type LookupFormHandle } from './components/intake/LookupForm';
import { Header } from './components/layout/Header';
import { TwoPane } from './components/layout/TwoPane';
import { PrintSlip } from './components/print/PrintSlip';
import { ResultPanel } from './components/result/ResultPanel';
import { useLookup } from './hooks/useLookup';
import { useStrings } from './i18n/useStrings';

const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true';

export function App() {
  const { s } = useStrings();
  const formRef = useRef<LookupFormHandle>(null);
  const { state, runLookup, runPlan, retry } = useLookup();
  const [params, setParams] = useState<Partial<Params> | undefined>(undefined);
  const [marks, setMarks] = useState<Partial<Record<Side, string>>>({});

  const live =
    state.phase === 'done'
      ? state.view.status === 'not_found'
        ? s.result.liveNotFound
        : state.view.status === 'blocked'
          ? s.result.liveBlocked
          : state.view.status === 'refused'
            ? s.result.liveRefused
            : s.result.liveReady
      : state.phase === 'error'
        ? s.result.liveError
        : '';

  const view = state.phase === 'done' ? state.view : undefined;

  return (
    <div className="flex h-screen flex-col">
      <a
        href="#result"
        className="screen-only sr-only z-50 bg-card px-3 py-2 text-accent focus:not-sr-only focus:absolute focus:top-2 focus:left-2"
      >
        {s.app.skipToResult}
      </a>
      <Header />
      {USE_MOCK ? (
        <p className="screen-only border-b border-warning bg-warning-tint px-5 py-1 text-label text-warning-text">
          {s.app.mockBanner}
        </p>
      ) : null}

      <TwoPane
        intakeLabel={s.intake.heading}
        intake={
          <LookupForm
            ref={formRef}
            busy={state.phase === 'loading'}
            planActive={Boolean(view?.geometry)}
            onLookup={(req) => {
              setParams(req.params);
              setMarks({});
              void runLookup(req);
            }}
            onPlan={(plan, lookup, fromHeightEdit) => {
              setParams(plan.params);
              if (!fromHeightEdit) setMarks({});
              void runPlan(plan, lookup, fromHeightEdit);
            }}
          />
        }
        result={
          <ResultPanel
            state={state}
            roadWidth={params?.road_width}
            marks={marks}
            onMark={(side, id) => setMarks((m) => ({ ...m, [side]: id || undefined }))}
            onRetry={retry}
            onCorrect={() => formRef.current?.focusField('plot_area')}
            onUseDimensions={() => formRef.current?.useDimensionsAsArea()}
          />
        }
      />

      {view ? <PrintSlip view={view} params={params} marks={marks} /> : null}

      <div aria-live="polite" role="status" className="sr-only">
        {live}
      </div>
    </div>
  );
}
