"use client";

import { CatalogAdminPage } from "@/features/admin/catalog-admin-page";

export default function AdminSkillsPage() {
  return (
    <CatalogAdminPage
      titleKey="admin.skills"
      path="/skills/"
      createPermission="skill.create"
    />
  );
}
