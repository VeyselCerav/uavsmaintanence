"use client";

import { PageHeader } from "@/components/system/page-header";
import { PartForm } from "@/features/parts/part-form";
import { useI18n } from "@/lib/i18n-context";

export default function NewPartPage() {
  const { t } = useI18n();
  return (
    <section>
      <PageHeader title={t("part.new")} />
      <PartForm />
    </section>
  );
}
