"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { PageHeader } from "@/components/system/page-header";
import { DemoBadge, RPNBadge } from "@/components/system/status-badge";
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
import { listFMEAs } from "@/services/fmea";

export default function FMEAListPage() {
  const { t } = useI18n();
  const user = useSessionUser();
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const canCreate = hasPermission(user, "fmea.create");
  const query = useQuery({
    queryKey: ["fmeas", appliedSearch],
    queryFn: () => listFMEAs(appliedSearch),
  });
  const items = query.data?.data ?? [];
  const error = query.error instanceof Error ? query.error.message : null;

  function onSearch(event: FormEvent) {
    event.preventDefault();
    setAppliedSearch(search);
  }

  return (
    <section>
      <PageHeader title={t("fmea.title")} description={t("fmea.hint")}>
        {canCreate ? (
          <Button asChild>
            <Link href="/fmea/new">{t("fmea.new")}</Link>
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
              <TableHead>{t("fmea.titleField")}</TableHead>
              <TableHead>{t("template.componentType")}</TableHead>
              <TableHead>{t("fmea.status")}</TableHead>
              <TableHead>RPN</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 ? (
              <TableRow>
                <TableCell className="text-muted-foreground" colSpan={5}>
                  {t("fmea.empty")}
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
                <TableRow
                  key={item.id}
                  className="cursor-pointer"
                  onClick={() => router.push(`/fmea/${item.id}`)}
                >
                  <TableCell>
                    <span className="mr-2">{item.code}</span>
                    <DemoBadge visible={item.is_demo} />
                  </TableCell>
                  <TableCell>{item.title}</TableCell>
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
    </section>
  );
}
