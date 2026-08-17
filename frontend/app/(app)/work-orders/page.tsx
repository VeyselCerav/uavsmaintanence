"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { PageHeader } from "@/components/system/page-header";
import { DemoBadge, WorkOrderBadge } from "@/components/system/status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
import { listWorkOrders } from "@/services/work-orders";

export default function WorkOrdersPage() {
  const { t } = useI18n();
  const user = useSessionUser();
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const canCreate = hasPermission(user, "work_order.create");
  const query = useQuery({
    queryKey: ["work-orders", appliedSearch],
    queryFn: () => listWorkOrders(appliedSearch),
  });
  const items = query.data?.data ?? [];
  const error = query.error instanceof Error ? query.error.message : null;

  function onSearch(event: FormEvent) {
    event.preventDefault();
    setAppliedSearch(search);
  }

  return (
    <section>
      <PageHeader title={t("workOrder.title")}>
        {canCreate ? (
          <Button asChild>
            <Link href="/work-orders/new">{t("workOrder.new")}</Link>
          </Button>
        ) : null}
      </PageHeader>
      <form onSubmit={onSearch} className="mb-4 flex gap-2">
        <Input
          className="w-72"
          placeholder={t("common.search")}
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <Button type="submit" variant="outline">
          {t("common.search")}
        </Button>
      </form>
      {error ? <p className="mb-3 text-sm text-destructive">{t(error)}</p> : null}
      <div className="overflow-hidden rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("workOrder.number")}</TableHead>
              <TableHead>{t("uav.registration")}</TableHead>
              <TableHead>{t("template.taskName")}</TableHead>
              <TableHead>{t("workOrder.assignee")}</TableHead>
              <TableHead>{t("workOrder.status")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 ? (
              <TableRow>
                <TableCell className="text-muted-foreground" colSpan={5}>
                  {t("workOrder.empty")}
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
                <TableRow
                  key={item.id}
                  className="cursor-pointer"
                  onClick={() => router.push(`/work-orders/${item.id}`)}
                >
                  <TableCell>
                    <span className="mr-2">{item.number}</span>
                    <DemoBadge visible={item.is_demo} />
                  </TableCell>
                  <TableCell>{item.uav_registration}</TableCell>
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
    </section>
  );
}
