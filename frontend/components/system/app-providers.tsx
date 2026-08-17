"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

import { Toaster } from "@/components/ui/sonner";
import { I18nProvider } from "@/lib/i18n-context";

export function AppProviders({ children }: { children: ReactNode }) {
  const [client] = useState(() => new QueryClient());
  return (
    <I18nProvider>
      <QueryClientProvider client={client}>
        {children}
        <Toaster theme="light" />
      </QueryClientProvider>
    </I18nProvider>
  );
}
