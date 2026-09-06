"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";

import { Toaster } from "@/components/ui/sonner";
import { I18nProvider } from "@/lib/i18n-context";

function backendOrigin(): string {
  const api = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
  return api.replace(/\/api\/v1\/?$/, "");
}

export function AppProviders({ children }: { children: ReactNode }) {
  const [client] = useState(() => new QueryClient());
  useEffect(() => {
    void fetch(`${backendOrigin()}/health/?db=1`, { cache: "no-store" }).catch(() => {});
  }, []);
  return (
    <I18nProvider>
      <QueryClientProvider client={client}>
        {children}
        <Toaster theme="light" />
      </QueryClientProvider>
    </I18nProvider>
  );
}
