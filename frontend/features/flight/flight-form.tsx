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
import { createFlight } from "@/services/flights";
import { listUAVs } from "@/services/uavs";

function toLocalInput(date: Date) {
  const pad = (value: number) => String(value).padStart(2, "0");
  const day = `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
  const clock = `${pad(date.getHours())}:${pad(date.getMinutes())}`;
  return `${day}T${clock}`;
}

export function FlightForm() {
  const { t } = useI18n();
  const router = useRouter();
  const uavs = useQuery({ queryKey: ["uavs", ""], queryFn: () => listUAVs() });
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const now = new Date();
  const later = new Date(now.getTime() + 60 * 60 * 1000);
  const [uav, setUav] = useState("");
  const [startAt, setStartAt] = useState(toLocalInput(now));
  const [endAt, setEndAt] = useState(toLocalInput(later));
  const [durationHours, setDurationHours] = useState("");
  const [notes, setNotes] = useState("");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      const saved = await createFlight({
        uav,
        start_at: new Date(startAt).toISOString(),
        end_at: new Date(endAt).toISOString(),
        duration_hours: durationHours || null,
        notes,
      });
      router.replace(`/flights/${saved.id}`);
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
      <Field label={t("flight.start")}>
        <Input
          required
          type="datetime-local"
          value={startAt}
          onChange={(event) => setStartAt(event.target.value)}
        />
      </Field>
      <Field label={t("flight.end")}>
        <Input
          required
          type="datetime-local"
          value={endAt}
          onChange={(event) => setEndAt(event.target.value)}
        />
      </Field>
      <Field label={t("flight.durationOverride")}>
        <Input
          value={durationHours}
          onChange={(event) => setDurationHours(event.target.value)}
          placeholder={t("flight.durationHint")}
        />
      </Field>
      <Field label={t("uav.notes")}>
        <Textarea rows={3} value={notes} onChange={(event) => setNotes(event.target.value)} />
      </Field>
      <div className="flex gap-2">
        <Button type="submit" disabled={pending}>
          {pending ? t("common.loading") : t("common.save")}
        </Button>
        <Button asChild variant="outline">
          <Link href="/flights">{t("common.cancel")}</Link>
        </Button>
      </div>
    </form>
  );
}
