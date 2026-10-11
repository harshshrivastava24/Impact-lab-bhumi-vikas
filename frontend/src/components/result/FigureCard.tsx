import { TriangleAlert } from 'lucide-react';
import { pdfUrl } from '../../api/client';
import type { Figure } from '../../api/schemas';
import { useStrings } from '../../i18n/useStrings';
import { formatValue, unitLabel } from '../../lib/format';
import { ConditionalCases } from './ConditionalCases';

export function FigureValue({ figure, size = 'figure' }: { figure: Figure; size?: 'figure' | 'body' }) {
  const { s } = useStrings();
  if (figure.value === null) return <span className="text-body text-muted-foreground">{s.result.noValue}</span>;
  const unit = unitLabel(figure.unit, s);
  return (
    <span className={`tabular font-bold text-foreground ${size === 'figure' ? 'text-figure' : 'text-body'}`}>
      {formatValue(figure.value, figure.unit)}
      {unit ? <span className="ml-1 text-body font-semibold text-muted-foreground">{unit}</span> : null}
    </span>
  );
}

/** One computed figure with its rule, page and calculation trace (FR-22, FR-47). */
export function FigureCard({ figure, index }: { figure: Figure; index: number }) {
  const { s, fmt } = useStrings();
  const traceId = `trace-${index}`;
  return (
    <article
      aria-labelledby={`fig-${index}`}
      className={`flex flex-col rounded-md border border-border bg-card p-3 shadow-card ${
        figure.conditional ? 'col-span-2 xl:col-span-4' : ''
      } ${figure.warning ? 'border-l-4 border-l-warning' : ''}`}
    >
      <h3 id={`fig-${index}`} className="text-label font-semibold text-muted-foreground">
        {figure.label}
      </h3>
      <p className="mt-0.5">
        <FigureValue figure={figure} />
      </p>
      {figure.derived ? <p className="text-xs font-semibold text-info-text">{s.result.derived}</p> : null}
      {figure.conditional && figure.cases?.length ? <ConditionalCases cases={figure.cases} /> : null}
      {figure.warning ? (
        <p className="mt-1 flex gap-1.5 text-xs text-warning-text">
          <TriangleAlert aria-hidden="true" className="mt-0.5 size-3.5 shrink-0" />
          <span>
            <strong>{s.result.warning}</strong>
            {': '}
            {figure.warning}
          </span>
        </p>
      ) : null}
      <div className="mt-auto flex flex-wrap items-baseline gap-x-3 pt-1.5">
        <a
          href={pdfUrl('en', figure.page)}
          target="_blank"
          rel="noopener noreferrer"
          className="text-label font-semibold text-accent underline-offset-2 hover:underline"
        >
          {fmt(s.result.rulePage, { rule: figure.rule, page: figure.page })}
        </a>
        <details className="group text-label">
          <summary className="text-accent marker:text-accent">{s.result.showTrace}</summary>
          <p id={traceId} className="mt-1 text-xs text-foreground">
            {figure.trace}
          </p>
        </details>
      </div>
    </article>
  );
}
