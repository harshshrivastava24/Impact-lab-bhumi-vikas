import { OctagonX } from 'lucide-react';
import type { Resolution } from '../../../api/schemas';
import { useStrings } from '../../../i18n/useStrings';
import { Disclaimer } from '../Disclaimer';

/** FR-39: area and dimensions disagree; the clerk must choose a resolution. */
export function Blocked({
  message,
  resolutions,
  disclaimer,
  onCorrect,
  onUseDimensions,
}: {
  message: string;
  resolutions: Resolution[];
  disclaimer: string;
  onCorrect: () => void;
  onUseDimensions: () => void;
}) {
  const { s } = useStrings();
  return (
    <section aria-labelledby="blocked-title" className="flex flex-col gap-3">
      <div className="rounded-md border-2 border-conflict bg-conflict-tint px-4 py-4">
        <h2 id="blocked-title" className="flex items-center gap-2 text-lg font-bold text-conflict-text">
          <OctagonX aria-hidden="true" className="size-5 shrink-0" />
          {s.states.blockedTitle}
        </h2>
        <p className="mt-1 text-body tabular">{message}</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {resolutions.includes('correct_inputs') ? (
            <button
              type="button"
              onClick={onCorrect}
              className="min-h-11 rounded-sm bg-accent px-4 text-body font-semibold text-on-accent hover:bg-accent-hover"
            >
              {s.states.correctInputs}
            </button>
          ) : null}
          {resolutions.includes('use_dimensions') ? (
            <button
              type="button"
              onClick={onUseDimensions}
              className="min-h-11 rounded-sm border-2 border-accent bg-card px-4 text-body font-semibold text-accent hover:bg-info-tint"
            >
              {s.states.useDimensions}
            </button>
          ) : null}
        </div>
      </div>
      <Disclaimer text={disclaimer} />
    </section>
  );
}
