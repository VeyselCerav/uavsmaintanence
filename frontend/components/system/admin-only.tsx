"use client";

import { useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { useSessionUser } from "@/hooks/use-session-user";
import { useI18n } from "@/lib/i18n-context";

export function AdminOnly({ children }: { children: ReactNode }) {
  const router = useRouter();
  const { t } = useI18n();
  const user = useSessionUser();
  const ok = user?.role === "ADMIN";

  useEffect(() => {
    if (user && !ok) {
      router.replace("/admin");
    }
  }, [ok, router, user]);

  if (!ok) {
    return <div className="text-sm text-muted-foreground">{t("common.loading")}</div>;
  }
  return children;
}
