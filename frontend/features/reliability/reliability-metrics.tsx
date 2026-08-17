"use client";

import { MetricCard } from "@/components/system/metric-card";
import { useI18n } from "@/lib/i18n-context";
import type { ReliabilityMetrics } from "@/types/reliability";

function display(value: string | null, empty: string) {
  return value ?? empty;
}

export function ReliabilityMetricsView({ metrics }: { metrics: ReliabilityMetrics }) {
  const { t } = useI18n();
  const empty = "—";
  const availability =
    metrics.availability == null ? empty : metrics.availability;
  return (
    <div className="space-y-3">
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard label={t("reliability.mtbf")} value={display(metrics.mtbf_hours, empty)} />
        <MetricCard label={t("reliability.mttr")} value={display(metrics.mttr_hours, empty)} />
        <MetricCard label={t("reliability.availability")} value={availability} />
        <MetricCard label={t("reliability.failures")} value={metrics.failure_count} />
      </div>
      <p className="text-sm text-muted-foreground">
        {t("reliability.operating")}: {metrics.operating_hours} · {t("reliability.repairs")}:{" "}
        {metrics.repair_count}
        {metrics.is_lower_bound ? ` · ${t("reliability.lowerBound")}` : ""}
      </p>
    </div>
  );
}
