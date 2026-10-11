import en from '../../../config/strings.en.json';
import hi from '../../../config/strings.hi.json';
import type { Language } from '../api/schemas';

/**
 * Interface strings live in config/strings.{en,hi}.json at the repo root
 * (NFR-11). Typing hi as Strings makes TypeScript fail the build if the two
 * files ever have different keys.
 */
export type Strings = typeof en;

const hiTyped: Strings = hi;

export const STRINGS: Record<Language, Strings> = { en, hi: hiTyped };

/** Replace {name} placeholders. Unknown placeholders are left visible on purpose. */
export function fmt(template: string, vars: Record<string, string | number> = {}): string {
  return template.replace(/\{(\w+)\}/g, (whole, key: string) =>
    key in vars ? String(vars[key]) : whole,
  );
}
