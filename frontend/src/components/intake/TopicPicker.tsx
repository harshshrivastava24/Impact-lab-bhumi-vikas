import type { FieldError, UseFormRegisterReturn } from 'react-hook-form';
import { TOPICS, type Topic } from '../../api/schemas';
import { useStrings } from '../../i18n/useStrings';

/** Lookup topics. Plan check has its own section and button, so it is not listed here. */
const LOOKUP_TOPICS = TOPICS.filter((t): t is Exclude<Topic, 'plan_check'> => t !== 'plan_check');

export function TopicPicker({ registration, error }: { registration: UseFormRegisterReturn; error?: Pick<FieldError, 'message'> | undefined }) {
  const { s } = useStrings();
  return (
    <fieldset
      id="field-topics"
      aria-describedby={error ? 'field-topics-error' : undefined}
      className="border-b border-border px-5 py-3"
    >
      <legend className="float-left mb-1 w-full text-label font-semibold">{s.topics.heading}</legend>
      <div className="clear-both grid grid-cols-2 gap-x-3">
        {LOOKUP_TOPICS.map((t) => (
          <label key={t} htmlFor={`topic-${t}`} className="flex min-h-8 items-center gap-2 text-label">
            <input id={`topic-${t}`} type="checkbox" value={t} className="size-4 shrink-0 accent-accent" {...registration} />
            {s.topics[t]}
          </label>
        ))}
      </div>
      {error?.message ? (
        <p id="field-topics-error" className="mt-1 text-xs font-semibold text-conflict-text">
          {error.message}
        </p>
      ) : null}
    </fieldset>
  );
}
