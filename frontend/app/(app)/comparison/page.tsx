"use client";

import { useQuery } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { GroupedBarChart } from "@/components/system/simple-charts";
import { MetricCard } from "@/components/system/metric-card";
import { PageHeader } from "@/components/system/page-header";
import { DemoBadge } from "@/components/system/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useSessionUser } from "@/hooks/use-session-user";
import { hasPermission } from "@/lib/auth";
import { useI18n } from "@/lib/i18n-context";
import { ApiClientError } from "@/services/api";
import { getApproachComparison } from "@/services/comparison";
import { downloadReport } from "@/services/reports";
import { listClasses, listMissions, listPlatforms } from "@/services/uavs";
import type { ComparisonArm } from "@/types/comparison";

function display(value: string | number | null | undefined) {
  if (value === null || value === undefined || value === "") return "—";
  return String(value);
}

export default function ComparisonPage() {
  const { t, locale } = useI18n();
  const user = useSessionUser();
  const canExport = hasPermission(user, "reports.export");
  const [classId, setClassId] = useState("");
  const [platformId, setPlatformId] = useState("");
  const [missionId, setMissionId] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [applied, setApplied] = useState({
    classId: "",
    platformId: "",
    missionId: "",
    from: "",
    to: "",
  });
  const classes = useQuery({ queryKey: ["uav-classes"], queryFn: listClasses });
  const platforms = useQuery({ queryKey: ["platforms"], queryFn: listPlatforms });
  const missions = useQuery({ queryKey: ["missions"], queryFn: listMissions });
  const query = useQuery({
    queryKey: ["approach-comparison", applied],
    queryFn: () =>
      getApproachComparison({
        classId: applied.classId,
        platformId: applied.platformId,
        missionId: applied.missionId,
        from: applied.from,
        to: applied.to,
      }),
  });
  const error = query.error instanceof ApiClientError ? query.error.message_key : query.error instanceof Error ? query.error.message : null;
  const standard = query.data?.arms.find((arm) => arm.approach === "STANDARD");
  const specific = query.data?.arms.find((arm) => arm.approach === "CLASS_SPECIFIC");

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setApplied({ classId, platformId, missionId, from, to });
  }

  async function onExport(kind: "pdf" | "xlsx") {
    await downloadReport(kind, "approach-comparison", {
      class: applied.classId,
      platform: applied.platformId,
      mission: applied.missionId,
      from: applied.from,
      to: applied.to,
      locale,
    });
  }

  return (
    <section className="space-y-4">
      <PageHeader title={t("comparison.title")} description={t("comparison.hint")} />
      {query.data?.is_demo ? <DemoBadge visible /> : null}
      <form onSubmit={onSubmit} className="flex flex-wrap gap-2">
        <NativeSelect className="w-48" value={classId} onChange={(event) => setClassId(event.target.value)}>
          <option value="">{t("part.allClasses")}</option>
          {(classes.data?.data ?? []).map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </NativeSelect>
        <NativeSelect className="w-48" value={platformId} onChange={(event) => setPlatformId(event.target.value)}>
          <option value="">{t("part.allPlatforms")}</option>
          {(platforms.data?.data ?? []).map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </NativeSelect>
        <NativeSelect className="w-48" value={missionId} onChange={(event) => setMissionId(event.target.value)}>
          <option value="">{t("comparison.allMissions")}</option>
          {(missions.data?.data ?? []).map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </NativeSelect>
        <Input type="date" className="w-40" value={from} onChange={(event) => setFrom(event.target.value)} />
        <Input type="date" className="w-40" value={to} onChange={(event) => setTo(event.target.value)} />
        <Button type="submit">{t("common.search")}</Button>
        {canExport ? (
          <>
            <Button type="button" variant="outline" onClick={() => onExport("pdf")}>
              {t("report.downloadPdf")}
            </Button>
            <Button type="button" variant="outline" onClick={() => onExport("xlsx")}>
              {t("report.downloadXlsx")}
            </Button>
          </>
        ) : null}
      </form>
      {error ? <p className="text-sm text-destructive">{t(error)}</p> : null}
      {query.isLoading ? <p className="text-sm text-muted-foreground">{t("common.loading")}</p> : null}
      {standard && specific ? (
        <>
          <div className="grid gap-4 lg:grid-cols-2">
            <ApproachCard arm={standard} />
            <ApproachCard arm={specific} />
          </div>
          <Card>
            <CardHeader>
              <CardTitle className="text-sm">{t("chart.comparison")}</CardTitle>
            </CardHeader>
            <CardContent>
              <GroupedBarChart
                categories={[
                  t("comparison.uavs"),
                  t("comparison.templateItems"),
                  t("comparison.dueAttention"),
                  t("reliability.failures"),
                  t("comparison.openWorkOrders"),
                ]}
                series={[
                  {
                    name: t("enums.maintenance_approach.STANDARD"),
                    color: "#506575",
                    data: [
                      standard.uav_count,
                      standard.template_item_count,
                      standard.due_attention,
                      standard.failure_count,
                      standard.work_order_open,
                    ],
                  },
                  {
                    name: t("enums.maintenance_approach.CLASS_SPECIFIC"),
                    color: "#79113e",
                    data: [
                      specific.uav_count,
                      specific.template_item_count,
                      specific.due_attention,
                      specific.failure_count,
                      specific.work_order_open,
                    ],
                  },
                ]}
              />
            </CardContent>
          </Card>
          <ComparisonTable standard={standard} specific={specific} />
        </>
      ) : null}
    </section>
  );
}

function ApproachCard({ arm }: { arm: ComparisonArm }) {
  const { t } = useI18n();
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-primary">{t(`enums.maintenance_approach.${arm.approach}`)}</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-3 sm:grid-cols-2">
        <MetricCard label={t("comparison.uavs")} value={arm.uav_count} />
        <MetricCard label={t("comparison.templateItems")} value={arm.template_item_count} />
        <MetricCard label={t("comparison.dueAttention")} value={arm.due_attention} tone={arm.due_attention ? "warning" : "default"} />
        <MetricCard label={t("comparison.dueOverdue")} value={arm.due_overdue} tone={arm.due_overdue ? "danger" : "default"} />
        <MetricCard label={t("reliability.mtbf")} value={display(arm.mtbf_hours)} />
        <MetricCard label={t("reliability.availability")} value={display(arm.availability)} />
      </CardContent>
    </Card>
  );
}

function ComparisonTable({ standard, specific }: { standard: ComparisonArm; specific: ComparisonArm }) {
  const { t } = useI18n();
  const rows: { key: string; standard: string; specific: string }[] = [
    { key: "comparison.uavs", standard: display(standard.uav_count), specific: display(specific.uav_count) },
    { key: "comparison.templates", standard: display(standard.template_count), specific: display(specific.template_count) },
    { key: "comparison.templateItems", standard: display(standard.template_item_count), specific: display(specific.template_item_count) },
    { key: "comparison.dueAttention", standard: display(standard.due_attention), specific: display(specific.due_attention) },
    { key: "comparison.dueOverdue", standard: display(standard.due_overdue), specific: display(specific.due_overdue) },
    { key: "comparison.openWorkOrders", standard: display(standard.work_order_open), specific: display(specific.work_order_open) },
    { key: "reliability.failures", standard: display(standard.failure_count), specific: display(specific.failure_count) },
    { key: "reliability.operating", standard: display(standard.operating_hours), specific: display(specific.operating_hours) },
    { key: "reliability.mtbf", standard: display(standard.mtbf_hours), specific: display(specific.mtbf_hours) },
    { key: "reliability.mttr", standard: display(standard.mttr_hours), specific: display(specific.mttr_hours) },
    { key: "reliability.availability", standard: display(standard.availability), specific: display(specific.availability) },
    { key: "cost.total", standard: display(standard.cost_total), specific: display(specific.cost_total) },
  ];
  return (
    <Card>
      <CardContent className="pt-6">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("comparison.metric")}</TableHead>
              <TableHead>{t("enums.maintenance_approach.STANDARD")}</TableHead>
              <TableHead>{t("enums.maintenance_approach.CLASS_SPECIFIC")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.key}>
                <TableCell>{t(row.key)}</TableCell>
                <TableCell className="tabular-nums">{row.standard}</TableCell>
                <TableCell className="tabular-nums">{row.specific}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
