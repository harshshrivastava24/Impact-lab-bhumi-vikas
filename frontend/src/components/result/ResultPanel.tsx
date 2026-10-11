import { ClipboardList, Printer } from 'lucide-react';
import type { Side } from '../../api/schemas';
import type { ResultState } from '../../hooks/useLookup';
import { useStrings } from '../../i18n/useStrings';
import { ExceptionsList } from '../plan/ExceptionsList';
import { PlanDrawing } from '../plan/PlanDrawing';
import { PlanResult } from '../plan/PlanResult';
import { SideTable } from '../plan/SideTable';
import type { Figure } from '../../api/schemas';
import { AmendmentFlag, AmendmentNotice } from './AmendmentFlag';
import { CitationCard } from './CitationCard';
import { Disclaimer } from './Disclaimer';
import { FigureCard } from './FigureCard';
import { Blocked } from './states/Blocked';
import { ErrorCard } from './states/ErrorCard';
import { NotFound } from './states/NotFound';
import { Refused } from './states/Refused';

interface Props {
  state: ResultState;
  roadWidth: number | undefined;
  marks: Partial<Record<Side, string>>;
  onMark: (side: Side, id: string) => void;
  onRetry: () => void;
  onCorrect: () => void;
  onUseDimensions: () => void;
}

/** FR-32 order: figures, drawing, citations, version, amendment flag, disclaimer, PDF links. */
export function ResultPanel({ state, roadWidth, marks, onMark, onRetry, onCorrect, onUseDimensions }: Props) {
  const { s } = useStrings();

  return (
    <div className="screen-only mx-auto flex max-w-[1100px] flex-col gap-3 px-5 py-3">
      <div className="flex items-center justify-between gap-3">
        <h2 id="result-heading" tabIndex={-1} className="text-xl font-bold">
          {s.result.heading}
        </h2>
        {state.phase === 'done' && state.view.status === 'answered' ? (
          <button
            type="button"
            onClick={() => window.print()}
            className="inline-flex min-h-10 items-center gap-2 rounded-sm border border-input-border bg-card px-3 text-label font-semibold hover:bg-muted"
          >
            <Printer aria-hidden="true" className="size-4" />
            {s.actions.print}
          </button>
        ) : null}
      </div>

      {state.phase === 'idle' ? (
        <div className="rounded-md border border-dashed border-input-border bg-card px-5 py-8 text-center">
          <ClipboardList aria-hidden="true" className="mx-auto size-10 text-muted-foreground" />
          <h3 className="mt-2 text-lg font-bold">{s.result.emptyTitle}</h3>
          <p className="mx-auto mt-1 max-w-lg text-body text-muted-foreground">{s.result.emptyBody}</p>
        </div>
      ) : null}

      {state.phase === 'loading' ? (
        <p aria-busy="true" className="rounded-md border border-border bg-card px-5 py-6 text-body text-muted-foreground">
          {s.actions.lookingUp}
        </p>
      ) : null}

      {state.phase === 'error' ? <ErrorCard error={state.error} onRetry={onRetry} /> : null}

      {state.phase === 'done' ? <Done state={state} roadWidth={roadWidth} marks={marks} onMark={onMark} onCorrect={onCorrect} onUseDimensions={onUseDimensions} /> : null}
    </div>
  );
}

/**
 * Full-width conditional cards go after the single-value cards so the grid
 * stays compact. The API order is kept within each group.
 */
function orderForGrid(figures: Figure[]): Figure[] {
  return [...figures.filter((f) => !f.conditional), ...figures.filter((f) => f.conditional)];
}

function Done({
  state,
  roadWidth,
  marks,
  onMark,
  onCorrect,
  onUseDimensions,
}: Omit<Props, 'onRetry' | 'state'> & { state: Extract<ResultState, { phase: 'done' }> }) {
  const { s } = useStrings();
  const { view, sideChanges } = state;

  if (view.status === 'not_found') return <NotFound disclaimer={view.disclaimer} />;
  if (view.status === 'blocked')
    return (
      <Blocked
        message={view.message ?? ''}
        resolutions={view.resolutions ?? []}
        disclaimer={view.disclaimer}
        onCorrect={onCorrect}
        onUseDimensions={onUseDimensions}
      />
    );
  if (view.status === 'refused') return <Refused message={view.message ?? ''} disclaimer={view.disclaimer} />;

  const g = view.geometry;
  return (
    <>
      {view.figures.length ? (
        <section aria-labelledby="figures-heading">
          <h3 id="figures-heading" className="sr-only">
            {s.result.figuresHeading}
          </h3>
          <div className="grid grid-cols-2 gap-2 xl:grid-cols-4">
            {orderForGrid(view.figures).map((f, i) => (
              <FigureCard key={`${f.topic}-${f.label}`} figure={f} index={i} />
            ))}
          </div>
        </section>
      ) : null}

      {view.amendment_flags.length ? <AmendmentNotice count={view.amendment_flags.length} /> : null}

      {g ? (
        <section aria-labelledby="plan-heading" className="rounded-md border border-border bg-card p-3 shadow-card">
          <h3 id="plan-heading" className="mb-2 text-body font-bold">
            {s.plan.heading}
          </h3>
          <div className="flex flex-col gap-3 2xl:flex-row">
            <div className="overflow-x-auto">
              <PlanDrawing geometry={g} roadWidth={roadWidth} marks={marks} exceptions={g.exceptions_available} />
            </div>
            <div className="flex min-w-0 flex-1 flex-col gap-3">
              <PlanResult geometry={g} sideChanges={sideChanges} />
              <SideTable sides={g.sides} />
              <ExceptionsList overlaps={g.overlaps} exceptions={g.exceptions_available} marks={marks} onMark={onMark} />
            </div>
          </div>
        </section>
      ) : null}

      {view.citations.length ? (
        <section aria-labelledby="citations-heading" className="flex flex-col gap-2">
          <h3 id="citations-heading" className="sr-only">
            {s.result.citationsHeading}
          </h3>
          {view.citations.map((c, i) => (
            <CitationCard key={`${c.rule}${c.sub_rule ?? ''}`} citation={c} index={i} />
          ))}
        </section>
      ) : null}

      <p className="text-label text-muted-foreground">
        <span className="font-semibold">{s.result.versionHeading}</span>
        {': '}
        {view.version.label}
      </p>

      <div id="amendments" className="flex scroll-mt-4 flex-col gap-2">
        {view.amendment_flags.map((f) => (
          <AmendmentFlag key={`${f.date}-${f.rule}`} flag={f} />
        ))}
      </div>

      <Disclaimer text={view.disclaimer} />
    </>
  );
}
