"use client";

import { CatalogAdminPage } from "@/features/admin/catalog-admin-page";

export default function AdminClassesPage() {
  return (
    <CatalogAdminPage
      titleKey="admin.classes"
      path="/uav-classes/"
      createPermission="uav_class.create"
    />
  );
}
