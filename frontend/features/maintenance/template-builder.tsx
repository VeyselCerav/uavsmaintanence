"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { FormEvent, useState } from "react";

import { PageHeader } from "@/components/system/page-header";
import { DemoBadge } from "@/components/system/status-badge";
import { TemplateHeaderForm } from "@/features/maintenance/template-header-form";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useSessionUser } from "@/hooks/use-session-user";
import { hasPermission } from "@/lib/auth";
import { useI18n } from "@/lib/i18n-context";
import { ApiClientError } from "@/services/api";
import {
  createTemplateItem,
  deleteTemplateItem,
  getTemplate,
  listComponentTypes,
  reorderTemplateItems,
} from "@/services/maintenance";
import {
  INSPECTION_TYPES,
  INTERVAL_UNITS,
  PRIORITIES,
  RCM_STRATEGIES,
  type InspectionType,
  type IntervalUnit,
  type Priority,
  type RCMStrategy,
  type TemplateItemWritePayload,
} from "@/types/maintenance";

const EMPTY_ITEM: TemplateItemWritePayload = {
  component_type: "",
  task_code: "",
  task_name: "",
  interval_value: "",
  interval_unit: "FLIGHT_HOURS",
  priority: "MEDIUM",
  estimated_duration_minutes: 60,
  inspection_type: "VISUAL",
  rcm_strategy: "SCHEDULED_INSPECTION",
};

