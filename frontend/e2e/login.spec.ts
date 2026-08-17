import { expect, test, type Page } from "@playwright/test";

test.setTimeout(60_000);

async function loginAsAdmin(page: Page) {
  await page.goto("/login");
  await page.locator('input[type="email"]').fill("admin@local.test");
  await page.locator('input[type="password"]').fill("admin12345");
  await page.locator('button[type="submit"]').click();
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 30_000 });
}

test("login opens the dashboard", async ({ page }) => {
  await loginAsAdmin(page);
  await expect(page.getByRole("heading", { name: /filo özeti|fleet overview|donanma/i })).toBeVisible();
});

test("global search finds a demo UAV", async ({ page }) => {
  await loginAsAdmin(page);
  const search = page.getByPlaceholder(/ara|search|axtar/i);
  await search.fill("TR-UAV-001");
  await expect(page.getByRole("link", { name: /TR-UAV-001/i }).first()).toBeVisible();
});
