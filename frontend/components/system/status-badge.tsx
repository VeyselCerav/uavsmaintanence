"use client";

import { Badge } from "@/components/ui/badge";
import { useI18n } from "@/lib/i18n-context";
import { cn } from "@/lib/utils";
import type { FailureSeverity } from "@/types/failure";
import type { RPNBand } from "@/types/fmea";
import type { DueStatus } from "@/types/maintenance";
import type { UAVStatus } from "@/types/uav";
import type { WorkOrderStatus } from "@/types/work-order";

const TONE: Record<UAVStatus, string> = {
  READY: "border-transparent bg-success/15 text-success",
  MAINTENANCE: "border-transparent bg-warning/15 text-warning",
  GROUNDED: "border-transparent bg-danger/15 text-danger",
  RETIRED: "border-transparent bg-muted text-muted-foreground",
};

export const DUE_TONE: Record<DueStatus, string> = {
  NORMAL: "border-transparent bg-success/15 text-success",
  APPROACHING: "border-transparent bg-info/15 text-info",
  DUE: "border-transparent bg-warning/15 text-warning",
  OVERDUE: "border-transparent bg-danger/15 text-danger",
  CRITICAL: "border-transparent bg-danger text-white",
};

const SEVERITY_TONE: Record<FailureSeverity, string> = {
  LOW: "border-transparent bg-success/15 text-success",
  MEDIUM: "border-transparent bg-info/15 text-info",
  HIGH: "border-transparent bg-warning/15 text-warning",
  CRITICAL: "border-transparent bg-danger text-white",
};

const WO_TONE: Record<WorkOrderStatus, string> = {
  OPEN: "border-transparent bg-info/15 text-info",
  ASSIGNED: "border-transparent bg-info/15 text-info",
  IN_PROGRESS: "border-transparent bg-warning/15 text-warning",
  WAITING_PARTS: "border-transparent bg-warning/15 text-warning",
  COMPLETED: "border-transparent bg-success/15 text-success",
  CANCELLED: "border-transparent bg-muted text-muted-foreground",
};

export function StatusBadge({ status }: { status: UAVStatus }) {
  const { t } = useI18n();
  return <Badge className={cn("rounded-md", TONE[status])}>{t(`enums.uav_status.${status}`)}</Badge>;
}

export function DueBadge({ status }: { status: DueStatus }) {
  const { t } = useI18n();
  return <Badge className={cn("rounded-md", DUE_TONE[status])}>{t(`enums.due_status.${status}`)}</Badge>;
}

export function FailureSeverityBadge({ severity }: { severity: FailureSeverity }) {
  const { t } = useI18n();
  return (
    <Badge className={cn("rounded-md", SEVERITY_TONE[severity])}>
      {t(`enums.failure_severity.${severity}`)}
    </Badge>
  );
}

export function RPNBadge({ rpn, band }: { rpn: number | null; band: RPNBand | null }) {
  const { t } = useI18n();
  if (rpn == null || !band) {
    return <span>—</span>;
  }
  return (
    <Badge className={cn("rounded-md", SEVERITY_TONE[band])}>
      {rpn} · {t(`enums.rpn_band.${band}`)}
    </Badge>
  );
}

export function WorkOrderBadge({ status }: { status: WorkOrderStatus }) {
  const { t } = useI18n();
  return (
    <Badge className={cn("rounded-md", WO_TONE[status])}>{t(`enums.work_order_status.${status}`)}</Badge>
  );
}

const COMPONENT_TONE: Record<string, string> = {
  INSTALLED: "border-transparent bg-success/15 text-success",
  REMOVED: "border-transparent bg-muted text-muted-foreground",
  QUARANTINE: "border-transparent bg-warning/15 text-warning",
  SCRAPPED: "border-transparent bg-danger/15 text-danger",
};

export function ComponentBadge({ status }: { status: string }) {
  const { t } = useI18n();
  return (
    <Badge className={cn("rounded-md", COMPONENT_TONE[status] ?? "bg-muted")}>
      {t(`enums.component_status.${status}`)}
    </Badge>
  );
}

export function DemoBadge({ visible }: { visible: boolean }) {
  const { t } = useI18n();
  if (!visible) return null;
  return (
    <Badge variant="outline" className="rounded-md border-warning text-warning">
      {t("common.demo")}
    </Badge>
  );
}
