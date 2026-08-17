"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useState } from "react";

import { PageHeader } from "@/components/system/page-header";
import { DemoBadge } from "@/components/system/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
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
  addTechnicianCertification,
  addTechnicianSkill,
  deleteTechnicianCertification,
  deleteTechnicianSkill,
  getTechnician,
  listSkills,
} from "@/services/technicians";

export default function AdminTechnicianDetailPage() {
  const { t } = useI18n();
  const params = useParams<{ id: string }>();
  const user = useSessionUser();
  const queryClient = useQueryClient();
  const canUpdate = hasPermission(user, "technician.update");
  const [skillId, setSkillId] = useState("");
  const [certifiedAt, setCertifiedAt] = useState("");
  const [skillExpires, setSkillExpires] = useState("");
  const [certName, setCertName] = useState("");
  const [issuer, setIssuer] = useState("");
  const [issuedAt, setIssuedAt] = useState("");
  const [certExpires, setCertExpires] = useState("");
  const [documentId, setDocumentId] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const query = useQuery({
    queryKey: ["technician", params.id],
    queryFn: () => getTechnician(params.id),
  });
  const skillsQuery = useQuery({
    queryKey: ["skills"],
    queryFn: listSkills,
  });
  const technician = query.data;
  const assignedSkillIds = new Set((technician?.skills ?? []).map((item) => item.skill_id));
  const availableSkills = (skillsQuery.data?.data ?? []).filter(
    (item) => item.is_active && !assignedSkillIds.has(item.id),
  );

  async function invalidate() {
    await queryClient.invalidateQueries({ queryKey: ["technician", params.id] });
    await queryClient.invalidateQueries({ queryKey: ["technicians"] });
  }

  const skillMutation = useMutation({
    mutationFn: () =>
      addTechnicianSkill(params.id, {
        skill: skillId,
        certified_at: certifiedAt || undefined,
        expires_at: skillExpires || undefined,
      }),
    onSuccess: async () => {
      setSkillId("");
      setCertifiedAt("");
      setSkillExpires("");
      setFormError(null);
      await invalidate();
    },
    onError: (err) => {
      setFormError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    },
  });
  const certMutation = useMutation({
    mutationFn: () =>
      addTechnicianCertification(params.id, {
        name: certName,
        issuer,
        issued_at: issuedAt || undefined,
        expires_at: certExpires || undefined,
        document_id: documentId || undefined,
      }),
    onSuccess: async () => {
      setCertName("");
      setIssuer("");
      setIssuedAt("");
      setCertExpires("");
      setDocumentId("");
      setFormError(null);
      await invalidate();
    },
    onError: (err) => {
      setFormError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    },
  });

  function onAddSkill(event: FormEvent) {
    event.preventDefault();
    skillMutation.mutate();
  }

  function onAddCert(event: FormEvent) {
    event.preventDefault();
    certMutation.mutate();
  }

  if (query.error instanceof Error) {
    return <p className="text-sm text-destructive">{t(query.error.message)}</p>;
  }
  if (!technician) {
    return <p className="text-sm text-muted-foreground">{t("common.loading")}</p>;
  }

  return (
    <section className="space-y-6">
      <PageHeader title={technician.full_name}>
        <DemoBadge visible={technician.is_demo} />
        <Button asChild variant="outline">
          <Link href="/admin/technicians">{t("common.back")}</Link>
        </Button>
      </PageHeader>
      {formError ? <p className="text-sm text-destructive">{t(formError)}</p> : null}
      <Card>
        <CardContent className="grid grid-cols-2 gap-4 text-sm">
          <p>
            {t("technician.employeeNumber")}: {technician.employee_number}
          </p>
          <p>
            {t("auth.email")}: {technician.email}
          </p>
          <p>
            {t("technician.status")}: {t(`enums.technician_status.${technician.status}`)}
          </p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>{t("technician.skills")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {canUpdate ? (
            <form onSubmit={onAddSkill} className="grid grid-cols-2 gap-2 md:grid-cols-4">
              <NativeSelect required value={skillId} onChange={(event) => setSkillId(event.target.value)}>
                <option value="">{t("technician.skill")}</option>
                {availableSkills.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.code} — {item.name}
                  </option>
                ))}
              </NativeSelect>
              <Input type="date" value={certifiedAt} onChange={(event) => setCertifiedAt(event.target.value)} />
              <Input type="date" value={skillExpires} onChange={(event) => setSkillExpires(event.target.value)} />
              <Button type="submit" disabled={!skillId}>
                {t("technician.addSkill")}
              </Button>
            </form>
          ) : null}
          <div className="overflow-hidden rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("catalog.code")}</TableHead>
                  <TableHead>{t("catalog.name")}</TableHead>
                  <TableHead>{t("technician.certifiedAt")}</TableHead>
                  <TableHead>{t("technician.expiresAt")}</TableHead>
                  <TableHead>{t("common.actions")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(technician.skills ?? []).length === 0 ? (
                  <TableRow>
                    <TableCell className="text-muted-foreground" colSpan={5}>
                      {t("technician.noSkills")}
                    </TableCell>
                  </TableRow>
                ) : (
                  (technician.skills ?? []).map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>{item.skill_code}</TableCell>
                      <TableCell>{item.skill_name}</TableCell>
                      <TableCell>{item.certified_at ?? "—"}</TableCell>
                      <TableCell>{item.expires_at ?? "—"}</TableCell>
                      <TableCell>
                        {canUpdate ? (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="text-destructive"
                            onClick={() =>
                              void deleteTechnicianSkill(params.id, item.id).then(invalidate)
                            }
                          >
                            {t("common.delete")}
                          </Button>
                        ) : (
                          "—"
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>{t("technician.certifications")}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {canUpdate ? (
            <form onSubmit={onAddCert} className="grid grid-cols-2 gap-2 md:grid-cols-3">
              <Input
                required
                placeholder={t("catalog.name")}
                value={certName}
                onChange={(event) => setCertName(event.target.value)}
              />
              <Input
                required
                placeholder={t("technician.issuer")}
                value={issuer}
                onChange={(event) => setIssuer(event.target.value)}
              />
              <Input
                placeholder={t("technician.documentId")}
                value={documentId}
                onChange={(event) => setDocumentId(event.target.value)}
              />
              <Input type="date" value={issuedAt} onChange={(event) => setIssuedAt(event.target.value)} />
              <Input type="date" value={certExpires} onChange={(event) => setCertExpires(event.target.value)} />
              <Button type="submit">{t("technician.addCertification")}</Button>
            </form>
          ) : null}
          <div className="overflow-hidden rounded-lg border">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>{t("catalog.name")}</TableHead>
                  <TableHead>{t("technician.issuer")}</TableHead>
                  <TableHead>{t("technician.documentId")}</TableHead>
                  <TableHead>{t("technician.issuedAt")}</TableHead>
                  <TableHead>{t("technician.expiresAt")}</TableHead>
                  <TableHead>{t("common.actions")}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(technician.certifications ?? []).length === 0 ? (
                  <TableRow>
                    <TableCell className="text-muted-foreground" colSpan={6}>
                      {t("technician.noCertifications")}
                    </TableCell>
                  </TableRow>
                ) : (
                  (technician.certifications ?? []).map((item) => (
                    <TableRow key={item.id}>
                      <TableCell>{item.name}</TableCell>
                      <TableCell>{item.issuer}</TableCell>
                      <TableCell>{item.document_id || "—"}</TableCell>
                      <TableCell>{item.issued_at ?? "—"}</TableCell>
                      <TableCell>{item.expires_at ?? "—"}</TableCell>
                      <TableCell>
                        {canUpdate ? (
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="text-destructive"
                            onClick={() =>
                              void deleteTechnicianCertification(params.id, item.id).then(invalidate)
                            }
                          >
                            {t("common.delete")}
                          </Button>
                        ) : (
                          "—"
                        )}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
