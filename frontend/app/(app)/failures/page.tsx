"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { PageHeader } from "@/components/system/page-header";
import { DemoBadge, FailureSeverityBadge } from "@/components/system/status-badge";
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
import { listFailures } from "@/services/failures";

export default function FailuresPage() {
  const { t } = useI18n();
  const user = useSessionUser();
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const [status, setStatus] = useState("open");
  const canCreate = hasPermission(user, "failure.create");
  const query = useQuery({
    queryKey: ["failures", appliedSearch, status],
    queryFn: () => listFailures(appliedSearch, status),
  });
  const items = query.data?.data ?? [];
  const error = query.error instanceof Error ? query.error.message : null;

  function onSearch(event: FormEvent) {
    event.preventDefault();
    setAppliedSearch(search);
  }

  return (
    <section>
      <PageHeader title={t("failure.title")} description={t("failure.hint")}>
        {canCreate ? (
          <Button asChild>
            <Link href="/failures/new">{t("failure.new")}</Link>
          </Button>
        ) : null}
      </PageHeader>
      <form onSubmit={onSearch} className="mb-4 flex flex-wrap gap-2">
        <Input
          className="w-72"
          placeholder={t("common.search")}
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <NativeSelect
          className="w-44"
          value={status}
          onChange={(event) => setStatus(event.target.value)}
        >
          <option value="">{t("failure.all")}</option>
          <option value="open">{t("failure.open")}</option>
          <option value="resolved">{t("failure.resolved")}</option>
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
              <TableHead>{t("failure.occurredAt")}</TableHead>
              <TableHead>{t("failure.mode")}</TableHead>
              <TableHead>{t("failure.severity")}</TableHead>
              <TableHead>{t("failure.status")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {query.isPending ? (
              <TableRow>
                <TableCell className="text-muted-foreground" colSpan={5}>
                  {t("common.loading")}
                </TableCell>
              </TableRow>
            ) : items.length === 0 ? (
              <TableRow>
                <TableCell className="text-muted-foreground" colSpan={5}>
                  {t("failure.empty")}
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
                <TableRow
                  key={item.id}
                  className="cursor-pointer"
                  onClick={() => router.push(`/failures/${item.id}`)}
                >
                  <TableCell>
                    <span className="mr-2">{item.uav_registration}</span>
                    <DemoBadge visible={item.is_demo} />
                  </TableCell>
                  <TableCell>{new Date(item.occurred_at).toLocaleString()}</TableCell>
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
    </section>
  );
}
