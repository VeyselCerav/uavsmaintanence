"use client";

import { PageHeader } from "@/components/system/page-header";
import { TemplateHeaderForm } from "@/features/maintenance/template-header-form";
import { useI18n } from "@/lib/i18n-context";

export default function NewTemplatePage() {
  const { t } = useI18n();
  return (
    <section>
      <PageHeader title={t("template.new")} />
      <TemplateHeaderForm />
    </section>
  );
}
