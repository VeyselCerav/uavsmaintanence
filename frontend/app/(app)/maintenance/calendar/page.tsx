"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";

import { MaintenanceNav } from "@/components/system/maintenance-nav";
import { PageHeader } from "@/components/system/page-header";
import { DUE_TONE, DueBadge } from "@/components/system/status-badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useI18n } from "@/lib/i18n-context";
import {
  localeTag,
  monthGrid,
  shiftAnchor,
  toDateKey,
  type CalendarView,
  visibleRange,
  weekGrid,
} from "@/lib/calendar-range";
import { cn } from "@/lib/utils";
import { listDues } from "@/services/maintenance";
import type { MaintenanceDue } from "@/types/maintenance";

const WEEKDAY_KEYS = ["1", "2", "3", "4", "5", "6", "7"] as const;
const VIEWS: CalendarView[] = ["day", "week", "month"];

function groupByDay(items: MaintenanceDue[]): Record<string, MaintenanceDue[]> {
  const grouped: Record<string, MaintenanceDue[]> = {};
  for (const item of items) {
    if (!item.due_at) continue;
    const key = toDateKey(item.due_at);
    grouped[key] ??= [];
    grouped[key].push(item);
  }
  return grouped;
}

export default function MaintenanceCalendarPage() {
  const { t, locale } = useI18n();
  const router = useRouter();
  const [view, setView] = useState<CalendarView>("month");
  const [anchor, setAnchor] = useState(() => new Date());
  const range = visibleRange(anchor, view);
  const query = useQuery({
    queryKey: ["dues", "calendar", range.from, range.to],
    queryFn: () => listDues("", "", "", range.from, range.to),
  });
  const items = query.data?.data ?? [];
  const byDay = useMemo(() => groupByDay(items), [items]);
  const days = view === "month" ? monthGrid(anchor) : view === "week" ? weekGrid(anchor) : [anchor];
  const todayKey = toDateKey(new Date());
  const selectedKey = toDateKey(anchor);
  const title = new Intl.DateTimeFormat(localeTag(locale), {
    day: view === "day" ? "numeric" : undefined,
    month: "long",
    year: "numeric",
  }).format(anchor);
  const error = query.error instanceof Error ? query.error.message : null;

  return (
    <section className="space-y-4">
      <PageHeader title={t("due.calendar")} description={t("due.calendarHint")}>
        <MaintenanceNav active="calendar" />
      </PageHeader>
      <div className="flex flex-wrap items-center gap-2">
        <Button type="button" variant="outline" onClick={() => setAnchor(shiftAnchor(anchor, view, -1))}>
          {t("due.prev")}
        </Button>
        <Button type="button" variant="outline" onClick={() => setAnchor(new Date())}>
          {t("due.today")}
        </Button>
        <Button type="button" variant="outline" onClick={() => setAnchor(shiftAnchor(anchor, view, 1))}>
          {t("due.next")}
        </Button>
        <p className="px-2 text-sm font-medium text-primary">{title}</p>
        <div className="ml-auto flex gap-1">
          {VIEWS.map((item) => (
            <Button
              key={item}
              type="button"
              size="sm"
              variant={view === item ? "default" : "outline"}
              onClick={() => setView(item)}
            >
              {t(`due.views.${item}`)}
            </Button>
          ))}
        </div>
      </div>
      {error ? <p className="text-sm text-destructive">{t(error)}</p> : null}
      {view === "day" ? (
        <DayList
          items={byDay[selectedKey] ?? []}
          onOpen={(due) => router.push(`/uavs/${due.uav}`)}
        />
      ) : (
        <div className="overflow-hidden rounded-lg border bg-card">
          <div className="grid grid-cols-7 border-b bg-muted/50 text-center text-xs font-medium text-muted-foreground">
            {WEEKDAY_KEYS.map((key) => (
              <div key={key} className="px-2 py-2">
                {t(`due.weekday.${key}`)}
              </div>
            ))}
          </div>
          <div className={cn("grid grid-cols-7", view === "week" ? "auto-rows-[12rem]" : "auto-rows-[8rem]")}>
            {days.map((day) => {
              const key = toDateKey(day);
              const inMonth = day.getMonth() === anchor.getMonth();
              const dayItems = byDay[key] ?? [];
              return (
                <div
                  key={key}
                  className={cn(
                    "flex min-h-0 flex-col gap-1 border-b border-r p-1.5",
                    view === "month" && !inMonth && "bg-muted/30 text-muted-foreground",
                    key === todayKey && "bg-info/5",
                  )}
                >
                  <button
                    type="button"
                    className={cn(
                      "flex size-6 items-center justify-center rounded-full text-xs",
                      key === todayKey && "bg-primary text-primary-foreground",
                    )}
                    onClick={() => {
                      setAnchor(day);
                      setView("day");
                    }}
                  >
                    {day.getDate()}
                  </button>
                  <div className="flex min-h-0 flex-1 flex-col gap-1 overflow-hidden">
                    {dayItems.slice(0, view === "week" ? 6 : 3).map((due) => (
                      <button
                        key={due.id}
                        type="button"
                        className={cn("truncate rounded px-1 py-0.5 text-left text-[11px]", DUE_TONE[due.status])}
                        onClick={() => router.push(`/uavs/${due.uav}`)}
                      >
                        {due.uav_registration} {due.task_code}
                      </button>
                    ))}
                    {dayItems.length > (view === "week" ? 6 : 3) ? (
                      <button
                        type="button"
                        className="text-left text-[11px] text-muted-foreground"
                        onClick={() => {
                          setAnchor(day);
                          setView("day");
                        }}
                      >
                        +{dayItems.length - (view === "week" ? 6 : 3)}
                      </button>
                    ) : null}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </section>
  );
}

function DayList({
  items,
  onOpen,
}: {
  items: MaintenanceDue[];
  onOpen: (due: MaintenanceDue) => void;
}) {
  const { t } = useI18n();
  return (
    <div className="overflow-hidden rounded-lg border bg-card">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>{t("uav.registration")}</TableHead>
            <TableHead>{t("template.taskCode")}</TableHead>
            <TableHead>{t("template.taskName")}</TableHead>
            <TableHead>{t("due.status")}</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.length === 0 ? (
            <TableRow>
              <TableCell className="text-muted-foreground" colSpan={4}>
                {t("due.calendarEmpty")}
              </TableCell>
            </TableRow>
          ) : (
            items.map((due) => (
              <TableRow key={due.id} className="cursor-pointer" onClick={() => onOpen(due)}>
                <TableCell>{due.uav_registration}</TableCell>
                <TableCell>{due.task_code}</TableCell>
                <TableCell>{due.task_name}</TableCell>
                <TableCell>
                  <DueBadge status={due.status} />
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
