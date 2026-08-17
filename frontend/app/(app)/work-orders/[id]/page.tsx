"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { DocumentSection } from "@/features/documents/document-section";
import { Field } from "@/components/system/field";
import { PageHeader } from "@/components/system/page-header";
import { DemoBadge, WorkOrderBadge } from "@/components/system/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
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
import {
  assignWorkOrder,
  cancelWorkOrder,
  completeWorkOrder,
  getWorkOrder,
  listAssignees,
  startWorkOrder,
  waitingPartsWorkOrder,
} from "@/services/work-orders";
import {
  createWorkOrderPart,
  deleteWorkOrderPart,
  listCosts,
  listParts,
  listWorkOrderParts,
  updateCost,
} from "@/services/parts";

export default function WorkOrderDetailPage() {
  const { t } = useI18n();
  const params = useParams<{ id: string }>();
  const user = useSessionUser();
  const queryClient = useQueryClient();
  const [findings, setFindings] = useState("");
  const [assigneeId, setAssigneeId] = useState("");
  const [partId, setPartId] = useState("");
  const [quantity, setQuantity] = useState("1.00");
  const [laborCost, setLaborCost] = useState("");
  const [otherCost, setOtherCost] = useState("");
  const query = useQuery({
    queryKey: ["work-order", params.id],
    queryFn: () => getWorkOrder(params.id),
  });
  const assignees = useQuery({
    queryKey: ["wo-assignees"],
    queryFn: listAssignees,
    enabled: hasPermission(user, "work_order.assign"),
  });
  const workOrder = query.data;
  const canUpdateWo = hasPermission(user, "work_order.update");
  const partsQuery = useQuery({
    queryKey: ["wo-parts", params.id],
    queryFn: () => listWorkOrderParts(params.id),
  });
  const catalogParts = useQuery({
    queryKey: ["parts", ""],
    queryFn: () => listParts(),
    enabled: canUpdateWo,
  });
  const costsQuery = useQuery({
    queryKey: ["costs", "wo", params.id],
    queryFn: () => listCosts("", params.id),
    enabled: hasPermission(user, "cost.view"),
  });

  async function invalidate(savedUav?: string) {
    await queryClient.invalidateQueries({ queryKey: ["work-order", params.id] });
    await queryClient.invalidateQueries({ queryKey: ["work-orders"] });
    await queryClient.invalidateQueries({ queryKey: ["wo-parts", params.id] });
    await queryClient.invalidateQueries({ queryKey: ["costs", "wo", params.id] });
    if (savedUav) {
      await queryClient.invalidateQueries({ queryKey: ["dues", savedUav] });
      await queryClient.invalidateQueries({ queryKey: ["uav", savedUav] });
      await queryClient.invalidateQueries({ queryKey: ["maintenance-records"] });
    }
  }

  const mutation = useMutation({
    mutationFn: async (action: string) => {
      if (action === "assign") return assignWorkOrder(params.id, assigneeId);
      if (action === "start") return startWorkOrder(params.id);
      if (action === "waiting") return waitingPartsWorkOrder(params.id);
      if (action === "complete") return completeWorkOrder(params.id, findings);
      return cancelWorkOrder(params.id);
    },
    onSuccess: async (saved) => {
      await invalidate(saved.uav);
    },
  });
  const error =
    mutation.error instanceof ApiClientError
      ? mutation.error.message_key
      : query.error instanceof Error
        ? query.error.message
        : null;

  if (!workOrder && !error) {
    return <p className="text-sm text-muted-foreground">{t("common.loading")}</p>;
  }
  if (!workOrder) {
    return <p className="text-sm text-destructive">{t(error ?? "errors.generic")}</p>;
  }

  const status = workOrder.status;
  const canAssign = hasPermission(user, "work_order.assign") && (status === "OPEN" || status === "ASSIGNED");
  const canStart =
    hasPermission(user, "work_order.start") && (status === "ASSIGNED" || status === "WAITING_PARTS");
  const canWait = hasPermission(user, "work_order.update") && status === "IN_PROGRESS";
  const canComplete =
    hasPermission(user, "work_order.complete") && (status === "IN_PROGRESS" || status === "WAITING_PARTS");
  const canCancel =
    hasPermission(user, "work_order.cancel") && status !== "COMPLETED" && status !== "CANCELLED";

  return (
    <section className="space-y-6">
      <PageHeader title={workOrder.number}>
        <WorkOrderBadge status={workOrder.status} />
        <DemoBadge visible={workOrder.is_demo} />
        <Button asChild variant="outline">
          <Link href="/work-orders">{t("common.back")}</Link>
        </Button>
      </PageHeader>
      {error ? <p className="text-sm text-destructive">{t(error)}</p> : null}
      <Card>
        <CardContent className="grid grid-cols-2 gap-6 text-sm">
          <p>
            {t("uav.registration")}:{" "}
            <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
              <Link href={`/uavs/${workOrder.uav}`}>{workOrder.uav_registration}</Link>
            </Button>
          </p>
          <p>
            {t("template.taskName")}: {workOrder.task_code} {workOrder.task_name}
          </p>
          <p>
            {t("template.componentType")}: {workOrder.component_name ?? "—"}
          </p>
          <p>
            {t("workOrder.type")}: {t(`enums.maintenance_type.${workOrder.maintenance_type}`)}
          </p>
          <p>
            {t("template.priority")}: {t(`enums.priority.${workOrder.priority}`)}
          </p>
          <p>
            {t("workOrder.assignee")}: {workOrder.assigned_name ?? "—"}
          </p>
        </CardContent>
      </Card>
      <div className="flex flex-wrap gap-2">
        {canAssign ? (
          <>
            <NativeSelect
              className="w-64"
              value={assigneeId}
              onChange={(event) => setAssigneeId(event.target.value)}
            >
              <option value="">{t("workOrder.assignee")}</option>
              {(assignees.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.employee_number} — {item.full_name}
                </option>
              ))}
            </NativeSelect>
            <Button
              type="button"
              disabled={!assigneeId || mutation.isPending}
              onClick={() => mutation.mutate("assign")}
            >
              {t("workOrder.assign")}
            </Button>
          </>
        ) : null}
        {canStart ? (
          <Button type="button" onClick={() => mutation.mutate("start")}>
            {t("workOrder.start")}
          </Button>
        ) : null}
        {canWait ? (
          <Button type="button" variant="outline" onClick={() => mutation.mutate("waiting")}>
            {t("workOrder.waitingParts")}
          </Button>
        ) : null}
        {canComplete ? (
          <>
            <Input
              className="w-64"
              placeholder={t("workOrder.findings")}
              value={findings}
              onChange={(event) => setFindings(event.target.value)}
            />
            <Button type="button" onClick={() => mutation.mutate("complete")}>
              {t("workOrder.complete")}
            </Button>
          </>
        ) : null}
        {canCancel ? (
          <Button
            type="button"
            variant="ghost"
            className="text-destructive"
            onClick={() => mutation.mutate("cancel")}
          >
            {t("workOrder.cancel")}
          </Button>
        ) : null}
      </div>
      <div className="space-y-3">
        <h2 className="text-base font-semibold text-primary">{t("part.title")}</h2>
        <div className="overflow-hidden rounded-lg border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("part.number")}</TableHead>
                <TableHead>{t("part.qty")}</TableHead>
                <TableHead>{t("cost.total")}</TableHead>
                {canUpdateWo ? <TableHead>{t("common.actions")}</TableHead> : null}
              </TableRow>
            </TableHeader>
            <TableBody>
              {(partsQuery.data?.data ?? []).length === 0 ? (
                <TableRow>
                  <TableCell className="text-muted-foreground" colSpan={canUpdateWo ? 4 : 3}>
                    {t("part.emptyLines")}
                  </TableCell>
                </TableRow>
              ) : (
                (partsQuery.data?.data ?? []).map((line) => (
                  <TableRow key={line.id}>
                    <TableCell>
                      {line.part_number} — {line.part_name}
                    </TableCell>
                    <TableCell>{line.quantity}</TableCell>
                    <TableCell>
                      {line.line_cost} {line.currency}
                    </TableCell>
                    {canUpdateWo ? (
                      <TableCell>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="text-destructive"
                          onClick={async () => {
                            try {
                              await deleteWorkOrderPart(params.id, line.id);
                              await invalidate(workOrder.uav);
                            } catch {
                              /* listed via next fetch */
                            }
                          }}
                        >
                          {t("common.delete")}
                        </Button>
                      </TableCell>
                    ) : null}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
        {canUpdateWo ? (
          <div className="flex flex-wrap gap-2">
            <NativeSelect className="w-64" value={partId} onChange={(event) => setPartId(event.target.value)}>
              <option value="">{t("part.select")}</option>
              {(catalogParts.data?.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.part_number} — {item.name}
                </option>
              ))}
            </NativeSelect>
            <Input className="w-28" value={quantity} onChange={(event) => setQuantity(event.target.value)} />
            <Button
              type="button"
              disabled={!partId}
              onClick={async () => {
                try {
                  await createWorkOrderPart(params.id, { part: partId, quantity });
                  setPartId("");
                  await invalidate(workOrder.uav);
                  await queryClient.invalidateQueries({ queryKey: ["parts"] });
                } catch {
                  /* listed via next fetch */
                }
              }}
            >
              {t("part.issue")}
            </Button>
          </div>
        ) : null}
      </div>
      {hasPermission(user, "cost.view") ? (
        <div className="space-y-3">
          <h2 className="text-base font-semibold text-primary">{t("cost.title")}</h2>
          {(costsQuery.data?.data ?? []).map((item) => (
            <p key={item.id} className="text-sm">
              {t("cost.part")}: {item.part_cost} · {t("cost.labor")}: {item.labor_cost} ·{" "}
              {t("cost.other")}: {item.other_cost} · {t("cost.total")}: {item.total_cost} {item.currency}
            </p>
          ))}
          {canUpdateWo && (costsQuery.data?.data ?? []).length > 0 ? (
            <div className="flex flex-wrap gap-2">
              <Field label={t("cost.labor")}>
                <Input
                  className="w-32"
                  value={laborCost}
                  onChange={(event) => setLaborCost(event.target.value)}
                />
              </Field>
              <Field label={t("cost.other")}>
                <Input
                  className="w-32"
                  value={otherCost}
                  onChange={(event) => setOtherCost(event.target.value)}
                />
              </Field>
              <Button
                type="button"
                variant="outline"
                onClick={async () => {
                  const current = costsQuery.data?.data[0];
                  if (!current) return;
                  await updateCost(current.id, {
                    labor_cost: laborCost || current.labor_cost,
                    other_cost: otherCost || current.other_cost,
                  });
                  await invalidate(workOrder.uav);
                }}
              >
                {t("common.save")}
              </Button>
            </div>
          ) : null}
        </div>
      ) : null}
      <DocumentSection uavId={workOrder.uav} workOrderId={workOrder.id} />
    </section>
  );
}
