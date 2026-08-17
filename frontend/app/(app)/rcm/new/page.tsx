"use client";

import { PageHeader } from "@/components/system/page-header";
import { RCMHeaderForm } from "@/features/rcm/rcm-header-form";
import { useI18n } from "@/lib/i18n-context";

export default function NewRCMPage() {
  const { t } = useI18n();
  return (
    <section>
      <PageHeader title={t("rcm.new")} />
      <RCMHeaderForm />
    </section>
  );
}
