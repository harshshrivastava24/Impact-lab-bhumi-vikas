import type { Strings } from '../i18n/strings';

const grouping = new Intl.NumberFormat('en-IN', { maximumFractionDigits: 0 });

/** Distances and areas: always two decimals (NFR-23). Western digits in both languages. */
export function fixed2(n: number): string {
  return n.toFixed(2);
}

/**
 * Format a figure value for display. Numbers are never rounded beyond what the
 * API returned except to the fixed display precision for each unit.
 */
export function formatValue(value: number, unit: string): string {
  switch (unit) {
    case 'Rs':
      return `₹ ${grouping.format(value)}`;
    case 'm':
    case 'sq m':
      return fixed2(value);
    case '%':
      return value.toFixed(1);
    default:
      return String(value);
  }
}

/** Localised unit suffix shown after a value. Currency is a prefix, so it has none. */
export function unitLabel(unit: string, s: Strings): string {
  switch (unit) {
    case 'm':
      return s.fields.m;
    case 'sq m':
      return s.fields.sqm;
    case 'Rs':
      return '';
    default:
      return unit;
  }
}

/** Parse a form string into a number, or undefined when empty. NaN marks invalid input. */
export function toNumber(raw: string | undefined): number | undefined {
  if (raw === undefined) return undefined;
  const trimmed = raw.trim();
  if (trimmed === '') return undefined;
  if (!/^-?\d+(\.\d+)?$/.test(trimmed)) return Number.NaN;
  return Number(trimmed);
}
