"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { Field } from "@/components/system/field";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";
import { Textarea } from "@/components/ui/textarea";
import { ApiClientError } from "@/services/api";
import { useI18n } from "@/lib/i18n-context";
import { createRCM, updateRCM } from "@/services/rcm";
import { listComponentTypes } from "@/services/maintenance";
import { listClasses, listMissions, listPlatforms } from "@/services/uavs";
import type { RCMAnalysis, RCMWritePayload } from "@/types/rcm";

type Props = {
  initial?: RCMAnalysis;
};

export function RCMHeaderForm({ initial }: Props) {
  const { t } = useI18n();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const classes = useQuery({ queryKey: ["uav-classes"], queryFn: listClasses });
  const platforms = useQuery({ queryKey: ["platforms"], queryFn: listPlatforms });
  const missions = useQuery({ queryKey: ["missions"], queryFn: listMissions });
  const types = useQuery({ queryKey: ["component-types"], queryFn: listComponentTypes });
  const [form, setForm] = useState<RCMWritePayload>({
    code: initial?.code ?? "",
    title: initial?.title ?? "",
    uav_class: initial?.uav_class ?? "",
    platform_type: initial?.platform_type ?? "",
    component_type: initial?.component_type ?? "",
    mission_type: initial?.mission_type ?? "",
    notes: initial?.notes ?? "",
  });

  function setField<K extends keyof RCMWritePayload>(key: K, value: RCMWritePayload[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      const payload = {
        ...form,
        mission_type: form.mission_type || null,
      };
      const saved = initial ? await updateRCM(initial.id, payload) : await createRCM(payload);
      router.replace(`/rcm/${saved.id}`);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="max-w-3xl space-y-4">
      {error ? <p className="text-sm text-destructive">{t(error)}</p> : null}
      <div className="grid grid-cols-2 gap-3">
        <Field label={t("catalog.code")}>
          <Input required value={form.code} onChange={(event) => setField("code", event.target.value)} />
        </Field>
        <Field label={t("rcm.titleField")}>
          <Input required value={form.title} onChange={(event) => setField("title", event.target.value)} />
        </Field>
        <Field label={t("uav.class")}>
          <NativeSelect
            required
            value={form.uav_class}
            onChange={(event) => setField("uav_class", event.target.value)}
          >
            <option value="" />
            {(classes.data?.data ?? []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </NativeSelect>
        </Field>
        <Field label={t("uav.platform")}>
          <NativeSelect
            required
            value={form.platform_type}
            onChange={(event) => setField("platform_type", event.target.value)}
          >
            <option value="" />
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
            value={form.component_type}
            onChange={(event) => setField("component_type", event.target.value)}
          >
            <option value="" />
            {(types.data?.data ?? []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </NativeSelect>
        </Field>
        <Field label={t("uav.mission")}>
          <NativeSelect
            value={form.mission_type ?? ""}
            onChange={(event) => setField("mission_type", event.target.value)}
          >
            <option value="">{t("rcm.allMissions")}</option>
            {(missions.data?.data ?? []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </NativeSelect>
        </Field>
      </div>
      <Field label={t("uav.notes")}>
        <Textarea value={form.notes} onChange={(event) => setField("notes", event.target.value)} />
      </Field>
      <div className="flex gap-2">
        <Button type="submit" disabled={pending}>
          {pending ? t("common.loading") : t("common.save")}
        </Button>
        <Button asChild variant="outline">
          <Link href={initial ? `/rcm/${initial.id}` : "/rcm"}>{t("common.cancel")}</Link>
        </Button>
      </div>
    </form>
  );
}
