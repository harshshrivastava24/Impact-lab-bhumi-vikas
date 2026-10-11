import { TriangleAlert } from 'lucide-react';
import { pdfUrl } from '../../api/client';
import type { SideRow } from '../../api/schemas';
import { useStrings } from '../../i18n/useStrings';
import { fixed2 } from '../../lib/format';

/** Required, provided and shortfall per side, with rule and page (FR-43, FR-47). */
export function SideTable({ sides }: { sides: SideRow[] }) {
  const { s, fmt } = useStrings();
  return (
    <table className="w-full border-collapse text-label tabular">
      <caption className="mb-1 text-left text-label font-semibold text-muted-foreground">{s.plan.tableCaption}</caption>
      <thead>
        <tr className="border-b-2 border-foreground text-left">
          <th scope="col" className="py-1 pr-2">{s.plan.colSide}</th>
          <th scope="col" className="py-1 pr-2 text-right">{s.plan.colRequired}</th>
          <th scope="col" className="py-1 pr-2 text-right">{s.plan.colProvided}</th>
          <th scope="col" className="py-1 pr-2 text-right">{s.plan.colShortfall}</th>
          <th scope="col" className="py-1">{s.plan.colRule}</th>
        </tr>
      </thead>
      <tbody>
        {sides.map((row) => {
          const short = row.shortfall > 0;
          return (
            <tr key={row.side} className={`border-b border-border ${short ? 'bg-conflict-tint font-semibold text-conflict-text' : ''}`}>
              <th scope="row" className="py-1.5 pr-2 text-left">
                <span className="inline-flex items-center gap-1">
                  {short ? <TriangleAlert aria-hidden="true" className="size-3.5" /> : null}
                  {s.sides[row.side]}
                </span>
              </th>
              <td className="py-1.5 pr-2 text-right">{`${fixed2(row.required)} ${s.fields.m}`}</td>
              <td className="py-1.5 pr-2 text-right">{`${fixed2(row.provided)} ${s.fields.m}`}</td>
              <td className="py-1.5 pr-2 text-right">{`${fixed2(row.shortfall)} ${s.fields.m}`}</td>
              <td className="py-1.5">
                <a href={pdfUrl('en', row.page)} target="_blank" rel="noopener noreferrer" className="text-accent underline-offset-2 hover:underline">
                  {fmt(s.result.rulePage, { rule: row.rule, page: row.page })}
                </a>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
