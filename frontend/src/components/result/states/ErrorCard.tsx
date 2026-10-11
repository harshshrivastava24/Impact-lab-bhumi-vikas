import { CircleAlert, RotateCcw } from 'lucide-react';
import type { ApiError } from '../../../api/client';
import { useStrings } from '../../../i18n/useStrings';
import { Disclaimer } from '../Disclaimer';

/** Network, HTTP or schema failure: readable message and a retry, never a blank screen. */
export function ErrorCard({ error, onRetry }: { error: ApiError; onRetry: () => void }) {
  const { s } = useStrings();
  const summary =
    error.kind === 'network' ? s.states.errorNetwork : error.kind === 'schema' ? s.states.errorSchema : s.states.errorHttp;
  return (
    <section aria-labelledby="error-title" className="flex flex-col gap-3">
      <div className="rounded-md border-2 border-conflict bg-card px-4 py-4">
        <h2 id="error-title" className="flex items-center gap-2 text-lg font-bold text-conflict-text">
          <CircleAlert aria-hidden="true" className="size-5 shrink-0" />
          {s.states.errorTitle}
        </h2>
        <p className="mt-1 text-body">{summary}</p>
        <p className="mt-1 text-label break-words text-muted-foreground">{error.message}</p>
        <button
          type="button"
          onClick={onRetry}
          className="mt-3 inline-flex min-h-11 items-center gap-2 rounded-sm bg-accent px-4 text-body font-semibold text-on-accent hover:bg-accent-hover"
        >
          <RotateCcw aria-hidden="true" className="size-4" />
          {s.states.retry}
        </button>
      </div>
      <Disclaimer text={s.states.disclaimer} />
    </section>
  );
}
