"use client";

import { PageHeader } from "@/components/system/page-header";
import { FailureForm } from "@/features/failure/failure-form";
import { useI18n } from "@/lib/i18n-context";

export default function NewFailurePage() {
  const { t } = useI18n();
  return (
    <section>
      <PageHeader title={t("failure.new")} />
      <FailureForm />
    </section>
  );
}
