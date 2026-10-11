import { z } from 'zod';
import {
  FEE_TOPICS,
  TopicSchema,
  UseTypeSchema,
  type DevelopmentType,
  type Footprint,
  type Params,
  type Topic,
  type UseType,
} from '../api/schemas';
import { fmt, type Strings } from '../i18n/strings';
import { toNumber } from './format';

/** Raw form state. Numeric inputs stay strings until validated. */
export interface FormValues {
  query_text: string;
  plot_area: string;
  road_width: string;
  use_type: UseType;
  built_up_area: string;
  height: string;
  development_type: '' | DevelopmentType;
  frontage: string;
  depth: string;
  floor_to_floor: string;
  existing_developed_area: '' | 'yes' | 'no';
  streets_abutting: '1' | '2';
  topics: Topic[];
  fp_front: string;
  fp_rear: string;
  fp_left: string;
  fp_right: string;
}

export type FieldName = keyof FormValues;

export const DEFAULT_TOPICS: Topic[] = [
  'front_setback',
  'rear_setback',
  'side_setback',
  'height_limit',
  'far',
  'application_fee',
  'permission_fee',
];

export const EMPTY_FORM: FormValues = {
  query_text: '',
  plot_area: '',
  road_width: '',
  use_type: 'residential',
  built_up_area: '',
  height: '',
  development_type: '',
  frontage: '',
  depth: '',
  floor_to_floor: '',
  existing_developed_area: '',
  streets_abutting: '1',
  topics: DEFAULT_TOPICS,
  fp_front: '',
  fp_rear: '',
  fp_left: '',
  fp_right: '',
};

type NumericField =
  | 'plot_area'
  | 'road_width'
  | 'built_up_area'
  | 'height'
  | 'frontage'
  | 'depth'
  | 'floor_to_floor'
  | 'fp_front'
  | 'fp_rear'
  | 'fp_left'
  | 'fp_right';

/** FR-04 ranges. Footprint distances may be 0 (a shared wall). */
export const RANGES: Record<NumericField, { min: number; max: number; unit: 'm' | 'sq m' }> = {
  plot_area: { min: 1, max: 100000, unit: 'sq m' },
  road_width: { min: 1, max: 100, unit: 'm' },
  built_up_area: { min: 1, max: 100000, unit: 'sq m' },
  height: { min: 0, max: 150, unit: 'm' },
  frontage: { min: 1, max: 500, unit: 'm' },
  depth: { min: 1, max: 500, unit: 'm' },
  floor_to_floor: { min: 2, max: 10, unit: 'm' },
  fp_front: { min: 0, max: 500, unit: 'm' },
  fp_rear: { min: 0, max: 500, unit: 'm' },
  fp_left: { min: 0, max: 500, unit: 'm' },
  fp_right: { min: 0, max: 500, unit: 'm' },
};

export const FOOTPRINT_FIELDS = ['fp_front', 'fp_rear', 'fp_left', 'fp_right'] as const;

export type SubmitMode = 'lookup' | 'plan';

export function fieldLabel(name: FieldName, s: Strings): string {
  switch (name) {
    case 'fp_front':
      return s.footprint.front;
    case 'fp_rear':
      return s.footprint.rear;
    case 'fp_left':
      return s.footprint.left;
    case 'fp_right':
      return s.footprint.right;
    case 'topics':
      return s.topics.heading;
    case 'query_text':
      return s.intake.freeTextLabel;
    default:
      return s.fields[name];
  }
}

/** True when the clerk asked a free-text question and picked no topic: a Rules search. */
export function isTextSearch(v: Pick<FormValues, 'topics' | 'query_text'>): boolean {
  return v.topics.length === 0 && v.query_text.trim() !== '';
}

/**
 * Validation schema for one submit mode. Mandatory fields (FR-01):
 * lookup needs plot area, road width and use type; fee topics need built-up
 * area; plan check also needs frontage, depth, development type, height and
 * the four footprint distances.
 */
