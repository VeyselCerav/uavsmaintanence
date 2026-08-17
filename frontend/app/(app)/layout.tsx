import type { ReactNode } from "react";

import { AppShell } from "@/components/system/app-shell";

export default function ApplicationLayout({ children }: { children: ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
