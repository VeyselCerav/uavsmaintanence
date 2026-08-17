"use client";

import { PageHeader } from "@/components/system/page-header";
import { useI18n } from "@/lib/i18n-context";

export default function PlaceholderPage({ titleKey }: { titleKey: string }) {
  const { t } = useI18n();
  return (
    <section>
      <PageHeader title={t(titleKey)} description={t("dashboard.placeholder")} />
    </section>
  );
}
