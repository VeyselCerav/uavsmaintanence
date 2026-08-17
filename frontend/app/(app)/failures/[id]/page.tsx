"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { PageHeader } from "@/components/system/page-header";
import { DemoBadge, FailureSeverityBadge } from "@/components/system/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useSessionUser } from "@/hooks/use-session-user";
import { hasPermission } from "@/lib/auth";
import { useI18n } from "@/lib/i18n-context";
import { ApiClientError } from "@/services/api";
import { getFailure, resolveFailure } from "@/services/failures";

export default function FailureDetailPage() {
  const { t } = useI18n();
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const user = useSessionUser();
  const queryClient = useQueryClient();
  const canResolve = hasPermission(user, "failure.update");
  const query = useQuery({
    queryKey: ["failure", params.id],
    queryFn: () => getFailure(params.id),
  });
  const failure = query.data;
  const mutation = useMutation({
    mutationFn: () => resolveFailure(params.id),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["failure", params.id] });
      await queryClient.invalidateQueries({ queryKey: ["failures"] });
      router.refresh();
    },
  });
  const error =
    mutation.error instanceof ApiClientError
      ? mutation.error.message_key
      : query.error instanceof Error
        ? query.error.message
        : null;

  if (!failure && !error) {
    return <p className="text-sm text-muted-foreground">{t("common.loading")}</p>;
  }
  if (!failure) {
    return <p className="text-sm text-destructive">{t(error ?? "errors.generic")}</p>;
  }

  return (
    <section className="space-y-6">
      <PageHeader title={failure.uav_registration}>
        <DemoBadge visible={failure.is_demo} />
        <FailureSeverityBadge severity={failure.severity} />
        <Button asChild variant="outline">
          <Link href="/failures">{t("common.back")}</Link>
        </Button>
        {canResolve && !failure.resolved_at ? (
          <Button type="button" onClick={() => mutation.mutate()} disabled={mutation.isPending}>
            {mutation.isPending ? t("common.loading") : t("failure.resolve")}
          </Button>
        ) : null}
      </PageHeader>
      {error ? <p className="text-sm text-destructive">{t(error)}</p> : null}
      {failure.is_demo ? <p className="text-sm text-warning">{t("failure.demoNote")}</p> : null}
      <Card>
        <CardContent className="grid grid-cols-2 gap-6 text-sm">
          <p>
            {t("uav.registration")}:{" "}
            <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
              <Link href={`/uavs/${failure.uav}`}>{failure.uav_registration}</Link>
            </Button>
          </p>
          <p>
            {t("failure.occurredAt")}: {new Date(failure.occurred_at).toLocaleString()}
          </p>
          <p>
            {t("failure.discovered")}: {t(`enums.discovered_during.${failure.discovered_during}`)}
          </p>
          <p>
            {t("failure.mode")}:{" "}
            {failure.failure_mode_code
              ? `${failure.failure_mode_code} — ${failure.failure_mode_name}`
              : "—"}
          </p>
          <p>
            {t("failure.component")}: {failure.component_name || "—"}
          </p>
          <p>
            {t("failure.downtime")}: {failure.downtime_hours}
          </p>
          <p>
            {t("failure.status")}:{" "}
            {failure.resolved_at ? t("failure.resolved") : t("failure.open")}
          </p>
          <p>
            {t("failure.resolvedAt")}:{" "}
            {failure.resolved_at ? new Date(failure.resolved_at).toLocaleString() : "—"}
          </p>
          <p>
            {t("workOrder.number")}:{" "}
            {failure.work_order ? (
              <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
                <Link href={`/work-orders/${failure.work_order}`}>{failure.work_order_number}</Link>
              </Button>
            ) : (
              "—"
            )}
          </p>
          <p className="col-span-2">
            {t("failure.description")}: {failure.description}
          </p>
        </CardContent>
      </Card>
    </section>
  );
}
