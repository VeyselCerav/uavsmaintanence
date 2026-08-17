"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useState } from "react";

import { Field } from "@/components/system/field";
import { PageHeader } from "@/components/system/page-header";
import { DemoBadge } from "@/components/system/status-badge";
import { PartForm } from "@/features/parts/part-form";
import { Button } from "@/components/ui/button";
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
import { ApiClientError } from "@/services/api";
import { listComponentTypes } from "@/services/maintenance";
import { createPartCompatibility, deletePartCompatibility, getPart } from "@/services/parts";
import { listClasses, listPlatforms } from "@/services/uavs";

export default function PartDetailPage() {
  const { t } = useI18n();
  const params = useParams<{ id: string }>();
  const user = useSessionUser();
  const queryClient = useQueryClient();
  const canUpdate = hasPermission(user, "part.update");
  const [formError, setFormError] = useState<string | null>(null);
  const [uavClass, setUavClass] = useState("");
  const [platform, setPlatform] = useState("");
  const [componentType, setComponentType] = useState("");
  const query = useQuery({
    queryKey: ["part", params.id],
    queryFn: () => getPart(params.id),
  });
  const classes = useQuery({ queryKey: ["uav-classes"], queryFn: listClasses, enabled: canUpdate });
  const platforms = useQuery({ queryKey: ["platforms"], queryFn: listPlatforms, enabled: canUpdate });
  const types = useQuery({
    queryKey: ["component-types"],
    queryFn: listComponentTypes,
    enabled: canUpdate,
  });
  const part = query.data;
  const rows = part?.compatibilities ?? [];

  const addMutation = useMutation({
    mutationFn: () =>
      createPartCompatibility(params.id, {
        uav_class: uavClass || null,
        platform_type: platform || null,
        component_type: componentType,
      }),
    onSuccess: async () => {
      setUavClass("");
      setPlatform("");
      setComponentType("");
      setFormError(null);
      await queryClient.invalidateQueries({ queryKey: ["part", params.id] });
    },
    onError: (err) => {
      setFormError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    },
  });

  async function onAdd(event: FormEvent) {
    event.preventDefault();
    addMutation.mutate();
  }

  async function onDelete(rowId: string) {
    try {
      await deletePartCompatibility(params.id, rowId);
      await queryClient.invalidateQueries({ queryKey: ["part", params.id] });
    } catch (err) {
      setFormError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    }
  }

  if (query.error) {
    return <p className="text-sm text-destructive">{t("errors.generic")}</p>;
  }
  if (!part) {
    return <p className="text-sm text-muted-foreground">{t("common.loading")}</p>;
  }

  return (
    <section className="space-y-8">
      <PageHeader title={part.part_number} description={part.name}>
        <DemoBadge visible={part.is_demo} />
        <Button asChild variant="outline">
          <Link href="/parts">{t("common.back")}</Link>
        </Button>
      </PageHeader>
      {formError ? <p className="text-sm text-destructive">{t(formError)}</p> : null}
      <p className="text-sm text-muted-foreground">
        {t("part.stock")}: {part.stock_qty}
        {part.stock_low ? ` · ${t("part.lowStock")}` : ""} · {part.unit_cost} {part.currency}
      </p>
      {canUpdate ? <PartForm initial={part} /> : null}
      <div>
        <h2 className="mb-3 text-base font-semibold text-primary">{t("part.compatibility")}</h2>
        <div className="overflow-x-auto rounded-lg border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("uav.class")}</TableHead>
                <TableHead>{t("uav.platform")}</TableHead>
                <TableHead>{t("template.componentType")}</TableHead>
                {canUpdate ? <TableHead>{t("common.actions")}</TableHead> : null}
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.length === 0 ? (
                <TableRow>
                  <TableCell className="text-muted-foreground" colSpan={canUpdate ? 4 : 3}>
                    {t("part.emptyCompatibility")}
                  </TableCell>
                </TableRow>
              ) : (
                rows.map((row) => (
                  <TableRow key={row.id}>
                    <TableCell>{row.uav_class_name || t("part.allClasses")}</TableCell>
                    <TableCell>{row.platform_name || t("part.allPlatforms")}</TableCell>
                    <TableCell>{row.component_type_name}</TableCell>
                    {canUpdate ? (
                      <TableCell>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="text-destructive"
                          onClick={() => onDelete(row.id)}
                        >
                          {t("common.delete")}
                        </Button>
                      </TableCell>
                    ) : null}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>
      {canUpdate ? (
        <form onSubmit={onAdd} className="max-w-3xl space-y-3 rounded-lg border bg-card p-4">
          <h3 className="text-sm font-semibold">{t("part.addCompatibility")}</h3>
          <div className="grid grid-cols-3 gap-3">
            <Field label={t("uav.class")}>
              <NativeSelect value={uavClass} onChange={(event) => setUavClass(event.target.value)}>
                <option value="">{t("part.allClasses")}</option>
                {(classes.data?.data ?? []).map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </NativeSelect>
            </Field>
            <Field label={t("uav.platform")}>
              <NativeSelect value={platform} onChange={(event) => setPlatform(event.target.value)}>
                <option value="">{t("part.allPlatforms")}</option>
                {(platforms.data?.data ?? []).map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </NativeSelect>
            </Field>
            <Field label={t("template.componentType")}>
              <NativeSelect
                required
                value={componentType}
                onChange={(event) => setComponentType(event.target.value)}
              >
                <option value="" />
                {(types.data?.data ?? []).map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.name}
                  </option>
                ))}
              </NativeSelect>
            </Field>
          </div>
          <Button type="submit" disabled={addMutation.isPending || !componentType}>
            {addMutation.isPending ? t("common.loading") : t("part.addCompatibility")}
          </Button>
        </form>
      ) : null}
    </section>
  );
}
