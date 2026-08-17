"use client";

import Link from "next/link";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const TONE = {
  default: "text-foreground",
  success: "text-success",
  warning: "text-warning",
  danger: "text-danger",
  info: "text-info",
} as const;

export function MetricCard({
  label,
  value,
  href,
  tone = "default",
}: {
  label: string;
  value: number | string;
  href?: string;
  tone?: keyof typeof TONE;
}) {
  const card = (
    <Card size="sm" className={href ? "transition-colors hover:bg-muted/40" : undefined}>
      <CardContent className="space-y-1">
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
        <p className={cn("text-2xl font-semibold tabular-nums", TONE[tone])}>{value}</p>
      </CardContent>
    </Card>
  );
  if (!href) {
    return card;
  }
  return <Link href={href}>{card}</Link>;
}
