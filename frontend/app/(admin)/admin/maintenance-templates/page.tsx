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
import { listTemplates } from "@/services/maintenance";

export default function AdminTemplatesPage() {
  const { t } = useI18n();
  const user = useSessionUser();
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const canCreate = hasPermission(user, "maintenance_template.create");
  const query = useQuery({
    queryKey: ["templates", appliedSearch],
    queryFn: () => listTemplates(appliedSearch),
  });
  const items = query.data?.data ?? [];
  const error = query.error instanceof Error ? query.error.message : null;

  function onSearch(event: FormEvent) {
    event.preventDefault();
    setAppliedSearch(search);
  }

  return (
    <section>
      <PageHeader title={t("template.title")}>
        {canCreate ? (
          <Button asChild>
            <Link href="/admin/maintenance-templates/new">{t("template.new")}</Link>
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
              <TableHead>{t("catalog.name")}</TableHead>
              <TableHead>{t("uav.class")}</TableHead>
              <TableHead>{t("uav.platform")}</TableHead>
              <TableHead>{t("uav.mission")}</TableHead>
              <TableHead>{t("uav.approach")}</TableHead>
              <TableHead>{t("template.itemCount")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 ? (
              <TableRow>
                <TableCell className="text-muted-foreground" colSpan={7}>
                  {t("template.empty")}
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
                <TableRow
                  key={item.id}
                  className="cursor-pointer"
                  onClick={() => router.push(`/admin/maintenance-templates/${item.id}`)}
                >
                  <TableCell>
                    <span className="mr-2">{item.code}</span>
                    <DemoBadge visible={item.is_demo} />
                  </TableCell>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>{item.uav_class_name}</TableCell>
                  <TableCell>{item.platform_name}</TableCell>
                  <TableCell>{item.mission_name}</TableCell>
                  <TableCell>{t(`enums.maintenance_approach.${item.approach}`)}</TableCell>
                  <TableCell>{item.item_count}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </section>
  );
}
