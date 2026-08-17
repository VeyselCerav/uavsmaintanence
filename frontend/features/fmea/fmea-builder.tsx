"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { FormEvent, useState } from "react";

import { Field } from "@/components/system/field";
import { PageHeader } from "@/components/system/page-header";
import { DemoBadge, RPNBadge } from "@/components/system/status-badge";
import { FMEAHeaderForm } from "@/features/fmea/fmea-header-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";
import { Textarea } from "@/components/ui/textarea";
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
import { approveFMEA, createFMEAItem, deleteFMEAItem, getFMEA } from "@/services/fmea";
import { listFailureModes } from "@/services/failures";
import type { FMEAItemWritePayload } from "@/types/fmea";

const EMPTY_ITEM: FMEAItemWritePayload = {
  function: "",
  functional_failure: "",
  failure_mode: "",
  catalog_mode: "",
  failure_cause: "",
  failure_effect: "",
  severity: 5,
  occurrence: 5,
  detection: 5,
  existing_control: "",
  recommended_action: "",
};

export function FMEABuilder({ fmeaId }: { fmeaId: string }) {
  const { t } = useI18n();
  const user = useSessionUser();
  const queryClient = useQueryClient();
  const canUpdate = hasPermission(user, "fmea.update");
  const canApprove = hasPermission(user, "fmea.approve");
  const [formError, setFormError] = useState<string | null>(null);
  const [itemForm, setItemForm] = useState<FMEAItemWritePayload>(EMPTY_ITEM);
  const query = useQuery({
    queryKey: ["fmea", fmeaId],
    queryFn: () => getFMEA(fmeaId),
  });
  const modes = useQuery({ queryKey: ["failure-modes"], queryFn: listFailureModes });
  const fmea = query.data;
  const items = fmea?.items ?? [];
  const editable = fmea ? fmea.status === "DRAFT" || fmea.status === "IN_REVIEW" : false;

  const createMutation = useMutation({
    mutationFn: () =>
      createFMEAItem(fmeaId, {
        ...itemForm,
        catalog_mode: itemForm.catalog_mode || null,
      }),
    onSuccess: async () => {
      setItemForm(EMPTY_ITEM);
      setFormError(null);
      await queryClient.invalidateQueries({ queryKey: ["fmea", fmeaId] });
    },
    onError: (err) => {
      setFormError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    },
  });

  async function onAdd(event: FormEvent) {
    event.preventDefault();
    createMutation.mutate();
  }

  async function onDelete(itemId: string) {
    try {
      await deleteFMEAItem(fmeaId, itemId);
      await queryClient.invalidateQueries({ queryKey: ["fmea", fmeaId] });
    } catch (err) {
      setFormError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    }
  }

  async function onApprove() {
    try {
      await approveFMEA(fmeaId);
      await queryClient.invalidateQueries({ queryKey: ["fmea", fmeaId] });
      await queryClient.invalidateQueries({ queryKey: ["fmeas"] });
    } catch (err) {
      setFormError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    }
  }

  if (query.error) {
    return <p className="text-sm text-destructive">{t("errors.generic")}</p>;
  }
  if (!fmea) {
    return <p className="text-sm text-muted-foreground">{t("common.loading")}</p>;
  }

  return (
    <section className="space-y-8">
      <PageHeader title={fmea.code} description={fmea.title}>
        <DemoBadge visible={fmea.is_demo} />
        <RPNBadge rpn={fmea.max_rpn} band={fmea.rpn_band} />
        <Button asChild variant="outline">
          <Link href="/fmea">{t("common.back")}</Link>
        </Button>
        {canApprove && editable ? (
          <Button type="button" onClick={onApprove}>
            {t("fmea.approve")}
          </Button>
        ) : null}
      </PageHeader>
      {formError ? <p className="text-sm text-destructive">{t(formError)}</p> : null}
      <p className="text-sm text-muted-foreground">
        {t("fmea.status")}: {t(`enums.fmea_status.${fmea.status}`)} · {t("fmea.revision")}:{" "}
        {fmea.revision}
        {fmea.component_type_name ? ` · ${fmea.component_type_name}` : ""}
      </p>
      {canUpdate && editable ? <FMEAHeaderForm initial={fmea} /> : null}
      <div>
        <h2 className="mb-3 text-base font-semibold text-primary">{t("fmea.items")}</h2>
        <div className="overflow-x-auto rounded-lg border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("fmea.function")}</TableHead>
                <TableHead>{t("fmea.functionalFailure")}</TableHead>
                <TableHead>{t("failure.mode")}</TableHead>
                <TableHead>S</TableHead>
                <TableHead>O</TableHead>
                <TableHead>D</TableHead>
                <TableHead>RPN</TableHead>
                {canUpdate && editable ? <TableHead>{t("common.actions")}</TableHead> : null}
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.length === 0 ? (
                <TableRow>
                  <TableCell className="text-muted-foreground" colSpan={canUpdate && editable ? 8 : 7}>
                    {t("fmea.emptyItems")}
                  </TableCell>
                </TableRow>
              ) : (
                items.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>{item.function}</TableCell>
                    <TableCell>{item.functional_failure}</TableCell>
                    <TableCell>
                      {item.catalog_mode_code
                        ? `${item.catalog_mode_code} — ${item.failure_mode}`
                        : item.failure_mode}
                    </TableCell>
                    <TableCell>{item.severity}</TableCell>
                    <TableCell>{item.occurrence}</TableCell>
                    <TableCell>{item.detection}</TableCell>
                    <TableCell>
                      <RPNBadge rpn={item.rpn} band={item.rpn_band} />
                    </TableCell>
                    {canUpdate && editable ? (
                      <TableCell>
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="text-destructive"
                          onClick={() => onDelete(item.id)}
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
      {canUpdate && editable ? (
        <form onSubmit={onAdd} className="max-w-3xl space-y-3 rounded-lg border bg-card p-4">
          <h3 className="text-sm font-semibold">{t("fmea.addItem")}</h3>
          <p className="text-xs text-muted-foreground">{t("fmea.rpnHint")}</p>
          <div className="grid grid-cols-2 gap-3">
            <Field label={t("fmea.function")}>
              <Input
                required
                value={itemForm.function}
                onChange={(event) => setItemForm({ ...itemForm, function: event.target.value })}
              />
            </Field>
            <Field label={t("fmea.functionalFailure")}>
              <Input
                required
                value={itemForm.functional_failure}
                onChange={(event) =>
                  setItemForm({ ...itemForm, functional_failure: event.target.value })
                }
              />
            </Field>
            <Field label={t("failure.mode")}>
              <NativeSelect
                value={itemForm.catalog_mode ?? ""}
                onChange={(event) => setItemForm({ ...itemForm, catalog_mode: event.target.value })}
              >
                <option value="">{t("failure.modeNone")}</option>
                {(modes.data?.data ?? []).map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.code} — {item.name}
                  </option>
                ))}
              </NativeSelect>
            </Field>
            <Field label={t("fmea.failureModeText")}>
              <Input
                required
                value={itemForm.failure_mode}
                onChange={(event) => setItemForm({ ...itemForm, failure_mode: event.target.value })}
              />
            </Field>
            <Field label="S (1–10)">
              <Input
                required
                type="number"
                min={1}
                max={10}
                value={itemForm.severity}
                onChange={(event) =>
                  setItemForm({ ...itemForm, severity: Number(event.target.value) })
                }
              />
            </Field>
            <Field label="O (1–10)">
              <Input
                required
                type="number"
                min={1}
                max={10}
                value={itemForm.occurrence}
                onChange={(event) =>
                  setItemForm({ ...itemForm, occurrence: Number(event.target.value) })
                }
              />
            </Field>
            <Field label="D (1–10)">
              <Input
                required
                type="number"
                min={1}
                max={10}
                value={itemForm.detection}
                onChange={(event) =>
                  setItemForm({ ...itemForm, detection: Number(event.target.value) })
                }
              />
            </Field>
            <Field label={t("fmea.cause")}>
              <Input
                value={itemForm.failure_cause}
                onChange={(event) => setItemForm({ ...itemForm, failure_cause: event.target.value })}
              />
            </Field>
          </div>
          <Field label={t("fmea.effect")}>
            <Textarea
              value={itemForm.failure_effect}
              onChange={(event) => setItemForm({ ...itemForm, failure_effect: event.target.value })}
            />
          </Field>
          <Button type="submit" disabled={createMutation.isPending}>
            {createMutation.isPending ? t("common.loading") : t("fmea.addItem")}
          </Button>
        </form>
      ) : null}
    </section>
  );
}
