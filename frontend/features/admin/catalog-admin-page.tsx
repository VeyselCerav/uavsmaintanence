"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { Field } from "@/components/system/field";
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
import { ApiClientError, apiFetchPage } from "@/services/api";
import { createCatalog } from "@/services/uavs";
import type { CatalogItem } from "@/types/uav";

type Props = {
  titleKey: string;
  path: string;
  createPermission: string;
};

export function CatalogAdminPage({ titleKey, path, createPermission }: Props) {
  const { t } = useI18n();
  const user = useSessionUser();
  const queryClient = useQueryClient();
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const canCreate = hasPermission(user, createPermission);
  const query = useQuery({
    queryKey: ["catalog", path],
    queryFn: () => apiFetchPage<CatalogItem>(`${path}?page_size=100`),
  });
  const mutation = useMutation({
    mutationFn: () => createCatalog(path, { code, name }),
    onSuccess: async () => {
      setCode("");
      setName("");
      setFormError(null);
      await queryClient.invalidateQueries({ queryKey: ["catalog", path] });
    },
    onError: (err) => {
      setFormError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    },
  });

  const items = query.data?.data ?? [];
  const error =
    formError ?? (query.error instanceof Error ? query.error.message : null);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    mutation.mutate();
  }

  return (
    <section>
      <PageHeader title={t(titleKey)} />
      {error ? <p className="mb-3 text-sm text-destructive">{t(error)}</p> : null}
      {canCreate ? (
        <form onSubmit={onSubmit} className="mb-4 flex flex-wrap items-end gap-2">
          <Field label={t("catalog.code")} className="w-40">
            <Input required value={code} onChange={(event) => setCode(event.target.value)} />
          </Field>
          <Field label={t("catalog.name")} className="w-56">
            <Input required value={name} onChange={(event) => setName(event.target.value)} />
          </Field>
          <Button type="submit">{t("common.create")}</Button>
        </form>
      ) : null}
      <div className="overflow-hidden rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("catalog.code")}</TableHead>
              <TableHead>{t("catalog.name")}</TableHead>
              <TableHead>{t("catalog.active")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.map((item) => (
              <TableRow key={item.id}>
                <TableCell>
                  <span className="mr-2">{item.code}</span>
                  <DemoBadge visible={item.is_demo} />
                </TableCell>
                <TableCell>{item.name}</TableCell>
                <TableCell>{item.is_active ? "•" : ""}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </section>
  );
}
