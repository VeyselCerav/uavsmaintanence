"use client";

import { useQuery } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { AdminOnly } from "@/components/system/admin-only";
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
import { localeTag } from "@/lib/calendar-range";
import { useI18n } from "@/lib/i18n-context";
import { listAuditLogs } from "@/services/admin";

function AuditBody() {
  const { t, locale } = useI18n();
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const dateFormat = new Intl.DateTimeFormat(localeTag(locale), {
    dateStyle: "short",
    timeStyle: "short",
  });
  const query = useQuery({
    queryKey: ["audit", appliedSearch],
    queryFn: () => listAuditLogs(appliedSearch),
  });
  const items = query.data?.data ?? [];
  const error = query.error instanceof Error ? query.error.message : null;

  function onSearch(event: FormEvent) {
    event.preventDefault();
    setAppliedSearch(search);
  }

  return (
    <section>
      <PageHeader title={t("admin.audit")} description={t("audit.hint")} />
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
              <TableHead>{t("audit.timestamp")}</TableHead>
              <TableHead>{t("audit.user")}</TableHead>
              <TableHead>{t("audit.action")}</TableHead>
              <TableHead>{t("audit.entity")}</TableHead>
              <TableHead>{t("audit.message")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 ? (
              <TableRow>
                <TableCell className="text-muted-foreground" colSpan={5}>
                  {t("audit.empty")}
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{dateFormat.format(new Date(item.timestamp))}</TableCell>
                  <TableCell>{item.user_email || "—"}</TableCell>
                  <TableCell>{item.action}</TableCell>
                  <TableCell>{item.entity_type}</TableCell>
                  <TableCell>{item.message || "—"}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </section>
  );
}

export default function AdminAuditPage() {
  return (
    <AdminOnly>
      <AuditBody />
    </AdminOnly>
  );
}
