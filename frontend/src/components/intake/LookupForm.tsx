import { zodResolver } from '@hookform/resolvers/zod';
import { RotateCcw, Search } from 'lucide-react';
import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react';
import { useForm, useWatch, type FieldErrors, type Resolver } from 'react-hook-form';
import { api } from '../../api/client';
import type { LookupRequest, Params, PlanCheckRequest, Topic } from '../../api/schemas';
import { useStrings } from '../../i18n/useStrings';
import {
  EMPTY_FORM,
  applyParsed,
  fieldLabel,
  isTextSearch,
  makeFormSchema,
  toFootprint,
  toParams,
  type FieldName,
  type FormValues,
  type SubmitMode,
} from '../../lib/formSchema';
import { toNumber } from '../../lib/format';
import { NumberField, RadioGroup, SelectField } from './Field';
import { FootprintFields } from './FootprintFields';
import { FreeTextParse, type ParseStatus } from './FreeTextParse';
import { TopicPicker } from './TopicPicker';

export interface LookupFormHandle {
  focusField: (name: FieldName) => void;
  useDimensionsAsArea: () => void;
  fill: (values: Partial<FormValues>) => void;
}

interface Props {
  busy: boolean;
  /** True once a plan check has produced geometry; enables height re-send (FR-44). */
  planActive: boolean;
  onLookup: (req: LookupRequest) => void;
  onPlan: (plan: PlanCheckRequest, lookup: LookupRequest | null, fromHeightEdit: boolean) => void;
}

const FIELD_ORDER: FieldName[] = [
  'query_text',
  'plot_area',
  'road_width',
  'use_type',
  'built_up_area',
  'height',
  'development_type',
  'frontage',
  'depth',
  'floor_to_floor',
  'existing_developed_area',
  'streets_abutting',
  'topics',
  'fp_front',
  'fp_rear',
  'fp_left',
  'fp_right',
];

