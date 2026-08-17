"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

import { LoginSkyBackground } from "@/components/system/login-sky-background";
import { UniversityBrand } from "@/components/system/university-brand";
import { Field } from "@/components/system/field";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useI18n } from "@/lib/i18n-context";
import { requestPasswordReset } from "@/services/auth";

export default function ForgotPasswordPage() {
  const { t } = useI18n();
  const [email, setEmail] = useState("");
  const [pending, setPending] = useState(false);
  const [sent, setSent] = useState(false);
  const [resetToken, setResetToken] = useState<string | null>(null);
  const [errorKey, setErrorKey] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setErrorKey(null);
    try {
      const data = await requestPasswordReset(email);
      setSent(true);
      setResetToken(data.reset_token ?? null);
    } catch (error) {
      setErrorKey(error instanceof Error ? error.message : "errors.generic");
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden">
      <LoginSkyBackground />
      <header className="absolute top-0 right-0 z-10 p-5 md:p-8">
        <UniversityBrand />
      </header>
      <div className="relative z-10 flex min-h-screen items-center justify-center p-4 pt-36 md:pt-4">
        <Card className="w-full max-w-md border-none ring-[#79113e]/12 shadow-[0_18px_50px_rgba(38,55,70,0.12)]">
          <CardHeader className="gap-2">
            <CardTitle className="text-lg font-semibold tracking-tight text-primary">
              {t("auth.forgotPassword")}
            </CardTitle>
            <div className="h-px w-14 bg-[#79113e]" />
            <CardDescription>{t("auth.resetHint")}</CardDescription>
          </CardHeader>
          <CardContent>
            {sent ? (
              <div className="space-y-3">
                <p className="text-sm text-secondary">{t("auth.resetSent")}</p>
                {resetToken ? (
                  <Button asChild className="w-full bg-[#79113e] text-white hover:bg-[#641034]">
                    <Link href={`/reset-password?token=${encodeURIComponent(resetToken)}`}>
                      {t("auth.resetContinue")}
                    </Link>
                  </Button>
                ) : null}
                <Button asChild variant="link" className="h-auto px-0">
                  <Link href="/login">{t("auth.login")}</Link>
                </Button>
              </div>
            ) : (
              <form onSubmit={onSubmit} className="space-y-4">
                <Field label={t("auth.email")}>
                  <Input
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    required
                  />
                </Field>
                {errorKey ? <p className="text-sm text-destructive">{t(errorKey)}</p> : null}
                <Button
                  type="submit"
                  disabled={pending}
                  className="w-full bg-[#79113e] text-white hover:bg-[#641034]"
                >
                  {pending ? t("common.loading") : t("auth.resetSubmit")}
                </Button>
                <Button asChild variant="link" className="h-auto px-0">
                  <Link href="/login">{t("auth.login")}</Link>
                </Button>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
