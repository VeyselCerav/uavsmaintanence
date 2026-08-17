"use client";

import { useParams } from "next/navigation";

import { FMEABuilder } from "@/features/fmea/fmea-builder";

export default function FMEADetailPage() {
  const params = useParams<{ id: string }>();
  return <FMEABuilder fmeaId={params.id} />;
}
