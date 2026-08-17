import type { ReactNode } from "react";

import { AdminShell } from "@/components/system/admin-shell";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return <AdminShell>{children}</AdminShell>;
}
