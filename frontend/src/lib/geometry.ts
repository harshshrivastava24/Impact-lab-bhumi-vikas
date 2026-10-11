/*
 * Pure layout helpers for the plan drawing. No arithmetic here produces a rule
 * figure: all distances and areas come from the API. These functions only map
 * metres to SVG pixels and keep labels apart.
 *
 * API coordinates: origin at the plot's front-left corner, x to the right along
 * the road, y into the plot away from the road. The SVG flips y so the road is
 * at the bottom.
 */

export interface Box {
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface DrawingLayout {
  scale: number;
  plot: Box;
  svgWidth: number;
  svgHeight: number;
  margins: { left: number; right: number; top: number; bottom: number };
  roadBand: Box;
}

export const MARGINS = { left: 56, right: 236, top: 64, bottom: 76 };
export const ROAD_BAND = 30;
export const MAX_PLOT_PX = { width: 380, height: 380 };

/** One scale factor fitting the plot into the drawing area. */
export function computeLayout(plotWidthM: number, plotDepthM: number, maxPx = MAX_PLOT_PX): DrawingLayout {
  if (plotWidthM <= 0 || plotDepthM <= 0) throw new Error('Plot dimensions must be positive');
  const scale = Math.min(maxPx.width / plotWidthM, maxPx.height / plotDepthM);
  const w = plotWidthM * scale;
  const h = plotDepthM * scale;
  const plot = { x: MARGINS.left, y: MARGINS.top, width: w, height: h };
  return {
    scale,
    plot,
    margins: MARGINS,
    svgWidth: MARGINS.left + w + MARGINS.right,
    svgHeight: MARGINS.top + h + MARGINS.bottom,
    roadBand: { x: MARGINS.left - 16, y: MARGINS.top + h, width: w + 32, height: ROAD_BAND },
  };
}

/** Map an API rectangle (metres, y from the road) to an SVG box (pixels, y down). */
export function toSvgRect(
  layout: DrawingLayout,
  plotDepthM: number,
  rect: { x: number; y: number; width: number; depth: number },
): Box {
  const { scale, plot } = layout;
  return {
    x: plot.x + rect.x * scale,
    y: plot.y + (plotDepthM - rect.y - rect.depth) * scale,
    width: rect.width * scale,
    height: rect.depth * scale,
  };
}

/** SVG y for a line at distance yM from the road edge. */
export function toSvgY(layout: DrawingLayout, plotDepthM: number, yM: number): number {
  return layout.plot.y + (plotDepthM - yM) * layout.scale;
}

/** SVG x for a line at distance xM from the left boundary. */
export function toSvgX(layout: DrawingLayout, xM: number): number {
  return layout.plot.x + xM * layout.scale;
}

export interface Callout<T = unknown> {
  anchorY: number;
  /** Height the label occupies in px (more for multi-line labels). */
  size?: number;
  data: T;
}

export interface PlacedCallout<T = unknown> extends Callout<T> {
  labelY: number;
}

/**
 * Place labels in a column so they never overlap: sort by anchor, push each
 * label down to clear the one above, then pull the column back up if it
 * overflows the bottom.
 */
export function placeCallouts<T>(items: Callout<T>[], minGap: number, top: number, bottom: number): PlacedCallout<T>[] {
  const sorted = [...items].sort((a, b) => a.anchorY - b.anchorY);
  const gapAfter = (c: Callout<T>) => Math.max(minGap, c.size ?? 0);
  const placed: PlacedCallout<T>[] = [];
  for (const item of sorted) {
    const prev = placed[placed.length - 1];
    const wanted = Math.max(item.anchorY, top);
    placed.push({ ...item, labelY: prev ? Math.max(wanted, prev.labelY + gapAfter(prev)) : wanted });
  }
  const last = placed[placed.length - 1];
  if (last && last.labelY > bottom) {
    last.labelY = bottom;
    for (let i = placed.length - 2; i >= 0; i--) {
      const current = placed[i];
      const next = placed[i + 1];
      if (current && next) current.labelY = Math.min(current.labelY, next.labelY - gapAfter(current));
    }
  }
  return placed;
}

/** Split a label at the last ", " before maxChars so it fits the callout column. */
export function splitLabel(text: string, maxChars = 30): string[] {
  if (text.length <= maxChars) return [text];
  const cut = text.lastIndexOf(', ', maxChars);
  if (cut <= 0) return [text];
  return [text.slice(0, cut + 1), ...splitLabel(text.slice(cut + 2), maxChars)];
}

/** Scale bar length in metres: 1 m for small plots, 5 m otherwise. */
export function scaleBarMetres(plotWidthM: number, plotDepthM: number): 1 | 5 {
  return Math.max(plotWidthM, plotDepthM) <= 15 ? 1 : 5;
}
