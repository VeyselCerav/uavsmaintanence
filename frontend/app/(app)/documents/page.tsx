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
import { ApiClientError } from "@/services/api";
import { downloadDocument, listDocuments } from "@/services/documents";

export default function DocumentsPage() {
  const { t } = useI18n();
  const user = useSessionUser();
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const [actionError, setActionError] = useState<string | null>(null);
  const canCreate = hasPermission(user, "document.create");
  const query = useQuery({
    queryKey: ["documents", appliedSearch],
    queryFn: () => listDocuments(appliedSearch),
  });
  const items = query.data?.data ?? [];
  const error =
    actionError ?? (query.error instanceof Error ? query.error.message : null);

  function onSearch(event: FormEvent) {
    event.preventDefault();
    setAppliedSearch(search);
  }

  return (
    <section>
      <PageHeader title={t("document.title")} description={t("document.hint")}>
        {canCreate ? (
          <Button asChild>
            <Link href="/documents/new">{t("document.new")}</Link>
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
              <TableHead>{t("document.titleField")}</TableHead>
              <TableHead>{t("document.fileName")}</TableHead>
              <TableHead>{t("document.type")}</TableHead>
              <TableHead>{t("uav.registration")}</TableHead>
              <TableHead>{t("workOrder.number")}</TableHead>
              <TableHead>{t("common.actions")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 ? (
              <TableRow>
                <TableCell className="text-muted-foreground" colSpan={6}>
                  {t("document.empty")}
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
                <TableRow
                  key={item.id}
                  className={item.uav ? "cursor-pointer" : undefined}
                  onClick={() => {
                    if (item.uav) router.push(`/uavs/${item.uav}`);
                  }}
                >
                  <TableCell>
                    <span className="mr-2">{item.title}</span>
                    <DemoBadge visible={item.is_demo} />
                  </TableCell>
                  <TableCell>{item.file_name}</TableCell>
                  <TableCell>{t(`enums.document_type.${item.document_type}`)}</TableCell>
                  <TableCell>{item.uav_registration || "—"}</TableCell>
                  <TableCell>{item.work_order_number || "—"}</TableCell>
                  <TableCell>
                    {item.has_file ? (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={async (event) => {
                          event.stopPropagation();
                          try {
                            await downloadDocument(item.id, item.file_name);
                            setActionError(null);
                          } catch (err) {
                            setActionError(
                              err instanceof ApiClientError ? err.message_key : "errors.generic",
                            );
                          }
                        }}
                      >
                        {t("document.download")}
                      </Button>
                    ) : (
                      <span className="text-xs text-muted-foreground">{t("document.noFile")}</span>
                    )}
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
