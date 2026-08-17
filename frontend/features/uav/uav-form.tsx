"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { Field } from "@/components/system/field";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";
import { Textarea } from "@/components/ui/textarea";
import { ApiClientError } from "@/services/api";
import { createUAV, listClasses, listMissions, listPlatforms, updateUAV } from "@/services/uavs";
import { useI18n } from "@/lib/i18n-context";
import type { CatalogItem, MaintenanceApproach, UAV, UAVClass, UAVStatus, UAVWritePayload } from "@/types/uav";

const STATUSES: UAVStatus[] = ["READY", "MAINTENANCE", "GROUNDED", "RETIRED"];
const APPROACHES: MaintenanceApproach[] = ["CLASS_SPECIFIC", "STANDARD"];

type Props = {
  initial?: UAV;
};

export function UAVForm({ initial }: Props) {
  const { t } = useI18n();
  const router = useRouter();
  const [classes, setClasses] = useState<UAVClass[]>([]);
  const [platforms, setPlatforms] = useState<CatalogItem[]>([]);
  const [missions, setMissions] = useState<CatalogItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [form, setForm] = useState<UAVWritePayload>({
    registration_number: initial?.registration_number ?? "",
    serial_number: initial?.serial_number ?? "",
    manufacturer: initial?.manufacturer ?? "",
    model: initial?.model ?? "",
    uav_class: initial?.uav_class ?? "",
    platform_type: initial?.platform_type ?? "",
    mission_type: initial?.mission_type ?? "",
    maintenance_approach: initial?.maintenance_approach ?? "CLASS_SPECIFIC",
    mtow_kg: initial?.mtow_kg ?? "",
    production_date: initial?.production_date ?? "",
    inventory_entry_date: initial?.inventory_entry_date ?? "",
    status: initial?.status ?? "READY",
    notes: initial?.notes ?? "",
  });

  useEffect(() => {
    void Promise.all([listClasses(), listPlatforms(), listMissions()]).then(
      ([classPage, platformPage, missionPage]) => {
        setClasses(classPage.data);
        setPlatforms(platformPage.data);
        setMissions(missionPage.data);
      },
    );
  }, []);

  function setField<K extends keyof UAVWritePayload>(key: K, value: UAVWritePayload[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    const payload: UAVWritePayload = {
      ...form,
      mtow_kg: form.mtow_kg || null,
      production_date: form.production_date || null,
      inventory_entry_date: form.inventory_entry_date || null,
    };
    try {
      const saved = initial ? await updateUAV(initial.id, payload) : await createUAV(payload);
      router.replace(`/uavs/${saved.id}`);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="max-w-3xl space-y-6">
      {error ? <p className="text-sm text-destructive">{t(error)}</p> : null}
      <fieldset className="space-y-3">
        <legend className="text-sm font-semibold text-primary">{t("uav.general")}</legend>
        <div className="grid grid-cols-2 gap-3">
          <Field label={t("uav.registration")}>
            <Input
              required
              value={form.registration_number}
              onChange={(event) => setField("registration_number", event.target.value)}
            />
          </Field>
          <Field label={t("uav.serial")}>
            <Input
              required
              value={form.serial_number}
              onChange={(event) => setField("serial_number", event.target.value)}
            />
          </Field>
          <Field label={t("uav.manufacturer")}>
            <Input
              required
              value={form.manufacturer}
              onChange={(event) => setField("manufacturer", event.target.value)}
            />
          </Field>
          <Field label={t("uav.model")}>
            <Input required value={form.model} onChange={(event) => setField("model", event.target.value)} />
          </Field>
        </div>
      </fieldset>
      <fieldset className="space-y-3">
        <legend className="text-sm font-semibold text-primary">{t("uav.technical")}</legend>
        <div className="grid grid-cols-2 gap-3">
          <Field label={t("uav.class")}>
            <NativeSelect
              required
              value={form.uav_class}
              onChange={(event) => setField("uav_class", event.target.value)}
            >
              <option value="" />
              {classes.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </NativeSelect>
          </Field>
          <Field label={t("uav.mtow")}>
            <Input value={form.mtow_kg ?? ""} onChange={(event) => setField("mtow_kg", event.target.value)} />
          </Field>
          <Field label={t("uav.productionDate")}>
            <Input
              type="date"
              value={form.production_date ?? ""}
              onChange={(event) => setField("production_date", event.target.value)}
            />
          </Field>
          <Field label={t("uav.inventoryDate")}>
            <Input
              type="date"
              value={form.inventory_entry_date ?? ""}
              onChange={(event) => setField("inventory_entry_date", event.target.value)}
            />
          </Field>
        </div>
      </fieldset>
      <fieldset className="space-y-3">
        <legend className="text-sm font-semibold text-primary">{t("uav.operational")}</legend>
        <div className="grid grid-cols-2 gap-3">
          <Field label={t("uav.platform")}>
            <NativeSelect
              required
              value={form.platform_type}
              onChange={(event) => setField("platform_type", event.target.value)}
            >
              <option value="" />
              {platforms.map((item) => (
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
              {missions.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </NativeSelect>
          </Field>
          <Field label={t("uav.status")}>
            <NativeSelect
              value={form.status}
              onChange={(event) => setField("status", event.target.value as UAVStatus)}
            >
              {STATUSES.map((status) => (
                <option key={status} value={status}>
                  {t(`enums.uav_status.${status}`)}
                </option>
              ))}
            </NativeSelect>
          </Field>
        </div>
      </fieldset>
      <fieldset className="space-y-3">
        <legend className="text-sm font-semibold text-primary">{t("uav.maintenance")}</legend>
        <Field label={t("uav.approach")}>
          <NativeSelect
            value={form.maintenance_approach}
            onChange={(event) => setField("maintenance_approach", event.target.value as MaintenanceApproach)}
          >
            {APPROACHES.map((approach) => (
              <option key={approach} value={approach}>
                {t(`enums.maintenance_approach.${approach}`)}
              </option>
            ))}
          </NativeSelect>
        </Field>
        <Field label={t("uav.notes")}>
          <Textarea
            rows={3}
            value={form.notes ?? ""}
            onChange={(event) => setField("notes", event.target.value)}
          />
        </Field>
      </fieldset>
      <div className="flex gap-2">
        <Button type="submit" disabled={pending}>
          {pending ? t("common.loading") : t("common.save")}
        </Button>
        <Button asChild variant="outline">
          <Link href="/uavs">{t("common.cancel")}</Link>
        </Button>
      </div>
    </form>
  );
}
