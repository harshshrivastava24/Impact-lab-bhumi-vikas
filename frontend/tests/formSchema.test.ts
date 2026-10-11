import { describe, expect, it } from 'vitest';
import { STRINGS } from '../src/i18n/strings';
import { EMPTY_FORM, applyParsed, makeFormSchema, toFootprint, toParams, type FormValues } from '../src/lib/formSchema';
import { formatValue, toNumber } from '../src/lib/format';

const s = STRINGS.en;
const errorPaths = (mode: 'lookup' | 'plan', v: Partial<FormValues>) => {
  const r = makeFormSchema(s, mode).safeParse({ ...EMPTY_FORM, ...v });
  return r.success ? [] : r.error.issues.map((i) => i.path.join('.'));
};

const appendixA: Partial<FormValues> = { plot_area: '200', road_width: '9', built_up_area: '250' };
const a5: Partial<FormValues> = {
  ...appendixA,
  height: '10',
  development_type: 'semi_detached',
  frontage: '10',
  depth: '20',
  fp_front: '2.4',
  fp_rear: '2.5',
  fp_left: '2.5',
  fp_right: '0',
};

describe('mandatory fields (FR-01)', () => {
  it('Appendix A lookup is valid with only plot area, road width and built-up area', () => {
    expect(errorPaths('lookup', appendixA)).toEqual([]);
  });

  it('a blank lookup requires plot area and road width', () => {
    expect(errorPaths('lookup', {})).toEqual(expect.arrayContaining(['plot_area', 'road_width']));
  });

  it('fee topics make built-up area mandatory', () => {
    expect(errorPaths('lookup', { plot_area: '200', road_width: '9' })).toContain('built_up_area');
    expect(errorPaths('lookup', { plot_area: '200', road_width: '9', topics: ['front_setback'] })).toEqual([]);
  });

  it('plan check needs development type, height, dimensions and all four footprint distances', () => {
    expect(errorPaths('plan', appendixA)).toEqual(
      expect.arrayContaining(['frontage', 'depth', 'development_type', 'height', 'fp_front', 'fp_rear', 'fp_left', 'fp_right']),
    );
    expect(errorPaths('plan', a5)).toEqual([]);
  });

  it('a free-text question with no topic is a Rules search and needs no plot fields', () => {
    expect(errorPaths('lookup', { topics: [], query_text: 'How do I pay my property tax online?' })).toEqual([]);
  });

  it('no topic and no text asks for a topic', () => {
    expect(errorPaths('lookup', { ...appendixA, topics: [] })).toEqual(['topics']);
  });
});

describe('ranges (FR-04)', () => {
  it('rejects a negative road width with a message naming the field', () => {
    const r = makeFormSchema(s, 'lookup').safeParse({ ...EMPTY_FORM, ...appendixA, road_width: '-3' });
    expect(r.success).toBe(false);
    const issue = r.success ? undefined : r.error.issues.find((i) => i.path[0] === 'road_width');
    expect(issue?.message).toContain('Road width');
  });

  it('rejects non-numbers and out-of-range values', () => {
    expect(errorPaths('lookup', { ...appendixA, plot_area: 'abc' })).toContain('plot_area');
    expect(errorPaths('lookup', { ...appendixA, plot_area: '100001' })).toContain('plot_area');
    expect(errorPaths('lookup', { ...appendixA, height: '151' })).toContain('height');
    expect(errorPaths('plan', { ...a5, frontage: '0' })).toContain('frontage');
  });

  it('accepts 0 for a footprint distance (shared wall)', () => {
    expect(errorPaths('plan', { ...a5, fp_right: '0' })).toEqual([]);
  });
});

describe('conversion', () => {
  it('builds API params and omits empty optional fields', () => {
    const p = toParams({ ...EMPTY_FORM, ...a5, existing_developed_area: 'yes' });
    expect(p).toEqual({
      plot_area: 200,
      road_width: 9,
      use_type: 'residential',
      built_up_area: 250,
      height: 10,
      development_type: 'semi_detached',
      frontage: 10,
      depth: 20,
      existing_developed_area: true,
      streets_abutting: 1,
    });
    expect(toFootprint({ ...EMPTY_FORM, ...a5 })).toEqual({ front: 2.4, rear: 2.5, left: 2.5, right: 0 });
  });

  it('applies parsed parameters and reports which fields were filled', () => {
    const { values, filled } = applyParsed(EMPTY_FORM, { plot_area: 200, road_width: 9 });
    expect(values.plot_area).toBe('200');
    expect(filled).toEqual(['plot_area', 'road_width']);
  });

  it('parses numbers strictly', () => {
    expect(toNumber('')).toBeUndefined();
    expect(toNumber('9.5')).toBe(9.5);
    expect(toNumber('9m')).toBeNaN();
  });

  it('formats figures without changing their value', () => {
    expect(formatValue(3, 'm')).toBe('3.00');
    expect(formatValue(3000, 'Rs')).toBe('₹ 3,000');
    expect(formatValue(54.4, '%')).toBe('54.4');
    expect(formatValue(1.25, '')).toBe('1.25');
  });
});
