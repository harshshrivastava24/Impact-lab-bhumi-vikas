import { FileText } from 'lucide-react';
import type { Citation } from '../../api/schemas';
import { useStrings } from '../../i18n/useStrings';

const pageOf = (url: string, fallback: number) => {
  const m = /#page=(\d+)/.exec(url);
  return m?.[1] ? Number(m[1]) : fallback;
};

/**
 * Verbatim English rule text (FR-29), collapsed to the cited sub-rule with the
 * full rule behind a disclosure, plus EN and HI PDF page links (FR-31).
 */
export function CitationCard({ citation, index }: { citation: Citation; index: number }) {
  const { s, fmt, lang } = useStrings();
  const ruleRef = `${citation.rule}${citation.sub_rule ?? ''}`;
  const enPage = pageOf(citation.pdf_en_url, citation.page_start);
  const hiPage = pageOf(citation.pdf_hi_url, citation.page_start);
  const headingId = `cite-${index}`;

  return (
    <article aria-labelledby={headingId} className="rounded-md border border-border bg-card shadow-card">
      <header className="flex flex-wrap items-baseline justify-between gap-x-3 border-b border-border px-3 py-2">
        <h3 id={headingId} className="text-body font-bold">
          {fmt(s.result.citationTitle, { rule: ruleRef, title: citation.title })}
        </h3>
        <p className="text-xs text-muted-foreground">
          {fmt(s.result.pages, { part: citation.part, start: citation.page_start, end: citation.page_end })}
        </p>
      </header>
      {lang === 'hi' ? <p className="px-3 pt-2 text-xs text-info-text">{s.result.hindiNote}</p> : null}
      <pre
        translate="no"
        lang="en"
        role="region"
        tabIndex={0}
        aria-label={ruleRef}
        className="mx-3 mt-2 max-h-44 overflow-auto rounded-sm bg-muted p-2 font-mono text-[13px] leading-[1.35] whitespace-pre text-foreground"
      >
        {citation.sub_rule_text_en ?? citation.text_en}
      </pre>
      {citation.sub_rule_text_en ? (
        <details className="mx-3 mt-1 text-label">
          <summary className="text-accent">{s.result.expandRule}</summary>
          <pre
            lang="en"
            role="region"
            tabIndex={0}
            aria-label={`${ruleRef} ${s.result.expandRule}`}
            className="mt-1 max-h-80 overflow-auto rounded-sm bg-muted p-2 font-mono text-[13px] leading-[1.35] whitespace-pre"
          >
            {citation.text_en}
          </pre>
        </details>
      ) : null}
      {citation.footnotes.length ? (
        <div className="mx-3 mt-2">
          <h4 className="text-xs font-semibold text-muted-foreground">{s.result.footnotesHeading}</h4>
          <ul className="list-disc pl-4 text-xs text-muted-foreground">
            {citation.footnotes.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
        </div>
      ) : null}
      <div className="flex flex-wrap gap-2 px-3 py-2">
        <a
          href={citation.pdf_en_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex min-h-9 items-center gap-1.5 rounded-sm border border-accent px-2.5 text-label font-semibold text-accent hover:bg-info-tint"
        >
          <FileText aria-hidden="true" className="size-4" />
          {fmt(s.result.openEnPdf, { page: enPage })}
        </a>
        <a
          href={citation.pdf_hi_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex min-h-9 items-center gap-1.5 rounded-sm border border-accent px-2.5 text-label font-semibold text-accent hover:bg-info-tint"
        >
          <FileText aria-hidden="true" className="size-4" />
          {fmt(s.result.openHiPdf, { page: hiPage })}
        </a>
      </div>
    </article>
  );
}
