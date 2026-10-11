import { Landmark } from 'lucide-react';
import type { Language } from '../../api/schemas';
import { useStrings } from '../../i18n/useStrings';

export function Header() {
  const { s, lang, setLang } = useStrings();
  const options: { value: Language; label: string; langAttr: string }[] = [
    { value: 'en', label: s.app.langEn, langAttr: 'en' },
    { value: 'hi', label: s.app.langHi, langAttr: 'hi' },
  ];

  return (
    <header className="screen-only flex items-center justify-between gap-4 bg-primary px-5 py-2.5 text-on-primary">
      <div className="flex min-w-0 items-center gap-3">
        <Landmark aria-hidden="true" className="size-6 shrink-0" />
        <div className="min-w-0">
          <h1 translate="no" className="text-lg leading-tight font-bold">{s.app.title}</h1>
          <p className="truncate text-label text-on-primary-muted">{s.app.subtitle}</p>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <p className="text-label text-on-primary-muted tabular">{s.app.versionStamp}</p>
        <div role="group" aria-label={s.app.languageLabel} className="flex rounded-md border border-on-primary-muted/60 p-0.5">
          {options.map((o) => (
            <button
              key={o.value}
              type="button"
              lang={o.langAttr}
              aria-pressed={lang === o.value}
              onClick={() => setLang(o.value)}
              className={`min-h-9 rounded-sm px-3 text-label font-semibold ${
                lang === o.value ? 'bg-on-primary text-primary' : 'text-on-primary hover:bg-white/10'
              }`}
            >
              {o.label}
            </button>
          ))}
        </div>
      </div>
    </header>
  );
}
