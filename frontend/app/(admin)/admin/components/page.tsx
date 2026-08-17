"use client";

import { CatalogAdminPage } from "@/features/admin/catalog-admin-page";

export default function AdminComponentsPage() {
  return (
    <CatalogAdminPage
      titleKey="admin.components"
      path="/component-types/"
      createPermission="component.create"
    />
  );
}
