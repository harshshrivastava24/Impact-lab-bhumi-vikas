import { PencilRuler } from 'lucide-react';
import type { FieldErrors, UseFormRegister } from 'react-hook-form';
import { FOOTPRINT_FIELDS, type FieldName, type FormValues } from '../../lib/formSchema';
import { useStrings } from '../../i18n/useStrings';
import { NumberField } from './Field';

/**
 * Plan check section (FR-42). Enter in any of these fields runs the plan
 * check instead of the lookup.
 */
export function FootprintFields({
  register,
  errors,
  highlighted,
  onRun,
  busy,
}: {
  register: UseFormRegister<FormValues>;
  errors: FieldErrors<FormValues>;
  highlighted: Set<FieldName>;
  onRun: () => void;
  busy: boolean;
}) {
  const { s } = useStrings();
  const labels = { fp_front: s.footprint.front, fp_rear: s.footprint.rear, fp_left: s.footprint.left, fp_right: s.footprint.right };

  return (
    <section aria-labelledby="plan-check-heading" className="px-5 py-3">
      <h2 id="plan-check-heading" className="text-body font-bold">
        {s.footprint.heading}
      </h2>
      <p id="footprint-hint" className="text-xs text-muted-foreground">
        {s.footprint.hint}
      </p>
      <div className="mt-2 grid grid-cols-2 gap-x-3 gap-y-2">
        {FOOTPRINT_FIELDS.map((name) => (
          <NumberField
            key={name}
            id={`field-${name}`}
            label={labels[name]}
            unit={s.fields.m}
            required
            error={errors[name]}
            highlighted={highlighted.has(name)}
            registration={register(name)}
            onEnter={onRun}
          />
        ))}
      </div>
      <button
        type="button"
        onClick={onRun}
        disabled={busy}
        className="mt-3 inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-sm border-2 border-accent bg-card px-4 text-body font-semibold text-accent hover:bg-info-tint disabled:opacity-60"
      >
        <PencilRuler aria-hidden="true" className="size-5" />
        {busy ? s.actions.lookingUp : s.actions.planCheck}
      </button>
    </section>
  );
}
