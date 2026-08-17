"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { FormEvent, useState } from "react";

import { Field } from "@/components/system/field";
import { PageHeader } from "@/components/system/page-header";
import { DemoBadge } from "@/components/system/status-badge";
import { RCMHeaderForm } from "@/features/rcm/rcm-header-form";
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
import { listFMEAs } from "@/services/fmea";
import {
  applyRCMToTemplate,
  approveRCM,
  createRCMItem,
  deleteRCMItem,
  evaluateRCM,
  getRCM,
} from "@/services/rcm";
import { RCM_STRATEGIES } from "@/types/maintenance";
import { DETECTABILITIES, type RCMItemWritePayload } from "@/types/rcm";

const EMPTY_ITEM: RCMItemWritePayload = {
  function: "",
  functional_failure: "",
  failure_mode: "",
  failure_effect: "",
  safety_effect: false,
  operational_effect: false,
  detectability: "MEDIUM",
  preventive_feasible: true,
  strategy: "",
  rationale: "",
  fmea_item: "",
};

export function RCMBuilder({ rcmId }: { rcmId: string }) {
  const { t } = useI18n();
  const user = useSessionUser();
  const queryClient = useQueryClient();
  const canUpdate = hasPermission(user, "rcm.update");
  const canApprove = hasPermission(user, "rcm.approve");
  const [formError, setFormError] = useState<string | null>(null);
  const [applyMessage, setApplyMessage] = useState<string | null>(null);
  const [itemForm, setItemForm] = useState<RCMItemWritePayload>(EMPTY_ITEM);
  const query = useQuery({
    queryKey: ["rcm", rcmId],
    queryFn: () => getRCM(rcmId),
  });
  const fmeas = useQuery({
    queryKey: ["fmeas"],
    queryFn: () => listFMEAs(),
    enabled: hasPermission(user, "fmea.view"),
  });
  const analysis = query.data;
  const items = analysis?.items ?? [];
  const editable = analysis
    ? analysis.status === "DRAFT" || analysis.status === "IN_REVIEW"
    : false;
  const fmeaItems = (fmeas.data?.data ?? []).flatMap((fmea) =>
    (fmea.items ?? []).map((item) => ({
      id: item.id,
      label: `${fmea.code} — ${item.function}`,
    })),
  );

  const createMutation = useMutation({
    mutationFn: () =>
      createRCMItem(rcmId, {
        ...itemForm,
        strategy: itemForm.strategy || undefined,
        fmea_item: itemForm.fmea_item || null,
      }),
    onSuccess: async () => {
      setItemForm(EMPTY_ITEM);
      setFormError(null);
      await queryClient.invalidateQueries({ queryKey: ["rcm", rcmId] });
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
      await deleteRCMItem(rcmId, itemId);
      await queryClient.invalidateQueries({ queryKey: ["rcm", rcmId] });
    } catch (err) {
      setFormError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    }
  }

  async function onApprove() {
    try {
      await approveRCM(rcmId);
      setFormError(null);
      await queryClient.invalidateQueries({ queryKey: ["rcm", rcmId] });
      await queryClient.invalidateQueries({ queryKey: ["rcms"] });
    } catch (err) {
      setFormError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    }
  }

  async function onEvaluate() {
    try {
      await evaluateRCM(rcmId);
      setFormError(null);
      await queryClient.invalidateQueries({ queryKey: ["rcm", rcmId] });
    } catch (err) {
      setFormError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    }
  }

  async function onApply() {
    try {
      const result = await applyRCMToTemplate(rcmId);
      setFormError(null);
      setApplyMessage(
        t("rcm.applyResult").replace("{count}", String(result.updated)).replace(
          "{strategy}",
          t(`enums.rcm_strategy.${result.strategy}`),
        ),
      );
    } catch (err) {
      setApplyMessage(null);
      setFormError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    }
  }

  if (query.error) {
    return <p className="text-sm text-destructive">{t("errors.generic")}</p>;
  }
  if (!analysis) {
    return <p className="text-sm text-muted-foreground">{t("common.loading")}</p>;
  }

  return (
    <section className="space-y-8">
      <PageHeader title={analysis.code} description={analysis.title}>
        <DemoBadge visible={analysis.is_demo} />
        <Button asChild variant="outline">
          <Link href="/rcm">{t("common.back")}</Link>
        </Button>
        {canUpdate && editable ? (
          <Button type="button" variant="outline" onClick={onEvaluate}>
            {t("rcm.evaluate")}
          </Button>
        ) : null}
        {canApprove && editable ? (
          <Button type="button" onClick={onApprove}>
            {t("rcm.approve")}
          </Button>
        ) : null}
        {canUpdate && analysis.status === "APPROVED" ? (
          <Button type="button" onClick={onApply}>
            {t("rcm.applyToTemplate")}
          </Button>
        ) : null}
      </PageHeader>
      {formError ? <p className="text-sm text-destructive">{t(formError)}</p> : null}
      {applyMessage ? <p className="text-sm text-muted-foreground">{applyMessage}</p> : null}
      <p className="text-sm text-muted-foreground">
        {t("rcm.status")}: {t(`enums.rcm_status.${analysis.status}`)} · {t("rcm.revision")}:{" "}
        {analysis.revision}
        {analysis.component_type_name ? ` · ${analysis.component_type_name}` : ""}
      </p>
      {canUpdate && editable ? <RCMHeaderForm initial={analysis} /> : null}
      <div>
        <h2 className="mb-3 text-base font-semibold text-primary">{t("rcm.items")}</h2>
        <div className="overflow-x-auto rounded-lg border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("rcm.function")}</TableHead>
                <TableHead>{t("rcm.functionalFailure")}</TableHead>
                <TableHead>{t("failure.mode")}</TableHead>
                <TableHead>{t("rcm.suggested")}</TableHead>
                <TableHead>{t("rcm.strategy")}</TableHead>
                {canUpdate && editable ? <TableHead>{t("common.actions")}</TableHead> : null}
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.length === 0 ? (
                <TableRow>
                  <TableCell className="text-muted-foreground" colSpan={canUpdate && editable ? 6 : 5}>
                    {t("rcm.emptyItems")}
                  </TableCell>
                </TableRow>
              ) : (
                items.map((item) => (
                  <TableRow key={item.id}>
                    <TableCell>{item.function}</TableCell>
                    <TableCell>{item.functional_failure}</TableCell>
                    <TableCell>{item.failure_mode}</TableCell>
                    <TableCell>{t(`enums.rcm_strategy.${item.suggested_strategy}`)}</TableCell>
                    <TableCell>
                      {t(`enums.rcm_strategy.${item.strategy}`)}
                      {item.is_overridden ? ` · ${t("rcm.overridden")}` : ""}
                      {item.grounded_warning ? ` · ${t("rcm.groundedWarning")}` : ""}
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
          <h3 className="text-sm font-semibold">{t("rcm.addItem")}</h3>
          <p className="text-xs text-muted-foreground">{t("rcm.treeHint")}</p>
          <div className="grid grid-cols-2 gap-3">
            <Field label={t("rcm.function")}>
              <Input
                required
                value={itemForm.function}
                onChange={(event) => setItemForm({ ...itemForm, function: event.target.value })}
              />
            </Field>
            <Field label={t("rcm.functionalFailure")}>
              <Input
                required
                value={itemForm.functional_failure}
                onChange={(event) =>
                  setItemForm({ ...itemForm, functional_failure: event.target.value })
                }
              />
            </Field>
            <Field label={t("rcm.failureModeText")}>
              <Input
                required
                value={itemForm.failure_mode}
                onChange={(event) => setItemForm({ ...itemForm, failure_mode: event.target.value })}
              />
            </Field>
            <Field label={t("rcm.fmeaItem")}>
              <NativeSelect
                value={itemForm.fmea_item ?? ""}
                onChange={(event) => setItemForm({ ...itemForm, fmea_item: event.target.value })}
              >
                <option value="">{t("rcm.fmeaItemNone")}</option>
                {fmeaItems.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.label}
                  </option>
                ))}
              </NativeSelect>
            </Field>
            <Field label={t("rcm.safetyEffect")}>
              <NativeSelect
                value={itemForm.safety_effect ? "true" : "false"}
                onChange={(event) =>
                  setItemForm({ ...itemForm, safety_effect: event.target.value === "true" })
                }
              >
                <option value="false">{t("rcm.no")}</option>
                <option value="true">{t("rcm.yes")}</option>
              </NativeSelect>
            </Field>
            <Field label={t("rcm.operationalEffect")}>
              <NativeSelect
                value={itemForm.operational_effect ? "true" : "false"}
                onChange={(event) =>
                  setItemForm({
                    ...itemForm,
                    operational_effect: event.target.value === "true",
                  })
                }
              >
                <option value="false">{t("rcm.no")}</option>
                <option value="true">{t("rcm.yes")}</option>
              </NativeSelect>
            </Field>
            <Field label={t("rcm.preventiveFeasible")}>
              <NativeSelect
                value={itemForm.preventive_feasible ? "true" : "false"}
                onChange={(event) =>
                  setItemForm({
                    ...itemForm,
                    preventive_feasible: event.target.value === "true",
                  })
                }
              >
                <option value="false">{t("rcm.no")}</option>
                <option value="true">{t("rcm.yes")}</option>
              </NativeSelect>
            </Field>
            <Field label={t("rcm.detectability")}>
              <NativeSelect
                value={itemForm.detectability}
                onChange={(event) =>
                  setItemForm({
                    ...itemForm,
                    detectability: event.target.value as RCMItemWritePayload["detectability"],
                  })
                }
              >
                {DETECTABILITIES.map((value) => (
                  <option key={value} value={value}>
                    {t(`enums.detectability.${value}`)}
                  </option>
                ))}
              </NativeSelect>
            </Field>
            <Field label={t("rcm.strategyOverride")}>
              <NativeSelect
                value={itemForm.strategy ?? ""}
                onChange={(event) =>
                  setItemForm({
                    ...itemForm,
                    strategy: event.target.value as RCMItemWritePayload["strategy"],
                  })
                }
              >
                <option value="">{t("rcm.useTree")}</option>
                {RCM_STRATEGIES.map((strategy) => (
                  <option key={strategy} value={strategy}>
                    {t(`enums.rcm_strategy.${strategy}`)}
                  </option>
                ))}
              </NativeSelect>
            </Field>
          </div>
          <Field label={t("rcm.effect")}>
            <Textarea
              value={itemForm.failure_effect}
              onChange={(event) => setItemForm({ ...itemForm, failure_effect: event.target.value })}
            />
          </Field>
          <Field label={t("rcm.rationale")}>
            <Textarea
              value={itemForm.rationale}
              onChange={(event) => setItemForm({ ...itemForm, rationale: event.target.value })}
            />
          </Field>
          <Button type="submit" disabled={createMutation.isPending}>
            {createMutation.isPending ? t("common.loading") : t("rcm.addItem")}
          </Button>
        </form>
      ) : null}
    </section>
  );
}
