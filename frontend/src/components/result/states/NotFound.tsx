import { SearchX } from 'lucide-react';
import { useStrings } from '../../../i18n/useStrings';
import { Disclaimer } from '../Disclaimer';

/** FR-26: no rule number, figure or text is shown. */
export function NotFound({ disclaimer }: { disclaimer: string }) {
  const { s } = useStrings();
  return (
    <section aria-labelledby="not-found-title" className="flex flex-col gap-3">
      <div className="rounded-md border-2 border-input-border bg-card px-5 py-6 text-center">
        <SearchX aria-hidden="true" className="mx-auto size-10 text-muted-foreground" />
        <h2 id="not-found-title" className="mt-2 text-2xl font-bold">
          {s.states.notFoundTitle}
        </h2>
        <p className="mt-1 text-body text-muted-foreground">{s.states.notFoundBody}</p>
      </div>
      <Disclaimer text={disclaimer} />
    </section>
  );
}
