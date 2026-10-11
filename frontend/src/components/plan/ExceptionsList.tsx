import type { Overlap, PlanException, Side } from '../../api/schemas';
import { useStrings } from '../../i18n/useStrings';

/**
 * FR-45: the clerk may mark an exception on a conflicting side. Marking adds an
 * annotation in the drawing; the hatched conflict always stays.
 */
export function ExceptionsList({
  overlaps,
  exceptions,
  marks,
  onMark,
}: {
  overlaps: Overlap[];
  exceptions: PlanException[];
  marks: Partial<Record<Side, string>>;
  onMark: (side: Side, exceptionId: string) => void;
}) {
  const { s, fmt } = useStrings();
  if (!overlaps.length || !exceptions.length) return null;
  return (
    <fieldset className="rounded-md border border-border p-3">
      <legend className="px-1 text-label font-semibold">{s.plan.exceptionsHeading}</legend>
      <p className="text-xs text-muted-foreground">{s.plan.exceptionsHint}</p>
      <div className="mt-2 flex flex-wrap gap-4">
        {overlaps.map((o) => {
          const id = `exception-${o.side}`;
          return (
            <div key={o.side} className="min-w-52">
              <label htmlFor={id} className="block text-label font-semibold">
                {s.sides[o.side]}
              </label>
              <select
                id={id}
                value={marks[o.side] ?? ''}
                onChange={(e) => onMark(o.side, e.target.value)}
                className="mt-1 block min-h-10 w-full rounded-sm border border-input-border bg-card px-2 text-label text-foreground"
              >
                <option value="">{s.developmentTypes.none}</option>
                {exceptions.map((ex) => (
                  <option key={ex.id} value={ex.id}>
                    {`${ex.label} (${fmt(s.result.rulePage, { rule: ex.rule, page: ex.page })})`}
                  </option>
                ))}
              </select>
            </div>
          );
        })}
      </div>
    </fieldset>
  );
}
