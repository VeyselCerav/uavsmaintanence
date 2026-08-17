export type CalendarView = "day" | "week" | "month";

function pad(value: number): string {
  return String(value).padStart(2, "0");
}

export function toDateKey(value: Date | string): string {
  const date = typeof value === "string" ? new Date(value) : value;
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

export function parseDateKey(key: string): Date {
  const [year, month, day] = key.split("-").map(Number);
  return new Date(year, (month ?? 1) - 1, day ?? 1);
}

export function addDays(date: Date, amount: number): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate() + amount);
}

export function startOfWeek(date: Date): Date {
  const weekday = date.getDay();
  const offset = weekday === 0 ? -6 : 1 - weekday;
  return addDays(date, offset);
}

export function monthGrid(anchor: Date): Date[] {
  const first = new Date(anchor.getFullYear(), anchor.getMonth(), 1);
  const start = startOfWeek(first);
  const last = new Date(anchor.getFullYear(), anchor.getMonth() + 1, 0);
  const end = addDays(startOfWeek(last), 6);
  const days: Date[] = [];
  for (let cursor = start; cursor <= end; cursor = addDays(cursor, 1)) {
    days.push(cursor);
  }
  return days;
}

export function weekGrid(anchor: Date): Date[] {
  const start = startOfWeek(anchor);
  return Array.from({ length: 7 }, (_, index) => addDays(start, index));
}

export function shiftAnchor(anchor: Date, view: CalendarView, direction: -1 | 1): Date {
  if (view === "day") {
    return addDays(anchor, direction);
  }
  if (view === "week") {
    return addDays(anchor, direction * 7);
  }
  return new Date(anchor.getFullYear(), anchor.getMonth() + direction, 1);
}

export function visibleRange(anchor: Date, view: CalendarView): { from: string; to: string } {
  if (view === "day") {
    const key = toDateKey(anchor);
    return { from: key, to: key };
  }
  const days = view === "week" ? weekGrid(anchor) : monthGrid(anchor);
  return { from: toDateKey(days[0]), to: toDateKey(days[days.length - 1]) };
}

export function localeTag(locale: string): string {
  if (locale === "az") return "az-AZ";
  if (locale === "en") return "en-US";
  return "tr-TR";
}
