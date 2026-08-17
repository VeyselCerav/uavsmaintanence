"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { PageHeader } from "@/components/system/page-header";
import { UAVForm } from "@/features/uav/uav-form";
import { useI18n } from "@/lib/i18n-context";
import { getUAV } from "@/services/uavs";
import type { UAV } from "@/types/uav";

export default function EditUAVPage() {
  const { t } = useI18n();
  const params = useParams<{ id: string }>();
  const [uav, setUav] = useState<UAV | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void getUAV(params.id)
      .then(setUav)
      .catch((err: Error) => setError(err.message));
  }, [params.id]);

  if (error) {
    return <p className="text-sm text-destructive">{t(error)}</p>;
  }
  if (!uav) {
    return <p className="text-sm text-muted-foreground">{t("common.loading")}</p>;
  }

  return (
    <section>
      <PageHeader title={t("uav.edit")} />
      <UAVForm initial={uav} />
    </section>
  );
}
