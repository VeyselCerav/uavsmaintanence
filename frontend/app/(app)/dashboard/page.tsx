"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { GroupedBarChart, StatusPieChart } from "@/components/system/simple-charts";
import { MetricCard } from "@/components/system/metric-card";
import { PageHeader } from "@/components/system/page-header";
import { DueBadge, WorkOrderBadge } from "@/components/system/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useI18n } from "@/lib/i18n-context";
import { getDashboard } from "@/services/dashboard";
import type { DashboardDueStatus } from "@/types/dashboard";
import type { UAVStatus } from "@/types/uav";
import type { WorkOrderStatus } from "@/types/work-order";

const FLEET_STATUSES: UAVStatus[] = ["READY", "MAINTENANCE", "GROUNDED", "RETIRED"];
const DUE_STATUSES: DashboardDueStatus[] = ["APPROACHING", "DUE", "OVERDUE", "CRITICAL"];
const FLEET_TONE: Record<UAVStatus, "success" | "warning" | "danger" | "default"> = {
  READY: "success",
  MAINTENANCE: "warning",
  GROUNDED: "danger",
  RETIRED: "default",
};
const FLEET_COLOR: Record<UAVStatus, string> = {
  READY: "#2e7d32",
  MAINTENANCE: "#b7791f",
  GROUNDED: "#b42318",
  RETIRED: "#506575",
};
const DUE_TONE: Record<DashboardDueStatus, "info" | "warning" | "danger"> = {
  APPROACHING: "info",
  DUE: "warning",
  OVERDUE: "danger",
  CRITICAL: "danger",
};

export default function DashboardPage() {
  const { t } = useI18n();
  const router = useRouter();
  const query = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
  });
  const summary = query.data;
  const error = query.error instanceof Error ? query.error.message : null;

  if (error) {
    return <p className="text-sm text-destructive">{t(error)}</p>;
  }
  if (!summary) {
    return <p className="text-sm text-muted-foreground">{t("common.loading")}</p>;
  }

  return (
    <section className="space-y-6">
      <PageHeader title={t("dashboard.title")} description={t("dashboard.subtitle")} />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">{t("chart.fleet")}</CardTitle>
          </CardHeader>
          <CardContent>
            <StatusPieChart
              title={t("chart.fleet")}
              slices={FLEET_STATUSES.map((status) => ({
                name: t(`enums.uav_status.${status}`),
                value: summary.fleet[status],
                color: FLEET_COLOR[status],
              }))}
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">{t("chart.dues")}</CardTitle>
          </CardHeader>
          <CardContent>
            <GroupedBarChart
              categories={DUE_STATUSES.map((status) => t(`enums.due_status.${status}`))}
              series={[
                {
                  name: t("dashboard.dues"),
                  color: "#79113e",
                  data: DUE_STATUSES.map((status) => summary.dues.counts[status]),
                },
              ]}
            />
          </CardContent>
        </Card>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {FLEET_STATUSES.map((status) => (
          <MetricCard
            key={status}
            label={t(`enums.uav_status.${status}`)}
            value={summary.fleet[status]}
            href="/uavs"
            tone={FLEET_TONE[status]}
          />
        ))}
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {DUE_STATUSES.map((status) => (
          <MetricCard
            key={status}
            label={t(`enums.due_status.${status}`)}
            value={summary.dues.counts[status]}
            tone={DUE_TONE[status]}
          />
        ))}
        <MetricCard
          label={t("dashboard.openWorkOrders")}
          value={summary.work_orders.counts.open}
          href="/work-orders"
          tone="info"
        />
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label={t("reliability.mtbf")}
          value={summary.reliability?.mtbf_hours ?? "—"}
          href="/reliability"
        />
        <MetricCard
          label={t("reliability.mttr")}
          value={summary.reliability?.mttr_hours ?? "—"}
          href="/reliability"
        />
        <MetricCard
          label={t("reliability.availability")}
          value={summary.reliability?.availability ?? "—"}
          href="/reliability"
        />
        <MetricCard
          label={t("reliability.failures")}
          value={summary.reliability?.failure_count ?? 0}
          href="/failures"
        />
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>{t("dashboard.dues")}</CardTitle>
            <Button asChild variant="outline" size="sm">
              <Link href="/uavs">{t("common.viewAll")}</Link>
            </Button>
          </CardHeader>
          <CardContent>
            <div className="overflow-hidden rounded-lg border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t("uav.registration")}</TableHead>
                    <TableHead>{t("template.taskName")}</TableHead>
                    <TableHead>{t("workOrder.status")}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {summary.dues.items.length === 0 ? (
                    <TableRow>
                      <TableCell className="text-muted-foreground" colSpan={3}>
                        {t("dashboard.emptyDues")}
                      </TableCell>
                    </TableRow>
                  ) : (
                    summary.dues.items.map((item) => (
                      <TableRow
                        key={item.id}
                        className="cursor-pointer"
                        onClick={() => router.push(`/uavs/${item.uav}`)}
                      >
                        <TableCell>{item.uav_registration}</TableCell>
                        <TableCell>{item.task_code}</TableCell>
                        <TableCell>
                          <DueBadge status={item.status} />
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>{t("dashboard.workOrders")}</CardTitle>
            <Button asChild variant="outline" size="sm">
              <Link href="/work-orders">{t("common.viewAll")}</Link>
            </Button>
          </CardHeader>
          <CardContent>
            <div className="overflow-hidden rounded-lg border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>{t("workOrder.number")}</TableHead>
                    <TableHead>{t("uav.registration")}</TableHead>
                    <TableHead>{t("workOrder.status")}</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {summary.work_orders.items.length === 0 ? (
                    <TableRow>
                      <TableCell className="text-muted-foreground" colSpan={3}>
                        {t("dashboard.emptyWorkOrders")}
                      </TableCell>
                    </TableRow>
                  ) : (
                    summary.work_orders.items.map((item) => (
                      <TableRow
                        key={item.id}
                        className="cursor-pointer"
                        onClick={() => router.push(`/work-orders/${item.id}`)}
                      >
                        <TableCell>{item.number}</TableCell>
                        <TableCell>{item.uav_registration}</TableCell>
                        <TableCell>
                          <WorkOrderBadge status={item.status as WorkOrderStatus} />
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
