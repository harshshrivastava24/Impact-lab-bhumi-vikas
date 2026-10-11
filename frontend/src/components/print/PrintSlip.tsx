import type { Params, Side } from '../../api/schemas';
import type { ResultView } from '../../hooks/useLookup';
import { useStrings } from '../../i18n/useStrings';
import { formatValue, unitLabel } from '../../lib/format';
import { PlanDrawing } from '../plan/PlanDrawing';
import { SideTable } from '../plan/SideTable';

/**
 * FR-33, FR-49: one A4 page. Hidden on screen; printed instead of the
 * interactive panels. PDF references are printed as page numbers.
 */
export function PrintSlip({
  view,
  params,
  marks,
}: {
  view: ResultView;
  params: Partial<Params> | undefined;
  marks: Partial<Record<Side, string>>;
}) {
  const { s, fmt } = useStrings();
  if (view.status !== 'answered') return null;
  const first = view.citations[0];
  const g = view.geometry;
  const inputs: [string, string][] = [];
  if (params?.plot_area !== undefined) inputs.push([s.fields.plot_area, `${params.plot_area} ${s.fields.sqm}`]);
  if (params?.road_width !== undefined) inputs.push([s.fields.road_width, `${params.road_width} ${s.fields.m}`]);
  if (params?.use_type) inputs.push([s.fields.use_type, s.useTypes[params.use_type]]);
  if (params?.built_up_area !== undefined) inputs.push([s.fields.built_up_area, `${params.built_up_area} ${s.fields.sqm}`]);
  if (params?.height !== undefined) inputs.push([s.fields.height, `${params.height} ${s.fields.m}`]);
  if (params?.development_type) inputs.push([s.fields.development_type, s.developmentTypes[params.development_type]]);

  return (
    // aria-hidden: on screen the slip is display:none; this also keeps screen readers
    // from reading the result twice if styles fail to load.
    <div aria-hidden="true" className="print-only print-slip text-[10pt] leading-snug">
      <h1 className="text-[14pt] font-bold">{`${s.app.title} · ${s.print.title}`}</h1>
      <p>{view.version.label}</p>

      <section className="mt-2">
        <h2 className="font-bold">{s.print.inputs}</h2>
        <p>{inputs.map(([k, v]) => `${k}: ${v}`).join(' · ')}</p>
      </section>

      <section className="mt-2">
        <h2 className="font-bold">{s.print.figures}</h2>
        <table className="w-full border-collapse">
          <tbody>
            {view.figures.map((f) => (
              <tr key={`${f.topic}-${f.label}`} className="border-b border-black/30">
                <th scope="row" className="py-0.5 pr-2 text-left font-normal">{f.label}</th>
                <td className="py-0.5 pr-2 font-bold tabular">
                  {f.value === null
                    ? (f.cases ?? []).map((c) => `${c.label}: ${formatValue(c.value ?? 0, c.unit)} ${unitLabel(c.unit, s)}`).join('; ')
                    : `${formatValue(f.value, f.unit)} ${unitLabel(f.unit, s)}`}
                  {f.derived ? ` (${s.result.derived})` : ''}
                </td>
                <td className="py-0.5">{fmt(s.result.rulePage, { rule: f.rule, page: f.page })}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {g ? (
        <section className="mt-2 flex gap-3">
          <div className="w-[55%]">
            <PlanDrawing geometry={g} roadWidth={params?.road_width} marks={marks} exceptions={g.exceptions_available} compact />
          </div>
          <div className="flex-1">
            <p className="font-bold">{g.result}</p>
            <SideTable sides={g.sides} />
            <p className="mt-1">{g.not_checked}</p>
          </div>
        </section>
      ) : null}

      {first ? (
        <section className="mt-2">
          <h2 className="font-bold">{`${s.print.citation}: ${first.rule}${first.sub_rule ?? ''} · ${fmt(s.print.pdfRef, { page: first.page_start })}`}</h2>
          <pre className="font-mono text-[8pt] whitespace-pre-wrap">{first.sub_rule_text_en ?? first.text_en}</pre>
        </section>
      ) : null}

      {view.amendment_flags.map((f) => (
        <p key={`${f.date}-${f.rule}`} className="mt-2 border border-black p-1">
          {`${s.amendment.heading}: ${f.date}, ${s.amendment.rule} ${f.rule}. ${f.concerns} ${f.note}`}
        </p>
      ))}

      <p className="mt-2 border-t border-black pt-1 font-bold">{view.disclaimer}</p>
    </div>
  );
}
