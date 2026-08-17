"use client";

import { AlertTriangle, Activity, BarChart3, Calendar, Clipboard, FileText, GitBranch, GitMerge, LayoutDashboard, Package, Plane, Scale, Wrench } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { GlobalSearch } from "@/components/system/global-search";
import { NotificationBell } from "@/components/system/notification-bell";
import { Button } from "@/components/ui/button";
import { useSessionUser } from "@/hooks/use-session-user";
import { canSeeAdminNav, clearSession } from "@/lib/auth";
import { useI18n } from "@/lib/i18n-context";
import { cn } from "@/lib/utils";

const APP_NAV = [
  { href: "/dashboard", key: "navigation.dashboard", icon: LayoutDashboard },
  { href: "/uavs", key: "navigation.fleet", icon: Plane },
  { href: "/flights", key: "navigation.flights", icon: Calendar },
  { href: "/maintenance", key: "navigation.maintenance", icon: Wrench },
  { href: "/work-orders", key: "navigation.workOrders", icon: Clipboard },
  { href: "/failures", key: "navigation.failures", icon: AlertTriangle },
  { href: "/fmea", key: "navigation.fmea", icon: GitBranch },
  { href: "/rcm", key: "navigation.rcm", icon: GitMerge },
  { href: "/parts", key: "navigation.parts", icon: Package },
  { href: "/documents", key: "navigation.documents", icon: FileText },
  { href: "/reliability", key: "navigation.reliability", icon: Activity },
  { href: "/comparison", key: "navigation.comparison", icon: Scale },
  { href: "/reports", key: "navigation.reports", icon: BarChart3 },
];

export function AppShell({ children }: { children: ReactNode }) {
  const { t } = useI18n();
  const pathname = usePathname();
  const router = useRouter();
  const user = useSessionUser();

  useEffect(() => {
    if (!user) {
      router.replace("/login");
    }
  }, [router, user]);

  if (!user) {
    return <div className="p-6 text-sm text-muted-foreground">{t("common.loading")}</div>;
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="flex h-14 items-center justify-between gap-4 border-b bg-card px-6">
        <p className="text-sm font-semibold tracking-wide text-primary">{t("common.appName")}</p>
        <GlobalSearch />
        <div className="flex items-center gap-3 text-sm text-secondary">
          <NotificationBell />
          <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
            <Link href="/profile">{user.full_name}</Link>
          </Button>
          <span className="text-muted-foreground">{user.role}</span>
          {canSeeAdminNav(user, "admin.access") ? (
            <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
              <Link href="/admin">{t("navigation.admin")}</Link>
            </Button>
          ) : null}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="text-destructive"
            onClick={() => {
              clearSession();
              router.replace("/login");
            }}
          >
            {t("auth.logout")}
          </Button>
        </div>
      </header>
      <div className="flex min-h-[calc(100vh-56px)]">
        <aside className="w-56 border-r bg-card p-3">
          <nav className="flex flex-col gap-1">
            {APP_NAV.map((item) => {
              const active = pathname.startsWith(item.href);
              return (
                <Button
                  key={item.href}
                  asChild
                  variant={active ? "default" : "ghost"}
                  className={cn("w-full justify-start", !active && "text-secondary")}
                >
                  <Link href={item.href}>
                    <item.icon />
                    {t(item.key)}
                  </Link>
                </Button>
              );
            })}
          </nav>
        </aside>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
