"use client";

import { PageHeader } from "@/components/system/page-header";
import { FMEAHeaderForm } from "@/features/fmea/fmea-header-form";
import { useI18n } from "@/lib/i18n-context";

export default function NewFMEAPage() {
  const { t } = useI18n();
  return (
    <section>
      <PageHeader title={t("fmea.new")} />
      <FMEAHeaderForm />
    </section>
  );
}
