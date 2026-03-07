import React, { createContext, useContext, useState, useEffect } from 'react';

const SUPPORTED_LANGUAGES = {
  en: 'English',
  hi: 'हिंदी (Hindi)',
  ta: 'தமிழ் (Tamil)',
  te: 'తెలుగు (Telugu)',
  or: 'ଓଡ଼ିଆ (Odia)'
};

const LanguageContext = createContext();

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within LanguageProvider');
  }
  return context;
};

export const LanguageProvider = ({ children }) => {
  const [language, setLanguage] = useState(() => {
    return localStorage.getItem('app_language') || 'en';
  });

  useEffect(() => {
    localStorage.setItem('app_language', language);
  }, [language]);

  const getTranslatedContent = (content, field = 'question') => {
    if (!content || !content.language_variants) {
      console.log('No translations available for:', field);
      return content?.[field] || '';
    }
    
    console.log('Current language:', language);
    console.log('Available translations:', Object.keys(content.language_variants));
    
    const variant = content.language_variants[language];
    if (variant && variant[field]) {
      console.log(`Using ${language} translation for ${field}:`, variant[field]);
      return variant[field];
    }
    
    // Fallback to English
    console.log(`No ${language} translation, using fallback`);
    return content.language_variants?.en?.[field] || content[field] || '';
  };

  const value = {
    language,
    setLanguage,
    languages: SUPPORTED_LANGUAGES,
    getTranslatedContent
  };

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  );
};

export const LanguageSelector = () => {
  const { language, setLanguage, languages } = useLanguage();

  return (
    <div className="language-selector">
      <select
        value={language}
        onChange={(e) => setLanguage(e.target.value)}
        className="select-input"
        aria-label="Select Language"
      >
        {Object.entries(languages).map(([code, name]) => (
          <option key={code} value={code}>
            {name}
          </option>
        ))}
      </select>
    </div>
  );
};
