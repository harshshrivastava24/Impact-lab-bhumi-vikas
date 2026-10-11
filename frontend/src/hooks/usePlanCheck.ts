import type { Geometry, Side } from '../api/schemas';

export interface SideChange {
  side: Side;
  from: number;
  to: number;
}

/**
 * Compare required open space between two plan-check responses (FR-44).
 * Used when a height edit re-sends the plan check: any side whose required
 * value changed produces a notice built from the two API values.
 */
export function diffRequired(prev: Geometry | undefined, next: Geometry | undefined): SideChange[] {
  if (!prev || !next) return [];
  const sides: Side[] = ['front', 'rear', 'left', 'right'];
  return sides
    .filter((side) => prev.required[side].value !== next.required[side].value)
    .map((side) => ({ side, from: prev.required[side].value, to: next.required[side].value }));
}
