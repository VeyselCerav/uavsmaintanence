"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { Field } from "@/components/system/field";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";
import { Textarea } from "@/components/ui/textarea";
import { useI18n } from "@/lib/i18n-context";
import { ApiClientError } from "@/services/api";
import { createDocument, listDocumentTargets } from "@/services/documents";
import { DOCUMENT_TYPES, type DocumentType, type DocumentWritePayload } from "@/types/document";

type Props = {
  defaultUav?: string;
  defaultWorkOrder?: string;
  defaultTemplate?: string;
};

export function DocumentForm({ defaultUav = "", defaultWorkOrder = "", defaultTemplate = "" }: Props) {
  const { t } = useI18n();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const targets = useQuery({
    queryKey: ["document-targets"],
    queryFn: listDocumentTargets,
  });
  const [form, setForm] = useState<DocumentWritePayload>({
    title: "",
    document_type: "OTHER",
    notes: "",
    uav: defaultUav || null,
    work_order: defaultWorkOrder || null,
    template: defaultTemplate || null,
  });
  const [uavs, workOrders, templates] = targets.data ?? [{ data: [] }, { data: [] }, { data: [] }];

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    try {
      await createDocument(
        {
          ...form,
          uav: form.uav || null,
          work_order: form.work_order || null,
          template: form.template || null,
        },
        file,
      );
      router.replace("/documents");
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
        <Field label={t("document.titleField")}>
          <Input
            required
            value={form.title}
            onChange={(event) => setForm({ ...form, title: event.target.value })}
          />
        </Field>
        <Field label={t("document.upload")}>
          <Input
            required
            type="file"
            onChange={(event) => {
              const next = event.target.files?.[0] ?? null;
              setFile(next);
              if (next && !form.title) {
                setForm({ ...form, title: next.name.replace(/\.[^.]+$/, "") });
              }
            }}
          />
        </Field>
        <Field label={t("document.type")}>
          <NativeSelect
            value={form.document_type}
            onChange={(event) =>
              setForm({ ...form, document_type: event.target.value as DocumentType })
            }
          >
            {DOCUMENT_TYPES.map((item) => (
              <option key={item} value={item}>
                {t(`enums.document_type.${item}`)}
              </option>
            ))}
          </NativeSelect>
        </Field>
        <Field label={t("uav.title")}>
          <NativeSelect
            value={form.uav ?? ""}
            onChange={(event) => setForm({ ...form, uav: event.target.value || null })}
          >
            <option value="">{t("document.noTarget")}</option>
            {uavs.data.map((item) => (
              <option key={item.id} value={item.id}>
                {item.registration_number}
              </option>
            ))}
          </NativeSelect>
        </Field>
        <Field label={t("workOrder.title")}>
          <NativeSelect
            value={form.work_order ?? ""}
            onChange={(event) => setForm({ ...form, work_order: event.target.value || null })}
          >
            <option value="">{t("document.noTarget")}</option>
            {workOrders.data.map((item) => (
              <option key={item.id} value={item.id}>
                {item.number}
              </option>
            ))}
          </NativeSelect>
        </Field>
        <Field label={t("template.title")}>
          <NativeSelect
            value={form.template ?? ""}
            onChange={(event) => setForm({ ...form, template: event.target.value || null })}
          >
            <option value="">{t("document.noTarget")}</option>
            {templates.data.map((item) => (
              <option key={item.id} value={item.id}>
                {item.code}
              </option>
            ))}
          </NativeSelect>
        </Field>
      </div>
      <Field label={t("uav.notes")}>
        <Textarea
          value={form.notes ?? ""}
          onChange={(event) => setForm({ ...form, notes: event.target.value })}
        />
      </Field>
      <p className="text-xs text-muted-foreground">{t("document.storageHint")}</p>
      <Button type="submit" disabled={pending || !file}>
        {pending ? t("common.loading") : t("common.save")}
      </Button>
    </form>
  );
}
