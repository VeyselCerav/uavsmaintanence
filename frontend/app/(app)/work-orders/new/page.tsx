"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { FormEvent, Suspense, useMemo, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { Field } from "@/components/system/field";
import { PageHeader } from "@/components/system/page-header";
import { DueBadge } from "@/components/system/status-badge";
import { Button } from "@/components/ui/button";
import { NativeSelect } from "@/components/ui/native-select";
import { useI18n } from "@/lib/i18n-context";
import { ApiClientError } from "@/services/api";
import { listDues } from "@/services/maintenance";
import { listUAVs } from "@/services/uavs";
import { createWorkOrderFromDue } from "@/services/work-orders";

export default function NewWorkOrderPage() {
  const { t } = useI18n();
  return (
    <Suspense fallback={<p className="text-sm text-muted-foreground">{t("common.loading")}</p>}>
      <NewWorkOrderForm />
    </Suspense>
  );
}

function NewWorkOrderForm() {
  const { t } = useI18n();
  const router = useRouter();
  const searchParams = useSearchParams();
  const presetDue = searchParams.get("due") ?? "";
  const presetUav = searchParams.get("uav") ?? "";
  const [uavId, setUavId] = useState(presetUav);
  const [dueId, setDueId] = useState(presetDue);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const uavs = useQuery({ queryKey: ["uavs", ""], queryFn: () => listUAVs() });
  const dues = useQuery({
    queryKey: ["dues", uavId],
    queryFn: () => listDues(uavId),
    enabled: Boolean(uavId),
  });
  const dueOptions = useMemo(() => dues.data?.data ?? [], [dues.data]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!dueId) return;
    setPending(true);
    setError(null);
    try {
      const saved = await createWorkOrderFromDue(dueId);
      router.replace(`/work-orders/${saved.id}`);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    } finally {
      setPending(false);
    }
  }

  return (
    <section>
      <PageHeader title={t("workOrder.new")} />
      <form onSubmit={onSubmit} className="max-w-xl space-y-4">
        {error ? <p className="text-sm text-destructive">{t(error)}</p> : null}
        <Field label={t("uav.registration")}>
          <NativeSelect
            required={!dueId}
            value={uavId}
            onChange={(event) => {
              setUavId(event.target.value);
              setDueId("");
            }}
          >
            <option value="" />
            {(uavs.data?.data ?? []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.registration_number}
              </option>
            ))}
          </NativeSelect>
        </Field>
        <Field label={t("due.title")}>
          <NativeSelect
            required
            value={dueId}
            onChange={(event) => setDueId(event.target.value)}
            disabled={!uavId}
          >
            <option value="" />
            {dueOptions.map((due) => (
              <option key={due.id} value={due.id}>
                {due.task_code} — {due.task_name} ({due.usage_percent}%)
              </option>
            ))}
          </NativeSelect>
        </Field>
        {dueOptions
          .filter((due) => due.id === dueId)
          .map((due) => (
            <p key={due.id} className="text-sm">
              <DueBadge status={due.status} />
            </p>
          ))}
        <div className="flex gap-2">
          <Button type="submit" disabled={pending || !dueId}>
            {pending ? t("common.loading") : t("common.create")}
          </Button>
          <Button asChild variant="outline">
            <Link href="/work-orders">{t("common.cancel")}</Link>
          </Button>
        </div>
      </form>
    </section>
  );
}
