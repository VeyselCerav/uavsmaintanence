"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { Field } from "@/components/system/field";
import { PageHeader } from "@/components/system/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";
import { useSessionUser } from "@/hooks/use-session-user";
import { hasPermission } from "@/lib/auth";
import { useI18n } from "@/lib/i18n-context";
import { ApiClientError } from "@/services/api";
import { downloadReport, PDF_TYPES, XLSX_TYPES, type PdfReportType, type XlsxReportType } from "@/services/reports";
import { listUAVs } from "@/services/uavs";

export default function ReportsPage() {
  const { t, locale } = useI18n();
  const user = useSessionUser();
  const canExport = hasPermission(user, "reports.export");
  const [pdfType, setPdfType] = useState<PdfReportType>("fleet");
  const [xlsxType, setXlsxType] = useState<XlsxReportType>("uavs");
  const [uavId, setUavId] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<"pdf" | "xlsx" | null>(null);
  const uavs = useQuery({
    queryKey: ["uavs", "report"],
    queryFn: () => listUAVs(),
  });

  async function onDownload(kind: "pdf" | "xlsx") {
    setError(null);
    const reportType = kind === "pdf" ? pdfType : xlsxType;
    if (kind === "pdf" && pdfType === "uav-history" && !uavId) {
      setError("errors.report.uav_required");
      return;
    }
    setPending(kind);
    try {
      await downloadReport(kind, reportType, {
        uav: uavId,
        from,
        to,
        locale,
        scope: uavId ? "uav" : "fleet",
        scope_id: uavId,
      });
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    } finally {
      setPending(null);
    }
  }

  return (
    <section className="max-w-3xl space-y-4">
      <PageHeader title={t("report.title")} description={t("report.hint")} />
      {error ? <p className="text-sm text-destructive">{t(error)}</p> : null}
      <Card>
        <CardContent className="space-y-4 pt-6">
          <div className="grid grid-cols-2 gap-3">
            <Field label={t("uav.title")}>
              <NativeSelect value={uavId} onChange={(event) => setUavId(event.target.value)}>
                <option value="">{t("report.allUavs")}</option>
                {(uavs.data?.data ?? []).map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.registration_number}
                  </option>
                ))}
              </NativeSelect>
            </Field>
            <Field label={t("report.from")}>
              <Input type="date" value={from} onChange={(event) => setFrom(event.target.value)} />
            </Field>
            <Field label={t("report.to")}>
              <Input type="date" value={to} onChange={(event) => setTo(event.target.value)} />
            </Field>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <Field label={t("report.pdf")}>
              <NativeSelect
                value={pdfType}
                onChange={(event) => setPdfType(event.target.value as PdfReportType)}
              >
                {PDF_TYPES.map((item) => (
                  <option key={item} value={item}>
                    {t(`report.types.${item}`)}
                  </option>
                ))}
              </NativeSelect>
            </Field>
            <Field label={t("report.xlsx")}>
              <NativeSelect
                value={xlsxType}
                onChange={(event) => setXlsxType(event.target.value as XlsxReportType)}
              >
                {XLSX_TYPES.map((item) => (
                  <option key={item} value={item}>
                    {t(`report.types.${item}`)}
                  </option>
                ))}
              </NativeSelect>
            </Field>
          </div>
          {canExport ? (
            <div className="flex gap-2">
              <Button type="button" disabled={pending !== null} onClick={() => onDownload("pdf")}>
                {pending === "pdf" ? t("common.loading") : t("report.downloadPdf")}
              </Button>
              <Button
                type="button"
                variant="outline"
                disabled={pending !== null}
                onClick={() => onDownload("xlsx")}
              >
                {pending === "xlsx" ? t("common.loading") : t("report.downloadXlsx")}
              </Button>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">{t("report.exportDenied")}</p>
          )}
        </CardContent>
      </Card>
    </section>
  );
}
