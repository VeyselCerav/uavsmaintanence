"use client";

import { FormEvent, useState } from "react";

import { Field } from "@/components/system/field";
import { PageHeader } from "@/components/system/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";
import { useSessionUser } from "@/hooks/use-session-user";
import { LOCALES, type Locale } from "@/lib/i18n";
import { useI18n } from "@/lib/i18n-context";
import { ApiClientError } from "@/services/api";
import { updateProfile } from "@/services/auth";

export default function ProfilePage() {
  const { t, setLocale } = useI18n();
  const user = useSessionUser();
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [localeValue, setLocaleValue] = useState<Locale>(user?.locale ?? "tr");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [pending, setPending] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setError(null);
    setSaved(false);
    try {
      await updateProfile({
        full_name: fullName,
        locale: localeValue,
        ...(newPassword
          ? { current_password: currentPassword, new_password: newPassword }
          : {}),
      });
      setLocale(localeValue);
      setCurrentPassword("");
      setNewPassword("");
      setSaved(true);
    } catch (err) {
      setError(err instanceof ApiClientError ? err.message_key : "errors.generic");
    } finally {
      setPending(false);
    }
  }

  if (!user) {
    return <p className="text-sm text-muted-foreground">{t("common.loading")}</p>;
  }

  return (
    <section className="max-w-xl">
      <PageHeader title={t("profile.title")} description={t("profile.hint")} />
      {error ? <p className="mb-3 text-sm text-destructive">{t(error)}</p> : null}
      {saved ? <p className="mb-3 text-sm text-success">{t("profile.saved")}</p> : null}
      <Card>
        <CardContent>
          <form onSubmit={onSubmit} className="space-y-4 pt-2">
            <Field label={t("auth.email")}>
              <Input value={user.email} disabled />
            </Field>
            <Field label={t("technician.fullName")}>
              <Input required value={fullName} onChange={(event) => setFullName(event.target.value)} />
            </Field>
            <Field label={t("profile.language")}>
              <NativeSelect
                value={localeValue}
                onChange={(event) => setLocaleValue(event.target.value as Locale)}
              >
                {LOCALES.map((item) => (
                  <option key={item} value={item}>
                    {item.toUpperCase()}
                  </option>
                ))}
              </NativeSelect>
            </Field>
            <p className="text-sm font-semibold text-primary">{t("profile.password")}</p>
            <Field label={t("profile.currentPassword")}>
              <Input
                type="password"
                value={currentPassword}
                onChange={(event) => setCurrentPassword(event.target.value)}
              />
            </Field>
            <Field label={t("profile.newPassword")}>
              <Input
                type="password"
                minLength={8}
                value={newPassword}
                onChange={(event) => setNewPassword(event.target.value)}
              />
            </Field>
            <Button type="submit" disabled={pending}>
              {pending ? t("common.loading") : t("common.save")}
            </Button>
          </form>
        </CardContent>
      </Card>
    </section>
  );
}
