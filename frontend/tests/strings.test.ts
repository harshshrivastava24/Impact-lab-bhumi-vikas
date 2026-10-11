import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { STRINGS, fmt } from '../src/i18n/strings';

type Tree = { [k: string]: string | boolean | Tree };

function keys(obj: Tree, prefix = ''): string[] {
  return Object.entries(obj).flatMap(([k, v]) =>
    typeof v === 'object' ? keys(v, `${prefix}${k}.`) : [`${prefix}${k}`],
  );
}

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const p = join(dir, name);
    return statSync(p).isDirectory() ? walk(p) : [p];
  });
}

describe('interface strings (NFR-11)', () => {
  it('English and Hindi have exactly the same keys', () => {
    expect(keys(STRINGS.hi as unknown as Tree).sort()).toEqual(keys(STRINGS.en as unknown as Tree).sort());
  });

  it('no string is empty', () => {
    for (const lang of ['en', 'hi'] as const) {
      const flat = keys(STRINGS[lang] as unknown as Tree);
      for (const k of flat) {
        const value = k.split('.').reduce<unknown>((o, part) => (o as Record<string, unknown>)[part], STRINGS[lang]);
        if (typeof value === 'string') expect(value.trim(), `${lang}:${k}`).not.toBe('');
      }
    }
  });

  it('the Hindi file is flagged for review by a Hindi-literate teammate', () => {
    expect(STRINGS.hi._meta._review).toBe(true);
  });

  it('fmt fills placeholders and leaves unknown ones visible', () => {
    expect(fmt('Rule {rule}, p. {page}', { rule: '56(1)(a)', page: 77 })).toBe('Rule 56(1)(a), p. 77');
    expect(fmt('{missing}')).toBe('{missing}');
  });
});

describe('forbidden words', () => {
  // Interface code and strings only. Mock fixtures are excluded because they
  // quote the Rules verbatim (for example "approved Development Plan").
  const sources = [
    ...walk(resolve(__dirname, '../src')).filter((f) => /\.(tsx?|css)$/.test(f)),
    resolve(__dirname, '../../config/strings.en.json'),
    resolve(__dirname, '../../config/strings.hi.json'),
  ];
  it.each(['chatbot', 'assistant', 'approved', 'compliant', 'sanctionable'])('"%s" appears nowhere in UI sources', (word) => {
    const hits = sources.filter((f) => new RegExp(`\\b${word}\\b`, 'i').test(readFileSync(f, 'utf8')));
    expect(hits).toEqual([]);
  });
});
