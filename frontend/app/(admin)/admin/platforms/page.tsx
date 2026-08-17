"use client";

import { CatalogAdminPage } from "@/features/admin/catalog-admin-page";

export default function AdminPlatformsPage() {
  return (
    <CatalogAdminPage
      titleKey="admin.platforms"
      path="/platforms/"
      createPermission="platform.create"
    />
  );
}
