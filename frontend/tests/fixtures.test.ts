import { readdirSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';
import { LookupResponseSchema, ParseResponseSchema, PlanCheckResponseSchema, type Figure } from '../src/api/schemas';

const dir = resolve(__dirname, '../src/mocks/fixtures');
const load = (name: string): unknown => JSON.parse(readFileSync(resolve(dir, name), 'utf8'));
const files = readdirSync(dir).filter((f) => f.endsWith('.json'));

describe('every fixture matches the API contract', () => {
  it.each(files)('%s', (file) => {
    const schema = file.startsWith('parse_') ? ParseResponseSchema : file.startsWith('plan_') ? PlanCheckResponseSchema : LookupResponseSchema;
    const result = schema.safeParse(load(file));
    expect(result.success, result.success ? '' : JSON.stringify(result.error.issues)).toBe(true);
  });
});

describe('fixture figures equal SRS Appendix A and A.5', () => {
  const a = LookupResponseSchema.parse(load('lookup_appendix_a_en.json'));
  const value = (label: string) => a.figures.find((f: Figure) => f.label === label)?.value;

  it('Appendix A', () => {
    expect(value('Front open space')).toBe(3.0);
    expect(value('Rear open space')).toBe(2.5);
    expect(value('Maximum height')).toBe(12.5);
    expect(value('Floor area ratio')).toBe(1.25);
    expect(value('Permitted floor area')).toBe(250);
    expect(value('Application fee')).toBe(250);
    expect(value('Permission fee')).toBe(3000);
    expect(a.citations[0]?.rule).toBe('56');
    expect(a.citations[0]?.sub_rule).toBe('(1)(a)');
    expect(a.citations[0]?.pdf_en_url).toBe('/pdf/en#page=77');
    expect(a.citations[0]?.sub_rule_text_en).toContain('Up to 9.0 meters');
  });

  it('A.5 at height 10', () => {
    const g = PlanCheckResponseSchema.parse(load('plan_a5_h10.json')).geometry;
    expect(g?.envelope).toMatchObject({ width: 7.5, depth: 14.5, area: 108.75 });
    expect(g?.footprint).toMatchObject({ width: 7.5, depth: 15.1, area: 113.25 });
    expect(g?.sides.find((s) => s.side === 'front')).toMatchObject({ required: 3, provided: 2.4, shortfall: 0.6, page: 77 });
    expect(g?.result).toBe('Setback conflict found');
    expect(g?.ground_coverage_derived).toBe(54.4);
  });

  it('A.5 at height 10.5 raises the left side to 3.0 m', () => {
    const g = PlanCheckResponseSchema.parse(load('plan_a5_h10_5.json')).geometry;
    expect(g?.required.left.value).toBe(3);
    expect(g?.sides.find((s) => s.side === 'left')?.shortfall).toBe(0.5);
  });

  it('narrow street uses Rule 56(1)(b)', () => {
    const n = LookupResponseSchema.parse(load('lookup_narrow_street.json'));
    expect(n.figures[0]).toMatchObject({ value: 3.5, rule: '56(1)(b)' });
  });

  it('not found carries no figures or citations', () => {
    const nf = LookupResponseSchema.parse(load('lookup_not_found.json'));
    expect(nf.status).toBe('not_found');
    expect(nf.figures).toHaveLength(0);
    expect(nf.citations).toHaveLength(0);
  });

  it('the amendment flag is process-only, secondary and not applied', () => {
    const flag = a.amendment_flags[0];
    expect(flag?.source_kind).toBe('secondary');
    expect(flag?.applied).toBe(false);
    expect(flag?.concerns).toMatch(/does not change the setback/);
  });
});
