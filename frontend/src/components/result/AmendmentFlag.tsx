import { Info } from 'lucide-react';
import type { AmendmentFlag as Flag } from '../../api/schemas';
import { useStrings } from '../../i18n/useStrings';

/** FR-25: potentially relevant later amendment, never applied in the figures. */
export function AmendmentFlag({ flag }: { flag: Flag }) {
  const { s } = useStrings();
  return (
    <aside
      aria-labelledby={`amend-${flag.date}`}
      className="rounded-md border border-warning border-l-4 bg-warning-tint px-3 py-2 text-warning-text"
    >
      <h3 id={`amend-${flag.date}`} className="flex items-center gap-1.5 text-label font-bold">
        <Info aria-hidden="true" className="size-4 shrink-0" />
        {s.amendment.heading}
      </h3>
      <p className="mt-0.5 text-label">
        <span className="font-semibold">{s.amendment.date}</span>
        {': '}
        <span className="tabular">{flag.date}</span>
        {' · '}
        <span className="font-semibold">{s.amendment.rule}</span>
        {': '}
        {flag.rule}
        {' · '}
        <span className="font-semibold">{s.amendment.source}</span>
        {': '}
        <a href={flag.source_url} target="_blank" rel="noopener noreferrer" className="underline">
          {flag.source_kind === 'primary' ? s.amendment.primary : s.amendment.secondary}
        </a>
      </p>
      <p className="text-label">
        <span className="font-semibold">{s.amendment.concerns}</span>
        {': '}
        {flag.concerns}
      </p>
      <p className="text-label font-semibold">{flag.note}</p>
    </aside>
  );
}

/**
 * One-line notice placed right after the figures so a potentially relevant
 * amendment is visible without scrolling (FR-32). Details stay in the full flag.
 */
export function AmendmentNotice({ count }: { count: number }) {
  const { s } = useStrings();
  return (
    <a
      href="#amendments"
      className="flex items-center gap-2 rounded-sm border border-warning border-l-4 bg-warning-tint px-3 py-1.5 text-label font-semibold text-warning-text hover:underline"
    >
      <Info aria-hidden="true" className="size-4 shrink-0" />
      {count > 1 ? `${s.amendment.heading} (${count})` : s.amendment.heading}
      <span className="font-normal">{s.amendment.noticeTail}</span>
    </a>
  );
}
