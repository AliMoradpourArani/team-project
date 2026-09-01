import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

const studentPassword = "e2e-student-pass";
const professorPassword = "e2e-professor-pass";

async function signIn(page: Page, username: string, password: string) {
  await page.goto("/");
  await page.getByLabel("Username").fill(username);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();
}

test("student signs in and manages only their activity", async ({ page }) => {
  const title = `E2E activity ${Date.now()}`;
  await signIn(page, "hossein", studentPassword);

  await expect(page.getByRole("heading", { name: "Hossein", level: 1 })).toBeVisible();
  await expect(page).toHaveURL(/\/users\/hossein$/);

  await page.getByLabel("Date").fill("2026-09-01");
  await page.getByLabel("Title").fill(title);
  await page.getByRole("button", { name: "Add activity" }).click();

  const timelineItem = page.locator(".timeline-item").filter({ hasText: title });
  await expect(timelineItem).toBeVisible();

  const calendarDay = page.getByRole("button", { name: /^2026-09-01,/ });
  await calendarDay.click();
  await expect(page.locator(".calendar-detail")).toContainText(title);

  page.once("dialog", (dialog) => dialog.accept());
  await timelineItem.getByRole("button", { name: "Delete" }).click();
  await expect(page.locator(".timeline-item").filter({ hasText: title })).toHaveCount(0);

  await page.getByRole("button", { name: "Sign out" }).click();
  await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
});

test("professor sees team overview and a read-only member drill-down", async ({ page }) => {
  await signIn(page, "professor", professorPassword);

  await expect(page).toHaveURL(/\/professor$/);
  await expect(page.getByText("Professor dashboard")).toBeVisible();
  await expect(page.getByRole("heading", { name: /Team overview/i, level: 1 })).toBeVisible();
  await expect(page.locator(".professor-member-row")).toHaveCount(3);

  await page.locator(".professor-member-row").filter({ hasText: "Hossein" }).click();
  await expect(page.getByText("Professor · read-only member view")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Hossein", level: 1 })).toBeVisible();
  await expect(page.getByRole("button", { name: "Add activity" })).toHaveCount(0);
  await expect(page.locator(".item-actions")).toHaveCount(0);
});
