"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";

import { PageHeader } from "@/components/system/page-header";
import { DocumentForm } from "@/features/documents/document-form";
import { useI18n } from "@/lib/i18n-context";

function NewDocumentForm() {
  const { t } = useI18n();
  const params = useSearchParams();
  return (
    <section>
      <PageHeader title={t("document.new")} description={t("document.storageHint")} />
      <DocumentForm
        defaultUav={params.get("uav") ?? ""}
        defaultWorkOrder={params.get("work_order") ?? ""}
        defaultTemplate={params.get("template") ?? ""}
      />
    </section>
  );
}

export default function NewDocumentPage() {
  const { t } = useI18n();
  return (
    <Suspense fallback={<p className="text-sm text-muted-foreground">{t("common.loading")}</p>}>
      <NewDocumentForm />
    </Suspense>
  );
}
