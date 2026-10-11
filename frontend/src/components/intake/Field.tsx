import type { ReactNode } from 'react';
import type { UseFormRegisterReturn } from 'react-hook-form';
import { useStrings } from '../../i18n/useStrings';

/** Only the message matters for display; accepts any react-hook-form error shape. */
type FieldError = { message?: string | undefined };

interface BaseProps {
  id: string;
  label: string;
  error?: FieldError | undefined;
  hint?: string | undefined;
  required?: boolean;
  highlighted?: boolean;
}

function Label({ id, label, required }: Pick<BaseProps, 'id' | 'label' | 'required'>) {
  const { s } = useStrings();
  return (
    <label htmlFor={id} className="block text-label font-semibold text-foreground">
      {label}
      {required ? <span className="sr-only">{` (${s.intake.requiredMark})`}</span> : null}
      {required ? (
        <span aria-hidden="true" className="ml-0.5 text-conflict">
          *
        </span>
      ) : null}
    </label>
  );
}

function Messages({ id, error, hint }: Pick<BaseProps, 'id' | 'error' | 'hint'>) {
  return (
    <>
      {hint && !error ? (
        <p id={`${id}-hint`} className="mt-0.5 text-xs text-muted-foreground">
          {hint}
        </p>
      ) : null}
      {error?.message ? (
        <p id={`${id}-error`} className="mt-0.5 text-xs font-semibold text-conflict-text">
          {error.message}
        </p>
      ) : null}
    </>
  );
}

const describedBy = (id: string, error?: FieldError, hint?: string) =>
  [error ? `${id}-error` : null, hint && !error ? `${id}-hint` : null].filter(Boolean).join(' ') || undefined;

const inputClass = (error?: FieldError, highlighted?: boolean) =>
  [
    'mt-1 block w-full min-h-10 rounded-sm border bg-card px-2.5 text-body tabular text-foreground',
    error ? 'border-conflict border-2' : 'border-input-border',
    highlighted ? 'ring-2 ring-info ring-offset-1' : '',
  ].join(' ');

export function NumberField({
  id,
  label,
  unit,
  error,
  hint,
  required,
  highlighted,
  registration,
  onEnter,
}: BaseProps & { unit: string; registration: UseFormRegisterReturn; onEnter?: () => void }) {
  return (
    <div>
      <Label id={id} label={label} required={required ?? false} />
      <div className="relative">
        <input
          id={id}
          type="text"
          inputMode="decimal"
          autoComplete="off"
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy(id, error, hint)}
          className={`${inputClass(error, highlighted)} pr-14`}
          onKeyDown={
            onEnter
              ? (e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    onEnter();
                  }
                }
              : undefined
          }
          {...registration}
        />
        <span aria-hidden="true" className="pointer-events-none absolute inset-y-0 right-2.5 flex items-center text-label text-muted-foreground">
          {unit}
        </span>
      </div>
      <Messages id={id} error={error} hint={hint} />
    </div>
  );
}

export function SelectField({
  id,
  label,
  error,
  hint,
  required,
  highlighted,
  registration,
  children,
}: BaseProps & { registration: UseFormRegisterReturn; children: ReactNode }) {
  return (
    <div>
      <Label id={id} label={label} required={required ?? false} />
      <select
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy(id, error, hint)}
        className={inputClass(error, highlighted)}
        {...registration}
      >
        {children}
      </select>
      <Messages id={id} error={error} hint={hint} />
    </div>
  );
}

export function RadioGroup({
  name,
  legend,
  options,
  registration,
  hint,
}: {
  name: string;
  legend: string;
  options: { value: string; label: string }[];
  registration: UseFormRegisterReturn;
  hint?: string;
}) {
  return (
    <fieldset className="col-span-2">
      <legend className="text-label font-semibold">{legend}</legend>
      {hint ? <p className="text-xs text-muted-foreground">{hint}</p> : null}
      <div className="mt-1 flex flex-wrap gap-x-5 gap-y-1">
        {options.map((o) => (
          <label key={o.value} htmlFor={`${name}-${o.value}`} className="flex min-h-9 items-center gap-2 text-body">
            <input id={`${name}-${o.value}`} type="radio" value={o.value} className="size-4 accent-accent" {...registration} />
            {o.label}
          </label>
        ))}
      </div>
    </fieldset>
  );
}
