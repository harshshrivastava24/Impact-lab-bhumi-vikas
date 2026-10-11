import { FileSearch } from 'lucide-react';
import type { UseFormRegisterReturn } from 'react-hook-form';
import { useStrings } from '../../i18n/useStrings';

export type ParseStatus = 'idle' | 'parsing' | 'filled' | 'partial' | 'nothing' | 'error';

export function FreeTextParse({
  registration,
  onParse,
  status,
}: {
  registration: UseFormRegisterReturn;
  onParse: () => void;
  status: ParseStatus;
}) {
  const { s } = useStrings();
  const message =
    status === 'filled'
      ? s.intake.parseFilled
      : status === 'partial'
        ? s.intake.parsePartial
        : status === 'nothing'
          ? s.intake.parseNothing
          : status === 'error'
            ? s.states.errorNetwork
            : null;

  return (
    <div className="border-b border-border px-5 pt-4 pb-4">
      <label htmlFor="field-query_text" className="block text-label font-semibold">
        {s.intake.freeTextLabel}
      </label>
      <textarea
        id="field-query_text"
        rows={2}
        aria-describedby="query-text-hint"
        className="mt-1 block w-full resize-y rounded-sm border border-input-border bg-card px-2.5 py-1.5 text-body"
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            onParse();
          }
        }}
        {...registration}
      />
      <p id="query-text-hint" className="mt-0.5 text-xs text-muted-foreground">
        {s.intake.freeTextHint}
      </p>
      <button
        type="button"
        onClick={onParse}
        disabled={status === 'parsing'}
        className="mt-2 inline-flex min-h-10 items-center gap-2 rounded-sm border border-accent px-3 text-label font-semibold text-accent hover:bg-info-tint disabled:opacity-60"
      >
        <FileSearch aria-hidden="true" className="size-4" />
        {status === 'parsing' ? s.intake.parsing : s.intake.parseButton}
      </button>
      <p role="status" className="mt-2 text-label text-info-text empty:hidden">
        {message}
      </p>
    </div>
  );
}
