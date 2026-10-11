import type { Figure } from '../../api/schemas';
import { useStrings } from '../../i18n/useStrings';
import { FigureValue } from './FigureCard';

/** Cases for a figure that depends on an input the clerk has not given (FR-16). */
export function ConditionalCases({ cases }: { cases: Figure[] }) {
  const { s, fmt } = useStrings();
  return (
    <div className="mt-1">
      <p className="text-xs font-semibold text-info-text">{s.result.conditional}</p>
      <ul className="mt-1 grid grid-cols-3 gap-2">
        {cases.map((c) => (
          <li key={`${c.label}-${c.rule}`} className="flex items-baseline justify-between gap-2 rounded-sm bg-muted px-2 py-1">
            <span className="text-xs leading-snug text-muted-foreground">
              {c.label}
              <span className="block">{fmt(s.result.rulePage, { rule: c.rule, page: c.page })}</span>
            </span>
            <FigureValue figure={c} size="body" />
          </li>
        ))}
      </ul>
    </div>
  );
}
