import type { ReactNode } from 'react';

/** Intake on the left (about 38 %), result on the right. Each pane scrolls on its own. */
export function TwoPane({ intake, result, intakeLabel }: { intake: ReactNode; result: ReactNode; intakeLabel: string }) {
  return (
    <div className="flex min-h-0 flex-1">
      <aside
        aria-label={intakeLabel}
        className="screen-only w-[38%] min-w-[330px] overflow-y-auto border-r border-border bg-card"
      >
        {intake}
      </aside>
      <main id="result" tabIndex={-1} className="min-w-0 flex-1 overflow-y-auto focus-visible:outline-none">
        {result}
      </main>
    </div>
  );
}
