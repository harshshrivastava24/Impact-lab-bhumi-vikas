import { Ban } from 'lucide-react';
import { useStrings } from '../../../i18n/useStrings';
import { Disclaimer } from '../Disclaimer';

/** FR-48: message rendered verbatim; blank lines separate paragraphs (corner-plot readings). */
export function Refused({ message, disclaimer }: { message: string; disclaimer: string }) {
  const { s } = useStrings();
  const paragraphs = message.split(/\n\s*\n/).filter(Boolean);
  return (
    <section aria-labelledby="refused-title" className="flex flex-col gap-3">
      <div className="rounded-md border-2 border-warning bg-warning-tint px-4 py-4 text-warning-text">
        <h2 id="refused-title" className="flex items-center gap-2 text-lg font-bold">
          <Ban aria-hidden="true" className="size-5 shrink-0" />
          {s.states.refusedTitle}
        </h2>
        {paragraphs.map((p) => (
          <p key={p} className="mt-2 text-body text-foreground">
            {p}
          </p>
        ))}
      </div>
      <Disclaimer text={disclaimer} />
    </section>
  );
}