export const LookupForm = forwardRef<LookupFormHandle, Props>(function LookupForm(
  { busy, planActive, onLookup, onPlan },
  ref,
) {
  const { s, lang } = useStrings();
  const mode = useRef<SubmitMode>('lookup');
  const resolver: Resolver<FormValues> = (values, context, options) =>
    zodResolver(makeFormSchema(s, mode.current))(values, context, options) as ReturnType<Resolver<FormValues>>;

  const { register, handleSubmit, formState, setFocus, getValues, reset, setValue, control } = useForm<FormValues>({
    defaultValues: EMPTY_FORM,
    resolver,
    mode: 'onSubmit',
    reValidateMode: 'onBlur',
    shouldFocusError: false,
  });
  const { errors } = formState;

  const [highlighted, setHighlighted] = useState<Set<FieldName>>(new Set());
  const [parseStatus, setParseStatus] = useState<ParseStatus>('idle');
  const [summaryErrors, setSummaryErrors] = useState<FieldName[]>([]);
  const [undoValues, setUndoValues] = useState<FormValues | null>(null);
  const summaryRef = useRef<HTMLHeadingElement>(null);
  const lastPlanHeight = useRef<string | null>(null);
  const resolution = useRef<'use_dimensions' | undefined>(undefined);

  const roadWidth = toNumber(useWatch({ control, name: 'road_width' }));
  const height = useWatch({ control, name: 'height' });

  const buildLookup = (v: FormValues, topics: Topic[]): LookupRequest => ({
    params: toParams(v),
    topics,
    language: lang,
    ...(isTextSearch(v) ? { query_text: v.query_text.trim() } : {}),
  });

  const onInvalid = (errs: FieldErrors<FormValues>) => {
    const names = FIELD_ORDER.filter((n) => errs[n]);
    setSummaryErrors(names);
    requestAnimationFrame(() => summaryRef.current?.focus());
  };

  const submitLookup = handleSubmit((v) => {
    setSummaryErrors([]);
    setUndoValues(null);
    lastPlanHeight.current = null;
    onLookup(buildLookup(v, v.topics));
  }, onInvalid);

  const submitPlan = (fromHeightEdit: boolean) =>
    handleSubmit(
      (v) => {
        setSummaryErrors([]);
        lastPlanHeight.current = v.height;
        const plan: PlanCheckRequest = {
          params: toParams(v) as Params,
          footprint: toFootprint(v),
          language: lang,
          ...(resolution.current ? { resolution: resolution.current } : {}),
        };
        // The plan check reports front, rear and side open space per side, so the
        // accompanying lookup leaves them out rather than repeat or contradict them.
        const PLAN_COVERED: Topic[] = ['plan_check', 'front_setback', 'rear_setback', 'side_setback'];
        const others = v.topics.filter((t) => !PLAN_COVERED.includes(t));
        onPlan(plan, others.length ? buildLookup(v, others) : null, fromHeightEdit);
      },
      fromHeightEdit ? undefined : onInvalid,
    );

  const runLookup = () => {
    mode.current = 'lookup';
    resolution.current = undefined;
    void submitLookup();
  };
  const runPlan = (fromHeightEdit = false) => {
    mode.current = 'plan';
    if (!fromHeightEdit) resolution.current = undefined;
    void submitPlan(fromHeightEdit)();
  };

  // FR-44: a height edit after a plan check re-sends it.
  useEffect(() => {
    if (!planActive || lastPlanHeight.current === null || height === lastPlanHeight.current) return;
    const n = toNumber(height);
    if (n === undefined || Number.isNaN(n)) return;
    const timer = window.setTimeout(() => runPlan(true), 500);
    return () => window.clearTimeout(timer);
    // runPlan is recreated each render; the effect should only follow height.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [height, planActive]);

  useImperativeHandle(ref, () => ({
    focusField: (name) => setFocus(name),
    useDimensionsAsArea: () => {
      const w = toNumber(getValues('frontage'));
      const d = toNumber(getValues('depth'));
      if (w !== undefined && d !== undefined && !Number.isNaN(w) && !Number.isNaN(d)) {
        setValue('plot_area', String(Math.round(w * d * 100) / 100));
      }
      resolution.current = 'use_dimensions';
      mode.current = 'plan';
      void submitPlan(false)();
    },
    fill: (values) => {
      reset({ ...EMPTY_FORM, ...values });
      setHighlighted(new Set());
      setParseStatus('idle');
    },
  }));

  const onParse = async () => {
    const text = getValues('query_text').trim();
    if (!text) return;
    setParseStatus('parsing');
    try {
      const res = await api.parse(text);
      const { values, filled } = applyParsed(getValues(), res.params);
      const topics = res.topics.length ? res.topics : filled.length ? values.topics : [];
      reset({ ...values, topics }, { keepDefaultValues: true });
      setHighlighted(new Set(filled));
      setParseStatus(filled.length === 0 ? 'nothing' : filled.length < 3 ? 'partial' : 'filled');
      const firstEmpty = (['plot_area', 'road_width', 'built_up_area'] as const).find((n) => !values[n]);
      if (firstEmpty && filled.length) setFocus(firstEmpty);
    } catch {
      setParseStatus('error');
    }
  };

  const req = (name: FieldName) => ({ id: `field-${name}`, error: errors[name], highlighted: highlighted.has(name) });

  return (
    <form
      noValidate
      aria-label={s.intake.heading}
      onSubmit={(e) => {
        e.preventDefault();
        runLookup();
      }}
    >
      <FreeTextParse registration={register('query_text')} onParse={() => void onParse()} status={parseStatus} />

      {summaryErrors.length > 0 ? (
        <div role="alert" className="mx-5 mt-3 rounded-sm border-2 border-conflict bg-conflict-tint p-3">
          <h2 ref={summaryRef} tabIndex={-1} className="text-label font-bold text-conflict-text">
            {s.validation.summaryHeading}
          </h2>
          <ul className="mt-1 list-disc pl-5 text-label">
            {summaryErrors.map((n) => (
              <li key={n}>
                <a
                  href={`#field-${n}`}
                  className="text-conflict-text underline"
                  onClick={(e) => {
                    e.preventDefault();
                    if (n === 'topics') document.getElementById('field-topics')?.querySelector('input')?.focus();
                    else setFocus(n);
                  }}
                >
                  {errors[n]?.message ?? fieldLabel(n, s)}
                </a>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <section aria-labelledby="params-heading" className="border-b border-border px-5 py-3">
        <h2 id="params-heading" className="text-body font-bold">
          {s.intake.formHeading}
        </h2>
        <div className="mt-2 grid grid-cols-2 gap-x-3 gap-y-2">
          <NumberField {...req('plot_area')} label={s.fields.plot_area} unit={s.fields.sqm} required registration={register('plot_area')} />
          <NumberField {...req('road_width')} label={s.fields.road_width} unit={s.fields.m} required registration={register('road_width')} />
          <SelectField {...req('use_type')} label={s.fields.use_type} required registration={register('use_type')}>
            {(['residential', 'commercial', 'public', 'industrial', 'agricultural'] as const).map((u) => (
              <option key={u} value={u}>
                {s.useTypes[u]}
              </option>
            ))}
          </SelectField>
          <NumberField
            {...req('built_up_area')}
            label={s.fields.built_up_area}
            unit={s.fields.sqm}
            hint={s.fields.builtUpHint}
            registration={register('built_up_area')}
          />
          <NumberField {...req('height')} label={s.fields.height} unit={s.fields.m} registration={register('height')} />
          <SelectField {...req('development_type')} label={s.fields.development_type} registration={register('development_type')}>
            <option value="">{s.developmentTypes.none}</option>
            {(['detached', 'semi_detached', 'row'] as const).map((d) => (
              <option key={d} value={d}>
                {s.developmentTypes[d]}
              </option>
            ))}
          </SelectField>
          <NumberField {...req('frontage')} label={s.fields.frontage} unit={s.fields.m} registration={register('frontage')} />
          <NumberField {...req('depth')} label={s.fields.depth} unit={s.fields.m} registration={register('depth')} />
          <NumberField
            {...req('floor_to_floor')}
            label={s.fields.floor_to_floor}
            unit={s.fields.m}
            registration={register('floor_to_floor')}
          />
          {roadWidth !== undefined && !Number.isNaN(roadWidth) && roadWidth < 6 ? (
            <RadioGroup
              name="existing_developed_area"
              legend={s.fields.existing_developed_area}
              hint={s.fields.narrowStreetHint}
              options={[
                { value: 'yes', label: s.fields.yes },
                { value: 'no', label: s.fields.no },
              ]}
              registration={register('existing_developed_area')}
            />
          ) : null}
          <RadioGroup
            name="streets_abutting"
            legend={s.fields.streets_abutting}
            options={[
              { value: '1', label: s.fields.streets1 },
              { value: '2', label: s.fields.streets2 },
            ]}
            registration={register('streets_abutting')}
          />
        </div>
      </section>

      <TopicPicker registration={register('topics')} error={errors.topics?.message ? { message: errors.topics.message } : undefined} />

      <div className="flex gap-2 border-b border-border px-5 py-3">
        <button
          type="submit"
          disabled={busy}
          className="inline-flex min-h-11 flex-1 items-center justify-center gap-2 rounded-sm bg-accent px-4 text-body font-semibold text-on-accent hover:bg-accent-hover disabled:opacity-60"
        >
          <Search aria-hidden="true" className="size-5" />
          {busy ? s.actions.lookingUp : s.actions.lookup}
        </button>
        <button
          type="button"
          onClick={() => {
            setUndoValues(getValues());
            reset(EMPTY_FORM);
            setHighlighted(new Set());
            setParseStatus('idle');
            setSummaryErrors([]);
            lastPlanHeight.current = null;
          }}
          className="inline-flex min-h-11 items-center gap-2 rounded-sm border border-input-border px-3 text-label font-semibold text-muted-foreground hover:bg-muted"
        >
          <RotateCcw aria-hidden="true" className="size-4" />
          {s.intake.clear}
        </button>
      </div>

      {undoValues ? (
        <p role="status" className="flex items-center gap-3 border-b border-border px-5 py-2 text-label">
          {s.intake.cleared}
          <button
            type="button"
            onClick={() => {
              reset(undoValues);
              setUndoValues(null);
            }}
            className="min-h-9 rounded-sm border border-accent px-3 font-semibold text-accent hover:bg-info-tint"
          >
            {s.intake.undo}
          </button>
        </p>
      ) : null}

      <FootprintFields register={register} errors={errors} highlighted={highlighted} onRun={() => runPlan(false)} busy={busy} />
    </form>
  );
});
