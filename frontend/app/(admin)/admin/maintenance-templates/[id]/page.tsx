"use client";

import { useParams } from "next/navigation";

import { TemplateBuilder } from "@/features/maintenance/template-builder";

export default function EditTemplatePage() {
  const params = useParams<{ id: string }>();
  return <TemplateBuilder templateId={params.id} />;
}
