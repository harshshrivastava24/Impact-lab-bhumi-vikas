import { Scale } from 'lucide-react';

/** C-04: shown on every result and every state. Text comes from the API or the strings file. */
export function Disclaimer({ text }: { text: string }) {
  return (
    <p className="flex items-start gap-2 rounded-sm border border-border bg-muted px-3 py-2 text-label text-foreground">
      <Scale aria-hidden="true" className="mt-0.5 size-4 shrink-0" />
      <span>{text}</span>
    </p>
  );
}
