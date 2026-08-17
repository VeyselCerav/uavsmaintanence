"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { FormEvent, useState } from "react";

import { DemoBadge } from "@/components/system/status-badge";
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
import { createDocument, deleteDocument, downloadDocument, listDocuments } from "@/services/documents";
import { DOCUMENT_TYPES, type DocumentType } from "@/types/document";

type Props = {
  uavId?: string;
  workOrderId?: string;
  templateId?: string;
};

export function DocumentSection({ uavId, workOrderId, templateId }: Props) {
  const { t } = useI18n();
  const user = useSessionUser();
  const queryClient = useQueryClient();
  const canCreate = hasPermission(user, "document.create");
  const canDelete = hasPermission(user, "document.delete");
  const [title, setTitle] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [documentType, setDocumentType] = useState<DocumentType>("OTHER");
  const [formError, setFormError] = useState<string | null>(null);
  const filters = {
    ...(uavId ? { uav: uavId } : {}),
    ...(workOrderId ? { work_order: workOrderId } : {}),
    ...(templateId ? { template: templateId } : {}),
  };
  const query = useQuery({
    queryKey: ["documents", filters],
    queryFn: () => listDocuments("", filters),
    enabled: hasPermission(user, "document.view"),
  });
  const createMutation = useMutation({
    mutationFn: () =>
      createDocument(
        {
          title: title || file?.name.replace(/\.[^.]+$/, "") || "document",
          document_type: documentType,
          uav: uavId,
          work_order: workOrderId,
          template: templateId,
        },
        file,
      ),
    onSuccess: async () => {
      setTitle("");
      setFile(null);
      setFormError(null);
      await queryClient.invalidateQueries({ queryKey: ["documents"] });
      if (uavId) {
        await queryClient.invalidateQueries({ queryKey: ["uav-timeline", uavId] });
      }
    },
    onError: (err) => {
      setFormError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    },
  });
  const items = query.data?.data ?? [];
  const error = formError ?? (query.error instanceof Error ? query.error.message : null);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    createMutation.mutate();
  }

  if (!hasPermission(user, "document.view")) {
    return null;
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-primary">{t("document.title")}</h2>
        <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
          <Link href="/documents">{t("common.viewAll")}</Link>
        </Button>
      </div>
      {error ? <p className="text-sm text-destructive">{t(error)}</p> : null}
      {canCreate ? (
        <form onSubmit={onSubmit} className="flex flex-wrap items-center gap-2">
          <Input
            className="w-44"
            placeholder={t("document.titleField")}
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
          <Input
            required
            type="file"
            className="w-56"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
          <NativeSelect
            className="w-40"
            value={documentType}
            onChange={(event) => setDocumentType(event.target.value as DocumentType)}
          >
            {DOCUMENT_TYPES.map((item) => (
              <option key={item} value={item}>
                {t(`enums.document_type.${item}`)}
              </option>
            ))}
          </NativeSelect>
          <Button type="submit" disabled={!file || createMutation.isPending}>
            {t("common.create")}
          </Button>
        </form>
      ) : null}
      <div className="overflow-hidden rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("document.titleField")}</TableHead>
              <TableHead>{t("document.fileName")}</TableHead>
              <TableHead>{t("document.type")}</TableHead>
              <TableHead>{t("common.actions")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 ? (
              <TableRow>
                <TableCell className="text-muted-foreground" colSpan={4}>
                  {t("document.empty")}
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>
                    <span className="mr-2">{item.title}</span>
                    <DemoBadge visible={item.is_demo} />
                  </TableCell>
                  <TableCell>{item.file_name}</TableCell>
                  <TableCell>{t(`enums.document_type.${item.document_type}`)}</TableCell>
                  <TableCell className="space-x-2">
                    {item.has_file ? (
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={async () => {
                          try {
                            await downloadDocument(item.id, item.file_name);
                            setFormError(null);
                          } catch (err) {
                            setFormError(
                              err instanceof ApiClientError ? err.message_key : "errors.generic",
                            );
                          }
                        }}
                      >
                        {t("document.download")}
                      </Button>
                    ) : (
                      <span className="text-xs text-muted-foreground">{t("document.noFile")}</span>
                    )}
                    {canDelete ? (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="text-destructive"
                        onClick={async () => {
                          await deleteDocument(item.id);
                          await queryClient.invalidateQueries({ queryKey: ["documents"] });
                        }}
                      >
                        {t("common.delete")}
                      </Button>
                    ) : null}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
