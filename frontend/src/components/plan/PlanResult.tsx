import { CircleCheck, Info, TriangleAlert } from 'lucide-react';
import type { Geometry } from '../../api/schemas';
import type { SideChange } from '../../hooks/usePlanCheck';
import { useStrings } from '../../i18n/useStrings';
import { fixed2 } from '../../lib/format';

/**
 * FR-46: the exact result sentence from the API, the checks performed and the
 * limitation statement. The UI adds no verdict words of its own.
 */
export function PlanResult({ geometry, sideChanges }: { geometry: Geometry; sideChanges: SideChange[] }) {
  const { s, fmt } = useStrings();
  const conflict = geometry.result_kind === 'conflict';
  return (
    <div className="flex flex-col gap-2">
      {sideChanges.map((c) => (
        <p key={c.side} role="status" className="flex items-start gap-2 rounded-sm border border-info bg-info-tint px-3 py-2 text-label text-info-text">
          <Info aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
          {fmt(s.plan.sideChanged, { side: s.sides[c.side], old: fixed2(c.from), new: fixed2(c.to) })}
        </p>
      ))}
      <p
        className={`flex items-center gap-2 rounded-sm border-2 px-3 py-2 text-body font-bold ${
          conflict ? 'border-conflict bg-conflict-tint text-conflict-text' : 'border-pass bg-pass-tint text-pass-text'
        }`}
      >
        {conflict ? <TriangleAlert aria-hidden="true" className="size-5 shrink-0" /> : <CircleCheck aria-hidden="true" className="size-5 shrink-0" />}
        {geometry.result}
      </p>
      <div className="text-label">
        <h4 className="font-semibold">{s.plan.checksHeading}</h4>
        <ul className="list-disc pl-5 text-muted-foreground">
          {geometry.checks_performed.map((c) => (
            <li key={c}>{c}</li>
          ))}
        </ul>
        <p className="mt-1 font-semibold">{geometry.not_checked}</p>
      </div>
    </div>
  );
}
