"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { Field } from "@/components/system/field";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";
import { Textarea } from "@/components/ui/textarea";
import { ApiClientError } from "@/services/api";
import { useI18n } from "@/lib/i18n-context";
import { createFailure, listFailureModes } from "@/services/failures";
import { listUAVs } from "@/services/uavs";
import type { DiscoveredDuring, FailureSeverity } from "@/types/failure";

function toLocalInput(date: Date) {
  const pad = (value: number) => String(value).padStart(2, "0");
  const day = `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
  const clock = `${pad(date.getHours())}:${pad(date.getMinutes())}`;
  return `${day}T${clock}`;
}

const DISCOVERED: DiscoveredDuring[] = ["FLIGHT", "INSPECTION", "MAINTENANCE", "OTHER"];
const SEVERITIES: FailureSeverity[] = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];

export function FailureForm() {
  const { t } = useI18n();
  const router = useRouter();
  const uavs = useQuery({ queryKey: ["uavs", ""], queryFn: () => listUAVs() });
  const modes = useQuery({ queryKey: ["failure-modes"], queryFn: () => listFailureModes() });
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [uav, setUav] = useState("");
  const [occurredAt, setOccurredAt] = useState(toLocalInput(new Date()));
  const [discoveredDuring, setDiscoveredDuring] = useState<DiscoveredDuring>("MAINTENANCE");
  const [severity, setSeverity] = useState<FailureSeverity>("MEDIUM");
  const [failureMode, setFailureMode] = useState("");
  const [description, setDescription] = useState("");
  const [downtimeHours, setDowntimeHours] = useState("0");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      const saved = await createFailure({
        uav,
        occurred_at: new Date(occurredAt).toISOString(),
        discovered_during: discoveredDuring,
        severity,
        failure_mode: failureMode || null,
        description,
        downtime_hours: downtimeHours || "0",
      });
      router.replace(`/failures/${saved.id}`);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="max-w-xl space-y-4">
      {error ? <p className="text-sm text-destructive">{t(error)}</p> : null}
      <Field label={t("uav.registration")}>
        <NativeSelect required value={uav} onChange={(event) => setUav(event.target.value)}>
          <option value="" />
          {(uavs.data?.data ?? []).map((item) => (
            <option key={item.id} value={item.id}>
              {item.registration_number}
            </option>
          ))}
        </NativeSelect>
      </Field>
      <Field label={t("failure.occurredAt")}>
        <Input
          required
          type="datetime-local"
          value={occurredAt}
          onChange={(event) => setOccurredAt(event.target.value)}
        />
      </Field>
      <Field label={t("failure.discovered")}>
        <NativeSelect
          required
          value={discoveredDuring}
          onChange={(event) => setDiscoveredDuring(event.target.value as DiscoveredDuring)}
        >
          {DISCOVERED.map((value) => (
            <option key={value} value={value}>
              {t(`enums.discovered_during.${value}`)}
            </option>
          ))}
        </NativeSelect>
      </Field>
      <Field label={t("failure.severity")}>
        <NativeSelect
          required
          value={severity}
          onChange={(event) => setSeverity(event.target.value as FailureSeverity)}
        >
          {SEVERITIES.map((value) => (
            <option key={value} value={value}>
              {t(`enums.failure_severity.${value}`)}
            </option>
          ))}
        </NativeSelect>
      </Field>
      <Field label={t("failure.mode")}>
        <NativeSelect value={failureMode} onChange={(event) => setFailureMode(event.target.value)}>
          <option value="">{t("failure.modeNone")}</option>
          {(modes.data?.data ?? []).map((item) => (
            <option key={item.id} value={item.id}>
              {item.code} — {item.name}
            </option>
          ))}
        </NativeSelect>
      </Field>
      <Field label={t("failure.downtime")}>
        <Input
          type="number"
          min="0"
          step="0.01"
          value={downtimeHours}
          onChange={(event) => setDowntimeHours(event.target.value)}
        />
      </Field>
      <Field label={t("failure.description")}>
        <Textarea
          required
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />
      </Field>
      <div className="flex gap-2">
        <Button type="submit" disabled={pending}>
          {pending ? t("common.loading") : t("common.save")}
        </Button>
        <Button asChild variant="outline">
          <Link href="/failures">{t("common.cancel")}</Link>
        </Button>
      </div>
    </form>
  );
}
