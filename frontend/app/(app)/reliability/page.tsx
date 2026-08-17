"use client";

import { useQuery } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { ReliabilityMetricsView } from "@/features/reliability/reliability-metrics";
import { PageHeader } from "@/components/system/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { NativeSelect } from "@/components/ui/native-select";
import { useI18n } from "@/lib/i18n-context";
import { getReliability } from "@/services/reliability";
import { listClasses, listUAVs } from "@/services/uavs";
import type { ReliabilityScope } from "@/types/reliability";

export default function ReliabilityPage() {
  const { t } = useI18n();
  const [scope, setScope] = useState<ReliabilityScope>("fleet");
  const [scopeId, setScopeId] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [applied, setApplied] = useState({
    scope: "fleet" as ReliabilityScope,
    scopeId: "",
    from: "",
    to: "",
  });
  const classes = useQuery({ queryKey: ["uav-classes"], queryFn: listClasses });
  const uavs = useQuery({ queryKey: ["uavs", ""], queryFn: () => listUAVs() });
  const query = useQuery({
    queryKey: ["reliability", applied],
    queryFn: () =>
      getReliability({
        scope: applied.scope,
        scopeId: applied.scopeId,
        from: applied.from,
        to: applied.to,
      }),
    enabled: applied.scope === "fleet" || Boolean(applied.scopeId),
  });
  const error = query.error instanceof Error ? query.error.message : null;

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setApplied({ scope, scopeId, from, to });
  }

  return (
    <section className="space-y-4">
      <PageHeader title={t("reliability.title")} description={t("reliability.hint")} />
      <form onSubmit={onSubmit} className="flex flex-wrap gap-2">
        <NativeSelect
          className="w-40"
          value={scope}
          onChange={(event) => {
            setScope(event.target.value as ReliabilityScope);
            setScopeId("");
          }}
        >
          <option value="fleet">{t("reliability.fleet")}</option>
          <option value="class">{t("uav.class")}</option>
          <option value="uav">{t("navigation.fleet")}</option>
        </NativeSelect>
        {scope === "class" ? (
          <NativeSelect
            className="w-56"
            value={scopeId}
            onChange={(event) => setScopeId(event.target.value)}
          >
            <option value="" />
            {(classes.data?.data ?? []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </NativeSelect>
        ) : null}
        {scope === "uav" ? (
          <NativeSelect
            className="w-56"
            value={scopeId}
            onChange={(event) => setScopeId(event.target.value)}
          >
            <option value="" />
            {(uavs.data?.data ?? []).map((item) => (
              <option key={item.id} value={item.id}>
                {item.registration_number}
              </option>
            ))}
          </NativeSelect>
        ) : null}
        <Input type="date" className="w-40" value={from} onChange={(event) => setFrom(event.target.value)} />
        <Input type="date" className="w-40" value={to} onChange={(event) => setTo(event.target.value)} />
        <Button type="submit">{t("common.search")}</Button>
      </form>
      {error ? <p className="text-sm text-destructive">{t(error)}</p> : null}
      {query.data ? <ReliabilityMetricsView metrics={query.data} /> : null}
      {query.isLoading ? <p className="text-sm text-muted-foreground">{t("common.loading")}</p> : null}
    </section>
  );
}
