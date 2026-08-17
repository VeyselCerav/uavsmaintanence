"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { PageHeader } from "@/components/system/page-header";
import { DemoBadge } from "@/components/system/status-badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useSessionUser } from "@/hooks/use-session-user";
import { hasPermission } from "@/lib/auth";
import { useI18n } from "@/lib/i18n-context";
import { listFlights } from "@/services/flights";

export default function FlightsPage() {
  const { t } = useI18n();
  const user = useSessionUser();
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const canCreate = hasPermission(user, "flight.create");
  const query = useQuery({
    queryKey: ["flights", appliedSearch],
    queryFn: () => listFlights(appliedSearch),
  });
  const items = query.data?.data ?? [];
  const error = query.error instanceof Error ? query.error.message : null;

  function onSearch(event: FormEvent) {
    event.preventDefault();
    setAppliedSearch(search);
  }

  return (
    <section>
      <PageHeader title={t("flight.title")}>
        {canCreate ? (
          <Button asChild>
            <Link href="/flights/new">{t("flight.new")}</Link>
          </Button>
        ) : null}
      </PageHeader>
      <form onSubmit={onSearch} className="mb-4 flex gap-2">
        <Input
          className="w-72"
          placeholder={t("common.search")}
          value={search}
          onChange={(event) => setSearch(event.target.value)}
        />
        <Button type="submit" variant="outline">
          {t("common.search")}
        </Button>
      </form>
      {error ? <p className="mb-3 text-sm text-destructive">{t(error)}</p> : null}
      <div className="overflow-hidden rounded-lg border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t("flight.number")}</TableHead>
              <TableHead>{t("uav.registration")}</TableHead>
              <TableHead>{t("flight.flownOn")}</TableHead>
              <TableHead>{t("flight.duration")}</TableHead>
              <TableHead>{t("flight.result")}</TableHead>
              <TableHead>{t("flight.counters")}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 ? (
              <TableRow>
                <TableCell className="text-muted-foreground" colSpan={6}>
                  {t("flight.empty")}
                </TableCell>
              </TableRow>
            ) : (
              items.map((item) => (
                <TableRow
                  key={item.id}
                  className="cursor-pointer"
                  onClick={() => router.push(`/flights/${item.id}`)}
                >
                  <TableCell>
                    <span className="mr-2">{item.flight_number}</span>
                    <DemoBadge visible={item.is_demo} />
                  </TableCell>
                  <TableCell>{item.uav_registration}</TableCell>
                  <TableCell>{item.flown_on}</TableCell>
                  <TableCell>{item.duration_hours}</TableCell>
                  <TableCell>{t(`enums.flight_result.${item.result}`)}</TableCell>
                  <TableCell>
                    {item.counters_applied ? t("flight.applied") : t("flight.pending")}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </section>
  );
}
