"use client";

import { PageHeader } from "@/components/system/page-header";
import { FlightForm } from "@/features/flight/flight-form";
import { useI18n } from "@/lib/i18n-context";

export default function NewFlightPage() {
  const { t } = useI18n();
  return (
    <section>
      <PageHeader title={t("flight.new")} />
      <FlightForm />
    </section>
  );
}
