"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { getStoredUser, subscribeSession } from "@/lib/auth";
import { LOCALES, translate, type Locale } from "@/lib/i18n";

type I18nContextValue = {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: string) => string;
};

const I18nContext = createContext<I18nContextValue | null>(null);
const STORAGE_KEY = "uavs.locale";

function isLocale(value: string | null | undefined): value is Locale {
  return Boolean(value && LOCALES.includes(value as Locale));
}

function readLocale(): Locale {
  if (typeof window === "undefined") return "tr";
  const user = getStoredUser();
  if (isLocale(user?.locale)) return user.locale;
  const stored = localStorage.getItem(STORAGE_KEY);
  if (isLocale(stored)) return stored;
  return "tr";
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("tr");

  useEffect(() => {
    setLocaleState(readLocale());
    return subscribeSession(() => {
      const user = getStoredUser();
      if (isLocale(user?.locale)) {
        setLocaleState(user.locale);
      }
    });
  }, []);

  const value = useMemo(
    () => ({
      locale,
      setLocale: (next: Locale) => {
        setLocaleState(next);
        localStorage.setItem(STORAGE_KEY, next);
      },
      t: (key: string) => translate(locale, key),
    }),
    [locale],
  );
  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    throw new Error("useI18n must be used within I18nProvider");
  }
  return ctx;
}
