import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { Language } from '../api/schemas';
import { STRINGS, fmt, type Strings } from './strings';

interface LanguageContextValue {
  lang: Language;
  setLang: (lang: Language) => void;
  s: Strings;
  fmt: typeof fmt;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children, initial = 'en' }: { children: ReactNode; initial?: Language }) {
  const [lang, setLang] = useState<Language>(initial);

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);

  const value = useMemo(() => ({ lang, setLang, s: STRINGS[lang], fmt }), [lang]);
  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useStrings(): LanguageContextValue {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useStrings must be used inside LanguageProvider');
  return ctx;
}