export function makeFormSchema(s: Strings, mode: SubmitMode) {
  const str = z.string();
  return z
    .object({
      query_text: str,
      plot_area: str,
      road_width: str,
      use_type: UseTypeSchema,
      built_up_area: str,
      height: str,
      development_type: z.union([z.literal(''), z.enum(['detached', 'semi_detached', 'row'])]),
      frontage: str,
      depth: str,
      floor_to_floor: str,
      existing_developed_area: z.enum(['', 'yes', 'no']),
      streets_abutting: z.enum(['1', '2']),
      topics: z.array(TopicSchema),
      fp_front: str,
      fp_rear: str,
      fp_left: str,
      fp_right: str,
    })
    .superRefine((v, ctx) => {
      const textSearch = mode === 'lookup' && isTextSearch(v);
      const required = new Set<FieldName>();

      if (mode === 'lookup' && v.topics.length === 0 && v.query_text.trim() === '') {
        ctx.addIssue({ code: 'custom', path: ['topics'], message: s.validation.needTopic });
      }
      if (!textSearch) {
        required.add('plot_area').add('road_width').add('use_type');
      }
      if (mode === 'lookup' && v.topics.some((t) => FEE_TOPICS.includes(t))) {
        required.add('built_up_area');
      }
      if (mode === 'plan') {
        (['frontage', 'depth', 'development_type', 'height', ...FOOTPRINT_FIELDS] as FieldName[]).forEach((f) =>
          required.add(f),
        );
      }

      for (const name of required) {
        const raw = v[name];
        if (typeof raw === 'string' && raw.trim() === '') {
          ctx.addIssue({ code: 'custom', path: [name], message: fmt(s.validation.required, { field: fieldLabel(name, s) }) });
        }
      }

      for (const [name, range] of Object.entries(RANGES) as [NumericField, (typeof RANGES)[NumericField]][]) {
        const n = toNumber(v[name]);
        if (n === undefined) continue;
        const label = fieldLabel(name, s);
        if (Number.isNaN(n)) {
          ctx.addIssue({ code: 'custom', path: [name], message: fmt(s.validation.number, { field: label }) });
        } else if (n < range.min || n > range.max) {
          ctx.addIssue({
            code: 'custom',
            path: [name],
            message: fmt(s.validation.range, {
              field: label,
              min: range.min,
              max: range.max,
              unit: range.unit === 'm' ? s.fields.m : s.fields.sqm,
            }),
          });
        }
      }
    });
}

/** Convert validated form values to API parameters. Empty optional fields are omitted. */
export function toParams(v: FormValues): Partial<Params> {
  const params: Partial<Params> = { use_type: v.use_type };
  const num = (raw: string) => {
    const n = toNumber(raw);
    return n === undefined || Number.isNaN(n) ? undefined : n;
  };
  const set = <K extends keyof Params>(key: K, value: Params[K] | undefined) => {
    if (value !== undefined) params[key] = value;
  };
  set('plot_area', num(v.plot_area));
  set('road_width', num(v.road_width));
  set('built_up_area', num(v.built_up_area));
  set('height', num(v.height));
  set('frontage', num(v.frontage));
  set('depth', num(v.depth));
  set('floor_to_floor', num(v.floor_to_floor));
  if (v.development_type !== '') params.development_type = v.development_type;
  if (v.existing_developed_area !== '') params.existing_developed_area = v.existing_developed_area === 'yes';
  params.streets_abutting = v.streets_abutting === '2' ? 2 : 1;
  return params;
}

export function toFootprint(v: FormValues): Footprint {
  return {
    front: Number(v.fp_front),
    rear: Number(v.fp_rear),
    left: Number(v.fp_left),
    right: Number(v.fp_right),
  };
}

/** Map parsed parameters back into form strings (FR-02). Returns the fields that were filled. */
export function applyParsed(current: FormValues, parsed: Partial<Params>): { values: FormValues; filled: FieldName[] } {
  const values = { ...current };
  const filled: FieldName[] = [];
  const put = (name: FieldName, value: string) => {
    (values as Record<FieldName, unknown>)[name] = value;
    filled.push(name);
  };
  if (parsed.plot_area !== undefined) put('plot_area', String(parsed.plot_area));
  if (parsed.road_width !== undefined) put('road_width', String(parsed.road_width));
  if (parsed.use_type !== undefined) put('use_type', parsed.use_type);
  if (parsed.built_up_area !== undefined) put('built_up_area', String(parsed.built_up_area));
  if (parsed.height !== undefined) put('height', String(parsed.height));
  if (parsed.frontage !== undefined) put('frontage', String(parsed.frontage));
  if (parsed.depth !== undefined) put('depth', String(parsed.depth));
  if (parsed.development_type !== undefined) put('development_type', parsed.development_type);
  return { values, filled };
}
