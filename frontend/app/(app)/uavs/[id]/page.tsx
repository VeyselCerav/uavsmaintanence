"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";

import { PageHeader } from "@/components/system/page-header";
import { DemoBadge, DueBadge, FailureSeverityBadge, RPNBadge, StatusBadge, WorkOrderBadge } from "@/components/system/status-badge";
import { DocumentSection } from "@/features/documents/document-section";
import { InstalledComponents } from "@/features/components/installed-components";
import { ReliabilityMetricsView } from "@/features/reliability/reliability-metrics";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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
import { listFailures } from "@/services/failures";
import { listFMEAs } from "@/services/fmea";
import { listFlights } from "@/services/flights";
import { listDues, listRecords } from "@/services/maintenance";
import { listCosts } from "@/services/parts";
import { listRCMs } from "@/services/rcm";
import { getReliability } from "@/services/reliability";
import { getUAV, getUAVTimeline } from "@/services/uavs";
import { listWorkOrders } from "@/services/work-orders";
import { localeTag } from "@/lib/calendar-range";
import type { DueStatus } from "@/types/maintenance";

const OPEN_WO_DUE_STATUSES: DueStatus[] = ["DUE", "OVERDUE", "CRITICAL"];

export default function UAVDetailPage() {
  const { t, locale } = useI18n();
  const params = useParams<{ id: string }>();
  const user = useSessionUser();
  const canEdit = hasPermission(user, "uav.update");
  const dateFormat = new Intl.DateTimeFormat(localeTag(locale), {
    dateStyle: "short",
    timeStyle: "short",
  });
  const uavQuery = useQuery({
    queryKey: ["uav", params.id],
    queryFn: () => getUAV(params.id),
  });
  const duesQuery = useQuery({
    queryKey: ["dues", params.id],
    queryFn: () => listDues(params.id),
  });
  const flightsQuery = useQuery({
    queryKey: ["flights", "", params.id],
    queryFn: () => listFlights("", params.id),
  });
  const workOrdersQuery = useQuery({
    queryKey: ["work-orders", "", params.id, "open"],
    queryFn: () => listWorkOrders("", params.id, "open"),
  });
  const recordsQuery = useQuery({
    queryKey: ["maintenance-records", "", params.id],
    queryFn: () => listRecords("", params.id),
  });
  const failuresQuery = useQuery({
    queryKey: ["failures", "", "", params.id],
    queryFn: () => listFailures("", "", params.id),
    enabled: hasPermission(user, "failure.view"),
  });
  const fmeaQuery = useQuery({
    queryKey: ["fmeas", "", params.id],
    queryFn: () => listFMEAs("", params.id),
    enabled: hasPermission(user, "fmea.view"),
  });
  const rcmQuery = useQuery({
    queryKey: ["rcms", "", params.id],
    queryFn: () => listRCMs("", params.id),
    enabled: hasPermission(user, "rcm.view"),
  });
  const reliabilityQuery = useQuery({
    queryKey: ["reliability", "uav", params.id],
    queryFn: () => getReliability({ scope: "uav", scopeId: params.id }),
    enabled: hasPermission(user, "reliability.view"),
  });
  const costsQuery = useQuery({
    queryKey: ["costs", params.id],
    queryFn: () => listCosts(params.id),
    enabled: hasPermission(user, "cost.view"),
  });
  const timelineQuery = useQuery({
    queryKey: ["uav-timeline", params.id],
    queryFn: () => getUAVTimeline(params.id),
  });
  const uav = uavQuery.data;
  const dues = duesQuery.data?.data ?? [];
  const flights = flightsQuery.data?.data ?? [];
  const openWorkOrders = workOrdersQuery.data?.data ?? [];
  const records = recordsQuery.data?.data ?? [];
  const failures = failuresQuery.data?.data ?? [];
  const fmeas = fmeaQuery.data?.data ?? [];
  const rcms = rcmQuery.data?.data ?? [];
  const costs = costsQuery.data?.data ?? [];
  const timeline = timelineQuery.data ?? [];
  const canCreateWorkOrder = hasPermission(user, "work_order.create");
  const canViewFailures = hasPermission(user, "failure.view");
  const canViewFmea = hasPermission(user, "fmea.view");
  const canViewRcm = hasPermission(user, "rcm.view");
  const canViewReliability = hasPermission(user, "reliability.view");
  const canViewCost = hasPermission(user, "cost.view");
  const error =
    uavQuery.error instanceof Error
      ? uavQuery.error.message
      : duesQuery.error instanceof Error
        ? duesQuery.error.message
        : null;

  if (error) {
    return <p className="text-sm text-destructive">{t(error)}</p>;
  }
  if (!uav) {
    return <p className="text-sm text-muted-foreground">{t("common.loading")}</p>;
  }

  return (
    <section className="space-y-6">
      <PageHeader title={uav.registration_number}>
        <StatusBadge status={uav.status} />
        <DemoBadge visible={uav.is_demo} />
        <Button asChild variant="outline">
          <Link href="/uavs">{t("common.back")}</Link>
        </Button>
        {canEdit ? (
          <Button asChild>
            <Link href={`/uavs/${uav.id}/edit`}>{t("common.edit")}</Link>
          </Button>
        ) : null}
      </PageHeader>
      <Card>
        <CardContent className="grid grid-cols-2 gap-6 text-sm">
          <div>
            <h2 className="mb-2 font-semibold text-primary">{t("uav.general")}</h2>
            <p>
              {t("uav.serial")}: {uav.serial_number}
            </p>
            <p>
              {t("uav.manufacturer")}: {uav.manufacturer}
            </p>
            <p>
              {t("uav.model")}: {uav.model}
            </p>
          </div>
          <div>
            <h2 className="mb-2 font-semibold text-primary">{t("uav.technical")}</h2>
            <p>
              {t("uav.class")}: {uav.uav_class_name}
            </p>
            <p>
              {t("uav.mtow")}: {uav.mtow_kg ?? "—"}
            </p>
            <p>
              {t("uav.hours")}: {uav.total_flight_hours}
            </p>
            <p>
              {t("uav.cycles")}: {uav.total_flight_cycles}
            </p>
          </div>
          <div>
            <h2 className="mb-2 font-semibold text-primary">{t("uav.operational")}</h2>
            <p>
              {t("uav.platform")}: {uav.platform_name}
            </p>
            <p>
              {t("uav.mission")}: {uav.mission_name}
            </p>
          </div>
          <div>
            <h2 className="mb-2 font-semibold text-primary">{t("uav.maintenance")}</h2>
            <p>
              {t("uav.approach")}: {t(`enums.maintenance_approach.${uav.maintenance_approach}`)}
            </p>
            <p>
              {t("uav.template")}: {uav.template_code ?? t("uav.noTemplate")}
              {uav.template_name ? ` — ${uav.template_name}` : ""}
            </p>
            {uav.is_demo ? <p className="mt-2 text-warning">{uav.notes}</p> : <p>{uav.notes}</p>}
          </div>
        </CardContent>
      </Card>
      <InstalledComponents uavId={uav.id} />
      <div>
        <h2 className="mb-3 text-base font-semibold text-primary">{t("due.title")}</h2>
        <div className="overflow-hidden rounded-lg border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("template.taskCode")}</TableHead>
                <TableHead>{t("template.taskName")}</TableHead>
                <TableHead>{t("template.componentType")}</TableHead>
                <TableHead>{t("due.usage")}</TableHead>
                <TableHead>{t("due.remaining")}</TableHead>
                <TableHead>{t("due.status")}</TableHead>
                <TableHead>{t("common.actions")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {dues.length === 0 ? (
                <TableRow>
                  <TableCell className="text-muted-foreground" colSpan={7}>
                    {t("due.empty")}
                  </TableCell>
                </TableRow>
              ) : (
                dues.map((due) => {
                  const existing = openWorkOrders.find(
                    (item) =>
                      item.component === due.component && item.template_item === due.template_item,
                  );
                  const canOpen =
                    canCreateWorkOrder && !existing && OPEN_WO_DUE_STATUSES.includes(due.status);
                  return (
                    <TableRow key={due.id}>
                      <TableCell>{due.task_code}</TableCell>
                      <TableCell>{due.task_name}</TableCell>
                      <TableCell>
                        {due.component_type_name}
                        {due.component_serial ? ` (${due.component_serial})` : ""}
                      </TableCell>
                      <TableCell>{due.usage_percent}%</TableCell>
                      <TableCell>
                        {due.remaining_value} {t(`enums.interval_unit.${due.remaining_unit}`)}
                      </TableCell>
                      <TableCell>
                        <DueBadge status={due.status} />
                      </TableCell>
                      <TableCell>
                        {existing ? (
                          <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
                            <Link href={`/work-orders/${existing.id}`}>{existing.number}</Link>
                          </Button>
                        ) : canOpen ? (
                          <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
                            <Link href={`/work-orders/new?uav=${uav.id}&due=${due.id}`}>
                              {t("workOrder.openFromDue")}
                            </Link>
                          </Button>
                        ) : (
                          "—"
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>
      </div>
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-primary">{t("workOrder.openTitle")}</h2>
          {canCreateWorkOrder ? (
            <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
              <Link href={`/work-orders/new?uav=${uav.id}`}>{t("workOrder.new")}</Link>
            </Button>
          ) : null}
        </div>
        <div className="overflow-hidden rounded-lg border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("workOrder.number")}</TableHead>
                <TableHead>{t("template.taskName")}</TableHead>
                <TableHead>{t("workOrder.assignee")}</TableHead>
                <TableHead>{t("workOrder.status")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {openWorkOrders.length === 0 ? (
                <TableRow>
                  <TableCell className="text-muted-foreground" colSpan={4}>
                    {t("workOrder.empty")}
                  </TableCell>
                </TableRow>
              ) : (
                openWorkOrders.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
                        <Link href={`/work-orders/${item.id}`}>{item.number}</Link>
                      </Button>
                    </TableCell>
                    <TableCell>{item.task_name ?? "—"}</TableCell>
                    <TableCell>{item.assigned_name ?? "—"}</TableCell>
                    <TableCell>
                      <WorkOrderBadge status={item.status} />
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-primary">{t("record.title")}</h2>
          <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
            <Link href="/maintenance/records">{t("common.viewAll")}</Link>
          </Button>
        </div>
        <div className="overflow-hidden rounded-lg border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("record.performedAt")}</TableHead>
                <TableHead>{t("workOrder.number")}</TableHead>
                <TableHead>{t("template.taskName")}</TableHead>
                <TableHead>{t("workOrder.assignee")}</TableHead>
                <TableHead>{t("workOrder.type")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {records.length === 0 ? (
                <TableRow>
                  <TableCell className="text-muted-foreground" colSpan={5}>
                    {t("record.empty")}
                  </TableCell>
                </TableRow>
              ) : (
                records.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>{dateFormat.format(new Date(item.performed_at))}</TableCell>
                    <TableCell>
                      <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
                        <Link href={`/work-orders/${item.work_order}`}>{item.work_order_number}</Link>
                      </Button>
                    </TableCell>
                    <TableCell>{item.task_name ?? item.description ?? "—"}</TableCell>
                    <TableCell>{item.technician_name ?? "—"}</TableCell>
                    <TableCell>{t(`enums.maintenance_type.${item.maintenance_type}`)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>
      {canViewFailures ? (
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-primary">{t("failure.title")}</h2>
          <div className="flex gap-3">
            {hasPermission(user, "failure.create") ? (
              <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
                <Link href="/failures/new">{t("failure.new")}</Link>
              </Button>
            ) : null}
            <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
              <Link href="/failures">{t("common.viewAll")}</Link>
            </Button>
          </div>
        </div>
        <div className="overflow-hidden rounded-lg border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("failure.occurredAt")}</TableHead>
                <TableHead>{t("failure.mode")}</TableHead>
                <TableHead>{t("failure.severity")}</TableHead>
                <TableHead>{t("failure.status")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {failures.length === 0 ? (
                <TableRow>
                  <TableCell className="text-muted-foreground" colSpan={4}>
                    {t("failure.empty")}
                  </TableCell>
                </TableRow>
              ) : (
                failures.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
                        <Link href={`/failures/${item.id}`}>
                          {dateFormat.format(new Date(item.occurred_at))}
                        </Link>
                      </Button>
                    </TableCell>
                    <TableCell>{item.failure_mode_code || "—"}</TableCell>
                    <TableCell>
                      <FailureSeverityBadge severity={item.severity} />
                    </TableCell>
                    <TableCell>
                      {item.resolved_at ? t("failure.resolved") : t("failure.open")}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>
      ) : null}
      {canViewFmea ? (
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-primary">{t("fmea.title")}</h2>
          <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
            <Link href="/fmea">{t("common.viewAll")}</Link>
          </Button>
        </div>
        <div className="overflow-hidden rounded-lg border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("catalog.code")}</TableHead>
                <TableHead>{t("template.componentType")}</TableHead>
                <TableHead>{t("fmea.status")}</TableHead>
                <TableHead>RPN</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {fmeas.length === 0 ? (
                <TableRow>
                  <TableCell className="text-muted-foreground" colSpan={4}>
                    {t("fmea.empty")}
                  </TableCell>
                </TableRow>
              ) : (
                fmeas.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
                        <Link href={`/fmea/${item.id}`}>{item.code}</Link>
                      </Button>
                    </TableCell>
                    <TableCell>{item.component_type_name}</TableCell>
                    <TableCell>{t(`enums.fmea_status.${item.status}`)}</TableCell>
                    <TableCell>
                      <RPNBadge rpn={item.max_rpn} band={item.rpn_band} />
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>
      ) : null}
      {canViewRcm ? (
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-primary">{t("rcm.title")}</h2>
          <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
            <Link href="/rcm">{t("common.viewAll")}</Link>
          </Button>
        </div>
        <div className="overflow-hidden rounded-lg border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("catalog.code")}</TableHead>
                <TableHead>{t("template.componentType")}</TableHead>
                <TableHead>{t("rcm.status")}</TableHead>
                <TableHead>{t("rcm.strategy")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {rcms.length === 0 ? (
                <TableRow>
                  <TableCell className="text-muted-foreground" colSpan={4}>
                    {t("rcm.empty")}
                  </TableCell>
                </TableRow>
              ) : (
                rcms.map((item) => {
                  const strategies = [...new Set((item.items ?? []).map((row) => row.strategy))];
                  return (
                    <TableRow key={item.id}>
                      <TableCell>
                        <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
                          <Link href={`/rcm/${item.id}`}>{item.code}</Link>
                        </Button>
                      </TableCell>
                      <TableCell>{item.component_type_name}</TableCell>
                      <TableCell>{t(`enums.rcm_status.${item.status}`)}</TableCell>
                      <TableCell>
                        {strategies.length === 1
                          ? t(`enums.rcm_strategy.${strategies[0]}`)
                          : strategies.length === 0
                            ? "—"
                            : t("rcm.mixedStrategy")}
                      </TableCell>
                    </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </div>
      </div>
      ) : null}
      {canViewReliability && reliabilityQuery.data ? (
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-primary">{t("reliability.title")}</h2>
          <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
            <Link href="/reliability">{t("common.viewAll")}</Link>
          </Button>
        </div>
        <ReliabilityMetricsView metrics={reliabilityQuery.data} />
      </div>
      ) : null}
      {canViewCost ? (
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-primary">{t("cost.title")}</h2>
        </div>
        <div className="overflow-hidden rounded-lg border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("cost.occurredAt")}</TableHead>
                <TableHead>{t("workOrder.number")}</TableHead>
                <TableHead>{t("cost.part")}</TableHead>
                <TableHead>{t("cost.labor")}</TableHead>
                <TableHead>{t("cost.total")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {costs.length === 0 ? (
                <TableRow>
                  <TableCell className="text-muted-foreground" colSpan={5}>
                    {t("cost.empty")}
                  </TableCell>
                </TableRow>
              ) : (
                costs.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>{dateFormat.format(new Date(item.occurred_at))}</TableCell>
                    <TableCell>{item.work_order_number || "—"}</TableCell>
                    <TableCell>{item.part_cost}</TableCell>
                    <TableCell>{item.labor_cost}</TableCell>
                    <TableCell>
                      {item.total_cost} {item.currency}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>
      ) : null}
      <DocumentSection uavId={uav.id} />
      <div>
        <h2 className="mb-3 text-base font-semibold text-primary">{t("timeline.title")}</h2>
        <div className="overflow-hidden rounded-lg border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("timeline.occurredAt")}</TableHead>
                <TableHead>{t("timeline.event")}</TableHead>
                <TableHead>{t("timeline.detail")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {timeline.length === 0 ? (
                <TableRow>
                  <TableCell className="text-muted-foreground" colSpan={3}>
                    {t("timeline.empty")}
                  </TableCell>
                </TableRow>
              ) : (
                timeline.map((item) => (
                  <TableRow key={`${item.event_type}-${item.entity_id}-${item.occurred_at}`}>
                    <TableCell>{dateFormat.format(new Date(item.occurred_at))}</TableCell>
                    <TableCell>{t(`timeline.${item.event_type}`)}</TableCell>
                    <TableCell>{item.detail}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-primary">{t("flight.title")}</h2>
          {hasPermission(user, "flight.create") ? (
            <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
              <Link href="/flights/new">{t("flight.new")}</Link>
            </Button>
          ) : null}
        </div>
        <div className="overflow-hidden rounded-lg border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("flight.number")}</TableHead>
                <TableHead>{t("flight.flownOn")}</TableHead>
                <TableHead>{t("flight.duration")}</TableHead>
                <TableHead>{t("flight.counters")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {flights.length === 0 ? (
                <TableRow>
                  <TableCell className="text-muted-foreground" colSpan={4}>
                    {t("flight.empty")}
                  </TableCell>
                </TableRow>
              ) : (
                flights.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>
                      <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
                        <Link href={`/flights/${item.id}`}>{item.flight_number}</Link>
                      </Button>
                    </TableCell>
                    <TableCell>{item.flown_on}</TableCell>
                    <TableCell>{item.duration_hours}</TableCell>
                    <TableCell>
                      {item.counters_applied ? t("flight.applied") : t("flight.pending")}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    </section>
  );
}
