"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { AdminOnly } from "@/components/system/admin-only";
import { PageHeader } from "@/components/system/page-header";
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
import { useI18n } from "@/lib/i18n-context";
import { ApiClientError } from "@/services/api";
import { createUser, listRoles, listUsers, updateUser } from "@/services/admin";

function UsersBody() {
  const { t } = useI18n();
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [roleId, setRoleId] = useState("");
  const [locale, setLocale] = useState("tr");
  const [formError, setFormError] = useState<string | null>(null);
  const usersQuery = useQuery({ queryKey: ["users"], queryFn: () => listUsers() });
  const rolesQuery = useQuery({ queryKey: ["roles"], queryFn: listRoles });
  const createMutation = useMutation({
    mutationFn: () =>
      createUser({
        email,
        full_name: fullName,
        password,
        role: roleId,
        locale,
      }),
    onSuccess: async () => {
      setEmail("");
      setFullName("");
      setPassword("");
      setFormError(null);
      await queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (err) => {
      setFormError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    },
  });
  const statusMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      updateUser(id, { is_active }),
    onSuccess: async () => {
      setFormError(null);
      await queryClient.invalidateQueries({ queryKey: ["users"] });
    },
    onError: (err) => {
      setFormError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    },
  });
  const items = usersQuery.data?.data ?? [];
  const roles = rolesQuery.data?.data ?? [];
  const error =
    formError ?? (usersQuery.error instanceof Error ? usersQuery.error.message : null);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    createMutation.mutate();
  }

  return (
    <section>
      <PageHeader title={t("admin.users")} description={t("user.hint")} />
      {error ? <p className="mb-3 text-sm text-destructive">{t(error)}</p> : null}
      <form onSubmit={onSubmit} className="mb-4 grid grid-cols-2 gap-2 md:grid-cols-6">
        <Input
          required
          type="email"
          placeholder={t("auth.email")}
          value={email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <Input
          required
          placeholder={t("technician.fullName")}
          value={fullName}
          onChange={(event) => setFullName(event.target.value)}
        />
        <Input
          required
          type="password"
          minLength={8}
          placeholder={t("auth.password")}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <NativeSelect required value={roleId} onChange={(event) => setRoleId(event.target.value)}>
          <option value="">{t("user.role")}</option>
          {roles.map((role) => (
            <option key={role.id} value={role.id}>
              {role.code}
            </option>
          ))}
        </NativeSelect>
        <NativeSelect value={locale} onChange={(event) => setLocale(event.target.value)}>
          <option value="tr">tr</option>
          <option value="en">en</option>
          <option value="az">az</option>
        </NativeSelect>
        <Button type="submit">{t("common.create")}</Button>
      </form>
      <div className="overflow-hidden rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("auth.email")}</TableHead>
              <TableHead>{t("technician.fullName")}</TableHead>
              <TableHead>{t("user.role")}</TableHead>
              <TableHead>{t("user.active")}</TableHead>
              <TableHead>{t("common.actions")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 ? (
              <TableRow>
                <TableCell className="text-muted-foreground" colSpan={5}>
                  {t("user.empty")}
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
                <TableRow key={item.id}>
                  <TableCell>{item.email}</TableCell>
                  <TableCell>{item.full_name}</TableCell>
                  <TableCell>{item.role_code}</TableCell>
                  <TableCell>
                    {item.is_active ? t("user.activeYes") : t("user.activeNo")}
                  </TableCell>
                  <TableCell>
                    <Button
                      type="button"
                      variant="link"
                      size="sm"
                      className="h-auto px-0 text-info"
                      onClick={() =>
                        statusMutation.mutate({ id: item.id, is_active: !item.is_active })
                      }
                    >
                      {item.is_active ? t("technician.deactivate") : t("technician.activate")}
                    </Button>
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

export default function AdminUsersPage() {
  return (
    <AdminOnly>
      <UsersBody />
    </AdminOnly>
  );
}
