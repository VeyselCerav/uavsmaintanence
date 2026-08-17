"use client";

import { useQuery } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { MaintenanceNav } from "@/components/system/maintenance-nav";
import { PageHeader } from "@/components/system/page-header";
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
import { useI18n } from "@/lib/i18n-context";
import { localeTag } from "@/lib/calendar-range";
import { listRecords } from "@/services/maintenance";

export default function MaintenanceRecordsPage() {
  const { t, locale } = useI18n();
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const query = useQuery({
    queryKey: ["maintenance-records", appliedSearch],
    queryFn: () => listRecords(appliedSearch),
  });
  const items = query.data?.data ?? [];
  const error = query.error instanceof Error ? query.error.message : null;
  const format = new Intl.DateTimeFormat(localeTag(locale), {
    dateStyle: "short",
    timeStyle: "short",
  });

  function onSearch(event: FormEvent) {
    event.preventDefault();
    setAppliedSearch(search);
  }

  return (
    <section>
      <PageHeader title={t("record.title")} description={t("record.hint")}>
        <MaintenanceNav active="records" />
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
              <TableHead>{t("record.performedAt")}</TableHead>
              <TableHead>{t("workOrder.number")}</TableHead>
              <TableHead>{t("uav.registration")}</TableHead>
              <TableHead>{t("template.taskName")}</TableHead>
              <TableHead>{t("workOrder.assignee")}</TableHead>
              <TableHead>{t("workOrder.type")}</TableHead>
              <TableHead>{t("uav.approach")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 ? (
              <TableRow>
                <TableCell className="text-muted-foreground" colSpan={7}>
                  {t("record.empty")}
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
                <TableRow
                  key={item.id}
                  className="cursor-pointer"
                  onClick={() => router.push(`/work-orders/${item.work_order}`)}
                >
                  <TableCell>{format.format(new Date(item.performed_at))}</TableCell>
                  <TableCell>{item.work_order_number}</TableCell>
                  <TableCell>{item.uav_registration}</TableCell>
                  <TableCell>{item.task_name ?? item.description ?? "—"}</TableCell>
                  <TableCell>{item.technician_name ?? "—"}</TableCell>
                  <TableCell>{t(`enums.maintenance_type.${item.maintenance_type}`)}</TableCell>
                  <TableCell>{t(`enums.maintenance_approach.${item.approach}`)}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </section>
  );
}
