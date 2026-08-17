"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { PageHeader } from "@/components/system/page-header";
import { DemoBadge } from "@/components/system/status-badge";
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
import { listRCMs } from "@/services/rcm";

export default function RCMListPage() {
  const { t } = useI18n();
  const user = useSessionUser();
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const canCreate = hasPermission(user, "rcm.create");
  const query = useQuery({
    queryKey: ["rcms", appliedSearch],
    queryFn: () => listRCMs(appliedSearch),
  });
  const items = query.data?.data ?? [];
  const error = query.error instanceof Error ? query.error.message : null;

  function onSearch(event: FormEvent) {
    event.preventDefault();
    setAppliedSearch(search);
  }

  return (
    <section>
      <PageHeader title={t("rcm.title")} description={t("rcm.hint")}>
        {canCreate ? (
          <Button asChild>
            <Link href="/rcm/new">{t("rcm.new")}</Link>
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
              <TableHead>{t("catalog.code")}</TableHead>
              <TableHead>{t("rcm.titleField")}</TableHead>
              <TableHead>{t("template.componentType")}</TableHead>
              <TableHead>{t("rcm.status")}</TableHead>
              <TableHead>{t("rcm.strategy")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 ? (
              <TableRow>
                <TableCell className="text-muted-foreground" colSpan={5}>
                  {t("rcm.empty")}
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => {
                const strategies = [...new Set((item.items ?? []).map((row) => row.strategy))];
                return (
                  <TableRow
                    key={item.id}
                    className="cursor-pointer"
                    onClick={() => router.push(`/rcm/${item.id}`)}
                  >
                    <TableCell>
                      <span className="mr-2">{item.code}</span>
                      <DemoBadge visible={item.is_demo} />
                    </TableCell>
                    <TableCell>{item.title}</TableCell>
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
    </section>
  );
}
