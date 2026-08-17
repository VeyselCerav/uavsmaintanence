"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useMemo, useState } from "react";

import { AdminOnly } from "@/components/system/admin-only";
import { Field } from "@/components/system/field";
import { PageHeader } from "@/components/system/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { NativeSelect } from "@/components/ui/native-select";
import { useI18n } from "@/lib/i18n-context";
import { ApiClientError } from "@/services/api";
import { listSettings, updateSetting } from "@/services/admin";
import type { DueRulesValue, RpnThresholdsValue } from "@/types/admin";

const DEFAULT_DUE: DueRulesValue = {
  approaching_percent: 80,
  due_percent: 100,
  overdue_percent: 110,
  critical_percent: 130,
};
const DEFAULT_RPN: RpnThresholdsValue = { low_max: 49, medium_max: 99, high_max: 199 };

function asDue(value: unknown): DueRulesValue {
  if (!value || typeof value !== "object") return DEFAULT_DUE;
  const raw = value as Record<string, number>;
  return {
    approaching_percent: Number(raw.approaching_percent ?? DEFAULT_DUE.approaching_percent),
    due_percent: Number(raw.due_percent ?? DEFAULT_DUE.due_percent),
    overdue_percent: Number(raw.overdue_percent ?? DEFAULT_DUE.overdue_percent),
    critical_percent: Number(raw.critical_percent ?? DEFAULT_DUE.critical_percent),
  };
}

function asRpn(value: unknown): RpnThresholdsValue {
  if (!value || typeof value !== "object") return DEFAULT_RPN;
  const raw = value as Record<string, number>;
  return {
    low_max: Number(raw.low_max ?? DEFAULT_RPN.low_max),
    medium_max: Number(raw.medium_max ?? DEFAULT_RPN.medium_max),
    high_max: Number(raw.high_max ?? DEFAULT_RPN.high_max),
  };
}

function SettingsBody() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [saved, setSaved] = useState(false);
  const query = useQuery({ queryKey: ["settings"], queryFn: listSettings });
  const byKey = useMemo(() => {
    const map = new Map((query.data ?? []).map((item) => [item.key, item.value]));
    return map;
  }, [query.data]);
  const [due, setDue] = useState<DueRulesValue | null>(null);
  const [rpn, setRpn] = useState<RpnThresholdsValue | null>(null);
  const [autoCreate, setAutoCreate] = useState<boolean | null>(null);
  const [policy, setPolicy] = useState<string | null>(null);
  const dueValue = due ?? asDue(byKey.get("maintenance.due_rules"));
  const rpnValue = rpn ?? asRpn(byKey.get("rpn.thresholds"));
  const autoValue = autoCreate ?? Boolean(byKey.get("work_order.auto_create_on_due"));
  const policyValue =
    policy ??
    (typeof byKey.get("reliability.zero_failure_policy") === "string"
      ? (byKey.get("reliability.zero_failure_policy") as string)
      : "undefined");
  const mutation = useMutation({
    mutationFn: async () => {
      await updateSetting("maintenance.due_rules", dueValue);
      await updateSetting("rpn.thresholds", rpnValue);
      await updateSetting("work_order.auto_create_on_due", autoValue);
      await updateSetting("reliability.zero_failure_policy", policyValue);
    },
    onSuccess: async () => {
      setSaved(true);
      await queryClient.invalidateQueries({ queryKey: ["settings"] });
      await queryClient.invalidateQueries({ queryKey: ["due-rules"] });
    },
  });
  const error =
    mutation.error instanceof ApiClientError
      ? mutation.error.message_key
      : query.error instanceof Error
        ? query.error.message
        : null;

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSaved(false);
    mutation.mutate();
  }

  if (!query.data) {
    return <p className="text-sm text-muted-foreground">{t("common.loading")}</p>;
  }

  return (
    <section className="max-w-xl">
      <PageHeader title={t("admin.settings")} description={t("settings.hint")} />
      {error ? <p className="mb-3 text-sm text-destructive">{t(error)}</p> : null}
      {saved ? <p className="mb-3 text-sm text-success">{t("settings.saved")}</p> : null}
      <Card>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            <p className="text-sm font-semibold text-primary">{t("admin.rules")}</p>
            {(
              [
                ["approaching_percent", "dueRules.approaching"],
                ["due_percent", "dueRules.due"],
                ["overdue_percent", "dueRules.overdue"],
                ["critical_percent", "dueRules.critical"],
              ] as const
            ).map(([key, label]) => (
              <Field key={key} label={t(label)}>
                <Input
                  required
                  type="number"
                  min={0.01}
                  step={0.01}
                  value={dueValue[key]}
                  onChange={(event) =>
                    setDue({ ...dueValue, [key]: Number(event.target.value) })
                  }
                />
              </Field>
            ))}
            <div className="flex items-start gap-2">
              <Checkbox
                id="auto-create-setting"
                className="mt-1"
                checked={autoValue}
                onCheckedChange={(checked: boolean | "indeterminate") =>
                  setAutoCreate(checked === true)
                }
              />
              <Label htmlFor="auto-create-setting">{t("dueRules.autoCreate")}</Label>
            </div>
            <p className="text-sm font-semibold text-primary">{t("settings.rpn")}</p>
            {(
              [
                ["low_max", "settings.rpnLow"],
                ["medium_max", "settings.rpnMedium"],
                ["high_max", "settings.rpnHigh"],
              ] as const
            ).map(([key, label]) => (
              <Field key={key} label={t(label)}>
                <Input
                  required
                  type="number"
                  min={1}
                  value={rpnValue[key]}
                  onChange={(event) =>
                    setRpn({ ...rpnValue, [key]: Number(event.target.value) })
                  }
                />
              </Field>
            ))}
            <Field label={t("settings.zeroFailure")}>
              <NativeSelect
                value={policyValue}
                onChange={(event) => setPolicy(event.target.value)}
              >
                <option value="undefined">{t("settings.zeroUndefined")}</option>
                <option value="operating_time_as_lower_bound">
                  {t("settings.zeroLowerBound")}
                </option>
              </NativeSelect>
            </Field>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? t("common.loading") : t("common.save")}
            </Button>
          </form>
        </CardContent>
      </Card>
    </section>
  );
}

export default function AdminSettingsPage() {
  return (
    <AdminOnly>
      <SettingsBody />
    </AdminOnly>
  );
}
