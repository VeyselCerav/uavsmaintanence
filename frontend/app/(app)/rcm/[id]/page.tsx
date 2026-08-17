"use client";

import { useParams } from "next/navigation";

import { RCMBuilder } from "@/features/rcm/rcm-builder";

export default function RCMDetailPage() {
  const params = useParams<{ id: string }>();
  return <RCMBuilder rcmId={params.id} />;
}
