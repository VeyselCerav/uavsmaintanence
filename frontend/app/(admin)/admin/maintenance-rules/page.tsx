"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { Field } from "@/components/system/field";
import { PageHeader } from "@/components/system/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useSessionUser } from "@/hooks/use-session-user";
import { hasPermission } from "@/lib/auth";
import { useI18n } from "@/lib/i18n-context";
import { ApiClientError } from "@/services/api";
import { getDueRules, updateDueRules } from "@/services/due-rules";
import type { DueRules } from "@/types/due-rules";

const FIELDS: Array<{ key: keyof Omit<DueRules, "auto_create_on_due">; label: string }> = [
  { key: "approaching_percent", label: "dueRules.approaching" },
  { key: "due_percent", label: "dueRules.due" },
  { key: "overdue_percent", label: "dueRules.overdue" },
  { key: "critical_percent", label: "dueRules.critical" },
];

export default function AdminRulesPage() {
  const { t } = useI18n();
  const user = useSessionUser();
  const queryClient = useQueryClient();
  const canUpdate = hasPermission(user, "maintenance_rule.update");
  const [draft, setDraft] = useState<DueRules | null>(null);
  const [saved, setSaved] = useState(false);
  const query = useQuery({
    queryKey: ["due-rules"],
    queryFn: getDueRules,
  });
  const values = draft ?? query.data ?? null;
  const mutation = useMutation({
    mutationFn: (payload: DueRules) => updateDueRules(payload),
    onSuccess: async (data) => {
      setDraft(null);
      setSaved(true);
      queryClient.setQueryData(["due-rules"], data);
      await queryClient.invalidateQueries({ queryKey: ["dues"] });
      await queryClient.invalidateQueries({ queryKey: ["work-orders"] });
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
    if (!values) return;
    setSaved(false);
    mutation.mutate(values);
  }

  if (!values) {
    return <p className="text-sm text-muted-foreground">{t("common.loading")}</p>;
  }

  return (
    <section className="max-w-xl">
      <PageHeader title={t("admin.rules")} description={t("dueRules.hint")} />
      {error ? <p className="mb-3 text-sm text-destructive">{t(error)}</p> : null}
      {saved ? <p className="mb-3 text-sm text-success">{t("dueRules.saved")}</p> : null}
      <Card>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4">
            {FIELDS.map((field) => (
              <Field key={field.key} label={t(field.label)}>
                <Input
                  required
                  type="number"
                  min={0.01}
                  step={0.01}
                  disabled={!canUpdate}
                  value={values[field.key]}
                  onChange={(event) =>
                    setDraft({
                      ...values,
                      [field.key]: Number(event.target.value),
                    })
                  }
                />
              </Field>
            ))}
            <p className="text-xs text-muted-foreground">{t("dueRules.orderHint")}</p>
            <div className="flex items-start gap-2">
              <Checkbox
                id="auto-create"
                className="mt-1"
                disabled={!canUpdate}
                checked={values.auto_create_on_due}
                onCheckedChange={(checked: boolean | "indeterminate") =>
                  setDraft({
                    ...values,
                    auto_create_on_due: checked === true,
                  })
                }
              />
              <Label htmlFor="auto-create" className="items-start">
                <span>
                  {t("dueRules.autoCreate")}
                  <span className="mt-1 block text-xs font-normal text-muted-foreground">
                    {t("dueRules.autoCreateHint")}
                  </span>
                </span>
              </Label>
            </div>
            {canUpdate ? (
              <Button type="submit" disabled={mutation.isPending}>
                {mutation.isPending ? t("common.loading") : t("common.save")}
              </Button>
            ) : null}
          </form>
        </CardContent>
      </Card>
    </section>
  );
}
