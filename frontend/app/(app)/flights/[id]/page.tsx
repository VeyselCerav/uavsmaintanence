"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { PageHeader } from "@/components/system/page-header";
import { DemoBadge } from "@/components/system/status-badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useSessionUser } from "@/hooks/use-session-user";
import { hasPermission } from "@/lib/auth";
import { useI18n } from "@/lib/i18n-context";
import { ApiClientError } from "@/services/api";
import { completeFlight, getFlight } from "@/services/flights";

export default function FlightDetailPage() {
  const { t } = useI18n();
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const user = useSessionUser();
  const queryClient = useQueryClient();
  const canComplete = hasPermission(user, "flight.complete");
  const query = useQuery({
    queryKey: ["flight", params.id],
    queryFn: () => getFlight(params.id),
  });
  const flight = query.data;
  const mutation = useMutation({
    mutationFn: () => completeFlight(params.id),
    onSuccess: async (saved) => {
      await queryClient.invalidateQueries({ queryKey: ["flight", params.id] });
      await queryClient.invalidateQueries({ queryKey: ["flights"] });
      await queryClient.invalidateQueries({ queryKey: ["uav", saved.uav] });
      await queryClient.invalidateQueries({ queryKey: ["dues", saved.uav] });
      router.refresh();
    },
  });
  const error =
    mutation.error instanceof ApiClientError
      ? mutation.error.message_key
      : query.error instanceof Error
        ? query.error.message
        : null;

  if (!flight && !error) {
    return <p className="text-sm text-muted-foreground">{t("common.loading")}</p>;
  }
  if (!flight) {
    return <p className="text-sm text-destructive">{t(error ?? "errors.generic")}</p>;
  }

  return (
    <section className="space-y-6">
      <PageHeader title={flight.flight_number}>
        <DemoBadge visible={flight.is_demo} />
        <Button asChild variant="outline">
          <Link href="/flights">{t("common.back")}</Link>
        </Button>
        {canComplete && !flight.counters_applied ? (
          <Button type="button" onClick={() => mutation.mutate()} disabled={mutation.isPending}>
            {mutation.isPending ? t("common.loading") : t("flight.complete")}
          </Button>
        ) : null}
      </PageHeader>
      {error ? <p className="text-sm text-destructive">{t(error)}</p> : null}
      {flight.is_demo ? <p className="text-sm text-warning">{t("flight.demoNote")}</p> : null}
      <Card>
        <CardContent className="grid grid-cols-2 gap-6 text-sm">
          <p>
            {t("uav.registration")}:{" "}
            <Button asChild variant="link" size="sm" className="h-auto px-0 text-info">
              <Link href={`/uavs/${flight.uav}`}>{flight.uav_registration}</Link>
            </Button>
          </p>
          <p>
            {t("uav.mission")}: {flight.mission_name}
          </p>
          <p>
            {t("flight.operator")}: {flight.operator_name || "—"}
          </p>
          <p>
            {t("flight.flownOn")}: {flight.flown_on}
          </p>
          <p>
            {t("flight.start")}: {new Date(flight.start_at).toLocaleString()}
          </p>
          <p>
            {t("flight.end")}: {new Date(flight.end_at).toLocaleString()}
          </p>
          <p>
            {t("flight.duration")}: {flight.duration_hours}
          </p>
          <p>
            {t("flight.result")}: {t(`enums.flight_result.${flight.result}`)}
          </p>
          <p>
            {t("flight.counters")}: {flight.counters_applied ? t("flight.applied") : t("flight.pending")}
          </p>
          <p>
            {t("uav.notes")}: {flight.notes || "—"}
          </p>
        </CardContent>
      </Card>
    </section>
  );
}
