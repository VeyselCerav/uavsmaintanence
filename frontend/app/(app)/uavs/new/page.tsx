"use client";

import { PageHeader } from "@/components/system/page-header";
import { UAVForm } from "@/features/uav/uav-form";
import { useI18n } from "@/lib/i18n-context";

export default function NewUAVPage() {
  const { t } = useI18n();
  return (
    <section>
      <PageHeader title={t("uav.new")} />
      <UAVForm />
    </section>
  );
}
