"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { PageHeader } from "@/components/system/page-header";
import { DemoBadge } from "@/components/system/status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
import { createTechnician, listTechnicians, updateTechnician } from "@/services/technicians";

export default function AdminTechniciansPage() {
  const { t } = useI18n();
  const user = useSessionUser();
  const router = useRouter();
  const queryClient = useQueryClient();
  const canCreate = hasPermission(user, "technician.create");
  const canUpdate = hasPermission(user, "technician.update");
  const [employeeNumber, setEmployeeNumber] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const query = useQuery({
    queryKey: ["technicians"],
    queryFn: () => listTechnicians(),
  });
  const createMutation = useMutation({
    mutationFn: () =>
      createTechnician({
        employee_number: employeeNumber,
        full_name: fullName,
        email,
        password,
      }),
    onSuccess: async () => {
      setEmployeeNumber("");
      setFullName("");
      setEmail("");
      setPassword("");
      setFormError(null);
      await queryClient.invalidateQueries({ queryKey: ["technicians"] });
    },
    onError: (err) => {
      setFormError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    },
  });
  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: "ACTIVE" | "INACTIVE" }) =>
      updateTechnician(id, { status }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["technicians"] });
    },
  });
  const items = query.data?.data ?? [];
  const error = formError ?? (query.error instanceof Error ? query.error.message : null);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    createMutation.mutate();
  }

  return (
    <section>
      <PageHeader title={t("admin.technicians")} />
      {error ? <p className="mb-3 text-sm text-destructive">{t(error)}</p> : null}
      {canCreate ? (
        <form onSubmit={onSubmit} className="mb-4 grid grid-cols-2 gap-2 md:grid-cols-5">
          <Input
            required
            placeholder={t("technician.employeeNumber")}
            value={employeeNumber}
            onChange={(event) => setEmployeeNumber(event.target.value)}
          />
          <Input
            required
            placeholder={t("technician.fullName")}
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
          />
          <Input
            required
            type="email"
            placeholder={t("auth.email")}
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />
          <Input
            required
            type="password"
            minLength={8}
            placeholder={t("auth.password")}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
          <Button type="submit">{t("common.create")}</Button>
        </form>
      ) : null}
      <div className="overflow-hidden rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("technician.employeeNumber")}</TableHead>
              <TableHead>{t("technician.fullName")}</TableHead>
              <TableHead>{t("auth.email")}</TableHead>
              <TableHead>{t("technician.status")}</TableHead>
              <TableHead>{t("technician.skills")}</TableHead>
              <TableHead>{t("common.actions")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 ? (
              <TableRow>
                <TableCell className="text-muted-foreground" colSpan={6}>
                  {t("technician.empty")}
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
                <TableRow
                  key={item.id}
                  className="cursor-pointer"
                  onClick={() => router.push(`/admin/technicians/${item.id}`)}
                >
                  <TableCell>
                    <span className="mr-2">{item.employee_number}</span>
                    <DemoBadge visible={item.is_demo} />
                  </TableCell>
                  <TableCell>{item.full_name}</TableCell>
                  <TableCell>{item.email}</TableCell>
                  <TableCell>{t(`enums.technician_status.${item.status}`)}</TableCell>
                  <TableCell>{item.skills?.length ?? 0}</TableCell>
                  <TableCell>
                    {canUpdate ? (
                      <Button
                        type="button"
                        variant="link"
                        size="sm"
                        className="h-auto px-0 text-info"
                        onClick={(event) => {
                          event.stopPropagation();
                          statusMutation.mutate({
                            id: item.id,
                            status: item.status === "ACTIVE" ? "INACTIVE" : "ACTIVE",
                          });
                        }}
                      >
                        {item.status === "ACTIVE" ? t("technician.deactivate") : t("technician.activate")}
                      </Button>
                    ) : (
                      <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
                        <Link href={`/admin/technicians/${item.id}`}>{t("common.edit")}</Link>
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </section>
  );
}
