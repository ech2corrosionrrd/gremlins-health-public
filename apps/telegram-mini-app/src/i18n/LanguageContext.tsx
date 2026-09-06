import React, { createContext, useContext, useState, useEffect } from 'react';
import { Language, translations, Translations } from './translations';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: Translations;
  availableLanguages: { code: Language; label: string; flag: string }[];
}

const availableLanguages: { code: Language; label: string; flag: string }[] = [
  { code: 'en', label: 'English', flag: '🇬🇧' },
  { code: 'uk', label: 'Українська', flag: '🇺🇦' },
  { code: 'pl', label: 'Polski', flag: '🇵🇱' },
  { code: 'de', label: 'Deutsch', flag: '🇩🇪' },
  { code: 'es', label: 'Español', flag: '🇪🇸' },
];

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export const LanguageProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [language, setLanguageState] = useState<Language>(() => {
    const saved = localStorage.getItem('gremlins_lang') as Language;
    if (saved && ['en', 'uk', 'pl', 'de', 'es'].includes(saved)) {
      return saved;
    }

    // Auto-detect from Telegram Web App or browser
    try {
      const tgLang = (window as any)?.Telegram?.WebApp?.initDataUnsafe?.user?.language_code;
      const browserLang = navigator.language?.toLowerCase();
      const code = (tgLang || browserLang || 'en').substring(0, 2);

      if (code === 'uk') return 'uk';
      if (code === 'pl') return 'pl';
      if (code === 'de') return 'de';
      if (code === 'es') return 'es';
    } catch {
      // ignore
    }

    return 'en'; // Strict default
  });

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('gremlins_lang', lang);
  };

  const t = translations[language] || translations.en;

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, availableLanguages }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = (): LanguageContextType => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};
