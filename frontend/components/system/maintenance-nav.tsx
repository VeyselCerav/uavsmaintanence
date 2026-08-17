"use client";

import Link from "next/link";

import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n-context";

const ITEMS = [
  { id: "dues", href: "/maintenance", key: "due.list" },
  { id: "calendar", href: "/maintenance/calendar", key: "due.calendar" },
  { id: "records", href: "/maintenance/records", key: "record.title" },
] as const;

export function MaintenanceNav({ active }: { active: (typeof ITEMS)[number]["id"] }) {
  const { t } = useI18n();
  return (
    <div className="flex flex-wrap gap-2">
      {ITEMS.map((item) => (
        <Button key={item.id} asChild size="sm" variant={item.id === active ? "default" : "outline"}>
          <Link href={item.href}>{t(item.key)}</Link>
        </Button>
      ))}
    </div>
  );
}
