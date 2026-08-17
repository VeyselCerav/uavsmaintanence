"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { Field } from "@/components/system/field";
import { ComponentBadge } from "@/components/system/status-badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";
import { Textarea } from "@/components/ui/textarea";
import { useSessionUser } from "@/hooks/use-session-user";
import { localeTag } from "@/lib/calendar-range";
import { hasPermission } from "@/lib/auth";
import { useI18n } from "@/lib/i18n-context";
import { ApiClientError } from "@/services/api";
import { installUAVComponent, listUAVComponents, removeUAVComponent } from "@/services/components";
import { listComponentTypes } from "@/services/maintenance";
import type { ComponentStatus } from "@/types/component";

const REMOVE_STATUSES: Exclude<ComponentStatus, "INSTALLED">[] = [
  "REMOVED",
  "QUARANTINE",
  "SCRAPPED",
];

export function InstalledComponents({ uavId }: { uavId: string }) {
  const { t, locale } = useI18n();
  const user = useSessionUser();
  const queryClient = useQueryClient();
  const canInstall = hasPermission(user, "component.create");
  const canRemove = hasPermission(user, "component.update");
  const dateFormat = new Intl.DateTimeFormat(localeTag(locale), {
    dateStyle: "short",
    timeStyle: "short",
  });
  const [error, setError] = useState<string | null>(null);
  const [componentType, setComponentType] = useState("");
  const [name, setName] = useState("");
  const [serial, setSerial] = useState("");
  const [partNumber, setPartNumber] = useState("");
  const [notes, setNotes] = useState("");
  const [removeStatus, setRemoveStatus] = useState<Record<string, Exclude<ComponentStatus, "INSTALLED">>>(
    {},
  );

  const componentsQuery = useQuery({
    queryKey: ["uav-components", uavId],
    queryFn: () => listUAVComponents(uavId),
    enabled: hasPermission(user, "component.view"),
  });
  const typesQuery = useQuery({
    queryKey: ["component-types"],
    queryFn: listComponentTypes,
    enabled: canInstall,
  });

  const installMutation = useMutation({
    mutationFn: () =>
      installUAVComponent({
        uav: uavId,
        component_type: componentType,
        name,
        serial_number: serial,
        part_number: partNumber,
        notes,
      }),
    onSuccess: async () => {
      setError(null);
      setName("");
      setSerial("");
      setPartNumber("");
      setNotes("");
      await invalidate();
    },
    onError: (err) => {
      setError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    },
  });

  const removeMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: Exclude<ComponentStatus, "INSTALLED"> }) =>
      removeUAVComponent(id, { status }),
    onSuccess: async () => {
      setError(null);
      await invalidate();
    },
    onError: (err) => {
      setError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    },
  });

  async function invalidate() {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["uav-components", uavId] }),
      queryClient.invalidateQueries({ queryKey: ["dues", uavId] }),
      queryClient.invalidateQueries({ queryKey: ["uav-timeline", uavId] }),
    ]);
  }

  function onInstall(event: FormEvent) {
    event.preventDefault();
    installMutation.mutate();
  }

  const rows = componentsQuery.data?.data ?? [];
  if (!hasPermission(user, "component.view")) {
    return null;
  }

  return (
    <div>
      <h2 className="mb-3 text-base font-semibold text-primary">{t("component.title")}</h2>
      {error ? <p className="mb-3 text-sm text-destructive">{t(error)}</p> : null}
      <div className="overflow-hidden rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("component.name")}</TableHead>
              <TableHead>{t("template.componentType")}</TableHead>
              <TableHead>{t("component.serial")}</TableHead>
              <TableHead>{t("component.hours")}</TableHead>
              <TableHead>{t("due.status")}</TableHead>
              <TableHead>{t("component.installedAt")}</TableHead>
              {canRemove ? <TableHead>{t("common.actions")}</TableHead> : null}
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.length === 0 ? (
              <TableRow>
                <TableCell className="text-muted-foreground" colSpan={canRemove ? 7 : 6}>
                  {t("component.empty")}
                </TableCell>
              </TableRow>
            ) : (
              rows.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.name}</TableCell>
                  <TableCell>{item.component_type_name}</TableCell>
                  <TableCell>{item.serial_number || "—"}</TableCell>
                  <TableCell>{item.operating_hours}</TableCell>
                  <TableCell>
                    <ComponentBadge status={item.status} />
                  </TableCell>
                  <TableCell>
                    {item.installed_at ? dateFormat.format(new Date(item.installed_at)) : "—"}
                    {item.removed_at
                      ? ` → ${dateFormat.format(new Date(item.removed_at))}`
                      : ""}
                  </TableCell>
                  {canRemove ? (
                    <TableCell>
                      {item.status === "INSTALLED" ? (
                        <div className="flex items-center gap-2">
                          <NativeSelect
                            className="w-36"
                            value={removeStatus[item.id] ?? "REMOVED"}
                            onChange={(event) =>
                              setRemoveStatus((current) => ({
                                ...current,
                                [item.id]: event.target.value as Exclude<ComponentStatus, "INSTALLED">,
                              }))
                            }
                          >
                            {REMOVE_STATUSES.map((status) => (
                              <option key={status} value={status}>
                                {t(`enums.component_status.${status}`)}
                              </option>
                            ))}
                          </NativeSelect>
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            disabled={removeMutation.isPending}
                            onClick={() =>
                              removeMutation.mutate({
                                id: item.id,
                                status: removeStatus[item.id] ?? "REMOVED",
                              })
                            }
                          >
                            {t("component.remove")}
                          </Button>
                        </div>
                      ) : (
                        <span className="text-xs text-muted-foreground">{t("component.removed")}</span>
                      )}
                    </TableCell>
                  ) : null}
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
      {canInstall ? (
        <form onSubmit={onInstall} className="mt-4 grid gap-3 rounded-lg border bg-card p-4 md:grid-cols-2">
          <Field label={t("template.componentType")}>
            <NativeSelect
              required
              value={componentType}
              onChange={(event) => setComponentType(event.target.value)}
            >
              <option value="" />
              {(typesQuery.data?.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </NativeSelect>
          </Field>
          <Field label={t("component.name")}>
            <Input value={name} onChange={(event) => setName(event.target.value)} />
          </Field>
          <Field label={t("component.serial")}>
            <Input value={serial} onChange={(event) => setSerial(event.target.value)} />
          </Field>
          <Field label={t("part.number")}>
            <Input value={partNumber} onChange={(event) => setPartNumber(event.target.value)} />
          </Field>
          <Field label={t("uav.notes")} className="md:col-span-2">
            <Textarea value={notes} onChange={(event) => setNotes(event.target.value)} />
          </Field>
          <div className="md:col-span-2">
            <Button type="submit" disabled={installMutation.isPending || !componentType}>
              {installMutation.isPending ? t("common.loading") : t("component.install")}
            </Button>
          </div>
        </form>
      ) : null}
    </div>
  );
}