export function TemplateBuilder({ templateId }: { templateId: string }) {
  const { t } = useI18n();
  const user = useSessionUser();
  const queryClient = useQueryClient();
  const canUpdate = hasPermission(user, "maintenance_template.update");
  const [formError, setFormError] = useState<string | null>(null);
  const [itemForm, setItemForm] = useState<TemplateItemWritePayload>(EMPTY_ITEM);
  const templateQuery = useQuery({
    queryKey: ["template", templateId],
    queryFn: () => getTemplate(templateId),
  });
  const typesQuery = useQuery({ queryKey: ["component-types"], queryFn: listComponentTypes });
  const template = templateQuery.data;
  const items = template?.items ?? [];

  const createMutation = useMutation({
    mutationFn: () => createTemplateItem(templateId, itemForm),
    onSuccess: async () => {
      setItemForm(EMPTY_ITEM);
      setFormError(null);
      await queryClient.invalidateQueries({ queryKey: ["template", templateId] });
    },
    onError: (err) => {
      setFormError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    },
  });

  async function onAdd(event: FormEvent) {
    event.preventDefault();
    createMutation.mutate();
  }

  async function onDelete(itemId: string) {
    try {
      await deleteTemplateItem(templateId, itemId);
      await queryClient.invalidateQueries({ queryKey: ["template", templateId] });
    } catch (err) {
      setFormError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    }
  }

  async function move(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= items.length) return;
    const ordered = items.map((item) => item.id);
    const [moved] = ordered.splice(index, 1);
    ordered.splice(target, 0, moved);
    try {
      await reorderTemplateItems(templateId, ordered);
      await queryClient.invalidateQueries({ queryKey: ["template", templateId] });
    } catch (err) {
      setFormError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    }
  }

  if (templateQuery.error) {
    return <p className="text-sm text-destructive">{t("errors.generic")}</p>;
  }
  if (!template) {
    return <p className="text-sm text-muted-foreground">{t("common.loading")}</p>;
  }

  return (
    <section className="space-y-8">
      <PageHeader title={template.code}>
        <DemoBadge visible={template.is_demo} />
        <Button asChild variant="outline">
          <Link href="/admin/maintenance-templates">{t("common.back")}</Link>
        </Button>
      </PageHeader>
      {template.is_demo ? <p className="text-sm text-warning">{template.notes}</p> : null}
      {canUpdate ? <TemplateHeaderForm initial={template} /> : null}

      <div>
        <h2 className="mb-3 text-base font-semibold text-primary">{t("template.items")}</h2>
        {formError ? <p className="mb-3 text-sm text-destructive">{t(formError)}</p> : null}
        {canUpdate ? (
          <form onSubmit={onAdd} className="mb-4 grid grid-cols-6 gap-2">
            <NativeSelect
              required
              value={itemForm.component_type}
              onChange={(event) => setItemForm({ ...itemForm, component_type: event.target.value })}
            >
              <option value="">{t("template.componentType")}</option>
              {(typesQuery.data?.data ?? []).map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </NativeSelect>
            <Input
              required
              placeholder={t("template.taskCode")}
              value={itemForm.task_code}
              onChange={(event) => setItemForm({ ...itemForm, task_code: event.target.value })}
            />
            <Input
              required
              placeholder={t("template.taskName")}
              value={itemForm.task_name}
              onChange={(event) => setItemForm({ ...itemForm, task_name: event.target.value })}
            />
            <Input
              required
              placeholder={t("template.interval")}
              value={itemForm.interval_value}
              onChange={(event) => setItemForm({ ...itemForm, interval_value: event.target.value })}
            />
            <NativeSelect
              value={itemForm.interval_unit}
              onChange={(event) =>
                setItemForm({ ...itemForm, interval_unit: event.target.value as IntervalUnit })
              }
            >
              {INTERVAL_UNITS.map((unit) => (
                <option key={unit} value={unit}>
                  {t(`enums.interval_unit.${unit}`)}
                </option>
              ))}
            </NativeSelect>
            <Button type="submit">{t("template.addItem")}</Button>
            <NativeSelect
              value={itemForm.priority}
              onChange={(event) =>
                setItemForm({ ...itemForm, priority: event.target.value as Priority })
              }
            >
              {PRIORITIES.map((priority) => (
                <option key={priority} value={priority}>
                  {t(`enums.priority.${priority}`)}
                </option>
              ))}
            </NativeSelect>
            <NativeSelect
              value={itemForm.inspection_type}
              onChange={(event) =>
                setItemForm({
                  ...itemForm,
                  inspection_type: event.target.value as InspectionType,
                })
              }
            >
              {INSPECTION_TYPES.map((type) => (
                <option key={type} value={type}>
                  {t(`enums.inspection_type.${type}`)}
                </option>
              ))}
            </NativeSelect>
            <NativeSelect
              value={itemForm.rcm_strategy}
              onChange={(event) =>
                setItemForm({ ...itemForm, rcm_strategy: event.target.value as RCMStrategy })
              }
            >
              {RCM_STRATEGIES.map((strategy) => (
                <option key={strategy} value={strategy}>
                  {t(`enums.rcm_strategy.${strategy}`)}
                </option>
              ))}
            </NativeSelect>
            <Input
              type="number"
              min={1}
              value={itemForm.estimated_duration_minutes}
              onChange={(event) =>
                setItemForm({
                  ...itemForm,
                  estimated_duration_minutes: Number(event.target.value),
                })
              }
            />
          </form>
        ) : null}
        <div className="overflow-hidden rounded-lg border bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t("template.sequence")}</TableHead>
                <TableHead>{t("template.taskCode")}</TableHead>
                <TableHead>{t("template.taskName")}</TableHead>
                <TableHead>{t("template.componentType")}</TableHead>
                <TableHead>{t("template.interval")}</TableHead>
                <TableHead>{t("template.priority")}</TableHead>
                <TableHead>{t("common.actions")}</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.length === 0 ? (
                <TableRow>
                  <TableCell className="text-muted-foreground" colSpan={7}>
                    {t("template.noItems")}
                  </TableCell>
                </TableRow>
              ) : (
                items.map((item, index) => (
                  <TableRow key={item.id}>
                    <TableCell>{item.sequence}</TableCell>
                    <TableCell>{item.task_code}</TableCell>
                    <TableCell>{item.task_name}</TableCell>
                    <TableCell>{item.component_type_name}</TableCell>
                    <TableCell>
                      {item.interval_value} {t(`enums.interval_unit.${item.interval_unit}`)}
                    </TableCell>
                    <TableCell>{t(`enums.priority.${item.priority}`)}</TableCell>
                    <TableCell>
                      {canUpdate ? (
                        <div className="flex gap-2">
                          <Button type="button" variant="outline" size="xs" onClick={() => void move(index, -1)}>
                            ↑
                          </Button>
                          <Button type="button" variant="outline" size="xs" onClick={() => void move(index, 1)}>
                            ↓
                          </Button>
                          <Button
                            type="button"
                            variant="ghost"
                            size="xs"
                            className="text-destructive"
                            onClick={() => void onDelete(item.id)}
                          >
                            {t("common.delete")}
                          </Button>
                        </div>
                      ) : null}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </div>
    </section>
  );
}
