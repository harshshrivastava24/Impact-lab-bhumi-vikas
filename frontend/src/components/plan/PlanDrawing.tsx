import { useId } from 'react';
import type { Geometry, PlanException, Side } from '../../api/schemas';
import { useStrings } from '../../i18n/useStrings';
import { fixed2 } from '../../lib/format';
import {
  computeLayout,
  placeCallouts,
  scaleBarMetres,
  splitLabel,
  toSvgRect,
  toSvgX,
  toSvgY,
  type Box,
  type Callout,
} from '../../lib/geometry';

const LINE_H = 15;
const LABEL_GAP = 8;

interface CalloutData {
  lines: string[];
  anchorX: number;
  tone: 'setback' | 'conflict' | 'footprint';
}

/**
 * FR-41 to FR-45: to-scale plot drawing. Every number shown comes from the API
 * geometry; this component only positions it. Road at the bottom.
 */
export function PlanDrawing({
  geometry,
  roadWidth,
  marks,
  exceptions,
  compact = false,
}: {
  geometry: Geometry;
  roadWidth: number | undefined;
  marks: Partial<Record<Side, string>>;
  exceptions: PlanException[];
  compact?: boolean;
}) {
  const { s, fmt } = useStrings();
  const uid = useId().replace(/:/g, '');
  const hatchId = `hatch-${uid}`;
  const { plot, required: req, envelope, footprint, overlaps } = geometry;
  const layout = computeLayout(plot.width, plot.depth);
  const P = layout.plot;
  const rect = (r: { x: number; y: number; width: number; depth: number }): Box => toSvgRect(layout, plot.depth, r);
  const sideName = (side: Side) => s.sides[side];

  const env = rect(envelope);
  const fp = rect(footprint);
  const frontY = toSvgY(layout, plot.depth, req.front.value);
  const rearY = toSvgY(layout, plot.depth, plot.depth - req.rear.value);
  const leftX = toSvgX(layout, req.left.value);
  const rightX = toSvgX(layout, plot.width - req.right.value);
  const rightEdge = P.x + P.width;

  const label = (side: Side) =>
    fmt(s.plan.setbackLabel, { side: sideName(side), value: fixed2(req[side].value), rule: req[side].rule });

  const callouts: Callout<CalloutData>[] = [
    { anchorY: frontY, data: { lines: splitLabel(label('front')), anchorX: rightEdge, tone: 'setback' as const } },
    { anchorY: rearY, data: { lines: splitLabel(label('rear')), anchorX: rightEdge, tone: 'setback' as const } },
    {
      anchorY: fp.y,
      data: {
        lines: splitLabel(fmt(s.plan.footprint, { w: fixed2(footprint.width), d: fixed2(footprint.depth), a: fixed2(footprint.area) })),
        anchorX: Math.min(fp.x + fp.width, rightEdge),
        tone: 'footprint' as const,
      },
    },
    ...overlaps.map((o) => {
      const r = rect(o);
      const exId = marks[o.side];
      const ex = exceptions.find((e) => e.id === exId);
      const lines = splitLabel(
        fmt(s.plan.short, { value: fixed2(o.shortfall), rule: req[o.side].rule, page: req[o.side].page }),
      );
      if (ex) lines.push(...splitLabel(fmt(s.plan.exceptionNote, { rule: ex.rule })));
      return { anchorY: r.y + r.height / 2, data: { lines, anchorX: r.x + r.width, tone: 'conflict' as const } };
    }),
  ].map((c) => ({ ...c, size: c.data.lines.length * LINE_H + LABEL_GAP }));

  const placed = placeCallouts(callouts, 2 * LINE_H, P.y - 8, P.y + P.height + 24);
  const labelX = rightEdge + 28;

  const barM = scaleBarMetres(plot.width, plot.depth);
  const barPx = barM * layout.scale;
  const barY = layout.roadBand.y + layout.roadBand.height + 30;

  // Three short lines so the label fits inside narrow envelopes.
  const envLines = [
    s.plan.legendEnvelope,
    `${fixed2(envelope.width)} x ${fixed2(envelope.depth)} ${s.fields.m}`,
    `${fixed2(envelope.area)} ${s.fields.sqm}`,
  ];
  const envLabelFits = env.width > 96 && env.height > envLines.length * LINE_H + 12;

  const summary = fmt(s.plan.drawingSummary, {
    w: fixed2(plot.width),
    d: fixed2(plot.depth),
    ew: fixed2(envelope.width),
    ed: fixed2(envelope.depth),
    fw: fixed2(footprint.width),
    fd: fixed2(footprint.depth),
    result: geometry.result,
  });

  const toneClass = { setback: 'fill-info-text', conflict: 'fill-conflict-text', footprint: 'fill-foreground' } as const;

  return (
    <svg
      role="img"
      aria-label={summary}
      viewBox={`0 0 ${layout.svgWidth} ${layout.svgHeight}`}
      width={layout.svgWidth}
      height={layout.svgHeight}
      className={`block h-auto max-w-full text-[12px] ${compact ? 'max-h-[300px] w-auto' : ''}`}
      fontFamily="inherit"
    >
      <title>{summary}</title>
      <defs>
        <pattern id={hatchId} width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
          <rect width="8" height="8" className="fill-conflict-tint" />
          <line x1="0" y1="0" x2="0" y2="8" className="stroke-conflict" strokeWidth="3" />
        </pattern>
      </defs>

      {/* Road band and labels */}
      <rect {...boxAttrs(layout.roadBand)} className="fill-road" />
      <text x={P.x + P.width / 2} y={layout.roadBand.y + 20} textAnchor="middle" className="fill-foreground font-semibold">
        {roadWidth !== undefined ? `${s.plan.road} ${fixed2(roadWidth)} ${s.fields.m}` : s.plan.road}
      </text>

      {/* Plot boundary with width and depth */}
      <rect {...boxAttrs(P)} className="fill-card stroke-foreground" strokeWidth="2" />
      <text x={P.x + P.width / 2} y={layout.roadBand.y + layout.roadBand.height + 14} textAnchor="middle" className="fill-muted-foreground">
        {fmt(s.plan.plotWidth, { w: fixed2(plot.width) })}
      </text>
      <text
        x={P.x - 14}
        y={P.y + P.height / 2}
        textAnchor="middle"
        transform={`rotate(-90 ${P.x - 14} ${P.y + P.height / 2})`}
        className="fill-muted-foreground"
      >
        {fmt(s.plan.plotDepth, { d: fixed2(plot.depth) })}
      </text>

      {/* Buildable envelope */}
      <rect {...boxAttrs(env)} className="envelope-fill fill-envelope" />
      {envLabelFits
        ? envLines.map((line, i) => (
            <text
              key={line}
              x={env.x + env.width / 2}
              y={env.y + env.height / 2 + (i - (envLines.length - 1) / 2) * LINE_H}
              textAnchor="middle"
              dominantBaseline="middle"
              className="fill-foreground font-semibold"
            >
              {line}
            </text>
          ))
        : null}

      {/* Setback lines */}
      <line x1={P.x} x2={rightEdge} y1={frontY} y2={frontY} className="stroke-setback" strokeWidth="1.5" strokeDasharray="6 4" />
      <line x1={P.x} x2={rightEdge} y1={rearY} y2={rearY} className="stroke-setback" strokeWidth="1.5" strokeDasharray="6 4" />
      <line x1={leftX} x2={leftX} y1={P.y} y2={P.y + P.height} className="stroke-setback" strokeWidth="1.5" strokeDasharray="6 4" />
      <line x1={rightX} x2={rightX} y1={P.y} y2={P.y + P.height} className="stroke-setback" strokeWidth="1.5" strokeDasharray="6 4" />

      {/* Side setback labels in two rows above the plot so they never collide */}
      <text x={clamp(leftX, P.x, rightEdge)} y={P.y - 30} textAnchor="middle" className="fill-info-text font-semibold">
        {label('left')}
      </text>
      <text x={clamp(rightX, P.x, rightEdge)} y={P.y - 12} textAnchor="middle" className="fill-info-text font-semibold">
        {label('right')}
      </text>

      {/* Overlaps: hatch pattern plus stroke, never colour alone */}
      {overlaps.map((o) => (
        <rect key={o.side} {...boxAttrs(rect(o))} fill={`url(#${hatchId})`} className="stroke-conflict" strokeWidth="1.5" />
      ))}

      {/* Proposed footprint outline */}
      <rect {...boxAttrs(fp)} fill="none" className="stroke-foreground" strokeWidth="2.5" />

      {/* Callouts with leader lines */}
      {placed.map((c) => (
        <g key={c.data.lines.join('|')}>
          <polyline
            points={`${c.data.anchorX},${c.anchorY} ${rightEdge + 12},${c.anchorY} ${labelX - 4},${c.labelY - 4}`}
            fill="none"
            className={c.data.tone === 'conflict' ? 'stroke-conflict' : 'stroke-muted-foreground'}
            strokeWidth="1"
          />
          {c.data.lines.map((line, i) => (
            <text
              key={line}
              x={labelX}
              y={c.labelY + i * LINE_H}
              className={`${toneClass[c.data.tone]} ${c.data.tone === 'conflict' ? 'font-bold' : 'font-semibold'}`}
            >
              {line}
            </text>
          ))}
        </g>
      ))}

      {/* Scale bar */}
      <g aria-hidden="true">
        <line x1={P.x} x2={P.x + barPx} y1={barY} y2={barY} className="stroke-foreground" strokeWidth="2" />
        <line x1={P.x} x2={P.x} y1={barY - 5} y2={barY + 5} className="stroke-foreground" strokeWidth="2" />
        <line x1={P.x + barPx} x2={P.x + barPx} y1={barY - 5} y2={barY + 5} className="stroke-foreground" strokeWidth="2" />
        <text x={P.x + barPx + 8} y={barY + 4} className="fill-foreground">
          {fmt(s.plan.scale, { n: barM })}
        </text>
      </g>
    </svg>
  );
}

function boxAttrs(b: Box) {
  return { x: b.x, y: b.y, width: Math.max(b.width, 0), height: Math.max(b.height, 0) };
}

function clamp(v: number, min: number, max: number) {
  return Math.min(Math.max(v, min + 40), max - 40);
}
