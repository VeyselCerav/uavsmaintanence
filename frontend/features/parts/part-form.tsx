"use client";

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
import { createPart, updatePart } from "@/services/parts";
import { CURRENCIES, PART_STATUSES, type Part, type PartWritePayload } from "@/types/parts";

type Props = {
  initial?: Part;
};

export function PartForm({ initial }: Props) {
  const { t } = useI18n();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [form, setForm] = useState<PartWritePayload>({
    part_number: initial?.part_number ?? "",
    name: initial?.name ?? "",
    manufacturer: initial?.manufacturer ?? "",
    model: initial?.model ?? "",
    stock_qty: initial?.stock_qty ?? "0.00",
    min_stock_qty: initial?.min_stock_qty ?? "0.00",
    unit_cost: initial?.unit_cost ?? "0.00",
    currency: initial?.currency ?? "TRY",
    supplier: initial?.supplier ?? "",
    location: initial?.location ?? "",
    status: initial?.status ?? "ACTIVE",
    notes: initial?.notes ?? "",
  });

  function setField<K extends keyof PartWritePayload>(key: K, value: PartWritePayload[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      const saved = initial ? await updatePart(initial.id, form) : await createPart(form);
      router.replace(`/parts/${saved.id}`);
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
        <Field label={t("part.number")}>
          <Input required value={form.part_number} onChange={(event) => setField("part_number", event.target.value)} />
        </Field>
        <Field label={t("catalog.name")}>
          <Input required value={form.name} onChange={(event) => setField("name", event.target.value)} />
        </Field>
        <Field label={t("uav.manufacturer")}>
          <Input value={form.manufacturer} onChange={(event) => setField("manufacturer", event.target.value)} />
        </Field>
        <Field label={t("uav.model")}>
          <Input value={form.model} onChange={(event) => setField("model", event.target.value)} />
        </Field>
        <Field label={t("part.stock")}>
          <Input value={form.stock_qty} onChange={(event) => setField("stock_qty", event.target.value)} />
        </Field>
        <Field label={t("part.minStock")}>
          <Input value={form.min_stock_qty} onChange={(event) => setField("min_stock_qty", event.target.value)} />
        </Field>
        <Field label={t("part.unitCost")}>
          <Input value={form.unit_cost} onChange={(event) => setField("unit_cost", event.target.value)} />
        </Field>
        <Field label={t("part.currency")}>
          <NativeSelect
            value={form.currency}
            onChange={(event) => setField("currency", event.target.value as PartWritePayload["currency"])}
          >
            {CURRENCIES.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </NativeSelect>
        </Field>
        <Field label={t("part.supplier")}>
          <Input value={form.supplier} onChange={(event) => setField("supplier", event.target.value)} />
        </Field>
        <Field label={t("part.location")}>
          <Input value={form.location} onChange={(event) => setField("location", event.target.value)} />
        </Field>
        <Field label={t("part.status")}>
          <NativeSelect
            value={form.status}
            onChange={(event) => setField("status", event.target.value as PartWritePayload["status"])}
          >
            {PART_STATUSES.map((item) => (
              <option key={item} value={item}>
                {t(`enums.part_status.${item}`)}
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
          <Link href={initial ? `/parts/${initial.id}` : "/parts"}>{t("common.cancel")}</Link>
        </Button>
      </div>
    </form>
  );
}
