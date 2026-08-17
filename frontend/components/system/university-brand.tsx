"use client";

import { useI18n } from "@/lib/i18n-context";
import { cn } from "@/lib/utils";

export function UniversityBrand({ className }: { className?: string }) {
  const { t } = useI18n();

  return (
    <div
      className={cn(
        "flex max-w-[24rem] items-center gap-4 rounded-2xl border border-white/70 bg-white/80 px-4 py-3 shadow-[0_8px_30px_rgba(38,55,70,0.08)] backdrop-blur-md",
        className,
      )}
    >
      <div className="flex h-16 w-16 shrink-0 items-center justify-center rounded-xl bg-white ring-1 ring-[#79113e]/10">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/brand/firat-university-logo.svg"
          alt={t("brand.university")}
          className="h-14 w-14 object-contain"
        />
      </div>
      <div className="min-w-0">
        <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-[#79113e]">
          {t("brand.university")}
        </p>
        <p className="mt-1 text-sm font-semibold leading-snug text-primary">
          {t("brand.program")}
        </p>
        <p className="mt-0.5 text-xs leading-relaxed text-secondary">{t("brand.degree")}</p>
        <div className="mt-2 border-t border-[#79113e]/10 pt-2">
          <p className="text-[11px] font-medium leading-snug text-primary">{t("brand.student")}</p>
          <p className="mt-0.5 text-[11px] leading-snug text-secondary">{t("brand.advisor")}</p>
        </div>
      </div>
    </div>
  );
}
