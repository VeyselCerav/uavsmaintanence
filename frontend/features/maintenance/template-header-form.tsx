"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { Field } from "@/components/system/field";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { NativeSelect } from "@/components/ui/native-select";
import { Textarea } from "@/components/ui/textarea";
import { ApiClientError } from "@/services/api";
import { useI18n } from "@/lib/i18n-context";
import { createTemplate, updateTemplate } from "@/services/maintenance";
import { listClasses, listMissions, listPlatforms } from "@/services/uavs";
import type { MaintenanceApproach } from "@/types/uav";
import type { MaintenanceTemplate, TemplateWritePayload } from "@/types/maintenance";

const APPROACHES: MaintenanceApproach[] = ["CLASS_SPECIFIC", "STANDARD"];

type Props = {
  initial?: MaintenanceTemplate;
};

export function TemplateHeaderForm({ initial }: Props) {
  const { t } = useI18n();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const classes = useQuery({ queryKey: ["uav-classes"], queryFn: listClasses });
  const platforms = useQuery({ queryKey: ["platforms"], queryFn: listPlatforms });
  const missions = useQuery({ queryKey: ["missions"], queryFn: listMissions });
  const [form, setForm] = useState<TemplateWritePayload>({
    code: initial?.code ?? "",
    name: initial?.name ?? "",
    description: initial?.description ?? "",
    uav_class: initial?.uav_class ?? "",
    platform_type: initial?.platform_type ?? "",
    mission_type: initial?.mission_type ?? "",
    approach: initial?.approach ?? "CLASS_SPECIFIC",
    is_active: initial?.is_active ?? true,
    notes: initial?.notes ?? "",
  });

  function setField<K extends keyof TemplateWritePayload>(key: K, value: TemplateWritePayload[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      const saved = initial ? await updateTemplate(initial.id, form) : await createTemplate(form);
      router.replace(`/admin/maintenance-templates/${saved.id}`);
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
        <Field label={t("catalog.name")}>
          <Input required value={form.name} onChange={(event) => setField("name", event.target.value)} />
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
        <Field label={t("uav.mission")}>
          <NativeSelect
            required
            value={form.mission_type}
            onChange={(event) => setField("mission_type", event.target.value)}
          >
            <option value="" />
            {(missions.data?.data ?? []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </NativeSelect>
        </Field>
        <Field label={t("uav.approach")}>
          <NativeSelect
            value={form.approach}
            onChange={(event) => setField("approach", event.target.value as MaintenanceApproach)}
          >
            {APPROACHES.map((approach) => (
              <option key={approach} value={approach}>
                {t(`enums.maintenance_approach.${approach}`)}
              </option>
            ))}
          </NativeSelect>
        </Field>
      </div>
      <div className="flex items-center gap-2">
        <Checkbox
          id="template-active"
          checked={form.is_active}
          onCheckedChange={(checked: boolean | "indeterminate") => setField("is_active", checked === true)}
        />
        <Label htmlFor="template-active">{t("catalog.active")}</Label>
      </div>
      <Field label={t("catalog.description")}>
        <Textarea
          rows={2}
          value={form.description ?? ""}
          onChange={(event) => setField("description", event.target.value)}
        />
      </Field>
      <div className="flex gap-2">
        <Button type="submit" disabled={pending}>
          {pending ? t("common.loading") : t("common.save")}
        </Button>
        <Button asChild variant="outline">
          <Link href="/admin/maintenance-templates">{t("common.cancel")}</Link>
        </Button>
      </div>
    </form>
  );
}
