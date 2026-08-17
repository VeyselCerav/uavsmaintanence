import az from "@/i18n/az.json";
import en from "@/i18n/en.json";
import tr from "@/i18n/tr.json";

export const LOCALES = ["tr", "en", "az"] as const;
export type Locale = (typeof LOCALES)[number];

const dictionaries = { tr, en, az } as const;

export function getDictionary(locale: Locale) {
  return dictionaries[locale] ?? dictionaries.tr;
}

export function translate(locale: Locale, key: string): string {
  const parts = key.split(".");
  let current: unknown = getDictionary(locale);
  for (const part of parts) {
    if (typeof current !== "object" || current === null || !(part in current)) {
      return key;
    }
    current = (current as Record<string, unknown>)[part];
  }
  return typeof current === "string" ? current : key;
}
