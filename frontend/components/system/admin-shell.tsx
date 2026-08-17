"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, type ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { useSessionUser } from "@/hooks/use-session-user";
import { canSeeAdminNav, clearSession } from "@/lib/auth";
import { useI18n } from "@/lib/i18n-context";
import { cn } from "@/lib/utils";

const ADMIN_NAV = [
  { href: "/admin", key: "admin.overview", permission: "admin.access", exact: true },
  { href: "/admin/classes", key: "admin.classes", permission: "uav_class.view" },
  { href: "/admin/platforms", key: "admin.platforms", permission: "platform.view" },
  { href: "/admin/missions", key: "admin.missions", permission: "mission.view" },
  { href: "/admin/components", key: "admin.components", permission: "component.view" },
  { href: "/admin/maintenance-templates", key: "admin.templates", permission: "maintenance_template.view" },
  { href: "/admin/maintenance-rules", key: "admin.rules", permission: "maintenance_rule.view" },
  { href: "/admin/technicians", key: "admin.technicians", permission: "technician.view" },
  { href: "/admin/skills", key: "admin.skills", permission: "skill.view" },
  { href: "/admin/users", key: "admin.users", permission: "user.view", adminOnly: true },
  { href: "/admin/settings", key: "admin.settings", permission: "settings.view", adminOnly: true },
  { href: "/admin/audit-logs", key: "admin.audit", permission: "audit.view", adminOnly: true },
];

export function AdminShell({ children }: { children: ReactNode }) {
  const { t } = useI18n();
  const pathname = usePathname();
  const router = useRouter();
  const user = useSessionUser();
  const allowed = Boolean(user && canSeeAdminNav(user, "admin.access"));

  useEffect(() => {
    if (!allowed) {
      router.replace("/dashboard");
    }
  }, [allowed, router]);

  if (!user || !allowed) {
    return <div className="p-6 text-sm text-muted-foreground">{t("common.loading")}</div>;
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="flex h-14 items-center justify-between bg-primary px-6 text-primary-foreground">
        <p className="text-sm font-semibold tracking-wide">{t("admin.title")}</p>
        <div className="flex items-center gap-2 text-sm">
          <Button asChild variant="ghost" size="sm" className="text-primary-foreground hover:bg-white/10 hover:text-primary-foreground">
            <Link href="/dashboard">{t("navigation.dashboard")}</Link>
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="text-primary-foreground hover:bg-white/10 hover:text-primary-foreground"
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
        <aside className="w-60 border-r bg-card p-3">
          <nav className="flex flex-col gap-1">
            {ADMIN_NAV.filter((item) => canSeeAdminNav(user, item.permission, item.adminOnly)).map(
              (item) => {
                const active = item.exact ? pathname === item.href : pathname.startsWith(item.href);
                return (
                  <Button
                    key={item.href}
                    asChild
                    variant={active ? "default" : "ghost"}
                    className={cn("w-full justify-start", !active && "text-secondary")}
                  >
                    <Link href={item.href}>{t(item.key)}</Link>
                  </Button>
                );
              },
            )}
          </nav>
        </aside>
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
}
