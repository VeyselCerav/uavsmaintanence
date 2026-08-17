"use client";

import { CatalogAdminPage } from "@/features/admin/catalog-admin-page";

export default function AdminMissionsPage() {
  return (
    <CatalogAdminPage
      titleKey="admin.missions"
      path="/missions/"
      createPermission="mission.create"
    />
  );
}
