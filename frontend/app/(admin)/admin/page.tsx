"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";

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
import type { UAVStatus } from "@/types/uav";
import type { WorkOrderStatus } from "@/types/work-order";

const FLEET_STATUSES: UAVStatus[] = ["READY", "MAINTENANCE", "GROUNDED", "RETIRED"];
const WORK_ORDER_STATUSES: WorkOrderStatus[] = [
  "OPEN",
  "ASSIGNED",
  "IN_PROGRESS",
  "WAITING_PARTS",
  "COMPLETED",
  "CANCELLED",
];
const FLEET_TONE: Record<UAVStatus, "success" | "warning" | "danger" | "default"> = {
  READY: "success",
  MAINTENANCE: "warning",
  GROUNDED: "danger",
  RETIRED: "default",
};
const WO_TONE: Record<WorkOrderStatus, "info" | "warning" | "success" | "default"> = {
  OPEN: "info",
  ASSIGNED: "info",
  IN_PROGRESS: "warning",
  WAITING_PARTS: "warning",
  COMPLETED: "success",
  CANCELLED: "default",
};

export default function AdminHomePage() {
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
      <PageHeader title={t("admin.overview")} description={t("admin.overviewSubtitle")} />
      <div>
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">{t("navigation.fleet")}</h2>
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
      </div>
      <div>
        <h2 className="mb-3 text-sm font-medium text-muted-foreground">{t("admin.workOrderDistribution")}</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
          {WORK_ORDER_STATUSES.map((status) => (
            <MetricCard
              key={status}
              label={t(`enums.work_order_status.${status}`)}
              value={summary.work_orders.counts[status]}
              href="/work-orders"
              tone={WO_TONE[status]}
            />
          ))}
        </div>
      </div>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>{t("admin.overdueTasks")}</CardTitle>
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
                  {summary.dues.overdue_items.length === 0 ? (
                    <TableRow>
                      <TableCell className="text-muted-foreground" colSpan={3}>
                        {t("admin.emptyOverdue")}
                      </TableCell>
                    </TableRow>
                  ) : (
                    summary.dues.overdue_items.map((item) => (
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
                          <WorkOrderBadge status={item.status} />
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
