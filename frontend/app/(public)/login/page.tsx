"use client";

import { useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { LoginSkyBackground } from "@/components/system/login-sky-background";
import { UniversityBrand } from "@/components/system/university-brand";
import { Field } from "@/components/system/field";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";
import { useI18n } from "@/lib/i18n-context";
import { login } from "@/services/auth";
import { getDashboard } from "@/services/dashboard";
import { listDues } from "@/services/maintenance";
import { listUAVs } from "@/services/uavs";
import { listWorkOrders } from "@/services/work-orders";

export default function LoginPage() {
  const { t, locale, setLocale } = useI18n();
  const router = useRouter();
  const queryClient = useQueryClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorKey, setErrorKey] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [slow, setSlow] = useState(false);

  useEffect(() => {
    if (!pending) {
      setSlow(false);
      return;
    }
    const timer = window.setTimeout(() => setSlow(true), 4000);
    return () => window.clearTimeout(timer);
  }, [pending]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setPending(true);
    setErrorKey(null);
    try {
      await login(email, password);
      void queryClient.prefetchQuery({ queryKey: ["dashboard"], queryFn: getDashboard });
      void queryClient.prefetchQuery({ queryKey: ["uavs", ""], queryFn: () => listUAVs("") });
      void queryClient.prefetchQuery({ queryKey: ["work-orders", ""], queryFn: () => listWorkOrders("") });
      void queryClient.prefetchQuery({
        queryKey: ["dues", "", "attention", ""],
        queryFn: () => listDues("", "attention", ""),
      });
      router.replace("/dashboard");
    } catch (error) {
      const key = error instanceof Error ? error.message : "errors.generic";
      setErrorKey(key);
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
              {t("common.appName")}
            </CardTitle>
            <div className="h-px w-14 bg-[#79113e]" />
            <CardDescription className="text-[#79113e]">{t("auth.login")}</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-4">
              <Field label={t("auth.email")}>
                <Input
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                />
              </Field>
              <Field label={t("auth.password")}>
                <Input
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                />
              </Field>
              {errorKey ? <p className="text-sm text-destructive">{t(errorKey)}</p> : null}
              <Button
                type="submit"
                disabled={pending}
                size="lg"
                className="w-full bg-[#79113e] text-white hover:bg-[#641034] focus-visible:border-[#79113e] focus-visible:ring-[#79113e]/30"
              >
                {pending ? (slow ? t("auth.waking") : t("common.loading")) : t("auth.submit")}
              </Button>
              <div className="flex items-center justify-between text-xs text-secondary">
                <Button asChild variant="link" size="sm" className="h-auto px-0">
                  <Link href="/forgot-password">{t("auth.forgotPassword")}</Link>
                </Button>
                <NativeSelect
                  className="w-auto"
                  value={locale}
                  onChange={(event) => setLocale(event.target.value as typeof locale)}
                >
                  <option value="tr">TR</option>
                  <option value="en">EN</option>
                  <option value="az">AZ</option>
                </NativeSelect>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
