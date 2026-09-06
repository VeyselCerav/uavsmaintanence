"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { MaintenanceNav } from "@/components/system/maintenance-nav";
import { PageHeader } from "@/components/system/page-header";
import { DueBadge } from "@/components/system/status-badge";
import { Button } from "@/components/ui/button";
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
import { listDues } from "@/services/maintenance";
import type { DueStatus } from "@/types/maintenance";

const OPEN_WO_DUE_STATUSES: DueStatus[] = ["DUE", "OVERDUE", "CRITICAL"];
const STATUS_FILTERS: Array<"" | "attention" | DueStatus> = [
  "attention",
  "",
  "APPROACHING",
  "DUE",
  "OVERDUE",
  "CRITICAL",
  "NORMAL",
];

export default function MaintenancePage() {
  const { t } = useI18n();
  const user = useSessionUser();
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const [status, setStatus] = useState("attention");
  const canCreateWorkOrder = hasPermission(user, "work_order.create");
  const query = useQuery({
    queryKey: ["dues", "", status, appliedSearch],
    queryFn: () => listDues("", status, appliedSearch),
  });
  const items = query.data?.data ?? [];
  const error = query.error instanceof Error ? query.error.message : null;

  function onSearch(event: FormEvent) {
    event.preventDefault();
    setAppliedSearch(search);
  }

  return (
    <section>
      <PageHeader title={t("due.title")} description={t("due.listHint")}>
        <MaintenanceNav active="dues" />
      </PageHeader>
      <form onSubmit={onSearch} className="mb-4 flex flex-wrap gap-2">
        <Input
          className="w-72"
          placeholder={t("common.search")}
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <NativeSelect
          className="w-52"
          value={status}
          onChange={(event) => setStatus(event.target.value)}
        >
          {STATUS_FILTERS.map((value) => (
            <option key={value || "all"} value={value}>
              {value === "attention"
                ? t("due.attention")
                : value === ""
                  ? t("due.all")
                  : t(`enums.due_status.${value}`)}
            </option>
          ))}
        </NativeSelect>
        <Button type="submit" variant="outline">
          {t("common.search")}
        </Button>
      </form>
      {error ? <p className="mb-3 text-sm text-destructive">{t(error)}</p> : null}
      <div className="overflow-hidden rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("uav.registration")}</TableHead>
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
            {query.isPending ? (
              <TableRow>
                <TableCell className="text-muted-foreground" colSpan={8}>
                  {t("common.loading")}
                </TableCell>
              </TableRow>
            ) : items.length === 0 ? (
              <TableRow>
                <TableCell className="text-muted-foreground" colSpan={8}>
                  {t("due.listEmpty")}
                </TableCell>
              </TableRow>
            ) : (
              items.map((due) => {
                const canOpen =
                  canCreateWorkOrder && OPEN_WO_DUE_STATUSES.includes(due.status);
                return (
                  <TableRow
                    key={due.id}
                    className="cursor-pointer"
                    onClick={() => router.push(`/uavs/${due.uav}`)}
                  >
                    <TableCell>{due.uav_registration}</TableCell>
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
                    <TableCell onClick={(event) => event.stopPropagation()}>
                      {canOpen ? (
                        <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
                          <Link href={`/work-orders/new?uav=${due.uav}&due=${due.id}`}>
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
    </section>
  );
}
